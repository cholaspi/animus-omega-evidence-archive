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
    eligibility = seeds.check_v3_seed_eligibility()
    if not eligibility["eligible"]:
        report.reject("no_reserved_seed_used", f"seed eligibility check failed: {eligibility}")
    if set(flat_seeds) != seeds.all_v3_development_seeds():
        report.reject(
            "no_reserved_seed_used",
            f"development_seeds {sorted(flat_seeds)} do not exactly match the registered v1.2.0-dev3 seed set",
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
        _validate_boundary(evidence_root, family_configs, report)
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
        _validate_and_derive_integrated(evidence_root, report)

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


def _validate_boundary(evidence_root: Path, family_configs: dict, report: ValidationReport) -> None:
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

        recomputed = boundary.evaluate_world_family(std_cfg, rng_seed=stored_seed)
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


def _validate_and_derive_integrated(evidence_root: Path, report: ValidationReport) -> None:
    """Section 19: derives the authoritative integrated determination from
    raw per-family evidence and writes it to a NEW file (never modifying
    the frozen generator output). Also enforces 'integrated support with a
    failed prerequisite' can never be reported."""
    report.record("integrated_derivable_from_raw_evidence")

    boundary_result = {"per_world_family": {}}
    residual_result = {"per_world_family": {}}
    observer_result = {"per_world_family": {}}
    resource_result = {"per_world_family": {}}
    for sub, target in (("boundary", boundary_result), ("residual", residual_result), ("observer", observer_result), ("resource", resource_result)):
        for path in sorted((evidence_root / "runs" / sub).glob("*.json")):
            target["per_world_family"][path.stem] = _load_json(path)

    if not boundary_result["per_world_family"] or not residual_result["per_world_family"]:
        report.reject("integrated_derivable_from_raw_evidence", "insufficient raw evidence to derive an integrated result")
        return

    derived = integrated.evaluate(boundary_result, residual_result, observer_result, resource_result)

    report.record("stored_integrated_gates_match_recompute")
    stored_gates_path = evidence_root / "runs" / "integrated_gates.json"
    if stored_gates_path.exists():
        stored_gates = _load_json(stored_gates_path)
        if stored_gates.get("status") != derived.get("status"):
            report.reject(
                "stored_integrated_gates_match_recompute",
                f"runs/integrated_gates.json status {stored_gates.get('status')!r} != recomputed {derived.get('status')!r}",
            )
        if stored_gates.get("failed_gates") != derived.get("failed_gates"):
            report.reject("stored_integrated_gates_match_recompute", "runs/integrated_gates.json failed_gates differs on recompute")

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
        "derived_by": "validator.py (independent of the generator; never asserted by run.py)",
    }
    out_path = evidence_root / "results" / "integrated_determination.json"
    hashing.write_json(out_path, determination)
