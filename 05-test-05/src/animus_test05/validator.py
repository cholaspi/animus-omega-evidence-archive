"""Independent validator for Test 05 development evidence (protocol v2,
update I).

This module never trusts a cached ``status`` field. For every component it
either (a) fully re-executes that component from the config/seed recorded
in the evidence and byte-diffs the result against what was persisted, or
(b) independently re-derives a specific conclusion (leakage, collision
counts, resource eligibility, integrated gating) straight from the
persisted raw data. A rejection is a structured finding, not an exception:
running the validator against corrupted evidence must produce a report
with ``valid: False`` and a specific violation, never a crash, so
corruption tests can assert on the report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from . import boundary, hashing, integrated, label_audit, observer, residual, resource, seeds, world, worlds


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


ALL_COMPONENTS = ("boundary", "residual", "observer", "resource", "integrated")


def validate(evidence_root: Path, components: tuple[str, ...] = ALL_COMPONENTS) -> ValidationReport:
    """``components`` restricts which per-component recompute-and-diff
    sections run (the structural checks -- manifest/hash/seed/label-audit
    integrity -- always run regardless, since they are cheap). Full
    end-to-end validation (the default) always uses every component;
    ``components`` exists mainly so targeted corruption tests can validate
    just the one component they corrupted without paying for a full
    05C observer re-enumeration every time."""
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

    report.record("evidence_manifest_files_exist_and_hash")
    for entry in result.get("evidence_manifest", []):
        path = evidence_root / entry["path"]
        if not path.exists():
            report.reject("evidence_manifest_files_exist_and_hash", f"missing evidence file: {entry['path']}")
            continue
        obj = _load_json(path)
        actual_hash = hashing.hash_obj(obj)
        if actual_hash != entry["sha256"]:
            report.reject(
                "evidence_manifest_files_exist_and_hash",
                f"{entry['path']}: recomputed hash {actual_hash} != manifest hash {entry['sha256']}",
            )

    # --- 2. Seed legitimacy ---------------------------------------------------
    report.record("no_reserved_seed_used")
    if result.get("reserved_seeds_used") is not False:
        report.reject("no_reserved_seed_used", "reserved_seeds_used is not explicitly False")
    dev_seeds = result.get("development_seeds", [])
    for s in dev_seeds:
        if seeds.is_reserved(s):
            report.reject("no_reserved_seed_used", f"seed {s} is in a reserved confirmatory band")
        if not seeds.is_development(s):
            report.reject("no_reserved_seed_used", f"seed {s} is not a registered development seed (any protocol version)")

    # --- 3. Arm-label leakage audit (recomputed fresh, not trusted from evidence) ---
    report.record("label_audit_clean")
    fresh_label_audit = label_audit.audit_no_label_leakage()
    if not fresh_label_audit["clean"]:
        report.reject("label_audit_clean", f"simulator-core functions leak labels: {fresh_label_audit['violations']}")
    stored_label_audit = result.get("label_audit")
    if stored_label_audit is not None and stored_label_audit.get("violations") != fresh_label_audit["violations"]:
        report.reject("label_audit_clean", "stored label_audit evidence does not match a fresh audit")

    # --- 4. Per-component full recompute-and-diff ----------------------------
    if "boundary" in components:
        _validate_boundary(evidence_root, result, report)
    if "residual" in components:
        _validate_residual(evidence_root, result, report)
    if "observer" in components:
        _validate_observer(evidence_root, result, report)
    if "resource" in components:
        _validate_resource(evidence_root, result, report)
    if "integrated" in components:
        _validate_integrated(evidence_root, result, report)

    return report


def _family_configs_from_records(result: dict) -> dict[str, tuple[world.WorldConfig, world.WorldConfig]]:
    out = {}
    for rec in result.get("world_families", []):
        out[rec["family_id"]] = (
            _config_from_dict(rec["standard_config"]),
            _config_from_dict(rec["observer_config"]),
        )
    return out


def _validate_boundary(evidence_root: Path, result: dict, report: ValidationReport) -> None:
    families = _family_configs_from_records(result)

    for fid, (std_cfg, _obs_cfg) in families.items():
        path = evidence_root / "evidence" / "boundary" / f"{fid}.json"
        report.record(f"boundary[{fid}]_recompute_matches")
        if not path.exists():
            report.reject(f"boundary[{fid}]_recompute_matches", f"missing evidence file {path}")
            continue
        stored = _load_json(path)
        stored_seed = stored.get("rng_seed")
        if stored_seed is None:
            report.reject(f"boundary[{fid}]_recompute_matches", "evidence does not record the rng_seed actually used")
            continue

        # Beginning-commitment / contract integrity checks (update E, I).
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
                "the evidence-record beginning_commitment must itself be unconsumed (it exists only to prove "
                "pre-tick-zero commitment, not to serve as an operational transition input)",
            )

        # Fully independent recomputation using the exact seed recorded in
        # the evidence itself.
        recomputed = boundary.evaluate_world_family(std_cfg, rng_seed=stored_seed)
        _diff_arms(fid, stored, recomputed, report)

        # Arm-level rejection semantics (update H/I): a "fake" intervention
        # (arm 6) must show executed data actually changed on the causal
        # path; arm 7 must show it did not.
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
                        "arm 7 (irrelevant intermediate mutation) modified the declared causal path -- it is "
                        "not actually irrelevant, or the world model's irrelevant-action policy is broken",
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
                    report.reject(
                        f"boundary[{fid}]_open_chain_no_fake_transition",
                        "arm 11 must record that no transition was executed, not a fabricated pass",
                    )
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
        # Compare the decision fields (never notes/description, which may
        # legitimately vary if a donor history or mutation tick differs
        # between runs due to enumeration-order ties broken identically
        # but described differently).
        for field_name in ("closes", "contract_satisfied", "contract_fail_reason", "exact_closure_fail_field", "return_value_used"):
            if s.get(field_name) != r.get(field_name):
                report.reject(
                    f"boundary[{fid}]_recompute_matches",
                    f"arm {arm_id}.{field_name}: stored={s.get(field_name)!r} recomputed={r.get(field_name)!r}",
                )
    if stored.get("status") != recomputed.get("status"):
        report.reject(
            f"boundary[{fid}]_recompute_matches",
            f"status: stored={stored.get('status')!r} recomputed={recomputed.get('status')!r}",
        )


def _validate_residual(evidence_root: Path, result: dict, report: ValidationReport) -> None:
    families = _family_configs_from_records(result)
    all_wf = {wf.family_id: wf for wf in worlds.all_world_families()}
    for fid, (std_cfg, _obs_cfg) in families.items():
        path = evidence_root / "evidence" / "residual" / f"{fid}.json"
        report.record(f"residual[{fid}]_recompute_matches")
        if not path.exists():
            report.reject(f"residual[{fid}]_recompute_matches", f"missing evidence file {path}")
            continue
        stored = _load_json(path)

        wf = all_wf.get(fid)
        if wf is None:
            report.reject(f"residual[{fid}]_recompute_matches", f"unknown world family id {fid}")
            continue
        stored_seed = stored.get("rng_seed")
        if stored_seed is None:
            report.reject(f"residual[{fid}]_recompute_matches", "evidence does not record the rng_seed actually used")
            continue
        recomputed = residual.evaluate_world_family(wf, rng_seed=stored_seed, reference_history=tuple(stored["reference_history"]))

        # Collision/microstate counts (update I: "incorrect microstate or
        # collision counts").
        report.record(f"residual[{fid}]_collision_counts_match")
        sc = stored["collision_analysis"]
        rc = recomputed["collision_analysis"]
        for key in ("admissible_microstate_count", "distinct_residual_count", "max_preimage_size", "non_injective"):
            if sc.get(key) != rc.get(key):
                report.reject(
                    f"residual[{fid}]_collision_counts_match",
                    f"{key}: stored={sc.get(key)!r} recomputed={rc.get(key)!r}",
                )

        # Leakage audit re-verified directly against the STORED residual
        # and ledger snapshot (not merely trusting the stored "clean"
        # flag) -- this is the actual persisted artifact, not a fresh
        # rebuild, so a leaked banned key written into the evidence itself
        # is caught even if the *code* that produced it is innocent.
        report.record(f"residual[{fid}]_leakage_audit_reverified")
        stored_residual = stored.get("residual_snapshot")
        stored_ledger = stored.get("ledger_snapshot")
        if stored_residual is None or stored_ledger is None:
            report.reject(f"residual[{fid}]_leakage_audit_reverified", "evidence does not include a residual/ledger snapshot to re-audit")
        else:
            reaudit = residual.leakage_audit(stored_residual, stored_ledger)
            if not reaudit["clean"]:
                report.reject(f"residual[{fid}]_leakage_audit_reverified", f"leakage found in persisted evidence: {reaudit['violations']}")
            if stored.get("leakage_audit", {}).get("clean") != reaudit["clean"]:
                report.reject(f"residual[{fid}]_leakage_audit_reverified", "stored leakage_audit.clean disagrees with a fresh re-audit of the stored snapshot")

        # Also cross-check against a fully independent rebuild from the
        # same reference history, to catch a code-level leakage regression
        # even if this particular evidence file wasn't hand-tampered.
        true_ending = world.run_history(std_cfg, tuple(stored["reference_history"]))
        fresh_residual = residual.build_residual(true_ending, std_cfg)
        fresh_ledger = residual.build_ledger(true_ending)
        fresh_leakage = residual.leakage_audit(fresh_residual, fresh_ledger)
        if not fresh_leakage["clean"]:
            report.reject(f"residual[{fid}]_leakage_audit_reverified", f"leakage found on fresh rebuild: {fresh_leakage['violations']}")

        # Probe/control grades and status (full recompute diff).
        report.record(f"residual[{fid}]_probe_grades_match")
        if stored.get("main_probe_grade", {}).get("all_pass") != recomputed.get("main_probe_grade", {}).get("all_pass"):
            report.reject(f"residual[{fid}]_probe_grades_match", "main_probe_grade.all_pass differs on recompute")
        for cid in stored.get("controls", {}):
            s_pass = stored["controls"][cid].get("all_pass")
            r_pass = recomputed.get("controls", {}).get(cid, {}).get("all_pass")
            if s_pass != r_pass:
                report.reject(f"residual[{fid}]_probe_grades_match", f"control {cid}.all_pass: stored={s_pass!r} recomputed={r_pass!r}")
        if stored.get("status") != recomputed.get("status"):
            report.reject(f"residual[{fid}]_recompute_matches", f"status: stored={stored.get('status')!r} recomputed={recomputed.get('status')!r}")


def _validate_observer(evidence_root: Path, result: dict, report: ValidationReport) -> None:
    all_wf = {wf.family_id: wf for wf in worlds.observer_world_families()}
    for rec in result.get("world_families", []):
        fid = rec["family_id"]
        path = evidence_root / "evidence" / "observer" / f"{fid}.json"
        report.record(f"observer[{fid}]_recompute_matches")
        if not path.exists():
            report.reject(f"observer[{fid}]_recompute_matches", f"missing evidence file {path}")
            continue
        stored = _load_json(path)
        wf = all_wf.get(fid)
        if wf is None:
            continue
        recomputed = observer.evaluate_world_family(wf)

        report.record(f"observer[{fid}]_positive_control_valid")
        pc = stored.get("positive_control_result", {})
        if pc.get("conclusion") != "positive_control_valid":
            report.reject(f"observer[{fid}]_positive_control_valid", f"positive control did not detect the boundary: {pc}")

        report.record(f"observer[{fid}]_statistics_recompute")
        s_primary = stored.get("primary_result", {})
        r_primary = recomputed.get("primary_result", {})
        for key in ("total_variation_distance", "bayes_optimal_accuracy", "mutual_information_bits", "conclusion"):
            if s_primary.get(key) != r_primary.get(key):
                report.reject(
                    f"observer[{fid}]_statistics_recompute",
                    f"primary_result.{key}: stored={s_primary.get(key)!r} recomputed={r_primary.get(key)!r}",
                )
        s_control = stored.get("positive_control_result", {})
        r_control = recomputed.get("positive_control_result", {})
        for key in ("total_variation_distance", "bayes_optimal_accuracy", "mutual_information_bits", "conclusion"):
            if s_control.get(key) != r_control.get(key):
                report.reject(
                    f"observer[{fid}]_statistics_recompute",
                    f"positive_control_result.{key}: stored={s_control.get(key)!r} recomputed={r_control.get(key)!r}",
                )
        if stored.get("status") != recomputed.get("status"):
            report.reject(f"observer[{fid}]_recompute_matches", f"status: stored={stored.get('status')!r} recomputed={recomputed.get('status')!r}")


def _validate_resource(evidence_root: Path, result: dict, report: ValidationReport) -> None:
    families = _family_configs_from_records(result)
    for fid, (std_cfg, _obs_cfg) in families.items():
        path = evidence_root / "evidence" / "resource" / f"{fid}.json"
        report.record(f"resource[{fid}]_recompute_matches")
        if not path.exists():
            report.reject(f"resource[{fid}]_recompute_matches", f"missing evidence file {path}")
            continue
        stored = _load_json(path)

        # Fidelity eligibility (update I: "fidelity-ineligible resource
        # comparisons"): every arm listed as eligible in pareto must itself
        # be semantic_eligible=True in the arms dict.
        report.record(f"resource[{fid}]_eligibility_consistent")
        eligible_listed = set(stored.get("pareto", {}).get("eligible_arms", []))
        actually_eligible = {aid for aid, a in stored.get("arms", {}).items() if a.get("semantic_eligible")}
        if eligible_listed != actually_eligible:
            report.reject(
                f"resource[{fid}]_eligibility_consistent",
                f"pareto.eligible_arms {eligible_listed} != arms actually marked semantic_eligible {actually_eligible}",
            )

        # Omitted resource buffers (update I): every arm's resource_breakdown
        # must declare every category in resource.RESOURCE_CATEGORIES.
        report.record(f"resource[{fid}]_no_omitted_categories")
        for aid, a in stored.get("arms", {}).items():
            breakdown = a.get("resource_breakdown", {})
            missing = [c for c in resource.RESOURCE_CATEGORIES if c not in breakdown]
            if missing:
                report.reject(f"resource[{fid}]_no_omitted_categories", f"arm {aid} omits categories {missing}")

        # Full recompute of byte counts (uses the stored reference_history).
        recomputed, _timing = resource.evaluate_world_family(std_cfg, tuple(stored["reference_history"]), seed=0)
        report.record(f"resource[{fid}]_byte_counts_match")
        for aid, a in stored.get("arms", {}).items():
            r_a = recomputed.get("arms", {}).get(aid)
            if r_a is None:
                report.reject(f"resource[{fid}]_byte_counts_match", f"arm {aid} missing from recomputation")
                continue
            if a.get("peak_canonical_bytes") != r_a.get("peak_canonical_bytes"):
                report.reject(
                    f"resource[{fid}]_byte_counts_match",
                    f"arm {aid}.peak_canonical_bytes: stored={a.get('peak_canonical_bytes')} recomputed={r_a.get('peak_canonical_bytes')}",
                )
        if stored.get("status") != recomputed.get("status"):
            report.reject(f"resource[{fid}]_recompute_matches", f"status: stored={stored.get('status')!r} recomputed={recomputed.get('status')!r}")


def _validate_integrated(evidence_root: Path, result: dict, report: ValidationReport) -> None:
    """Update I: 'integrated support with any failed prerequisite' must be
    rejected. Recomputes the gate table from the persisted component
    evidence (not the cached component_results summaries) and checks the
    stored integrated_result is consistent with it."""
    report.record("integrated_recompute_matches")
    path = evidence_root / "evidence" / "integrated.json"
    if not path.exists():
        report.reject("integrated_recompute_matches", f"missing {path}")
        return
    stored_integrated = _load_json(path)

    boundary_result = {"per_world_family": {}}
    residual_result = {"per_world_family": {}}
    observer_result = {"per_world_family": {}}
    resource_result = {"per_world_family": {}}
    for rec in result.get("world_families", []):
        fid = rec["family_id"]
        b_path = evidence_root / "evidence" / "boundary" / f"{fid}.json"
        r_path = evidence_root / "evidence" / "residual" / f"{fid}.json"
        o_path = evidence_root / "evidence" / "observer" / f"{fid}.json"
        s_path = evidence_root / "evidence" / "resource" / f"{fid}.json"
        if b_path.exists():
            boundary_result["per_world_family"][fid] = _load_json(b_path)
        if r_path.exists():
            residual_result["per_world_family"][fid] = _load_json(r_path)
        if o_path.exists():
            observer_result["per_world_family"][fid] = _load_json(o_path)
        if s_path.exists():
            resource_result["per_world_family"][fid] = _load_json(s_path)

    recomputed_integrated = integrated.evaluate(boundary_result, residual_result, observer_result, resource_result)
    if stored_integrated.get("status") != recomputed_integrated.get("status"):
        report.reject(
            "integrated_recompute_matches",
            f"integrated status: stored={stored_integrated.get('status')!r} recomputed={recomputed_integrated.get('status')!r}",
        )

    # Never allow "supported" with a failed/ineligible/invalid gate: a
    # direct, paranoid re-check independent of the boolean logic above.
    report.record("integrated_supported_requires_all_gates_ok")
    if recomputed_integrated.get("status") == "supported":
        if recomputed_integrated.get("failed_gates") or recomputed_integrated.get("ineligible_gates") or recomputed_integrated.get("invalid_gates"):
            report.reject(
                "integrated_supported_requires_all_gates_ok",
                "status is 'supported' despite a nonempty failed/ineligible/invalid gate list",
            )
    top_level_integrated = result.get("integrated_result", {})
    if top_level_integrated.get("status") == "supported":
        if top_level_integrated.get("failed_gates") or top_level_integrated.get("ineligible_gates") or top_level_integrated.get("invalid_gates"):
            report.reject(
                "integrated_supported_requires_all_gates_ok",
                "top-level result claims integrated support despite a nonempty failed/ineligible/invalid gate list",
            )
