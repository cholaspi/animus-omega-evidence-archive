#!/usr/bin/env python3
"""Entrypoint: executes the Test 05 development protocol (currently
v1.3.0-dev4) and writes canonical evidence to
evidence/test05/revised_development_v1.3.0-dev4/ at the repository root.

Never executes a reserved confirmatory seed -- see src/animus_test05/seeds.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from animus_test05 import run

if __name__ == "__main__":
    run.main()
