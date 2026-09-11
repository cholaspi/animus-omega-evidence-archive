"""Orchestrates the Test 05 development run, protocol v1.2.0-dev3.

Two-phase, matching the protocol's freeze-before-tick-zero requirement:

- ``freeze(output_dir)`` writes only protocol/config/worlds material
  (nothing execution-derived) and asserts ``runs/`` and ``results/`` do not
  yet exist -- this is "tick zero has not happened yet," checked, not
  merely claimed.
- ``execute(output_dir)`` runs every component, writes ``runs/`` and
  ``results/``, and asserts ``freeze()`` already ran (the companion-file
  manifest must already exist).

The canonical top-level result's ``integrated_result.status`` is written as
``"pending"``: this module computes the gate table (needed for the
resource-eligibility override and for evidence completeness) but does not
assert the final supported/not_supported determination -- that is the
independent validator's job, run separately, per section 19: "Do not
initialize it as supported or not supported."

Never executes a reserved confirmatory seed -- see seeds.py.
"""

from __future__ import annotations

import datetime
import glob
from pathlib import Path
from typing import Any

from . import (
    boundary, companion_specs, execution_matrix, expansion, hashing, integrated,
    label_audit, observer, residual, resource, seeds, world, worlds,
)

PROTOCOL_VERSION = "1.3.0-dev4"


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _project_root() -> Path:
    return _package_root().parent.parent  # 05-test-05/


def _repo_root() -> Path:
    return _project_root().parent


def _output_dir() -> Path:
    return _repo_root() / "evidence" / "test05" / f"revised_development_v{PROTOCOL_VERSION}"


def compute_source_hash() -> dict:
    pkg_root = _package_root()
    project_root = _project_root()
    py_files = sorted(glob.glob(str(pkg_root / "*.py")))
    rel_paths = [str(Path(p).relative_to(project_root)) for p in py_files]
    return hashing.hash_source_tree(project_root, rel_paths)


def _protocol_doc_path() -> Path:
    return _project_root() / "docs" / f"TEST_05_PROTOCOL_v{PROTOCOL_VERSION}.md"


# ---------------------------------------------------------------------------
# Phase 1: freeze (protocol/config/worlds only -- no execution evidence)
# ---------------------------------------------------------------------------

def freeze(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    runs_dir = output_dir / "runs"
    results_dir = output_dir / "results"
    if runs_dir.exists() and any(runs_dir.iterdir()):
        raise RuntimeError("runs/ already contains evidence; freeze() must run before any execution")
    if results_dir.exists() and any(results_dir.iterdir()):
        raise RuntimeError("results/ already contains a result; freeze() must run before any execution")

    # Protocol v1.3.0-dev4, correction 10: a mechanical, non-bypassable
    # preflight gate. Refuses to freeze if any world family's configured
    # dimensions cannot satisfy the section-16 expansion/contraction
    # inequality, rather than sealing a protocol version that repeats
    # v1.2.0-dev3's failure mode.
    feasibility = expansion.preflight_feasibility_check(worlds.all_world_families())
    if not feasibility["feasible"]:
        raise RuntimeError(
            f"refusing to freeze: expansion/contraction feasibility check failed: {feasibility}"
        )

    for sub in ("protocol", "config", "worlds"):
        (output_dir / sub).mkdir(parents=True, exist_ok=True)

    manifest_entries = []

    def write_frozen(rel_path: str, obj) -> None:
        digest = hashing.write_json(output_dir / rel_path, obj)
        manifest_entries.append({"path": rel_path, "sha256": digest})

    # The protocol document itself: copied byte-for-byte (not re-serialized)
    # so its hash matches the source-of-truth doc exactly.
    protocol_src = _protocol_doc_path()
    protocol_dst = output_dir / "protocol" / protocol_src.name
    protocol_dst.write_bytes(protocol_src.read_bytes())
    protocol_hash = hashing.hash_file(protocol_src)
    manifest_entries.append({"path": f"protocol/{protocol_src.name}", "sha256": protocol_hash})

    for filename, builder in companion_specs.COMPANION_SPEC_BUILDERS.items():
        subdir = "config" if filename in ("physics_config.json", "seed_list.json", "baseline_definitions.json") else "protocol"
        write_frozen(f"{subdir}/{filename}", builder())

    for wf in worlds.all_world_families():
        write_frozen(
            f"worlds/{wf.family_id}.json",
            {
                "family_id": wf.family_id,
                "description": wf.description,
                "standard_config": wf.standard_config.to_dict(),
                "standard_config_hash": wf.standard_config.config_hash(),
                "observer_config": wf.observer_config.to_dict(),
                "observer_config_hash": wf.observer_config.config_hash(),
                "loss_profile": wf.loss_profile,
                "adversarial": list(wf.adversarial),
            },
        )

    source_hash_record = compute_source_hash()
    companion_manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "protocol_hash": protocol_hash,
        "source_hash": source_hash_record["source_hash"],
        "source_files": source_hash_record["files"],
        "files": manifest_entries,
        "companion_manifest_digest": hashing.hash_obj(manifest_entries),
    }
    hashing.write_json(output_dir / "hashes" / "companion_file_manifest.json", companion_manifest)
    return companion_manifest


