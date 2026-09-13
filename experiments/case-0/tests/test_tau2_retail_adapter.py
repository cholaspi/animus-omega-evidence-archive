from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapter.tau2_retail import (  # noqa: E402
    TAU2_COMMIT,
    TAU2_REPOSITORY,
    adapt_simulation_run,
)


def fixture_run() -> dict:
    return {
        "id": "sim-case0-fixture",
        "task_id": "retail-cancel-fixture",
        "seed": 1,
        "reward_info": {"reward": 1.0},
        "messages": [
            {"role": "system", "content": "retail policy"},
            {"role": "user", "content": "Cancel my pending order."},
            {
                "role": "assistant",
                "content": "Cancel order #1 because it is no longer needed. Confirm yes?",
            },
            {"role": "user", "content": "Yes."},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "name": "cancel_pending_order",
                        "arguments": {
                            "order_id": "#1",
                            "reason": "no longer needed",
                        },
                        "requestor": "assistant",
                    }
                ],
            },
            {
                "role": "tool",
                "id": "call-1",
                "content": "{\"status\":\"cancelled\"}",
                "requestor": "assistant",
                "error": False,
            },
        ],
    }


def fixture_manifest() -> dict:
    return {
        "tau2_repository": TAU2_REPOSITORY,
        "tau2_commit": TAU2_COMMIT,
        "domain": "retail",
        "after_message_index": 2,
        "model_a": "provider/model-a",
        "model_b": "provider/model-b",
        "transferred_context_sha256": "a" * 64,
    }


class Tau2RetailAdapterTests(unittest.TestCase):
    def test_preserves_messages_calls_results_and_swap_boundary(self) -> None:
        result = adapt_simulation_run(fixture_run(), fixture_manifest())
        kinds = [event["type"] for event in result["events"]]
        self.assertEqual(
            kinds,
            [
                "message",
                "message",
                "message",
                "model_swap",
                "message",
                "message",
                "tool_call",
                "tool_result",
            ],
        )
        call = next(event for event in result["events"] if event["type"] == "tool_call")
        self.assertEqual(call["name"], "cancel_pending_order")
        self.assertEqual(call["arguments"]["order_id"], "#1")
        self.assertIn("Structural extraction only", result["adapter_boundary"])

    def test_does_not_mutate_source_records(self) -> None:
        run = fixture_run()
        manifest = fixture_manifest()
        before_run = copy.deepcopy(run)
        before_manifest = copy.deepcopy(manifest)
        adapt_simulation_run(run, manifest)
        self.assertEqual(run, before_run)
        self.assertEqual(manifest, before_manifest)

    def test_rejects_wrong_source_pin(self) -> None:
        manifest = fixture_manifest()
        manifest["tau2_commit"] = "wrong"
        with self.assertRaises(ValueError):
            adapt_simulation_run(fixture_run(), manifest)

    def test_rejects_same_model_on_both_sides(self) -> None:
        manifest = fixture_manifest()
        manifest["model_b"] = manifest["model_a"]
        with self.assertRaises(ValueError):
            adapt_simulation_run(fixture_run(), manifest)

    def test_rejects_invalid_boundary(self) -> None:
        manifest = fixture_manifest()
        manifest["after_message_index"] = len(fixture_run()["messages"]) - 1
        with self.assertRaises(ValueError):
            adapt_simulation_run(fixture_run(), manifest)


if __name__ == "__main__":
    unittest.main()