#!/usr/bin/env python3
"""Adapt a pinned tau2-bench half-duplex SimulationRun to Case 0 events.

This module performs structural extraction only. It does not infer C1,
confirmation, oracle truth, reward validity, or closure.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

TAU2_REPOSITORY = "https://github.com/sierra-research/tau2-bench"
TAU2_COMMIT = "2174a603f6d014ef94473ffa95957f6ce27100db"
DOMAIN = "retail"


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _tool_events(message: dict[str, Any], message_index: int) -> list[dict[str, Any]]:
    tool_calls = message.get("tool_calls") or []
    if not isinstance(tool_calls, list):
        raise ValueError(f"messages[{message_index}].tool_calls must be a list")
    events: list[dict[str, Any]] = []
    for tool_index, call in enumerate(tool_calls):
        if not isinstance(call, dict):
            raise ValueError(
                f"messages[{message_index}].tool_calls[{tool_index}] must be an object"
            )
        events.append(
            {
                "type": "tool_call",
                "event_index": None,
                "source_message_index": message_index,
                "source_tool_index": tool_index,
                "id": _require_string(
                    call.get("id"), f"messages[{message_index}].tool_calls[{tool_index}].id"
                ),
                "requestor": call.get("requestor", message["role"]),
                "name": _require_string(
                    call.get("name"),
                    f"messages[{message_index}].tool_calls[{tool_index}].name",
                ),
                "arguments": copy.deepcopy(call.get("arguments") or {}),
            }
        )
    return events


def _message_events(message: dict[str, Any], message_index: int) -> list[dict[str, Any]]:
    if not isinstance(message, dict):
        raise ValueError(f"messages[{message_index}] must be an object")
    role = message.get("role")
    if role not in {"system", "user", "assistant", "tool"}:
        raise ValueError(f"messages[{message_index}].role is unsupported: {role!r}")

    if role == "tool" and isinstance(message.get("tool_messages"), list):
        events: list[dict[str, Any]] = []
        for tool_index, item in enumerate(message["tool_messages"]):
            if not isinstance(item, dict):
                raise ValueError(
                    f"messages[{message_index}].tool_messages[{tool_index}] must be an object"
                )
            events.extend(_message_events(item, message_index))
        return events

    if role == "tool":
        return [
            {
                "type": "tool_result",
                "event_index": None,
                "source_message_index": message_index,
                "id": _require_string(message.get("id"), f"messages[{message_index}].id"),
                "requestor": message.get("requestor", "assistant"),
                "content": message.get("content"),
                "error": bool(message.get("error", False)),
            }
        ]

    events = [
        {
            "type": "message",
            "event_index": None,
            "source_message_index": message_index,
            "role": role,
            "content": message.get("content"),
        }
    ]
    if role in {"user", "assistant"}:
        events.extend(_tool_events(message, message_index))
    return events


def adapt_simulation_run(
    simulation_run: dict[str, Any], swap_manifest: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(simulation_run, dict):
        raise ValueError("simulation_run must be an object")
    messages = simulation_run.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("simulation_run.messages must be a non-empty list")

    if swap_manifest.get("tau2_repository") != TAU2_REPOSITORY:
        raise ValueError("swap manifest repository does not match the pinned adapter")
    if swap_manifest.get("tau2_commit") != TAU2_COMMIT:
        raise ValueError("swap manifest commit does not match the pinned adapter")
    if swap_manifest.get("domain") != DOMAIN:
        raise ValueError("swap manifest domain must be retail")

    boundary = swap_manifest.get("after_message_index")
    if not isinstance(boundary, int) or boundary < 0 or boundary >= len(messages) - 1:
        raise ValueError("after_message_index must split two existing messages")
    model_a = _require_string(swap_manifest.get("model_a"), "model_a")
    model_b = _require_string(swap_manifest.get("model_b"), "model_b")
    if model_a == model_b:
        raise ValueError("Case 0 requires different Model A and Model B identifiers")

    events: list[dict[str, Any]] = []
    for message_index, message in enumerate(messages):
        events.extend(_message_events(message, message_index))
        if message_index == boundary:
            events.append(
                {
                    "type": "model_swap",
                    "event_index": None,
                    "after_source_message_index": boundary,
                    "model_a": model_a,
                    "model_b": model_b,
                    "transferred_context_sha256": _require_string(
                        swap_manifest.get("transferred_context_sha256"),
                        "transferred_context_sha256",
                    ),
                }
            )

    for event_index, event in enumerate(events):
        event["event_index"] = event_index

    return {
        "schema_version": "case-0-tau2-events-v1",
        "source": {
            "repository": TAU2_REPOSITORY,
            "commit": TAU2_COMMIT,
            "domain": DOMAIN,
            "simulation_id": _require_string(simulation_run.get("id"), "simulation_run.id"),
            "task_id": _require_string(simulation_run.get("task_id"), "simulation_run.task_id"),
            "seed": simulation_run.get("seed"),
            "official_reward_info": copy.deepcopy(simulation_run.get("reward_info")),
        },
        "swap_manifest": copy.deepcopy(swap_manifest),
        "events": events,
        "adapter_boundary": (
            "Structural extraction only; no C1, confirmation, oracle, reward, "
            "or closure inference."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("simulation_run", type=Path)
    parser.add_argument("swap_manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run = json.loads(args.simulation_run.read_text(encoding="utf-8"))
    manifest = json.loads(args.swap_manifest.read_text(encoding="utf-8"))
    adapted = adapt_simulation_run(run, manifest)
    args.output.write_text(
        json.dumps(adapted, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()