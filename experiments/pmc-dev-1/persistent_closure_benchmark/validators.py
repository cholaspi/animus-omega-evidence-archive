"""Blinded invariant, ordinary replay, and closure validators."""

from __future__ import annotations

import copy
from typing import Any

from .ledger import Ledger
from .protocol import AGENT_IDS
from .serialization import checksum
from .world import observation

def _semantic_projection(candidate: dict[str, Any]) -> dict[str, Any]:
    try:
        tip = Ledger.from_list(candidate["ledger"]).tip
    except (TypeError, ValueError, KeyError):
        tip = None
    return {
        "tick": candidate.get("tick"),
        "identities": copy.deepcopy(candidate.get("identities")),
        "positions": copy.deepcopy(candidate.get("positions")),
        "energy": copy.deepcopy(candidate.get("energy")),
        "inventory": copy.deepcopy(candidate.get("inventory")),
        "obligations": copy.deepcopy(candidate.get("obligations")),
        "semantic_counter": candidate.get("semantic_counter"),
        "ledger_tip": tip,
        "authority": copy.deepcopy(candidate.get("authority")),
    }

def _world_view(candidate: dict[str, Any]) -> dict[str, Any]:
    return {**copy.deepcopy(candidate),
            "observer_outputs": copy.deepcopy(candidate.get("observer_outputs", {}))}

def validate_proposals(proposals: list[dict[str, Any]]) -> dict[str, Any]:
    reasons: list[str] = []
    if not isinstance(proposals, list):
        reasons.append("proposal_schema")
        proposals = []
    ids = [p.get("agent_id") for p in proposals if isinstance(p, dict)]
    if set(ids) != set(AGENT_IDS):
        reasons.append("proposal_ownership")
    by_tick: dict[Any, list[str]] = {}
    for proposal in proposals:
        if isinstance(proposal, dict):
            by_tick.setdefault(proposal.get("tick"), []).append(
                proposal.get("agent_id"))
    for tick_ids in by_tick.values():
        if len(tick_ids) != len(set(tick_ids)):
            reasons.append("duplicate_proposal")
        if set(tick_ids) != set(AGENT_IDS):
            reasons.append("proposal_ownership")
    for proposal in proposals:
        if not isinstance(proposal, dict) or set(proposal) != {
            "agent_id", "tick", "action", "model_version", "request_digest",
            "token_count"}:
            reasons.append("proposal_schema")
            continue
        if proposal["action"] not in {"move", "gather", "hold"}:
            reasons.append("unauthorized_action")
        if proposal["agent_id"] not in AGENT_IDS:
            reasons.append("proposal_ownership")
    return {"ok": not reasons, "reasons": sorted(set(reasons)),
            "validation_steps": max(1, len(proposals))}

def validate_invariants(candidate: dict[str, Any]) -> dict[str, Any]:
    """Validate only public candidate data; no arm or truth labels are accepted."""
    reasons: list[str] = []
    identities = candidate.get("identities", [])
    if identities != list(AGENT_IDS):
        reasons.append("identity_divergence")
    obligations = candidate.get("obligations", [])
    ids = [o.get("id") for o in obligations if isinstance(o, dict)]
    if set(ids) != {"obligation-0", "obligation-1"} or len(ids) != len(set(ids)):
        reasons.append("obligation_divergence")
    authority = candidate.get("authority", {})
    permissions = authority.get("permissions", {}) if isinstance(authority, dict) else {}
    if (not isinstance(authority, dict) or authority.get("writer") != "authoritative-merge"
            or set(permissions) != set(AGENT_IDS)):
        reasons.append("authority_divergence")
    ledger = candidate.get("ledger")
    try:
        ledger_object = Ledger.from_list(ledger)
        ledger_check = ledger_object.verify()
    except (TypeError, ValueError, KeyError):
        ledger_object = None
        ledger_check = {"ok": False, "reason": "ledger_tamper"}
    if not ledger_check.get("ok"):
        reasons.append("ledger_tamper")
    event_by_hash = ({event["hash"]: event for event in ledger_object.events}
                     if ledger_object is not None else {})
    for event in (ledger_object.events if ledger_object else ()):
        actor = event.get("actor")
        if event["kind"] == "genesis":
            if actor != "system":
                reasons.append("event_ownership")
        elif actor not in AGENT_IDS:
            reasons.append("event_ownership")
        elif event["kind"] == "action":
            if event["payload"].get("action") not in {"move", "gather", "hold"}:
                reasons.append("event_permission")
            if event["payload"].get("model_version") not in {
                "deterministic-adapter-v1", "deterministic-adapter-v2"}:
                reasons.append("event_permission")
        elif event["kind"] == "fulfilment":
            oid = event["payload"].get("obligation_id")
            matching = [o for o in obligations if o.get("id") == oid]
            if len(matching) != 1 or matching[0].get("debtor") != actor:
                reasons.append("event_ownership")
            if matching and matching[0].get("provenance") != event["hash"]:
                reasons.append("provenance_causal_link")
            if matching and event["tick"] > matching[0].get("due_tick", -1):
                reasons.append("deadline_violation")
        else:
            reasons.append("event_permission")
    if any(o.get("status") == "fulfilled" and
           o.get("provenance") not in event_by_hash
           for o in obligations if isinstance(o, dict)):
        reasons.append("unsupported_provenance")
    expected_digest = checksum(_semantic_projection(candidate))
    if candidate.get("semantic_digest") != expected_digest:
        reasons.append("semantic_digest_stale")
    try:
        for index, agent in enumerate(AGENT_IDS):
            records = candidate["observer_outputs"][agent]
            if not records:
                reasons.append("observer_output_missing")
                continue
            expected = observation(_world_view(candidate), index)
            if records[-1] != expected:
                reasons.append("observer_output_inconsistent")
    except (KeyError, TypeError, IndexError):
        reasons.append("observer_output_inconsistent")
    return {
        "ok": not reasons, "reasons": sorted(set(reasons)),
        "identity_divergence_count": int("identity_divergence" in reasons),
        "obligation_divergence_count": int("obligation_divergence" in reasons),
        "unsupported_provenance_count": int(any(
            x in reasons for x in ("unsupported_provenance", "provenance_causal_link"))),
        "ledger": ledger_check,
        "validation_steps": 8 + len(obligations) + len(ledger or []),
    }