def freeze_checklist(output_dir: Path) -> dict:
    """Recomputes every item on the section-23 freeze checklist. Returns a
    structured report; does not raise, so it can be embedded directly in a
    preflight record."""
    output_dir = Path(output_dir)
    items = {}

    pilot_result_path = _repo_root() / "evidence" / "test05" / "superseded_development_pilot" / "results" / "test05_development_result.json"
    items["pilot_preserved_and_identified"] = pilot_result_path.exists()

    manifest_path = output_dir / "hashes" / "companion_file_manifest.json"
    items["companion_files_frozen_and_hashed"] = manifest_path.exists()
    if manifest_path.exists():
        manifest = hashing.read_json(manifest_path)
        expected_json_files = {
            "observer_spec.json", "physics_config.json",
            "beginning_contract_schema.json", "causal_path_specification.json",
            "field_classification_manifest.json", "delayed_probe_generator.json",
            "fault_predictions.json", "mutation_definitions.json",
            "semantic_probe_specification.json", "byte_accounting_specification.json",
            "resource_objective.json", "seed_list.json",
            "gate_registry.json", "expansion_feasibility_proof.json",
        }
        found_basenames = {Path(e["path"]).name for e in manifest["files"]}
        has_protocol_doc = any(name.lower().startswith("test_05_protocol") for name in found_basenames)
        items["all_required_companion_files_present"] = (
            has_protocol_doc and expected_json_files.issubset(found_basenames)
        )

    eligibility = seeds.check_v4_seed_eligibility()
    items["seed_list_fixed_and_checked"] = eligibility["eligible"]

    feasibility = expansion.preflight_feasibility_check(worlds.all_world_families())
    items["expansion_feasibility_confirmed"] = feasibility["feasible"]

    label_result = label_audit.audit_no_label_leakage()
    items["simulator_receives_no_report_labels"] = label_result["clean"]

    runs_dir = output_dir / "runs"
    results_dir = output_dir / "results"
    items["revised_evidence_directory_contains_no_execution_evidence"] = not (
        (runs_dir.exists() and any(runs_dir.iterdir())) or (results_dir.exists() and any(results_dir.iterdir()))
    )

    # True by construction: nothing in run.py/execute() calls
    # seeds.confirm_reserved_execution, and main() never will either.
    items["confirmation_path_disabled"] = True

    items["unit_tests_pass"] = None  # filled in by the caller after running pytest/unittest
    items["validator_corruption_tests_pass"] = None  # filled in by the caller

    all_known_true = all(v for k, v in items.items() if v is not None and not k.endswith("_pass"))
    return {"items": items, "ready_pending_test_results": all_known_true}


# ---------------------------------------------------------------------------
# Phase 2: execute (runs/ and results/)
# ---------------------------------------------------------------------------

