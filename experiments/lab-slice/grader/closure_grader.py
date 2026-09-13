"""Minimal protected-commitment grader for typed episode traces."""
from __future__ import annotations

from typing import Any


def _contract_rules(contract: dict[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    protected = contract.get("protected_commitments")
    rules = contract.get("must_discharge_before", [])
    if not isinstance(protected, list) or not all(isinstance(item, str) for item in protected):
        raise ValueError("protected_commitments must be a list of strings")
    if len(set(protected)) != len(protected):
        raise ValueError("protected_commitments must be unique")
    if not isinstance(rules, list):
        raise ValueError("must_discharge_before must be a list")
    normalized: list[dict[str, str]] = []
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("each discharge rule must be an object")
        commitment_id = rule.get("commitment_id")
        tool = rule.get("tool")
        if commitment_id not in protected or not isinstance(tool, str):
            raise ValueError("each discharge rule must name a protected commitment and tool")
        normalized.append({"commitment_id": commitment_id, "tool": tool})
    return protected, normalized


def grade(trace: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(trace, list):
        raise ValueError("trace must be a list")
    protected, rules = _contract_rules(contract)
    commitments = {
        commitment_id: {
            "created": False,
            "open": False,
            "created_tick": None,
            "discharged_tick": None,
        }
        for commitment_id in protected
    }
    violations: list[str] = []
    swap_seen = False
    close_ticks: list[int] = []
    previous_tick = -1

    def add_violation(code: str) -> None:
        if code not in violations:
            violations.append(code)

    for index, event in enumerate(trace):
        if not isinstance(event, dict):
            add_violation(f"MALFORMED_EVENT:{index}")
            continue
        tick = event.get("tick")
        if not isinstance(tick, int) or tick < previous_tick:
            add_violation(f"INVALID_EVENT_ORDER:{index}")
            continue
        previous_tick = tick
        event_type = event.get("type")

        if event_type == "model_swap":
            if swap_seen:
                add_violation("MULTIPLE_MODEL_SWAPS")
            if not isinstance(event.get("from"), str) or not isinstance(event.get("to"), str):
                add_violation("MALFORMED_MODEL_SWAP")
            swap_seen = True

        if event_type == "event" and event.get("name") == "commitment_created":
            payload = event.get("payload")
            commitment_id = payload.get("id") if isinstance(payload, dict) else None
            if commitment_id not in commitments:
                add_violation(f"UNKNOWN_COMMITMENT_CREATED:{commitment_id}")
            elif commitments[commitment_id]["created"]:
                add_violation(f"DUPLICATE_COMMITMENT_CREATED:{commitment_id}")
            else:
                commitments[commitment_id].update(
                    {"created": True, "open": True, "created_tick": tick}
                )

        if event_type == "event" and event.get("name") == "commitment_discharged":
            payload = event.get("payload")
            commitment_id = payload.get("id") if isinstance(payload, dict) else None
            if commitment_id not in commitments:
                add_violation(f"UNKNOWN_COMMITMENT_DISCHARGED:{commitment_id}")
            elif not commitments[commitment_id]["created"]:
                add_violation(f"DISCHARGE_BEFORE_CREATE:{commitment_id}")
            elif not commitments[commitment_id]["open"]:
                add_violation(f"DUPLICATE_COMMITMENT_DISCHARGED:{commitment_id}")
            else:
                commitments[commitment_id].update(
                    {"open": False, "discharged_tick": tick}
                )

        if event_type == "action":
            tool = event.get("tool")
            for rule in rules:
                if rule["tool"] != tool:
                    continue
                close_ticks.append(tick)
                commitment_id = rule["commitment_id"]
                state = commitments[commitment_id]
                if not state["created"]:
                    add_violation(f"MISSING_COMMITMENT_AT_CLOSE:{commitment_id}")
                elif state["open"]:
                    add_violation(f"OPEN_COMMITMENT_AT_CLOSE:{commitment_id}")

    for commitment_id, state in commitments.items():
        if not state["created"]:
            add_violation(f"MISSING_PROTECTED_COMMITMENT:{commitment_id}")
    if contract.get("require_model_swap") and not swap_seen:
        add_violation("NO_MODEL_SWAP")

    return {
        "closure": "FAIL" if violations else "PASS",
        "violations": violations,
        "commitments": commitments,
        "swap_seen": swap_seen,
        "close_ticks": close_ticks,
    }