def validate_execution(candidate: dict[str, Any],
                       proposals: list[dict[str, Any]]) -> dict[str, Any]:
    invariant = validate_invariants(candidate)
    proposal_check = validate_proposals(proposals)
    reasons = sorted(set(invariant["reasons"] + proposal_check["reasons"]))
    return {
        "ok": not reasons, "detected": bool(reasons), "reasons": reasons,
        "invariant": invariant, "proposals": proposal_check,
        "semantic_state_mismatch_count": int("semantic_digest_stale" in reasons),
        "observer_output_mismatch_count": int(any(
            x in reasons for x in ("observer_output_inconsistent",
                                   "observer_output_missing"))),
        "validation_steps": invariant["validation_steps"] +
        proposal_check["validation_steps"],
    }

def _first_mismatch(expected: Any, actual: Any, path: str = "") -> str | None:
    if type(expected) is not type(actual):
        return path or "type"
    if isinstance(expected, dict):
        for key in sorted(set(expected) | set(actual)):
            if key not in expected or key not in actual:
                return f"{path}.{key}".strip(".")
            found = _first_mismatch(expected[key], actual[key],
                                    f"{path}.{key}".strip("."))
            if found:
                return found
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            return f"{path}.length".strip(".")
        for index, (left, right) in enumerate(zip(expected, actual)):
            found = _first_mismatch(left, right, f"{path}[{index}]")
            if found:
                return found
    elif expected != actual:
        return path or "value"
    return None

def validate_return_package(package: dict[str, Any],
                            endpoint: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    required = {"schema_version", "authored_by", "eligible_authors",
                "permitted_fields", "ending_derived", "beginning_requirements",
                "return_digest", "immediate_round_trip"}
    if set(package) != required:
        reasons.append("return_schema")
    if package.get("authored_by") != "authoritative-merge":
        reasons.append("return_authorship")
    if set(package.get("eligible_authors", [])) != set(AGENT_IDS):
        reasons.append("return_eligibility")
    permitted = {"identities", "obligation_ids", "ledger_tip", "semantic_digest"}
    if set(package.get("permitted_fields", [])) != permitted:
        reasons.append("return_permissions")
    ending = package.get("ending_derived", {})
    if set(ending) != permitted:
        reasons.append("return_fields")
    if "unauthorized" in package or set(ending) - permitted:
        reasons.append("unauthorized_return_field")
    body = {k: package.get(k) for k in required if k != "return_digest"}
    if package.get("return_digest") != checksum(body):
        reasons.append("return_digest")
    if package.get("immediate_round_trip") is not True:
        reasons.append("immediate_round_trip")
    try:
        endpoint_tip = Ledger.from_list(endpoint["ledger"]).tip
    except (TypeError, ValueError, KeyError):
        endpoint_tip = None
        reasons.append("return_endpoint_ledger")
    expected = {
        "identities": endpoint.get("identities"),
        "obligation_ids": [o.get("id") for o in endpoint.get("obligations", [])],
        "ledger_tip": endpoint_tip,
        "semantic_digest": endpoint.get("semantic_digest"),
    }
    if ending != expected:
        reasons.append("return_endpoint_mismatch")
    return {"ok": not reasons, "reasons": sorted(set(reasons)),
            "validation_steps": 5}

def validate_closure(candidate: dict[str, Any], replayed: dict[str, Any],
                     package_check: dict[str, Any]) -> dict[str, Any]:
    base = validate_invariants(candidate)
    reasons = list(base["reasons"]) + list(package_check["reasons"])
    semantic_path = _first_mismatch(
        _semantic_projection(replayed), _semantic_projection(candidate))
    observer_path = _first_mismatch(replayed.get("observer_outputs", {}),
                                    candidate.get("observer_outputs", {}))
    if semantic_path:
        reasons.append("semantic_state_divergence")
    if observer_path:
        reasons.append("observer_output_divergence")
    reasons = sorted(set(reasons))
    return {
        "closure_pass": not reasons, "detected": bool(reasons),
        "reasons": reasons, "first_divergence": semantic_path or observer_path,
        "semantic_state_mismatch_count": int(bool(semantic_path)),
        "observer_output_mismatch_count": int(bool(observer_path)),
        "base_invariants": base, "validation_steps": base["validation_steps"] + 5,
    }