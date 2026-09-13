from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from demo.commitment_task import run_episode  # noqa: E402
from grader.closure_grader import grade  # noqa: E402


class ClosureGraderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "demo" / "contract.json").read_text(encoding="utf-8")
        )

    def test_demo_is_baseline_success_and_closure_fail(self) -> None:
        trace, environment = run_episode()
        result = grade(trace, self.contract)
        self.assertEqual(environment["baseline_reward"], 1.0)
        self.assertEqual(result["closure"], "FAIL")
        self.assertEqual(result["violations"], ["OPEN_COMMITMENT_AT_CLOSE:C1"])

    def test_discharge_before_close_passes(self) -> None:
        trace, _ = run_episode()
        trace.insert(
            -1,
            {
                "type": "event",
                "tick": 6,
                "name": "commitment_discharged",
                "payload": {"id": "C1"},
                "model": "policy-b",
            },
        )
        self.assertEqual(grade(trace, self.contract)["closure"], "PASS")

    def test_missing_creation_does_not_begin_open(self) -> None:
        trace, _ = run_episode()
        trace = [
            event
            for event in trace
            if not (
                event.get("type") == "event"
                and event.get("name") == "commitment_created"
            )
        ]
        result = grade(trace, self.contract)
        self.assertIn("MISSING_COMMITMENT_AT_CLOSE:C1", result["violations"])
        self.assertIn("MISSING_PROTECTED_COMMITMENT:C1", result["violations"])

    def test_discharge_before_creation_is_rejected(self) -> None:
        trace, _ = run_episode()
        trace.insert(
            1,
            {
                "type": "event",
                "tick": 0,
                "name": "commitment_discharged",
                "payload": {"id": "C1"},
            },
        )
        self.assertIn("DISCHARGE_BEFORE_CREATE:C1", grade(trace, self.contract)["violations"])

    def test_missing_swap_is_rejected(self) -> None:
        trace, _ = run_episode()
        trace = [event for event in trace if event.get("type") != "model_swap"]
        self.assertIn("NO_MODEL_SWAP", grade(trace, self.contract)["violations"])

    def test_contract_is_not_mutated(self) -> None:
        before = copy.deepcopy(self.contract)
        trace, _ = run_episode()
        grade(trace, self.contract)
        self.assertEqual(self.contract, before)

    def test_invalid_contract_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            grade([], {"protected_commitments": ["C1", "C1"]})


if __name__ == "__main__":
    unittest.main()