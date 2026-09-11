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

from animus_test05 import validator


def main() -> int:
    if len(sys.argv) > 1:
        evidence_root = Path(sys.argv[1])
    else:
        evidence_root = Path(__file__).resolve().parent.parent / "evidence" / "test05" / "revised_development_v1.2.0-dev3"

    report = validator.validate(evidence_root)
    result = report.to_dict()
    print(json.dumps(result, indent=2))

    if result["valid"]:
        print(f"\nVALID: {len(result['checks_run'])} checks run, 0 violations.", file=sys.stderr)
        return 0
    else:
        print(f"\nINVALID: {result['violation_count']} violation(s) found.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
