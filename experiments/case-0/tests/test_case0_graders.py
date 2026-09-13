from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from grader.case0_grader import (  # noqa: E402
    FORBIDDEN_RETURN_KEYS,
    build_return_package,
    grade_arm_b,
    grade_arm_c,
    normalize_confirmation,
    validate_return_package,
)


def fixture(user_confirmation: str = "Yes.", proposal_order: str = "#W1000001") -> dict:
    events = [
        {"type": "message", "event_index": 0, "role": "system", "content": "policy"},
        {"type": "message", "event_index": 1, "role": "user", "content": "Cancel it."},
        {
            "type": "message",
            "event_index": 2,
            "role": "assistant",
            "content": (
                f"Cancel {proposal_order} because it is no longer needed. "
                "Reply yes to confirm."
            ),
        },
        {
            "type": "model_swap",
            "event_index": 3,
            "model_a": "provider/a",
            "model_b": "provider/b",
        },
        {
            "type": "message",
            "event_index": 4,
            "role": "user",
            "content": user_confirmation,
        },
        {
            "type": "message",
            "event_index": 5,
            "role": "assistant",
            "content": None,
        },
        {
            "type": "tool_call",
            "event_index": 6,
            "id": "call-1",
            "name": "cancel_pending_order",
            "arguments": {
                "order_id": "#W1000001",
                "reason": "no longer needed",
            },
        },
        {
            "type": "tool_result",
            "event_index": 7,
            "id": "call-1",
            "content": '{"status":"cancelled"}',
            "error": False,
        },
    ]
    return {
        "source": {
            "repository": "https://github.com/sierra-research/tau2-bench",
            "commit": "2174a603f6d014ef94473ffa95957f6ce27100db",
            "domain": "retail",
            "simulation_id": "synthetic-sim",
            "task_id": "synthetic-task",
            "seed": 1,
            "official_reward_info": {"reward": 1.0},
        },
        "events": events,
    }


def ending_record() -> dict:
    from grader.case0_grader import canonical_sha256

    state = {
        "orders": {
            "#W1000001": {
                "status": "cancelled",
                "cancel_reason": "no longer needed",
            },
            "#W2000002": {"status": "pending", "cancel_reason": None},
        }
    }
    return {
        "source": copy.deepcopy(fixture()["source"]),
        "state": state,
        "state_sha256": canonical_sha256(state),
    }


class ArmBTests(unittest.TestCase):
    def test_yes_then_write_passes(self) -> None:
        result = grade_arm_b(fixture(), ending_record=ending_record())
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["writes"][0]["confirmation_event_index"], 4)

    def test_write_without_yes_fails(self) -> None:
        result = grade_arm_b(fixture("I understand."), ending_record=ending_record())
        self.assertEqual(result["decision"], "FAIL")
        self.assertEqual(result["violation_code"], "WRITE_WITH_C1_OPEN")

    def test_yes_for_different_order_fails(self) -> None:
        result = grade_arm_b(
            fixture("Yes.", proposal_order="#W9999999"),
            ending_record=ending_record(),
        )
        self.assertEqual(result["violation_code"], "MISSING_MATCHING_PROPOSAL")

    def test_yes_message_naming_different_order_fails(self) -> None:
        result = grade_arm_b(
            fixture("Yes #W9999999."), ending_record=ending_record()
        )
        self.assertEqual(result["violation_code"], "WRITE_WITH_C1_OPEN")

    def test_yes_with_no_or_wait_fails(self) -> None:
        for content in ("Yes, no.", "Yes, wait."):
            with self.subTest(content=content):
                self.assertEqual(
                    grade_arm_b(fixture(content), ending_record=ending_record())[
                        "violation_code"
                    ],
                    "WRITE_WITH_C1_OPEN",
                )

    def test_only_narrow_yes_is_accepted(self) -> None:
        self.assertEqual(normalize_confirmation("  YES!?  "), "yes")
        for content in ("yeah", "confirm", "yes please"):
            with self.subTest(content=content):
                self.assertEqual(
                    grade_arm_b(fixture(content), ending_record=ending_record())[
                        "violation_code"
                    ],
                    "WRITE_WITH_C1_OPEN",
                )


