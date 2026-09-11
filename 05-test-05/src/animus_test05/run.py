"""Orchestrates the Test 05 development run, protocol v2: executes all
five components across the two frozen world families, assembles the
canonical gated-dashboard result, writes detailed per-component evidence
files (with wall-clock timing kept separate and non-canonical), and
computes every required hash. Never executes a reserved confirmatory seed."""

from __future__ import annotations

import datetime
import glob
from pathlib import Path
from typing import Any

from . import (
    boundary, hashing, integrated, label_audit, observer, residual, resource,
    seeds, world, worlds,
)

PROTOCOL_VERSION = "1.2.0-dev3"

SEED_BASES = {
    "05A": 57000,
    "05B": 57100,
    "05D": 57300,
}


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _project_root() -> Path:
    # 05-test-05/
    return _package_root().parent.parent


def _repo_root() -> Path:
    # the repository root (parent of 05-test-05/); canonical evidence for
    # this test now lives under <repo_root>/evidence/test05/, not under
    # 05-test-05/, so pilot and revised runs are separated from the source
    # tree itself.
    return _project_root().parent


def compute_source_hash() -> dict:
    pkg_root = _package_root()
    project_root = _project_root()
    py_files = sorted(glob.glob(str(pkg_root / "*.py")))
    rel_paths = [str(Path(p).relative_to(project_root)) for p in py_files]
    return hashing.hash_source_tree(project_root, rel_paths)


def compute_protocol_hash() -> tuple[str, str, str]:
    """Returns (pilot_protocol_path, protocol_path, protocol_hash).
    ``protocol_hash`` is what this run's ``protocol_hash`` field is set to;
    the pilot's own protocol document is unchanged and its path is
    recorded for provenance only."""
    pilot_path = _project_root() / "docs" / "TEST_05_PROTOCOL.md"
    v3_path = _project_root() / "docs" / "TEST_05_PROTOCOL_v1.2.0-dev3.md"
    return str(pilot_path.relative_to(_project_root())), str(v3_path.relative_to(_project_root())), hashing.hash_file(v3_path)


def _boundary_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "world_family_count": len(families),
        "supported_family_count": sum(1 for r in families.values() if r["status"] == "supported"),
        "unsupported_family_count": sum(1 for r in families.values() if r["status"] == "unsupported"),
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
        "per_family_total_histories": {fid: r.get("total_histories") for fid, r in families.items()},
    }


def _observer_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "world_family_count": len(families),
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
        "per_family_primary_tv": {
            fid: r.get("primary_result", {}).get("total_variation_distance") for fid, r in families.items()
        },
        "per_family_positive_control_tv": {
            fid: r.get("positive_control_result", {}).get("total_variation_distance") for fid, r in families.items()
        },
        "per_family_enumeration_count": {
            fid: r.get("primary_result", {}).get("enumeration_count") for fid, r in families.items()
        },
    }


def _resource_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "world_family_count": len(families),
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
        "per_family_dominates_count": {fid: r["pareto"].get("dominates_count") for fid, r in families.items()},
        "primary_metric": "peak_canonical_bytes",
    }


