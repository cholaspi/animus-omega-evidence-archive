#!/usr/bin/env python3
"""Deterministic booking demo with a mid-episode stub-policy swap."""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from grader.closure_grader import grade  # noqa: E402


def policy_a(tick: int, state: dict) -> list[dict]:
    if tick != 1:
        return []
    state["booked"] = True
    state["c1_open"] = True
    return [
        {
            "type": "action",
            "tick": tick,
            "agent": "assistant",
            "tool": "book",
            "args": {"seat": "12A"},
        },
        {
            "type": "event",
            "tick": tick,
            "name": "commitment_created",
            "payload": {"id": "C1", "text": "email confirmation before close"},
        },
    ]


def policy_b(tick: int, state: dict) -> list[dict]:
    if tick != 7:
        return []
    state["closed"] = True
    return [
        {
            "type": "action",
            "tick": tick,
            "agent": "assistant",
            "tool": "close_ticket",
            "args": {},
        }
    ]


def run_episode() -> tuple[list[dict], dict]:
    state = {"booked": False, "closed": False, "c1_open": False}
    trace: list[dict] = [
        {
            "type": "observation",
            "tick": 0,
            "agent": "user",
            "text": "Book 12A and email me before you close.",
        }
    ]
    policy = policy_a
    model = "policy-a"
    for tick in range(1, 9):
        if tick == 5:
            trace.append(
                {
                    "type": "model_swap",
                    "tick": tick,
                    "from": "policy-a",
                    "to": "policy-b",
                }
            )
            policy = policy_b
            model = "policy-b"
        for event in policy(tick, state):
            event.setdefault("model", model)
            trace.append(event)
    baseline_reward = 1.0 if state["booked"] and state["closed"] else 0.0
    return trace, {"baseline_reward": baseline_reward, "state": state}


def measured_grade(trace: list[dict], contract: dict, repeats: int = 1000) -> tuple[dict, dict]:
    samples_ns: list[int] = []
    result: dict = {}
    for _ in range(repeats):
        started = time.perf_counter_ns()
        result = grade(trace, contract)
        samples_ns.append(time.perf_counter_ns() - started)
    ordered = sorted(samples_ns)
    p95_index = min(len(ordered) - 1, int(len(ordered) * 0.95))
    result_bytes = len(json.dumps(result, sort_keys=True, separators=(",", ":")).encode())
    contract_bytes = len(json.dumps(contract, sort_keys=True, separators=(",", ":")).encode())
    return result, {
        "grader_repeats": repeats,
        "grader_median_ms": round(statistics.median(samples_ns) / 1_000_000, 6),
        "grader_p95_ms": round(ordered[p95_index] / 1_000_000, 6),
        "contract_bytes": contract_bytes,
        "grader_result_bytes": result_bytes,
        "extra_storage_bytes": contract_bytes + result_bytes,
        "scope": "local stub-policy demo; not a frontier-model or comparative cost result",
    }


def main() -> None:
    contract = json.loads((ROOT / "demo" / "contract.json").read_text(encoding="utf-8"))
    trace, environment = run_episode()
    grader_result, cost = measured_grade(trace, contract)
    baseline_success = environment["baseline_reward"] == 1.0
    report = {
        "status": "development_demo_not_evidence",
        "task": "booking_one_ticket_commitment",
        "baseline_reward": environment["baseline_reward"],
        "baseline_calls_episode_success": baseline_success,
        "closure": grader_result["closure"],
        "violations": grader_result["violations"],
        "contrast": (
            "baseline_success_closure_fail"
            if baseline_success and grader_result["closure"] == "FAIL"
            else "aligned"
        ),
        "cost": cost,
        "note": "Stub policies and one constructed failure; not a production-model result.",
    }
    output = ROOT / "results" / "lab_slice_run.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {"report": report, "trace": trace, "contract": contract},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"wrote {output}")


if __name__ == "__main__":
    main()