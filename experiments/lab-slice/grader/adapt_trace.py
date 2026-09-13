"""Sketch adapter for common public tool-use trace shapes.

This is not an official integration with any named benchmark.
"""
from __future__ import annotations

from typing import Any


def from_tool_turns(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for tick, turn in enumerate(turns):
        role = turn.get("role") or turn.get("agent")
        if role in {"user", "system"}:
            trace.append(
                {
                    "type": "observation",
                    "tick": tick,
                    "agent": role,
                    "text": turn.get("content", ""),
                }
            )
        if turn.get("tool") or turn.get("name"):
            trace.append(
                {
                    "type": "action",
                    "tick": tick,
                    "agent": "assistant",
                    "tool": turn.get("tool") or turn.get("name"),
                    "args": turn.get("arguments") or turn.get("args") or {},
                }
            )
        model_swap = turn.get("model_swap")
        if isinstance(model_swap, dict):
            trace.append(
                {
                    "type": "model_swap",
                    "tick": tick,
                    "from": model_swap.get("from"),
                    "to": model_swap.get("to"),
                }
            )
        for key, name in (
            ("commitment_created", "commitment_created"),
            ("commitment_discharged", "commitment_discharged"),
        ):
            if isinstance(turn.get(key), dict):
                trace.append(
                    {
                        "type": "event",
                        "tick": tick,
                        "name": name,
                        "payload": turn[key],
                    }
                )
    return trace