def run(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    for sub in ("boundary", "residual", "observer", "resource"):
        (output_dir / "evidence" / sub).mkdir(parents=True, exist_ok=True)

    families = worlds.all_world_families()

    dev_seeds_used = (
        [SEED_BASES["05A"] + i for i in range(len(families))]
        + [SEED_BASES["05B"] + i for i in range(len(families))]
        + [SEED_BASES["05D"] + i for i in range(len(families))]
    )
    seeds.require_development_seeds(dev_seeds_used)

    # --- run every component -------------------------------------------------
    boundary_result = boundary.run_component(families, SEED_BASES["05A"])
    residual_result = residual.run_component(families, SEED_BASES["05B"])
    observer_result = observer.run_component(worlds.observer_world_families())

    boundary_reference_histories = {
        fid: (tuple(r["reference_history"]) if r.get("reference_history") else None)
        for fid, r in boundary_result["per_world_family"].items()
    }
    resource_result = resource.run_component(families, boundary_reference_histories, SEED_BASES["05D"])
    resource_timing = resource_result.pop("per_world_family_noncanonical_timing", {})

    integrated_result = integrated.evaluate(boundary_result, residual_result, observer_result, resource_result)
    loss_result = integrated_result["component_summaries"]["genuine_information_loss"]
    semantic_result = integrated_result["component_summaries"]["semantic_continuity"]
    ledger_causality = integrated_result["component_summaries"]["ledger_causality"]
    resource_dashboard = integrated_result["component_summaries"]["resource_advantage"]

    label_audit_result = label_audit.audit_no_label_leakage()

    # --- counts (update D: report, don't let arms masquerade as families) ---
    enumerated_histories = {}
    enumerated_microstates = {}
    for wf in families:
        enumerated_histories[f"{wf.family_id}:standard_config"] = len(world.enumerate_histories(wf.standard_config))
        enumerated_histories[f"{wf.family_id}:observer_config"] = len(world.enumerate_histories(wf.observer_config))
        enumerated_microstates[wf.family_id] = residual_result["per_world_family"][wf.family_id]["collision_analysis"]["admissible_microstate_count"]

    counts = {
        "world_family_count": len(families),
        "configuration_count": len(families) * 2,  # standard_config + observer_config each
        "development_seed_count": len(set(dev_seeds_used)),
        "component_executions": 4 * len(families),  # 05A/05B/05D per family + 05C per family (observer uses same families)
        "exhaustively_enumerated_histories_by_configuration": enumerated_histories,
        "exhaustively_enumerated_microstates_by_family": enumerated_microstates,
        "total_exhaustively_enumerated_histories": sum(enumerated_histories.values()),
        "total_exhaustively_enumerated_microstates": sum(enumerated_microstates.values()),
    }

    # --- evidence writing -----------------------------------------------------
    evidence_manifest = []

    def write_evidence(rel_path: str, obj: Any, description: str):
        full_path = output_dir / rel_path
        digest = hashing.write_json(full_path, obj)
        evidence_manifest.append({"path": rel_path, "sha256": digest, "description": description})

    for fid, r in boundary_result["per_world_family"].items():
        write_evidence(f"evidence/boundary/{fid}.json", r, f"Test 05A raw evidence for world family {fid}")
    for fid, r in residual_result["per_world_family"].items():
        write_evidence(f"evidence/residual/{fid}.json", r, f"Test 05B raw evidence for world family {fid}")
    for fid, r in observer_result["per_world_family"].items():
        write_evidence(f"evidence/observer/{fid}.json", r, f"Test 05C raw evidence for world family {fid}")
    for fid, r in resource_result["per_world_family"].items():
        write_evidence(f"evidence/resource/{fid}.json", r, f"Test 05D raw evidence for world family {fid}")
    write_evidence("evidence/integrated.json", integrated_result, "Test 05E integrated gating evaluation")
    write_evidence("evidence/label_audit.json", label_audit_result, "Protocol v2 update F: arm-label leakage audit")

    # Noncanonical timing: written for transparency but NEVER added to
    # evidence_manifest (and therefore never reachable from canonical_digest).
    (output_dir / "evidence" / "resource").mkdir(parents=True, exist_ok=True)
    hashing.write_json(output_dir / "evidence" / "resource" / "_noncanonical_timing.json", resource_timing)

    source_hash_record = compute_source_hash()
    pilot_protocol_path, protocol_path, protocol_hash = compute_protocol_hash()

    world_family_records = [
        {
            "family_id": wf.family_id,
            "description": wf.description,
            "standard_config": wf.standard_config.to_dict(),
            "standard_config_hash": wf.standard_config.config_hash(),
            "observer_config": wf.observer_config.to_dict(),
            "observer_config_hash": wf.observer_config.config_hash(),
            "loss_profile": wf.loss_profile,
            "adversarial": list(wf.adversarial),
        }
        for wf in families
    ]

    config_hash = hashing.hash_obj(
        {
            "world_families": [
                {"standard": w["standard_config_hash"], "observer": w["observer_config_hash"]}
                for w in world_family_records
            ],
            "seed_bases": SEED_BASES,
            "protocol_version": PROTOCOL_VERSION,
            "observer_thresholds": {
                "indistinguishability_tv": observer.INDISTINGUISHABILITY_TV_THRESHOLD,
                "positive_control_tv": observer.POSITIVE_CONTROL_TV_THRESHOLD,
            },
            "primary_observer_spec_hash": observer._PRIMARY_OBSERVER_SPEC_HASH,
        }
    )

    result: dict[str, Any] = {
        "test_id": "test-05-development",
        "status": "development",
        "protocol_version": PROTOCOL_VERSION,
        "protocol_path": protocol_path,
        "superseded_protocol_paths": [pilot_protocol_path],
        "superseded_pilot_evidence_path": "evidence/test05/superseded_development_pilot",
        "source_hash": source_hash_record["source_hash"],
        "source_files": source_hash_record["files"],
        "protocol_hash": protocol_hash,
        "config_hash": config_hash,
        "development_seeds": sorted(set(dev_seeds_used)),
        "reserved_seeds_used": False,
        "world_families": world_family_records,
        "counts": counts,
        "label_audit": label_audit_result,
        "component_results": {
            "reciprocal_closure": {
                "status": boundary_result["status"],
                "reason": boundary_result.get("reason", ""),
                "metrics": _boundary_metrics(boundary_result),
                "evidence_refs": [f"evidence/boundary/{fid}.json" for fid in boundary_result["per_world_family"]],
            },
            "genuine_information_loss": {
                "status": loss_result["status"],
                "reason": loss_result["reason"],
                "metrics": {"per_world_family": loss_result["per_world_family"]},
                "evidence_refs": [f"evidence/residual/{fid}.json" for fid in residual_result["per_world_family"]],
            },
            "semantic_continuity": {
                "status": semantic_result["status"],
                "reason": semantic_result["reason"],
                "metrics": {"per_world_family": semantic_result["per_world_family"]},
                "evidence_refs": [f"evidence/residual/{fid}.json" for fid in residual_result["per_world_family"]],
            },
            "observer_boundary": {
                "status": observer_result["status"],
                "reason": observer_result.get("reason", ""),
                "metrics": _observer_metrics(observer_result),
                "evidence_refs": [f"evidence/observer/{fid}.json" for fid in observer_result["per_world_family"]],
            },
            "ledger_causality": {
                "status": ledger_causality["status"],
                "reason": ledger_causality["reason"],
                "metrics": {"per_family": ledger_causality["per_family"]},
                "evidence_refs": (
                    [f"evidence/residual/{fid}.json" for fid in residual_result["per_world_family"]]
                    + [f"evidence/boundary/{fid}.json" for fid in boundary_result["per_world_family"]]
                ),
            },
            "resource_advantage": {
                "status": resource_dashboard["status"],
                "reason": resource_dashboard["reason"],
                "internal_status": resource_dashboard.get("internal_status"),
                "metrics": _resource_metrics(resource_result),
                "evidence_refs": [f"evidence/resource/{fid}.json" for fid in resource_result["per_world_family"]],
            },
        },
        "integrated_result": {
            "status": integrated_result["status"],
            "failed_gates": integrated_result["failed_gates"],
            "ineligible_gates": integrated_result["ineligible_gates"],
            "invalid_gates": integrated_result["invalid_gates"],
            "interpretation": integrated_result["interpretation"],
            "gates": integrated_result["gates"],
        },
        "evidence_manifest": evidence_manifest,
    }

    # canonical_digest is computed over the result BEFORE created_at is
    # added: identical seeds and inputs must produce an identical digest,
    # and a wall-clock timestamp would break that on every single run.
    canonical_digest = hashing.hash_obj(result)
    result["canonical_digest"] = canonical_digest
    result["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    hashing.write_json(output_dir / "results" / "test05_development_result.json", result)
    hashing.write_json(output_dir / "MANIFEST.json", {"evidence_manifest": evidence_manifest, "result_digest": canonical_digest})

    return result


def main():
    output_dir = _repo_root() / "evidence" / "test05" / "revised_development_v1.2.0-dev3"
    result = run(output_dir)
    print(f"Wrote canonical result to {output_dir / 'results' / 'test05_development_result.json'}")
    print(f"canonical_digest={result['canonical_digest']}")
    print(f"integrated status: {result['integrated_result']['status']}")
    return result


if __name__ == "__main__":
    main()
