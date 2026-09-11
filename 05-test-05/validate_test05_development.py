#!/usr/bin/env python3
"""Entrypoint: independently validates a Test 05 development evidence
directory (default: evidence/test05/revised_development_v1.2.0-dev3/ at
the repository root), recomputing every conclusion from raw evidence
rather than trusting any cached status field. Exits nonzero if any
violation is found.

Usage:
    python3 validate_test05_development.py [path/to/evidence/dir]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from animus_test05 import hashing, run, validator


def _finalize_assessment_digest(evidence_root: Path, validation_report: dict) -> None:
    """Protocol v1.3.0-dev4, corrections 16-17: validator._write_assessment_digest
    (called inside validator.validate()) cannot include this validation
    report's own hash, since the report does not exist until validate()
    returns. This recomputes the true, final assessment_digest -- stage-1
    evidence_digest + integrated_determination.json + THIS validation
    report + the evidence manifest -- and overwrites hashes/digest_manifest.json
    with that final value, once."""
    digest_manifest_path = evidence_root / "hashes" / "digest_manifest.json"
    determination_path = evidence_root / "results" / "integrated_determination.json"
    evidence_manifest_path = evidence_root / "hashes" / "evidence_manifest.json"
    if not (digest_manifest_path.exists() and determination_path.exists() and evidence_manifest_path.exists()):
        return
    digest_manifest = json.loads(digest_manifest_path.read_text(encoding="utf-8"))
    determination = json.loads(determination_path.read_text(encoding="utf-8"))
    evidence_manifest = json.loads(evidence_manifest_path.read_text(encoding="utf-8"))
    evidence_digest = digest_manifest["evidence_digest"]["value"]
    final_assessment_input = {
        "evidence_digest": evidence_digest,
        "integrated_determination": determination,
        "validation_report": validation_report,
        "evidence_manifest": evidence_manifest,
    }
    final_assessment_digest = hashing.hash_obj(final_assessment_input)
    digest_manifest["assessment_digest"] = {
        "value": final_assessment_digest,
        "coverage": (
            "the stage-1 evidence_digest, the complete results/integrated_determination.json, the "
            "complete validator/validation_report.json, and hashes/evidence_manifest.json (the sha256 of "
            "every runs/*.json file). This is the final assessment_digest; it supersedes the placeholder "
            "written mid-validate() (which could not yet include this validation report's own hash)."
        ),
    }
    hashing.write_json(digest_manifest_path, digest_manifest)


def main() -> int:
    if len(sys.argv) > 1:
        evidence_root = Path(sys.argv[1])
    else:
        evidence_root = Path(__file__).resolve().parent.parent / "evidence" / "test05" / f"revised_development_v{run.PROTOCOL_VERSION}"

    report = validator.validate(evidence_root)
    result = report.to_dict()
    print(json.dumps(result, indent=2))

    validation_report_path = evidence_root / "validator" / "validation_report.json"
    validation_report_path.parent.mkdir(parents=True, exist_ok=True)
    validation_report = {
        "validator_version": "animus_test05.validator (v1.3.0-dev4 schema)",
        "valid": result["valid"],
        "num_checks_run": len(result["checks_run"]),
        "checks_run": result["checks_run"],
        "violation_count": result["violation_count"],
        "violations": result["violations"],
        "note": (
            "Zero violations means the evidence is structurally and causally consistent with itself "
            "under recomputation. It does NOT mean the conjecture was supported -- see "
            "results/integrated_determination.json for the derived status and "
            "results/test05_development_result.json for full component evidence."
        ),
    }
    hashing.write_json(validation_report_path, validation_report)
    _finalize_assessment_digest(evidence_root, validation_report)

    if result["valid"]:
        print(f"\nVALID: {len(result['checks_run'])} checks run, 0 violations.", file=sys.stderr)
        return 0
    else:
        print(f"\nINVALID: {result['violation_count']} violation(s) found.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
