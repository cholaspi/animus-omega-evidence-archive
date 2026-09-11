"""Orchestrates the full Test 05 development run: executes all five
components across the declared world families, assembles the canonical
result object, writes detailed per-component evidence files, and computes
every required hash. Never executes a reserved confirmatory seed."""

from __future__ import annotations

import datetime
import glob
import os
from pathlib import Path
from typing import Any

from . import boundary, hashing, integrated, observer, residual, resource, seeds, world, worlds

PROTOCOL_VERSION = "test05-development-1.0.0"

SEED_BASES = {
    "05A": 55000,
    "05B": 55100,
    "05D": 55300,
}


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _project_root() -> Path:
    # 05-test-05/
    return _package_root().parent.parent


def compute_source_hash() -> dict:
    pkg_root = _package_root()
    project_root = _project_root()
    py_files = sorted(glob.glob(str(pkg_root / "*.py")))
    rel_paths = [str(Path(p).relative_to(project_root)) for p in py_files]
    return hashing.hash_source_tree(project_root, rel_paths)


def compute_protocol_hash() -> tuple[str, str]:
    protocol_path = _project_root() / "docs" / "TEST_05_PROTOCOL.md"
    return str(protocol_path.relative_to(_project_root())), hashing.hash_file(protocol_path)


def _boundary_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "world_family_count": len(families),
        "supported_family_count": sum(1 for r in families.values() if r["status"] == "supported"),
        "unsupported_family_count": sum(1 for r in families.values() if r["status"] == "unsupported"),
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
    }


def _residual_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "world_family_count": len(families),
        "supported_family_count": sum(1 for r in families.values() if r["status"] == "supported"),
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
        "per_family_collision": {
            fid: {
                "admissible_microstate_count": r["collision_analysis"]["admissible_microstate_count"],
                "distinct_residual_count": r["collision_analysis"]["distinct_residual_count"],
                "max_preimage_size": r["collision_analysis"]["max_preimage_size"],
                "cardinality_reduction_ratio": r["collision_analysis"]["cardinality_reduction_ratio"],
            }
            for fid, r in families.items()
        },
    }


def _observer_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "world_family_count": len(families),
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
        "per_family_observer_tv": {
            fid: {o["observer_id"]: o["total_variation_distance"] for o in r.get("observers", [])}
            for fid, r in families.items()
        },
    }


def _resource_metrics(result: dict) -> dict:
    families = result.get("per_world_family", {})
    return {
        "world_family_count": len(families),
        "per_family_status": {fid: r["status"] for fid, r in families.items()},
        "per_family_dominates_count": {
            fid: r["pareto"].get("dominates_count") for fid, r in families.items()
        },
    }


def _ledger_controls_summary(residual_result: dict) -> dict:
    families = residual_result.get("per_world_family", {})
    ledger_control_ids = [
        "shuffled_identities", "deleted_obligation", "changed_causal_dependency",
        "contradictory_ledger_entry", "missing_provenance", "stale_ledger_entry",
        "duplicate_event", "random_reconstructed_payload",
    ]
    per_family = {}
    for fid, r in families.items():
        controls = r.get("controls", {})
        per_family[fid] = {
            cid: {"all_pass": controls[cid]["all_pass"], "pass_count": controls[cid]["pass_count"], "total": controls[cid]["total"]}
            for cid in ledger_control_ids if cid in controls
        }
    all_correctly_fail = all(
        not c["all_pass"] for fam in per_family.values() for c in fam.values()
    ) if per_family else False
    return {
        "status": "supported" if all_correctly_fail else "unsupported",
        "reason": (
            "every ledger fault-injection control correctly fails at least one semantic probe in every world family"
            if all_correctly_fail
            else "at least one ledger fault-injection control failed to produce a semantic failure somewhere"
        ),
        "per_world_family": per_family,
    }


