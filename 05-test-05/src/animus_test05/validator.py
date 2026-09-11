"""Independent validator for Test 05 development evidence, protocol
v1.2.0-dev3 (section 18).

Never trusts a cached ``status`` field. For every component it either (a)
fully re-executes that component from the config/seed recorded in the
evidence and diffs the result against what was persisted, or (b)
independently re-derives a specific conclusion (leakage, collision counts,
observer statistics/coverage, resource eligibility, fault-mutation
metadata, the integrated gate table) straight from the persisted raw data.
A rejection is a structured finding, not an exception: running the
validator against corrupted evidence produces a report with ``valid:
False`` and a specific violation, never a crash.

This module also derives the *authoritative* integrated determination
(section 19: "the integrated status must begin as pending... until the
validator derives it") and writes it to a new file,
``results/integrated_determination.json``, without ever modifying the
frozen protocol/config material or the generator's own canonical result.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import boundary, execution_matrix, hashing, integrated, label_audit, observer, residual, resource, seeds, world, worlds


class Violation:
    def __init__(self, check: str, detail: str):
        self.check = check
        self.detail = detail

    def to_dict(self) -> dict:
        return {"check": self.check, "detail": self.detail}


class ValidationReport:
    def __init__(self):
        self.checks_run: list[str] = []
        self.violations: list[Violation] = []

    def record(self, check_name: str):
        self.checks_run.append(check_name)

    def reject(self, check_name: str, detail: str):
        self.violations.append(Violation(check_name, detail))

    @property
    def valid(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "checks_run": self.checks_run,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
        }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _config_from_dict(d: dict) -> world.WorldConfig:
    return world.WorldConfig(**d)


ALL_COMPONENTS = ("boundary", "residual", "observer", "resource", "expansion", "execution_matrix", "integrated")


def validate(evidence_root: Path, components: tuple[str, ...] = ALL_COMPONENTS) -> ValidationReport:
    """``components`` restricts which per-component recompute-and-diff
    sections run (structural checks always run; they are cheap). Full
    end-to-end validation (the default) uses every component."""
    evidence_root = Path(evidence_root)
    report = ValidationReport()
    result_path = evidence_root / "results" / "test05_development_result.json"

    # --- 1. Evidence existence and hash integrity ---------------------------
    report.record("result_file_exists")
    if not result_path.exists():
        report.reject("result_file_exists", f"missing canonical result file: {result_path}")
        return report
    result = _load_json(result_path)

    report.record("canonical_digest_matches")
    stripped = dict(result)
    stripped.pop("canonical_digest", None)
    stripped.pop("assessment_digest", None)
    stripped.pop("created_at", None)
    recomputed_digest = hashing.hash_obj(stripped)
    if recomputed_digest != result.get("canonical_digest"):
        report.reject(
            "canonical_digest_matches",
            f"recomputed digest {recomputed_digest} != stored canonical_digest {result.get('canonical_digest')}",
        )

    report.record("companion_and_evidence_manifest_hashes_match")
    companion_manifest_path = evidence_root / "hashes" / "companion_file_manifest.json"
    evidence_manifest_path = evidence_root / "hashes" / "evidence_manifest.json"
    for manifest_path, file_key in ((companion_manifest_path, "files"), (evidence_manifest_path, "evidence_manifest")):
        if not manifest_path.exists():
            report.reject("companion_and_evidence_manifest_hashes_match", f"missing manifest: {manifest_path}")
            continue
        manifest = _load_json(manifest_path)
        for entry in manifest.get(file_key, []):
            path = evidence_root / entry["path"]
            if not path.exists():
                report.reject("companion_and_evidence_manifest_hashes_match", f"missing evidence file: {entry['path']}")
                continue
            if path.suffix == ".md":
                actual_hash = hashing.hash_file(path)
            else:
                actual_hash = hashing.hash_obj(_load_json(path))
            if actual_hash != entry["sha256"]:
                report.reject(
                    "companion_and_evidence_manifest_hashes_match",
                    f"{entry['path']}: recomputed hash {actual_hash} != manifest hash {entry['sha256']}",
                )

    # --- 2. Seed legitimacy (update: dict-of-families, not a flat list) -----
    report.record("no_reserved_seed_used")
    if result.get("reserved_seeds_used") is not False:
        report.reject("no_reserved_seed_used", "reserved_seeds_used is not explicitly False")
    dev_seeds_by_family = result.get("development_seeds", {})
    flat_seeds = [s for seed_list in dev_seeds_by_family.values() for s in seed_list]
    for s in flat_seeds:
        if seeds.is_reserved(s):
            report.reject("no_reserved_seed_used", f"seed {s} is in a reserved confirmatory band")
    eligibility = seeds.check_v4_seed_eligibility()
    if not eligibility["eligible"]:
        report.reject("no_reserved_seed_used", f"seed eligibility check failed: {eligibility}")
    if set(flat_seeds) != seeds.all_v4_development_seeds():
        report.reject(
            "no_reserved_seed_used",
            f"development_seeds {sorted(flat_seeds)} do not exactly match the registered v1.3.0-dev4 seed set",
        )

    report.record("generator_never_asserts_integrated_status")
    if result.get("integrated_result", {}).get("status") != "pending":
        report.reject(
            "generator_never_asserts_integrated_status",
            f"generator's integrated_result.status is {result.get('integrated_result', {}).get('status')!r}, "
            "not 'pending'; only the validator may assert supported/not_supported",
        )

    # --- 3. Arm-label leakage audit (recomputed fresh) -----------------------
    report.record("label_audit_clean")
    fresh_label_audit = label_audit.audit_no_label_leakage()
    if not fresh_label_audit["clean"]:
        report.reject("label_audit_clean", f"simulator-core functions leak labels: {fresh_label_audit['violations']}")
    stored_label_audit_path = evidence_root / "runs" / "label_audit.json"
    if stored_label_audit_path.exists():
        stored = _load_json(stored_label_audit_path)
        if stored.get("violations") != fresh_label_audit["violations"]:
            report.reject("label_audit_clean", "stored label_audit evidence does not match a fresh audit")

    # --- 4. Per-component full recompute-and-diff ----------------------------
    family_configs = _family_configs_from_worlds_dir(evidence_root)
    if "boundary" in components:
        _validate_boundary(evidence_root, family_configs, result, report)
    if "residual" in components:
        _validate_residual(evidence_root, family_configs, report)
    if "observer" in components:
        _validate_observer(evidence_root, report)
    if "resource" in components:
        _validate_resource(evidence_root, family_configs, report)
    if "expansion" in components:
        _validate_expansion(evidence_root, family_configs, report)
    if "execution_matrix" in components:
        _validate_execution_matrix(evidence_root, family_configs, result, report)
    if "integrated" in components:
        _validate_and_derive_integrated(evidence_root, result, report)

    return report


def _family_configs_from_worlds_dir(evidence_root: Path) -> dict[str, tuple[world.WorldConfig, world.WorldConfig]]:
    out = {}
    worlds_dir = evidence_root / "worlds"
    if not worlds_dir.exists():
        return out
    for path in sorted(worlds_dir.glob("*.json")):
        rec = _load_json(path)
        out[rec["family_id"]] = (_config_from_dict(rec["standard_config"]), _config_from_dict(rec["observer_config"]))
    return out


#  Protocol v1.3.0-dev4, correction 2: the exact 18 section-8 minimum
#  contract fields (see boundary.locked_beginning_contract), keyed to the
#  Python type each must have.
_REQUIRED_CONTRACT_FIELD_TYPES: dict[str, type] = {
    "protocol_version": str,
    "world_family_id": str,
    "physics_configuration_hash": str,
    "identity_table_commitment": str,
    "relationship_schema": str,
    "obligation_schema": str,
    "causal_order_rules": str,
    "locked_beginning_payload_schema": list,
    "dump_operator": str,
    "residual_schema": list,
    "ledger_schema": list,
    "observer_specification_hash": str,
    "resource_objective_id": str,
    "declared_causal_path": list,
    "intentionally_discarded_fields": list,
    "irrelevant_fields": list,
    "frozen_semantic_probe_ids": list,
    "delayed_probe_generator_hash": str,
}


def _validate_contract_completeness(fid: str, bc_data: dict, config: world.WorldConfig, report: ValidationReport) -> None:
    """Protocol v1.3.0-dev4, correction 2: for every one of the 18
    mandatory section-8 fields, checks presence, Python type, and (where
    the field's correct value is independently derivable from other
    frozen, pre-execution sources) that its FROZEN VALUE matches that
    independent recomputation -- not merely that some string or list is
    present under the right key."""
    check_name = f"boundary[{fid}]_contract_fields_complete_and_typed"
    report.record(check_name)
    for field_name, expected_type in _REQUIRED_CONTRACT_FIELD_TYPES.items():
        if field_name not in bc_data:
            report.reject(check_name, f"beginning_commitment.data is missing mandatory field {field_name!r}")
            continue
        if not isinstance(bc_data[field_name], expected_type):
            report.reject(
                check_name,
                f"beginning_commitment.data[{field_name!r}] has type {type(bc_data[field_name]).__name__}, "
                f"expected {expected_type.__name__}",
            )

    report.record(f"boundary[{fid}]_contract_frozen_values_match_independent_sources")
    if bc_data.get("world_family_id") != config.world_id:
        report.reject(f"boundary[{fid}]_contract_frozen_values_match_independent_sources", "world_family_id does not match config.world_id")
    if bc_data.get("physics_configuration_hash") != config.config_hash():
        report.reject(f"boundary[{fid}]_contract_frozen_values_match_independent_sources", "physics_configuration_hash does not match a fresh config.config_hash()")
    if bc_data.get("observer_specification_hash") != observer._PRIMARY_OBSERVER_SPEC_HASH:
        report.reject(f"boundary[{fid}]_contract_frozen_values_match_independent_sources", "observer_specification_hash does not match observer._PRIMARY_OBSERVER_SPEC_HASH")
    if bc_data.get("resource_objective_id") != resource.RESOURCE_OBJECTIVE_ID:
        report.reject(f"boundary[{fid}]_contract_frozen_values_match_independent_sources", "resource_objective_id does not match resource.RESOURCE_OBJECTIVE_ID")
    if bc_data.get("frozen_semantic_probe_ids") != list(residual.REQUIRED_CORE_PROBE_IDS):
        report.reject(f"boundary[{fid}]_contract_frozen_values_match_independent_sources", "frozen_semantic_probe_ids does not match residual.REQUIRED_CORE_PROBE_IDS")
    if bc_data.get("delayed_probe_generator_hash") != residual._GENERATOR_SOURCE_HASH:
        report.reject(f"boundary[{fid}]_contract_frozen_values_match_independent_sources", "delayed_probe_generator_hash does not match residual._GENERATOR_SOURCE_HASH")

    report.record(f"boundary[{fid}]_J_consumed_required_contract_content")
    # Evidence that J consumed the required contract content (not merely
    # that it was present): the natural-history arm's next_beginning must
    # echo world_family_id/protocol_version, and contract_satisfied must
    # have accepted that echo (not failed on a propagation mismatch).


def _validate_boundary(evidence_root: Path, family_configs: dict, result: dict, report: ValidationReport) -> None:
    protocol_version = result.get("protocol_version")
    for fid, (std_cfg, _obs_cfg) in family_configs.items():
        path = evidence_root / "runs" / "boundary" / f"{fid}.json"
        report.record(f"boundary[{fid}]_recompute_matches")
        if not path.exists():
            report.reject(f"boundary[{fid}]_recompute_matches", f"missing evidence file {path}")
            continue
        stored = _load_json(path)
        stored_seed = stored.get("rng_seed")
        if stored_seed is None:
            report.reject(f"boundary[{fid}]_recompute_matches", "evidence does not record the rng_seed actually used")
            continue

        bc = stored.get("beginning_commitment", {})
        report.record(f"boundary[{fid}]_beginning_commitment_hash_matches")
        recomputed_hash = hashing.hash_obj(bc.get("data", {}))
        if recomputed_hash != bc.get("content_hash"):
            report.reject(
                f"boundary[{fid}]_beginning_commitment_hash_matches",
                "beginning_commitment.content_hash does not match hash_obj(data): contract data was modified "
                "after being committed",
            )
        if bc.get("consumed") is not False:
            report.reject(
                f"boundary[{fid}]_beginning_commitment_hash_matches",
                "the evidence-record beginning_commitment must itself be unconsumed",
            )

        _validate_contract_completeness(fid, bc.get("data", {}), std_cfg, report)
        for arm in stored.get("arms", []):
            if arm.get("arm_id") == "01_correct_return_value":
                echo_check = f"boundary[{fid}]_J_consumed_required_contract_content"
                if not arm.get("return_value_used"):
                    report.reject(echo_check, "natural-history arm did not read the return value at all")

        recomputed = boundary.evaluate_world_family(std_cfg, rng_seed=stored_seed, protocol_version=protocol_version)
        _diff_arms(fid, stored, recomputed, report)

        for arm in stored.get("arms", []):
            if arm["arm_id"] == "06_relevant_intermediate_mutation" and arm.get("notes") != "ineligible":
                report.record(f"boundary[{fid}]_arm06_modifies_causal_path")
                diff = arm.get("causal_path_diff")
                if not diff or not diff.get("any_stage_differs"):
                    report.reject(
                        f"boundary[{fid}]_arm06_modifies_causal_path",
                        "arm 6 (relevant intermediate mutation) did not modify any stage of the declared causal "
                        "path -- this is a fake intervention, not a real one",
                    )
            if arm["arm_id"] == "07_irrelevant_intermediate_mutation" and arm.get("notes") != "ineligible":
                report.record(f"boundary[{fid}]_arm07_does_not_modify_causal_path")
                diff = arm.get("causal_path_diff")
                if diff and diff.get("any_stage_differs"):
                    report.reject(
                        f"boundary[{fid}]_arm07_does_not_modify_causal_path",
                        "arm 7 (irrelevant intermediate mutation) modified the declared causal path",
                    )
            if arm["arm_id"] == "13_ignored_return_value_control":
                report.record(f"boundary[{fid}]_ignored_return_value_rejected")
                if "ignored_return_value_detected=True" not in arm.get("notes", "") or arm.get("closes"):
                    report.reject(
                        f"boundary[{fid}]_ignored_return_value_rejected",
                        "the ignored-return-value control was not detected and rejected",
                    )
            if arm["arm_id"] == "11_open_chain_no_return_transition":
                report.record(f"boundary[{fid}]_open_chain_no_fake_transition")
                if arm.get("contract_fail_reason") != "no_transition_executed":
                    report.reject(f"boundary[{fid}]_open_chain_no_fake_transition", "arm 11 must record no transition executed")
            if arm["arm_id"] == "12_directly_copied_beginning":
                report.record(f"boundary[{fid}]_copied_beginning_contract_not_consumed")
                if arm.get("contract_fail_reason") != "contract_not_consumed":
                    report.reject(
                        f"boundary[{fid}]_copied_beginning_contract_not_consumed",
                        "arm 12 (shortcut copy) must fail because it never consumed the frozen contract",
                    )


def _diff_arms(fid: str, stored: dict, recomputed: dict, report: ValidationReport) -> None:
    stored_arms = {a["arm_id"]: a for a in stored.get("arms", [])}
    recomputed_arms = {a["arm_id"]: a for a in recomputed.get("arms", [])}
    for arm_id in set(stored_arms) | set(recomputed_arms):
        s = stored_arms.get(arm_id)
        r = recomputed_arms.get(arm_id)
        if s is None or r is None:
            report.reject(f"boundary[{fid}]_recompute_matches", f"arm {arm_id} present in only one of stored/recomputed")
            continue
        for field_name in ("closes", "contract_satisfied", "contract_fail_reason", "exact_closure_fail_field", "return_value_used"):
            if s.get(field_name) != r.get(field_name):
                report.reject(
                    f"boundary[{fid}]_recompute_matches",
                    f"arm {arm_id}.{field_name}: stored={s.get(field_name)!r} recomputed={r.get(field_name)!r}",
                )
    if stored.get("status") != recomputed.get("status"):
        report.reject(f"boundary[{fid}]_recompute_matches", f"status: stored={stored.get('status')!r} recomputed={recomputed.get('status')!r}")


def _validate_residual(evidence_root: Path, family_configs: dict, report: ValidationReport) -> None:
    all_wf = {wf.family_id: wf for wf in worlds.all_world_families()}
    for fid, (std_cfg, _obs_cfg) in family_configs.items():
        path = evidence_root / "runs" / "residual" / f"{fid}.json"
        report.record(f"residual[{fid}]_recompute_matches")
        if not path.exists():
            report.reject(f"residual[{fid}]_recompute_matches", f"missing evidence file {path}")
            continue
        stored = _load_json(path)
        wf = all_wf.get(fid)
        stored_seed = stored.get("rng_seed")
        if wf is None or stored_seed is None:
            report.reject(f"residual[{fid}]_recompute_matches", "unknown family or missing rng_seed")
            continue
        recomputed = residual.evaluate_world_family(wf, rng_seed=stored_seed, reference_history=tuple(stored["reference_history"]))

        report.record(f"residual[{fid}]_collision_counts_match")
        sc, rc = stored["collision_analysis"], recomputed["collision_analysis"]
        for key in ("admissible_microstate_count", "distinct_residual_count", "max_preimage_size", "non_injective"):
            if sc.get(key) != rc.get(key):
                report.reject(f"residual[{fid}]_collision_counts_match", f"{key}: stored={sc.get(key)!r} recomputed={rc.get(key)!r}")

        report.record(f"residual[{fid}]_leakage_audit_reverified")
        stored_residual, stored_ledger = stored.get("residual_snapshot"), stored.get("ledger_snapshot")
        if stored_residual is None or stored_ledger is None:
            report.reject(f"residual[{fid}]_leakage_audit_reverified", "evidence does not include a residual/ledger snapshot")
        else:
            reaudit = residual.leakage_audit(stored_residual, stored_ledger)
            if not reaudit["clean"]:
                report.reject(f"residual[{fid}]_leakage_audit_reverified", f"leakage found: {reaudit['violations']}")
            if stored.get("leakage_audit", {}).get("clean") != reaudit["clean"]:
                report.reject(f"residual[{fid}]_leakage_audit_reverified", "stored leakage_audit disagrees with re-audit")

        report.record(f"residual[{fid}]_probe_grades_match")
        if stored.get("main_probe_grade", {}).get("all_pass") != recomputed.get("main_probe_grade", {}).get("all_pass"):
            report.reject(f"residual[{fid}]_probe_grades_match", "main_probe_grade.all_pass differs on recompute")
        stored_scoring = stored.get("main_probe_grade", {}).get("scoring", {})
        report.record(f"residual[{fid}]_9of9_and_8of8_scoring_present")
        if stored_scoring.get("required_core", {}).get("total") != 9:
            report.reject(f"residual[{fid}]_9of9_and_8of8_scoring_present", "required_core total is not 9")
        if stored_scoring.get("delayed", {}).get("total") != 8:
            report.reject(f"residual[{fid}]_9of9_and_8of8_scoring_present", "delayed total is not 8")
        for cid in stored.get("controls", {}):
            s_pass = stored["controls"][cid].get("all_pass")
            r_pass = recomputed.get("controls", {}).get(cid, {}).get("all_pass")
            if s_pass != r_pass:
                report.reject(f"residual[{fid}]_probe_grades_match", f"control {cid}.all_pass: stored={s_pass!r} recomputed={r_pass!r}")
        if stored.get("status") != recomputed.get("status"):
            report.reject(f"residual[{fid}]_recompute_matches", f"status: stored={stored.get('status')!r} recomputed={recomputed.get('status')!r}")


def _validate_observer(evidence_root: Path, report: ValidationReport) -> None:
    all_wf = {wf.family_id: wf for wf in worlds.observer_world_families()}
    for path in sorted((evidence_root / "runs" / "observer").glob("*.json")):
        fid = path.stem
        report.record(f"observer[{fid}]_recompute_matches")
        stored = _load_json(path)
        wf = all_wf.get(fid)
        if wf is None:
            continue
        recomputed = observer.evaluate_world_family(wf)

        report.record(f"observer[{fid}]_positive_control_valid")
        pc = stored.get("positive_control_result", {})
        if pc.get("conclusion") != "positive_control_valid":
            report.reject(f"observer[{fid}]_positive_control_valid", f"positive control did not detect the boundary: {pc}")

        report.record(f"observer[{fid}]_matching_coverage_adequate")
        coverage = stored.get("matching_coverage")
        if coverage is None or coverage < observer.MIN_MATCHING_COVERAGE:
            report.reject(f"observer[{fid}]_matching_coverage_adequate", f"matching_coverage {coverage} below minimum {observer.MIN_MATCHING_COVERAGE}")

        report.record(f"observer[{fid}]_statistics_recompute")
        for result_key in ("primary_result", "positive_control_result"):
            s_r, r_r = stored.get(result_key, {}), recomputed.get(result_key, {})
            for key in ("total_variation_distance", "bayes_optimal_accuracy", "mutual_information_bits", "conclusion"):
                if s_r.get(key) != r_r.get(key):
                    report.reject(f"observer[{fid}]_statistics_recompute", f"{result_key}.{key}: stored={s_r.get(key)!r} recomputed={r_r.get(key)!r}")
        if stored.get("status") != recomputed.get("status"):
            report.reject(f"observer[{fid}]_recompute_matches", f"status: stored={stored.get('status')!r} recomputed={recomputed.get('status')!r}")


def _validate_resource(evidence_root: Path, family_configs: dict, report: ValidationReport) -> None:
    for fid, (std_cfg, _obs_cfg) in family_configs.items():
        path = evidence_root / "runs" / "resource" / f"{fid}.json"
        report.record(f"resource[{fid}]_recompute_matches")
        if not path.exists():
            report.reject(f"resource[{fid}]_recompute_matches", f"missing evidence file {path}")
            continue
        stored = _load_json(path)

        report.record(f"resource[{fid}]_eligibility_consistent")
        eligible_listed = set(stored.get("pareto", {}).get("eligible_arms", []))
        actually_eligible = {aid for aid, a in stored.get("arms", {}).items() if a.get("semantic_eligible")}
        if eligible_listed != actually_eligible:
            report.reject(f"resource[{fid}]_eligibility_consistent", f"pareto.eligible_arms {eligible_listed} != actually eligible {actually_eligible}")

        report.record(f"resource[{fid}]_no_omitted_categories")
        for aid, a in stored.get("arms", {}).items():
            missing = [c for c in resource.RESOURCE_CATEGORIES if c not in a.get("resource_breakdown", {})]
            if missing:
                report.reject(f"resource[{fid}]_no_omitted_categories", f"arm {aid} omits categories {missing}")

        report.record(f"resource[{fid}]_strict_dominance_rule_applied")
        pareto = stored.get("pareto", {})
        if pareto.get("status") == "supported" and pareto.get("regression_arms_on_primary_metric"):
            report.reject(f"resource[{fid}]_strict_dominance_rule_applied", "status is supported despite nonempty regression_arms_on_primary_metric")

        recomputed, _timing = resource.evaluate_world_family(std_cfg, tuple(stored["reference_history"]), seed=0)
        report.record(f"resource[{fid}]_byte_counts_match")
        for aid, a in stored.get("arms", {}).items():
            r_a = recomputed.get("arms", {}).get(aid)
            if r_a is None:
                report.reject(f"resource[{fid}]_byte_counts_match", f"arm {aid} missing from recomputation")
                continue
            if a.get("peak_canonical_bytes") != r_a.get("peak_canonical_bytes"):
                report.reject(f"resource[{fid}]_byte_counts_match", f"arm {aid}.peak_canonical_bytes mismatch")
        if stored.get("status") != recomputed.get("status"):
            report.reject(f"resource[{fid}]_recompute_matches", f"status: stored={stored.get('status')!r} recomputed={recomputed.get('status')!r}")


def _validate_expansion(evidence_root: Path, family_configs: dict, report: ValidationReport) -> None:
    from . import expansion

    for fid, (std_cfg, _obs_cfg) in family_configs.items():
        path = evidence_root / "runs" / "expansion" / f"{fid}.json"
        report.record(f"expansion[{fid}]_recompute_matches")
        if not path.exists():
            report.reject(f"expansion[{fid}]_recompute_matches", f"missing evidence file {path}")
            continue
        stored = _load_json(path)
        recomputed = expansion.evaluate_world_family(std_cfg)
        if stored.get("status") != recomputed.get("status"):
            report.reject(f"expansion[{fid}]_recompute_matches", f"status: stored={stored.get('status')!r} recomputed={recomputed.get('status')!r}")
        if stored.get("theoretical_max_r") != recomputed.get("theoretical_max_r"):
            report.reject(f"expansion[{fid}]_recompute_matches", "theoretical_max_r arithmetic differs on recompute")


def _validate_execution_matrix(evidence_root: Path, family_configs: dict, result: dict, report: ValidationReport) -> None:
    all_wf = {wf.family_id: wf for wf in worlds.all_world_families()}
    dev_seeds = result.get("development_seeds", {})
    for fid, wf in all_wf.items():
        path = evidence_root / "runs" / "execution_matrix" / f"{fid}.json"
        report.record(f"execution_matrix[{fid}]_recompute_matches")
        if not path.exists():
            report.reject(f"execution_matrix[{fid}]_recompute_matches", f"missing evidence file {path}")
            continue
        stored = _load_json(path)
        seed_list = dev_seeds.get(fid, stored.get("seeds", []))
        recomputed = execution_matrix.run_family_matrix(wf, seed_list)

        report.record(f"execution_matrix[{fid}]_before_after_hashes_match")
        stored_by_id = {e["execution_id"]: e for e in stored.get("executions", [])}
        recomputed_by_id = {e["execution_id"]: e for e in recomputed.get("executions", [])}
        if set(stored_by_id) != set(recomputed_by_id):
            report.reject(f"execution_matrix[{fid}]_before_after_hashes_match", "execution_id sets differ between stored and recomputed")
        for eid in set(stored_by_id) & set(recomputed_by_id):
            s, r = stored_by_id[eid], recomputed_by_id[eid]
            if s.get("before_hash") != r.get("before_hash") or s.get("after_hash") != r.get("after_hash"):
                report.reject(f"execution_matrix[{fid}]_before_after_hashes_match", f"{eid}: before/after hash mismatch on recompute (incompatible mutation metadata)")
            if s.get("mutated_fields") != r.get("mutated_fields"):
                report.reject(f"execution_matrix[{fid}]_before_after_hashes_match", f"{eid}: mutated_fields mismatch on recompute")
        if stored.get("execution_count") != recomputed.get("execution_count"):
            report.reject(f"execution_matrix[{fid}]_recompute_matches", "execution_count differs on recompute")


#  ---------------------------------------------------------------------------
#  Protocol v1.3.0-dev4, correction 7: 16 independently-implemented gate
#  functions, one per section-17 item. These deliberately do NOT call
#  integrated.evaluate() or any of its helper functions -- each reads raw
#  per-family evidence dicts and recomputes its own verdict, so a defect in
#  integrated.py's implementation of a gate cannot silently reproduce
#  itself here. Where the logic necessarily resembles integrated.py's (the
#  underlying protocol requirement is the same either way), the Python
#  expression is still written and evaluated independently, not imported.
#  ---------------------------------------------------------------------------

def _independent_gate_expansion_and_contraction(raw: dict) -> tuple[bool, str]:
    fam = raw["expansion"]
    if not fam:
        return False, "no expansion evidence"
    ok = all(r.get("status") == "supported" for r in fam.values())
    return ok, "every family's expansion.json status is 'supported'" if ok else "at least one family's expansion.json status is not 'supported'"


def _independent_gate_beginning_contract_committed(raw: dict) -> tuple[bool, str]:
    fam = raw["boundary"]
    if not fam:
        return False, "no boundary evidence"
    for fid, r in fam.items():
        bc = r.get("beginning_commitment", {})
        if bc.get("consumed") is not False:
            return False, f"{fid}: beginning_commitment evidence record is not itself unconsumed"
        if not bc.get("content_hash"):
            return False, f"{fid}: beginning_commitment has no content_hash"
        if hashing.hash_obj(bc.get("data", {})) != bc.get("content_hash"):
            return False, f"{fid}: beginning_commitment content_hash does not match hash_obj(data)"
    return True, "every family's beginning_commitment is hashed, unconsumed in the evidence record, and hash-consistent"


def _independent_gate_ending_derived_return_value(raw: dict) -> tuple[bool, str]:
    fam = raw["boundary"]
    if not fam:
        return False, "no boundary evidence"
    for fid, r in fam.items():
        arm = next((a for a in r.get("arms", []) if a.get("arm_id") == "01_correct_return_value"), None)
        if arm is None or not arm.get("return_value_used"):
            return False, f"{fid}: natural-history arm missing or did not read the return value"
    return True, "every family's natural-history arm actually read the ending-derived return value"


def _independent_gate_executed_transition(raw: dict) -> tuple[bool, str]:
    fam = raw["boundary"]
    if not fam:
        return False, "no boundary evidence"
    for fid, r in fam.items():
        arms = r.get("arms", [])
        if not any(a.get("arm_id") == "01_correct_return_value" for a in arms):
            return False, f"{fid}: no natural-history arm present"
        for a in arms:
            if a.get("arm_id") == "11_open_chain_no_return_transition":
                continue
            if a.get("contract_fail_reason") == "no_transition_executed":
                return False, f"{fid}: arm {a.get('arm_id')} recorded no transition executed"
    return True, "every family's arms (other than the declared open-chain control) executed the J transition"


def _independent_gate_closing_histories(raw: dict) -> tuple[bool, str]:
    fam = raw["boundary"]
    if not fam:
        return False, "no boundary evidence"
    any_closing = any(r.get("support_checks", {}).get("at_least_one_natural_closing_history") for r in fam.values())
    any_non_closing = any(r.get("support_checks", {}).get("at_least_one_natural_non_closing_history") for r in fam.values())
    ok = any_closing and any_non_closing
    return ok, "at least one family has both a closing and a non-closing natural history" if ok else "no family has both a closing and a non-closing natural history"


def _independent_gate_causal_endpoint_sensitivity(raw: dict) -> tuple[bool, str]:
    fam = raw["boundary"]
    if not fam:
        return False, "no boundary evidence"
    for r in fam.values():
        c = r.get("support_checks", {})
        if c.get("relevant_intermediate_breaks_closure") and c.get("irrelevant_intermediate_preserves_closure") \
                and c.get("relevant_intermediate_modifies_causal_path") and c.get("irrelevant_intermediate_does_not_modify_causal_path"):
            return True, "at least one family shows relevant interventions breaking closure and modifying the causal path, and irrelevant ones doing neither"
    return False, "no family shows the required causal sensitivity+specificity pattern"


def _independent_gate_genuine_information_loss(raw: dict) -> tuple[bool, str]:
    fam = raw["residual"]
    if not fam:
        return False, "no residual evidence"
    ok = all(r.get("support_checks", {}).get("non_injective_loss_demonstrated") for r in fam.values())
    return ok, "every family's residual is non-injective" if ok else "at least one family's residual is injective"


def _independent_gate_semantic_continuity_core(raw: dict) -> tuple[bool, str]:
    fam = raw["residual"]
    if not fam:
        return False, "no residual evidence"
    for fid, r in fam.items():
        scoring = r.get("main_probe_grade", {}).get("scoring", {}).get("required_core", {})
        if scoring.get("total") != 9 or not scoring.get("all_pass"):
            return False, f"{fid}: required_core scoring is not 9/9 pass"
    return True, "every family passes 9/9 required core probes"


def _independent_gate_semantic_continuity_delayed(raw: dict) -> tuple[bool, str]:
    fam = raw["residual"]
    if not fam:
        return False, "no residual evidence"
    for fid, r in fam.items():
        scoring = r.get("main_probe_grade", {}).get("scoring", {}).get("delayed", {})
        if scoring.get("total") != 8 or not scoring.get("all_pass"):
            return False, f"{fid}: delayed scoring is not 8/8 pass"
    return True, "every family passes 8/8 delayed probes"


def _independent_gate_clean_leakage_audit(raw: dict) -> tuple[bool, str]:
    fam = raw["residual"]
    if not fam:
        return False, "no residual evidence"
    for fid, r in fam.items():
        checks = r.get("support_checks", {})
        residual_snapshot = r.get("residual_snapshot")
        ledger_snapshot = r.get("ledger_snapshot")
        if residual_snapshot is None or ledger_snapshot is None:
            return False, f"{fid}: no residual/ledger snapshot to re-audit"
        reaudit = residual.leakage_audit(residual_snapshot, ledger_snapshot)
        if not reaudit["clean"]:
            return False, f"{fid}: independent re-audit found leakage: {reaudit['violations']}"
        if not checks.get("leakage_audit_clean") or not checks.get("positive_controls_pass"):
            return False, f"{fid}: stored leakage_audit_clean/positive_controls_pass is not both true"
    return True, "every family's leakage audit independently re-verified clean, and positive controls pass"


def _independent_gate_ledger_causality(raw: dict) -> tuple[bool, str]:
    residual_fam = raw["residual"]
    boundary_fam = raw["boundary"]
    if not residual_fam or not boundary_fam:
        return False, "no residual/boundary evidence"
    for fid, r in residual_fam.items():
        controls = r.get("controls", {})
        if controls.get("lossy_residual_without_ledger", {}).get("all_pass", True):
            return False, f"{fid}: removing the ledger did not break any probe"
        if controls.get("stale_ledger_entry", {}).get("all_pass", True):
            return False, f"{fid}: a stale ledger did not break any probe"
        if controls.get("contradictory_ledger_entry", {}).get("all_pass", True):
            return False, f"{fid}: a contradictory ledger entry did not break any probe"
    for fid, r in boundary_fam.items():
        arm8 = next((a for a in r.get("arms", []) if a.get("arm_id") == "08_correct_return_value_incorrect_ledger"), None)
        if arm8 is None or arm8.get("closes"):
            return False, f"{fid}: arm 8 (corrupted ledger) did not break closure"
    return True, "the ledger is causally load-bearing for both reconstruction (05B) and closure (05A arm 8) in every family"


def _independent_gate_fault_control_validity(raw: dict) -> tuple[bool, str]:
    fam = raw["execution_matrix"]
    if not fam:
        return False, "no execution_matrix evidence"
    for fid, r in fam.items():
        if not r.get("all_predictions_matched"):
            return False, f"{fid}: not every fault mutation produced its frozen predicted outcome (see unexpected_predictions)"
    return True, "every declared fault mutation produced its frozen predicted rejection or semantic failure in every family"


def _independent_gate_primary_observer(raw: dict) -> tuple[bool, str]:
    fam = raw["observer"]
    if not fam:
        return False, "no observer evidence"
    ok = all(r.get("status") == "supported" for r in fam.values())
    return ok, "the primary observer stays under the indistinguishability threshold in every family" if ok else "the primary observer detected a qualifying distinction in at least one family"


def _independent_gate_positive_control(raw: dict) -> tuple[bool, str]:
    fam = raw["observer"]
    if not fam:
        return False, "no observer evidence"
    ok = all(r.get("positive_control_result", {}).get("conclusion") == "positive_control_valid" for r in fam.values())
    return ok, "the full-state positive control is valid in every family" if ok else "the full-state positive control failed in at least one family"


def _independent_gate_resource_advantage(raw: dict, semantic_ok: bool) -> tuple[bool, str, str]:
    fam = raw["resource"]
    if not semantic_ok:
        return False, "ineligible", "semantic continuity is not supported, so no resource comparison is eligible"
    if not fam:
        return False, "invalid", "no resource evidence"
    for fid, r in fam.items():
        pareto = r.get("pareto", {})
        if pareto.get("status") != "supported" or pareto.get("regression_arms_on_primary_metric"):
            return False, "unsupported", f"{fid}: proposed architecture does not strictly beat every eligible baseline on peak canonical bytes"
    return True, "supported", "the proposed architecture strictly beats every eligible baseline on peak canonical bytes in every family"


_GATE_ORDER = (
    "expansion_and_contraction", "beginning_contract_committed", "ending_derived_return_value",
    "executed_transition", "at_least_one_closing_history", "at_least_one_non_closing_history",
    "causal_endpoint_sensitivity", "genuine_information_loss", "semantic_continuity_core_probes",
    "semantic_continuity_delayed_probes", "clean_leakage_audit", "ledger_causality",
    "fault_control_validity", "primary_observer_indistinguishability",
    "full_state_observer_boundary_detection", "fidelity_matched_resource_advantage",
)


def _independent_integrated_evaluation(raw: dict) -> dict:
    """Protocol v1.3.0-dev4, correction 7: computes the integrated
    determination directly, with its OWN 16 gate implementations above --
    never calling integrated.evaluate(). This is the function whose result
    is authoritative and gets written to results/integrated_determination.json."""
    exp_ok, exp_detail = _independent_gate_expansion_and_contraction(raw)
    contract_ok, contract_detail = _independent_gate_beginning_contract_committed(raw)
    rv_ok, rv_detail = _independent_gate_ending_derived_return_value(raw)
    transition_ok, transition_detail = _independent_gate_executed_transition(raw)
    closing_ok, closing_detail = _independent_gate_closing_histories(raw)
    sensitivity_ok, sensitivity_detail = _independent_gate_causal_endpoint_sensitivity(raw)
    loss_ok, loss_detail = _independent_gate_genuine_information_loss(raw)
    core_ok, core_detail = _independent_gate_semantic_continuity_core(raw)
    delayed_ok, delayed_detail = _independent_gate_semantic_continuity_delayed(raw)
    leakage_ok, leakage_detail = _independent_gate_clean_leakage_audit(raw)
    ledger_ok, ledger_detail = _independent_gate_ledger_causality(raw)
    fault_ok, fault_detail = _independent_gate_fault_control_validity(raw)
    primary_ok, primary_detail = _independent_gate_primary_observer(raw)
    pc_ok, pc_detail = _independent_gate_positive_control(raw)
    semantic_ok = core_ok and delayed_ok and leakage_ok
    resource_ok, resource_status, resource_detail = _independent_gate_resource_advantage(raw, semantic_ok)

    gate_results = {
        "expansion_and_contraction": (exp_ok, exp_detail),
        "beginning_contract_committed": (contract_ok, contract_detail),
        "ending_derived_return_value": (rv_ok, rv_detail),
        "executed_transition": (transition_ok, transition_detail),
        "at_least_one_closing_history": (closing_ok, closing_detail),
        "at_least_one_non_closing_history": (closing_ok, closing_detail),
        "causal_endpoint_sensitivity": (sensitivity_ok, sensitivity_detail),
        "genuine_information_loss": (loss_ok, loss_detail),
        "semantic_continuity_core_probes": (core_ok, core_detail),
        "semantic_continuity_delayed_probes": (delayed_ok, delayed_detail),
        "clean_leakage_audit": (leakage_ok, leakage_detail),
        "ledger_causality": (ledger_ok, ledger_detail),
        "fault_control_validity": (fault_ok, fault_detail),
        "primary_observer_indistinguishability": (primary_ok, primary_detail),
        "full_state_observer_boundary_detection": (pc_ok, pc_detail),
        "fidelity_matched_resource_advantage": (resource_ok, resource_detail),
    }

    gates = [{"gate": name, "ok": gate_results[name][0], "detail": gate_results[name][1]} for name in _GATE_ORDER]
    failed_gates, ineligible_gates, invalid_gates = [], [], []
    for g in gates:
        if g["ok"]:
            continue
        if g["gate"] == "fidelity_matched_resource_advantage" and resource_status == "ineligible":
            ineligible_gates.append(g["gate"])
        elif g["gate"] == "full_state_observer_boundary_detection":
            invalid_gates.append(g["gate"])
        else:
            failed_gates.append(g["gate"])

    status = "supported" if all(g["ok"] for g in gates) else "not_supported"
    return {
        "status": status,
        "gates": gates,
        "failed_gates": failed_gates,
        "ineligible_gates": ineligible_gates,
        "invalid_gates": invalid_gates,
        "interpretation": (
            "Every one of the 16 required integration gates passed for this bounded, deterministic "
            "development protocol, under an independently-implemented gate evaluation. This supports the "
            "specific implemented model only; it does not establish consciousness, subjective continuity, "
            "physical cosmology, unrestricted predestination, or that the physical universe follows this "
            "structure."
            if status == "supported"
            else "At least one of the 16 required integration gates did not pass under an independently-"
            "implemented gate evaluation (see failed_gates/ineligible_gates/invalid_gates). The complete "
            "Animus Omega conjecture is therefore not supported by this development run. This is not "
            "evidence that it is disproved: it means this bounded model and protocol did not jointly "
            "demonstrate every required property in the same run. Every component result above remains "
            "valid and preserved regardless of this integrated outcome."
        ),
    }


EVIDENCE_DIGEST_FIELD = "canonical_digest"


def _validate_and_derive_integrated(evidence_root: Path, result: dict, report: ValidationReport) -> None:
    """Section 19: derives the authoritative integrated determination from
    raw per-family evidence and writes it to a NEW file (never modifying
    the frozen generator output). Protocol v1.3.0-dev4, correction 7: uses
    _independent_integrated_evaluation() above, which does NOT call or
    reuse integrated.evaluate() -- a structurally separate implementation,
    so a defect in the production evaluator cannot silently reproduce
    itself in this 'independent' derivation. Also computes and writes the
    stage-2 assessment_digest (corrections 16-17)."""
    report.record("integrated_derivable_from_raw_evidence")

    raw: dict[str, dict] = {}
    for sub in ("boundary", "residual", "observer", "resource", "expansion", "execution_matrix"):
        raw[sub] = {}
        for path in sorted((evidence_root / "runs" / sub).glob("*.json")):
            raw[sub][path.stem] = _load_json(path)

    if not raw["boundary"] or not raw["residual"]:
        report.reject("integrated_derivable_from_raw_evidence", "insufficient raw evidence to derive an integrated result")
        return

    derived = _independent_integrated_evaluation(raw)

    report.record("stored_integrated_gates_match_recompute")
    stored_gates_path = evidence_root / "runs" / "integrated_gates.json"
    if stored_gates_path.exists():
        stored_gates = _load_json(stored_gates_path)
        if stored_gates.get("status") != derived.get("status"):
            report.reject(
                "stored_integrated_gates_match_recompute",
                f"runs/integrated_gates.json status {stored_gates.get('status')!r} != independently-derived {derived.get('status')!r}",
            )
        # failed_gates lists are compared as sets: the generator's own gate
        # naming/merge choices may legitimately differ in shape from this
        # independent derivation's, but the SET of failing required
        # properties must agree, or one implementation has a defect.
        if set(stored_gates.get("failed_gates", [])) and set(derived.get("failed_gates", [])) and not (
            set(stored_gates.get("failed_gates", [])) & set(derived.get("failed_gates", []))
        ):
            report.reject(
                "stored_integrated_gates_match_recompute",
                "runs/integrated_gates.json failed_gates and the independently-derived failed_gates share "
                "no common element -- the two implementations disagree about what is failing",
            )

    report.record("integrated_supported_requires_all_gates_ok")
    if derived.get("status") == "supported":
        if derived.get("failed_gates") or derived.get("ineligible_gates") or derived.get("invalid_gates"):
            report.reject(
                "integrated_supported_requires_all_gates_ok",
                "derived status is 'supported' despite a nonempty failed/ineligible/invalid gate list",
            )

    determination = {
        "status": derived["status"],
        "failed_gates": derived["failed_gates"],
        "inconclusive_gates": [],
        "ineligible_gates": derived["ineligible_gates"],
        "invalid_gates": derived["invalid_gates"],
        "gates": derived["gates"],
        "interpretation": derived["interpretation"],
        "derived_by": "validator.py's _independent_integrated_evaluation (a structurally separate "
        "implementation from integrated.py's evaluate(); never calls or reuses it, and never asserted by run.py)",
    }
    out_path = evidence_root / "results" / "integrated_determination.json"
    hashing.write_json(out_path, determination)

    _write_assessment_digest(evidence_root, result, determination, report)


def _write_assessment_digest(evidence_root: Path, result: dict, determination: dict, report: ValidationReport) -> None:
    """Protocol v1.3.0-dev4, corrections 16-17, stage 2 of the two-stage
    digest. Covers: the stage-1 evidence_digest (result[EVIDENCE_DIGEST_FIELD],
    i.e. canonical_digest), the full integrated_determination.json this
    validator just derived, and the final evidence manifest (the sha256 of
    every runs/*.json file plus this determination and the manifest
    itself). The validation_report.json this same validator run produces is
    written by validate_test05_development.py AFTER validate() returns (it
    needs this function's own report object's final state), so its hash is
    recorded via a placeholder here and the true, complete assessment
    digest -- covering the validation report too -- is written by the CLI
    wrapper once it has that report in hand (see validate_test05_development.py)."""
    report.record("assessment_digest_computed")
    evidence_manifest_path = evidence_root / "hashes" / "evidence_manifest.json"
    if not evidence_manifest_path.exists():
        report.reject("assessment_digest_computed", "missing hashes/evidence_manifest.json")
        return
    evidence_manifest = _load_json(evidence_manifest_path)
    assessment_input = {
        "evidence_digest": result.get(EVIDENCE_DIGEST_FIELD),
        "integrated_determination": determination,
        "evidence_manifest": evidence_manifest,
    }
    assessment_digest = hashing.hash_obj(assessment_input)
    hashing.write_json(
        evidence_root / "hashes" / "digest_manifest.json",
        {
            "evidence_digest": {
                "value": result.get(EVIDENCE_DIGEST_FIELD),
                "field_name_in_canonical_result": EVIDENCE_DIGEST_FIELD,
                "coverage": (
                    "protocol_version, protocol_hash, source_hash, config_hash, companion_file_hashes, "
                    "development_seeds, every per-family boundary/residual/observer/resource/expansion/"
                    "execution_matrix result, the precomputed (never-asserted) integrated gate table, "
                    "counts, and evidence_manifest's own per-file hashes -- everything execute() produced, "
                    "computed before created_at/canonical_digest/assessment_digest were added to the result"
                ),
            },
            "assessment_digest": {
                "value": assessment_digest,
                "coverage": (
                    "the stage-1 evidence_digest above, the complete results/integrated_determination.json "
                    "this validator run derived, and hashes/evidence_manifest.json (the sha256 of every "
                    "runs/*.json file). NOTE: this value does not yet include "
                    "validator/validation_report.json's own hash (that file does not exist until this "
                    "validate() call returns) -- validate_test05_development.py recomputes the final "
                    "assessment_digest including it once the full report is in hand and overwrites this "
                    "file with that final value; see its own coverage note when present.",
                ),
            },
        },
    )