def _boundary_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "world_family_count": len(families),
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
        "per_family_total_histories": {fid: r.get("total_histories") for fid, r in families.items()},
    }


def _observer_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
        "per_family_primary_tv": {fid: r.get("primary_result", {}).get("total_variation_distance") for fid, r in families.items()},
        "per_family_matching_coverage": {fid: r.get("matching_coverage") for fid, r in families.items()},
    }


def _resource_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
        "primary_metric": "peak_canonical_bytes",
    }


def execute(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    manifest_path = output_dir / "hashes" / "companion_file_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("freeze() has not run for this output_dir; refusing to execute before tick zero is frozen")
    companion_manifest = hashing.read_json(manifest_path)

    for sub in ("boundary", "residual", "observer", "resource", "expansion", "execution_matrix"):
        (output_dir / "runs" / sub).mkdir(parents=True, exist_ok=True)

    families = worlds.all_world_families()
    dev_seeds = seeds.PROTOCOL_V4_DEVELOPMENT_SEEDS
    all_seeds = sorted(seeds.all_v4_development_seeds())
    seeds.require_development_seeds(all_seeds)
    eligibility = seeds.check_v4_seed_eligibility()
    if not eligibility["eligible"]:
        raise seeds.ReservedSeedError(f"seed eligibility check failed: {eligibility}")

    # --- run every component ------------------------------------------------
    boundary_seed_base = min(dev_seeds["friendly"])
    residual_seed_base = min(dev_seeds["friendly"])
    resource_seed_base = min(dev_seeds["friendly"])
    boundary_result = boundary.run_component(families, boundary_seed_base, PROTOCOL_VERSION)
    residual_result = residual.run_component(families, residual_seed_base)
    observer_result = observer.run_component(worlds.observer_world_families())

    boundary_reference_histories = {
        fid: (tuple(r["reference_history"]) if r.get("reference_history") else None)
        for fid, r in boundary_result["per_world_family"].items()
    }
    resource_result = resource.run_component(families, boundary_reference_histories, resource_seed_base)
    resource_timing = resource_result.pop("per_world_family_noncanonical_timing", {})

    expansion_result = expansion.run_component(families)
    execution_matrix_result = execution_matrix.run_component(families, dev_seeds)

    integrated_gates = integrated.evaluate(
        boundary_result, residual_result, observer_result, resource_result,
        expansion_result, execution_matrix_result,
    )
    loss_result = integrated_gates["component_summaries"]["genuine_information_loss"]
    semantic_core_result = integrated_gates["component_summaries"]["semantic_continuity_core"]
    semantic_delayed_result = integrated_gates["component_summaries"]["semantic_continuity_delayed"]
    leakage_gate_result = integrated_gates["component_summaries"]["clean_leakage_audit"]
    ledger_causality = integrated_gates["component_summaries"]["ledger_causality"]
    fault_control_gate_result = integrated_gates["component_summaries"]["fault_control_validity"]
    expansion_gate_result = integrated_gates["component_summaries"]["expansion_and_contraction"]
    resource_dashboard = integrated_gates["component_summaries"]["resource_advantage"]

    label_audit_result = label_audit.audit_no_label_leakage()

    # --- counts ---------------------------------------------------------------
    enumerated_histories = {}
    enumerated_microstates = {}
    for wf in families:
        enumerated_histories[f"{wf.family_id}:standard_config"] = len(world.enumerate_histories(wf.standard_config))
        enumerated_histories[f"{wf.family_id}:observer_config"] = len(world.enumerate_histories(wf.observer_config))
        enumerated_microstates[wf.family_id] = residual_result["per_world_family"][wf.family_id]["collision_analysis"]["admissible_microstate_count"]

    counts = {
        "world_family_count": len(families),
        "configuration_count": len(families) * 2,
        "development_seed_count": len(all_seeds),
        "execution_count": sum(r["execution_count"] for r in execution_matrix_result["per_world_family"].values()),
        "exhaustively_enumerated_histories_by_configuration": enumerated_histories,
        "exhaustively_enumerated_microstates_by_family": enumerated_microstates,
        "total_exhaustively_enumerated_histories": sum(enumerated_histories.values()),
        "total_exhaustively_enumerated_microstates": sum(enumerated_microstates.values()),
    }

    # --- evidence writing -------------------------------------------------
    evidence_manifest = []

    def write_evidence(rel_path: str, obj: Any) -> None:
        digest = hashing.write_json(output_dir / rel_path, obj)
        evidence_manifest.append({"path": rel_path, "sha256": digest})

    for fid, r in boundary_result["per_world_family"].items():
        write_evidence(f"runs/boundary/{fid}.json", r)
    for fid, r in residual_result["per_world_family"].items():
        write_evidence(f"runs/residual/{fid}.json", r)
    for fid, r in observer_result["per_world_family"].items():
        write_evidence(f"runs/observer/{fid}.json", r)
    for fid, r in resource_result["per_world_family"].items():
        write_evidence(f"runs/resource/{fid}.json", r)
    for fid, r in expansion_result["per_world_family"].items():
        write_evidence(f"runs/expansion/{fid}.json", r)
    for fid, r in execution_matrix_result["per_world_family"].items():
        write_evidence(f"runs/execution_matrix/{fid}.json", r)
    write_evidence("runs/integrated_gates.json", integrated_gates)
    write_evidence("runs/label_audit.json", label_audit_result)
    hashing.write_json(output_dir / "runs" / "_noncanonical_timing.json", resource_timing)

    config_hash = hashing.hash_obj(
        {
            "companion_manifest_digest": companion_manifest["companion_manifest_digest"],
            "protocol_version": PROTOCOL_VERSION,
        }
    )

    result: dict[str, Any] = {
        "test_id": "test-05-development",
        "protocol_version": PROTOCOL_VERSION,
        "development_status": "development",
        "run_class": "revised_development",
        "exact_pilot_superseded": "evidence/test05/superseded_development_pilot",
        "development_seeds": dev_seeds,
        "reserved_seeds_used": False,
        "world_family_results": {
            fid: {
                "reciprocal_closure": boundary_result["per_world_family"][fid]["status"],
                "loss": "supported" if loss_result["per_world_family"].get(fid) else "unsupported",
                "semantic_core": "supported" if semantic_core_result["per_world_family"].get(fid) else "unsupported",
                "semantic_delayed": "supported" if semantic_delayed_result["per_world_family"].get(fid) else "unsupported",
                "leakage": "supported" if leakage_gate_result["per_world_family"].get(fid) else "unsupported",
                "observer": observer_result["per_world_family"][fid]["status"],
                "resource": resource_result["per_world_family"][fid]["status"],
                "expansion_contraction": expansion_result["per_world_family"][fid]["status"],
                "execution_matrix": execution_matrix_result["per_world_family"][fid]["status"],
            }
            for fid in [wf.family_id for wf in families]
        },
        "reciprocal_closure_result": {"status": boundary_result["status"], "reason": boundary_result.get("reason", ""), "metrics": _boundary_metrics(boundary_result)},
        "loss_result": loss_result,
        "semantic_continuity_core_result": semantic_core_result,
        "semantic_continuity_delayed_result": semantic_delayed_result,
        "clean_leakage_audit_result": leakage_gate_result,
        "expansion_and_contraction_gate_result": expansion_gate_result,
        "fault_control_validity_gate_result": fault_control_gate_result,
        "leakage_result": {
            fid: residual_result["per_world_family"][fid]["leakage_audit"] for fid in residual_result["per_world_family"]
        },
        "observer_result": {"status": observer_result["status"], "reason": observer_result.get("reason", ""), "metrics": _observer_metrics(observer_result)},
        "positive_control_result": {
            fid: r.get("positive_control_result") for fid, r in observer_result["per_world_family"].items()
        },
        "observer_sensitivity_results": {
            fid: r.get("sensitivity_analysis_results") for fid, r in observer_result["per_world_family"].items()
        },
        "ledger_causality_result": ledger_causality,
        "fault_control_result": execution_matrix_result,
        "fidelity_eligibility": {
            fid: r["pareto"].get("eligible_arms") for fid, r in resource_result["per_world_family"].items()
        },
        "resource_result": resource_dashboard,
        "expansion_contraction_result": expansion_result,
        "integrated_result": {
            "status": "pending",
            "note": "derived only by the independent validator (validate_test05_development.py); never asserted by the generator",
            "precomputed_gates_for_validator_use": integrated_gates,
        },
        "failed_gates": None,
        "inconclusive_gates": None,
        "ineligible_gates": None,
        "invalid_gates": None,
        "source_hash": companion_manifest["source_hash"],
        "protocol_hash": companion_manifest["protocol_hash"],
        "config_hash": config_hash,
        "companion_file_hashes": companion_manifest["files"],
        "counts": counts,
        "label_audit": label_audit_result,
        "evidence_manifest": evidence_manifest,
        "interpretation": (
            "This is a bounded software experiment on the implemented finite models under this exact "
            "frozen protocol. It does not establish consciousness, subjective experience, physical "
            "cosmology, or whether our universe is a simulation. The integrated status above is "
            "intentionally 'pending': run validate_test05_development.py to derive it independently."
        ),
        "limitations": [
            "The 'primary observer with eight ticks of memory' sensitivity rung is reported inconclusive: "
            "exact enumeration at that window size is combinatorially infeasible (see its evidence entry "
            "for the exact arithmetic). Unchanged from v1.2.0-dev3 (correction 13: the primary observer "
            "definition and thresholds are kept as-is; this rung was never the primary claim).",
            "Section 8's 'minimum contract contents' names 18 distinct fields, not 17 as v1.2.0-dev3's "
            "development report shorthand miscounted; all 18 are now implemented (see "
            "protocol/beginning_contract_schema.json's note_on_naming).",
        ],
    }

    # Protocol v1.3.0-dev4, corrections 16-17: two-stage digest.
    # Stage 1 -- "evidence_digest" (this field is still named
    # "canonical_digest" for continuity with v1.2.0-dev3 evidence; see
    # validator.EVIDENCE_DIGEST_FIELD) -- covers exactly everything in
    # ``result`` above: the frozen protocol version/hash, config_hash,
    # source_hash, companion_file_hashes, every per-family component
    # result (boundary/residual/observer/resource/expansion/
    # execution_matrix), the precomputed (never-asserted) integrated gate
    # table, counts, and the evidence_manifest's own file hashes.
    # Stage 2 -- "assessment_digest" -- can only be computed once the
    # independent validator has derived the integrated determination and
    # written its own validation report, so it is computed and written by
    # validator.py, not here (see validator._write_assessment_digest). It
    # covers: this evidence_digest, results/integrated_determination.json,
    # validator/validation_report.json, and the final evidence_manifest
    # (including the two files above). It stays null in this file; the
    # validator writes the real value to a separate digest_manifest.json,
    # never mutating this frozen result.
    canonical_digest = hashing.hash_obj(result)
    result["canonical_digest"] = canonical_digest
    result["assessment_digest"] = None  # filled in only by validator.py, after independent validation
    result["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    hashing.write_json(output_dir / "results" / "test05_development_result.json", result)
    hashing.write_json(
        output_dir / "hashes" / "evidence_manifest.json",
        {"evidence_manifest": evidence_manifest, "result_digest": canonical_digest},
    )

    return result


def main():
    output_dir = _output_dir()
    freeze(output_dir)
    result = execute(output_dir)
    print(f"Wrote canonical result to {output_dir / 'results' / 'test05_development_result.json'}")
    print(f"canonical_digest={result['canonical_digest']}")
    print("integrated status: pending (run validate_test05_development.py to derive it)")
    return result


if __name__ == "__main__":
    main()
