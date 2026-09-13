"""Development fault injection, isolated from execution and oracle scoring.

Fault records are opaque data to the runner.  They contain an operation, not a
fixture/truth label, and are sealed before being placed in public inputs.
"""

from __future__ import annotations

import copy
from typing import Any

from .protocol import AGENT_IDS
from .serialization import checksum

_DEV_SCENARIOS = {
    "dev-valid": ("valid", {"stage": "none"}),
    "dev-identity": ("nonclosure", {"stage": "endpoint", "op": "identity"}),
    "dev-obligation": ("nonclosure", {"stage": "endpoint", "op": "obligation"}),
    "dev-provenance": ("nonclosure", {"stage": "endpoint", "op": "provenance"}),
    "dev-ledger": ("nonclosure", {"stage": "endpoint", "op": "ledger"}),
    "dev-semantic": ("closure", {"stage": "endpoint", "op": "semantic"}),
    "dev-observer": ("closure", {"stage": "endpoint", "op": "observer"}),
    "dev-unauthorized": ("closure", {"stage": "return", "op": "unauthorized"}),
    "dev-duplicate": ("nonclosure", {"stage": "proposals", "op": "duplicate"}),
    "dev-unauthorized-proposal": (
        "nonclosure", {"stage": "proposals", "op": "unauthorized"}),
    "dev-stale-digest": ("closure", {"stage": "endpoint", "op": "stale_digest"}),
}

# Reserved identifiers are intentionally not exported and are not accepted by
# scenario_for_label or execution APIs.
_RESERVED_SCENARIO_IDS = frozenset({"reserved-family-alpha", "reserved-family-beta"})
DEVELOPMENT_SCENARIO_IDS = tuple(_DEV_SCENARIOS)
DEVELOPMENT_FAMILY_ALLOWLIST = frozenset(v[0] for v in _DEV_SCENARIOS.values())

def scenario_for_label(label: str) -> dict[str, Any]:
    """Development-only convenience mapping; validators never receive labels."""
    aliases = {
        "valid": "dev-valid", "identity_change": "dev-identity",
        "obligation_drop": "dev-obligation", "missing_provenance": "dev-provenance",
        "ledger_tamper": "dev-ledger", "semantic_state": "dev-semantic",
        "observer_output": "dev-observer", "unauthorized_fields": "dev-unauthorized",
        "duplicate_proposals": "dev-duplicate", "stale_digest": "dev-stale-digest",
        "unauthorized_proposals": "dev-unauthorized-proposal",
    }
    try:
        scenario_id = aliases[label]
    except KeyError as exc:
        raise ValueError("scenario is not in the development allow-list") from exc
    return seal_scenario(scenario_id)

def seal_scenario(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in DEVELOPMENT_SCENARIO_IDS:
        raise ValueError("scenario is not in the development allow-list")
    _, operation = _DEV_SCENARIOS[scenario_id]
    # Family/truth metadata remains in this module and the separate oracle;
    # it is deliberately not serialized into execution inputs.
    body = {"scenario_id": scenario_id,
            "operation": copy.deepcopy(operation)}
    return {**body, "scenario_digest": checksum(body)}

def validate_scenario(record: dict[str, Any]) -> None:
    if not isinstance(record, dict) or set(record) != {
        "scenario_id", "operation", "scenario_digest"}:
        raise ValueError("malformed sealed scenario")
    body = {k: record[k] for k in ("scenario_id", "operation")}
    if checksum(body) != record["scenario_digest"]:
        raise ValueError("scenario digest mismatch")
    if record["scenario_id"] not in DEVELOPMENT_SCENARIO_IDS:
        raise ValueError("scenario is not in the development allow-list")

def apply_endpoint_fault(endpoint: dict[str, Any],
                         record: dict[str, Any]) -> dict[str, Any]:
    """Apply only the sealed operation, without consulting truth/oracle data."""
    validate_scenario(record)
    result = copy.deepcopy(endpoint)
    operation = record["operation"]
    if operation["stage"] != "endpoint":
        return result
    kind = operation["op"]
    if kind == "identity":
        result["identities"][0] = "agent-forged"
    elif kind == "obligation":
        result["obligations"].pop()
    elif kind == "provenance":
        for obligation in result["obligations"]:
            if obligation["status"] == "fulfilled":
                obligation["provenance"] = None
                break
    elif kind == "ledger":
        result["ledger"][-1]["payload"] = {"tampered": True}
    elif kind in ("semantic", "stale_digest"):
        result["positions"][0] = (result["positions"][0] + 3) % 12
    elif kind == "observer":
        result["observer_outputs"][AGENT_IDS[0]][-1]["own_energy"] += 1
    else:
        raise ValueError("unsupported endpoint operation")
    return result

def apply_proposal_fault(proposals: list[dict[str, Any]],
                         record: dict[str, Any]) -> list[dict[str, Any]]:
    validate_scenario(record)
    if record["operation"]["stage"] != "proposals":
        return copy.deepcopy(proposals)
    if record["operation"]["op"] == "duplicate":
        return copy.deepcopy(proposals + [proposals[-1]])
    if record["operation"]["op"] == "unauthorized":
        result = copy.deepcopy(proposals)
        result[0]["agent_id"] = "external-agent"
        return result
    raise ValueError("unsupported proposal operation")