def run(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    evidence_dir = output_dir / "evidence"
    for sub in ("boundary", "residual", "observer", "resource"):
        (evidence_dir / sub).mkdir(parents=True, exist_ok=True)

    families = worlds.all_world_families()
    obs_families = worlds.observer_world_families()

    dev_seeds_used = (
        [SEED_BASES["05A"] + i for i in range(len(families))]
        + [SEED_BASES["05B"] + i for i in range(len(families))]
        + [SEED_BASES["05D"] + i for i in range(len(families))]
    )
    seeds.require_development_seeds(dev_seeds_used)

    boundary_result = boundary.run_component(families, SEED_BASES["05A"])
    residual_result = residual.run_component(families, SEED_BASES["05B"])
    observer_result = observer.run_component(obs_families)

    boundary_reference_histories = {
        fid: (tuple(r["reference_history"]) if r.get("reference_history") else None)
        for fid, r in boundary_result["per_world_family"].items()
    }
    resource_result = resource.run_component(families, boundary_reference_histories, SEED_BASES["05D"])

    integrated_result = integrated.evaluate(boundary_result, residual_result, observer_result, resource_result)
    ledger_controls_result = _ledger_controls_summary(residual_result)

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

    source_hash_record = compute_source_hash()
    protocol_rel_path, protocol_hash = compute_protocol_hash()

    world_family_records = [
        {
            "family_id": wf.family_id,
            "description": wf.description,
            "config": wf.config.to_dict(),
            "config_hash": wf.config.config_hash(),
            "loss_profile": wf.loss_profile,
            "adversarial": list(wf.adversarial),
        }
        for wf in families
    ] + [
        {
            "family_id": wf.family_id,
            "description": wf.description,
            "config": wf.config.to_dict(),
            "config_hash": wf.config.config_hash(),
            "loss_profile": wf.loss_profile,
            "adversarial": list(wf.adversarial),
            "role": "observer_dedicated",
        }
        for wf in obs_families
    ]

    config_hash = hashing.hash_obj(
        {
            "world_families": [w["config_hash"] for w in world_family_records],
            "seed_bases": SEED_BASES,
            "protocol_version": PROTOCOL_VERSION,
            "observer_thresholds": {
                "indistinguishability_tv": observer.INDISTINGUISHABILITY_TV_THRESHOLD,
                "positive_control_tv": observer.POSITIVE_CONTROL_TV_THRESHOLD,
            },
        }
    )

    result: dict[str, Any] = {
        "test_id": "test-05-development",
        "status": "development",
        "protocol_version": PROTOCOL_VERSION,
        "protocol_path": protocol_rel_path,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_hash": source_hash_record["source_hash"],
        "source_files": source_hash_record["files"],
        "protocol_hash": protocol_hash,
        "config_hash": config_hash,
        "development_seeds": sorted(set(dev_seeds_used)),
        "reserved_seeds_used": False,
        "world_families": world_family_records,
        "component_results": {
            "reciprocal_closure": {
                "status": boundary_result["status"],
                "reason": boundary_result.get("reason", ""),
                "metrics": _boundary_metrics(boundary_result),
                "evidence_refs": [f"evidence/boundary/{fid}.json" for fid in boundary_result["per_world_family"]],
            },
            "semantic_continuity": {
                "status": residual_result["status"],
                "reason": residual_result.get("reason", ""),
                "metrics": _residual_metrics(residual_result),
                "evidence_refs": [f"evidence/residual/{fid}.json" for fid in residual_result["per_world_family"]],
            },
            "observer_boundary": {
                "status": observer_result["status"],
                "reason": observer_result.get("reason", ""),
                "metrics": _observer_metrics(observer_result),
                "evidence_refs": [f"evidence/observer/{fid}.json" for fid in observer_result["per_world_family"]],
            },
            "resource_advantage": {
                "status": resource_result["status"],
                "reason": resource_result.get("reason", ""),
                "metrics": _resource_metrics(resource_result),
                "evidence_refs": [f"evidence/resource/{fid}.json" for fid in resource_result["per_world_family"]],
            },
            "ledger_controls": {
                "status": ledger_controls_result["status"],
                "reason": ledger_controls_result["reason"],
                "metrics": {"per_world_family": ledger_controls_result["per_world_family"]},
                "evidence_refs": [f"evidence/residual/{fid}.json" for fid in residual_result["per_world_family"]],
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

    canonical_digest = hashing.hash_obj(result)
    result["canonical_digest"] = canonical_digest

    hashing.write_json(output_dir / "results" / "test05_development_result.json", result)
    hashing.write_json(output_dir / "MANIFEST.json", {"evidence_manifest": evidence_manifest, "result_digest": canonical_digest})

    return result


def main():
    project_root = _project_root()
    date_str = datetime.date.today().isoformat()
    output_dir = project_root / f"development-{date_str}"
    result = run(output_dir)
    print(f"Wrote canonical result to {output_dir / 'results' / 'test05_development_result.json'}")
    print(f"canonical_digest={result['canonical_digest']}")
    print(f"integrated status: {result['integrated_result']['status']}")
    return result


if __name__ == "__main__":
    main()