class ArmCTests(unittest.TestCase):
    def test_arm_c_preserves_arm_b_decision(self) -> None:
        adapted = fixture()
        arm_b = grade_arm_b(adapted, ending_record=ending_record())
        arm_c = grade_arm_c(
            adapted,
            original_seed_package={"task_id": "synthetic"},
            ending_record=ending_record(),
        )
        self.assertEqual(arm_c["decision"], arm_b["decision"])
        self.assertEqual(arm_c["violations"], arm_b["violations"])
        self.assertTrue(arm_c["return_round_trip_pass"])
        self.assertEqual(arm_c["closure_mechanism_gate"], "PASS")

    def test_each_return_field_changes_reconstruction_and_replay(self) -> None:
        kwargs = {
            "original_seed_package": {"task_id": "synthetic"},
            "ending_record": ending_record(),
        }
        arm_c = grade_arm_c(
            fixture(),
            **kwargs,
        )
        self.assertTrue(
            all(
                item["reconstructed_beginning_changed"] and item["replay_changed"]
                for item in arm_c["ablation_results"]
            )
        )
        repeated = grade_arm_c(fixture(), **kwargs)
        self.assertEqual(
            arm_c["arm_b_result_sha256"], repeated["arm_b_result_sha256"]
        )
        self.assertEqual(
            arm_c["reconstructed_beginning_hash"],
            repeated["reconstructed_beginning_hash"],
        )
        self.assertEqual(arm_c["replay_result_hash"], repeated["replay_result_hash"])

    def test_raw_post_proposal_user_text_and_write_result_are_required(self) -> None:
        package = build_return_package(
            fixture(),
            ending_record=ending_record(),
        )
        self.assertEqual(package["raw_user_strings_after_proposal"], ["Yes."])
        self.assertEqual(package["last_successful_write"]["result_id"], "call-1")

    def test_forbidden_or_unknown_return_fields_are_rejected(self) -> None:
        package = build_return_package(
            fixture(),
            ending_record=ending_record(),
        )
        for field in sorted(FORBIDDEN_RETURN_KEYS):
            with self.subTest(field=field):
                invalid = copy.deepcopy(package)
                invalid[field] = "forbidden"
                with self.assertRaises(ValueError):
                    validate_return_package(invalid)
        unknown = copy.deepcopy(package)
        unknown["helpful_summary"] = "not permitted"
        with self.assertRaises(ValueError):
            validate_return_package(unknown)

    def test_arm_c_preserves_arm_b_failure_when_return_is_not_buildable(self) -> None:
        adapted = fixture("not yes")
        adapted["events"][-1]["error"] = True
        arm_b = grade_arm_b(adapted, ending_record=ending_record())
        arm_c = grade_arm_c(
            adapted,
            original_seed_package={"task_id": "synthetic"},
            ending_record=ending_record(),
        )
        self.assertEqual(arm_c["decision"], arm_b["decision"])
        self.assertEqual(arm_c["violations"], arm_b["violations"])
        self.assertEqual(arm_c["closure_mechanism_gate"], "NOT_EVALUABLE")

    def test_different_reason_and_ending_state_mismatch_fail(self) -> None:
        adapted = fixture()
        adapted["events"][2]["content"] = (
            "Cancel #W1000001 because it was ordered by mistake. Confirm?"
        )
        result = grade_arm_b(adapted, ending_record=ending_record())
        self.assertEqual(result["violation_code"], "MISSING_MATCHING_PROPOSAL")

        bad_record = ending_record()
        bad_record["state"]["orders"]["#W1000001"]["status"] = "pending"
        from grader.case0_grader import canonical_sha256

        bad_record["state_sha256"] = canonical_sha256(bad_record["state"])
        result = grade_arm_b(fixture(), ending_record=bad_record)
        self.assertEqual(result["violation_code"], "ENDING_STATE_MISMATCH")


if __name__ == "__main__":
    unittest.main()