"""Independent paired-arm execution and development result assembly."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from typing import Any

from .faults import (
    DEVELOPMENT_SCENARIO_IDS, apply_endpoint_fault, apply_proposal_fault,
    scenario_for_label, validate_scenario,
)
from .model_adapter import Proposal, make_adapter
from .oracle import join_blinded_outcomes
from .protocol import (
    AGENT_IDS, ARMS, DEVELOPMENT_SEEDS, DIAGNOSTIC_BUDGET, MIDPOINT_TICK,
    REPLAY_HORIZON, SCHEMA_VERSION, SCORING_VERSION, VALIDATOR_VERSION,
    validate_seed,
)
from .serialization import canonical_bytes, checksum, deserialize_result, result_checksum
from .validators import (
    validate_closure, validate_execution, validate_invariants,
    validate_return_package,
)
from .world import (
    apply_proposals, initial_world, observation, public_world, semantic_state,
)

def _new_world(initial_state: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(initial_state)

def _run_forward(initial_state: dict[str, Any], swap: bool = True,
                 horizon: int = REPLAY_HORIZON) -> tuple[
                     dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Run one arm's own adapter and world, starting from serialized input."""
    world = _new_world(initial_state)
    adapter = make_adapter(world["seed"], "deterministic-adapter-v1")
    proposals: list[dict[str, Any]] = []
    information: list[dict[str, Any]] = []
    adapter_instances = [adapter.__class__.__name__]
    for tick in range(1, horizon + 1):
        if swap and tick == MIDPOINT_TICK + 1:
            adapter = make_adapter(world["seed"], "deterministic-adapter-v2")
            adapter_instances.append(adapter.__class__.__name__)
        views = [observation(world, i) for i in range(6)]
        information.append({"tick": tick, "views": copy.deepcopy(views)})
        batch = [adapter.propose(aid, tick, views[i])
                 for i, aid in enumerate(AGENT_IDS)]
        proposals.extend(p.to_dict() for p in batch)
        apply_proposals(world, batch)
    versions = [p["model_version"] for p in proposals]
    return world, proposals, {
        "model_versions": versions, "model_calls": len(proposals),
        "versions": versions,
        "tokens": sum(p["token_count"] for p in proposals),
        "observations": information, "adapter_instances": adapter_instances,
        "replacement": bool(swap), "simulated_adapter_replacement": True,
        "swap_occurred": bool(swap),
        "replacement_tick": MIDPOINT_TICK + 1 if swap else None,
    }

def _replay_proposals(initial_state: dict[str, Any],
                      proposals: list[dict[str, Any]],
                      horizon: int = REPLAY_HORIZON) -> tuple[dict[str, Any], int]:
    """Ordinary replay from serialized state and serialized accepted actions."""
    world = _new_world(initial_state)
    for start in range(0, horizon * len(AGENT_IDS), len(AGENT_IDS)):
        batch = [Proposal(**p) for p in proposals[start:start + len(AGENT_IDS)]]
        apply_proposals(world, batch)
    return world, horizon * len(AGENT_IDS)

def _return_package(endpoint: dict[str, Any],
                    initial_state: dict[str, Any]) -> dict[str, Any]:
    """Create an ending-derived, explicitly authorized return package."""
    permitted = ["identities", "obligation_ids", "ledger_tip", "semantic_digest"]
    ending = {
        "identities": copy.deepcopy(endpoint["identities"]),
        "obligation_ids": [o["id"] for o in endpoint["obligations"]],
        "ledger_tip": endpoint["ledger"][-1]["hash"],
        "semantic_digest": endpoint["semantic_digest"],
    }
    body = {
        "schema_version": SCHEMA_VERSION,
        "authored_by": "authoritative-merge",
        "eligible_authors": list(AGENT_IDS),
        "permitted_fields": permitted,
        "ending_derived": ending,
        "beginning_requirements": {
            "identities": list(initial_state["identities"]),
            "obligation_ids": [o["id"] for o in initial_state["obligations"]],
            "initial_state_digest": checksum(initial_state),
        },
    }
    package = {**body, "return_digest": checksum(body)}
    package["immediate_round_trip"] = (
        json.loads(canonical_bytes(package).decode("utf-8")) == package)
    package["return_digest"] = checksum({
        **body, "immediate_round_trip": package["immediate_round_trip"]})
    return package

def _reconstruct_beginning(initial_state: dict[str, Any],
                           package: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct from return requirements, not by rerunning a seed."""
    result = copy.deepcopy(initial_state)
    ending = package["ending_derived"]
    requirements = package["beginning_requirements"]
    # Ending-derived identity and obligation requirements participate in J.
    result["identities"] = copy.deepcopy(ending["identities"])
    if requirements["initial_state_digest"] != checksum(initial_state):
        raise ValueError("initial state digest mismatch")
    if ending["obligation_ids"] != requirements["obligation_ids"]:
        raise ValueError("ending obligation requirements do not reconstruct beginning")
    return result

def _apply_return_fault(package: dict[str, Any],
                        record: dict[str, Any]) -> dict[str, Any]:
    if record["operation"]["stage"] != "return":
        return copy.deepcopy(package)
    result = copy.deepcopy(package)
    result["unauthorized"] = {"overwrite": "protected-state"}
    return result

def _score(outcome: dict[str, Any]) -> dict[str, Any]:
    return {
        "detected": bool(outcome["detected"]),
        "error_count": len(outcome["reasons"]),
        "scoring_version": SCORING_VERSION,
        "replay_horizon": REPLAY_HORIZON,
        "diagnostic_budget": DIAGNOSTIC_BUDGET,
    }

def _arm_result(arm: str, initial_state: dict[str, Any],
                shared_inputs: dict[str, Any], scenario: dict[str, Any],
                swap: bool) -> dict[str, Any]:
    # Every arm owns its world, adapter calls, proposals, endpoint, and
    # validator invocation.  Shared inputs are serialized and copied.
    world, proposals, schedule = _run_forward(initial_state, swap=swap)
    proposal_input = apply_proposal_fault(proposals, scenario)
    candidate = apply_endpoint_fault(public_world(world), scenario)
    proposal_check = validate_execution(candidate, proposal_input)
    schedule_match = proposals == shared_inputs["action_schedule"]
    if not schedule_match:
        proposal_check["reasons"].append("shared_schedule_mismatch")
    replay_steps = 0
    conventional = proposal_check
    work_kind = "forward_only"
    package = None
    reconstruction = None
    return_check = {"ok": True, "reasons": [], "validation_steps": 0}
    if arm == "enhanced_forward_matched":
        replayed, replay_work = _replay_proposals(initial_state, proposals)
        replay_steps = replay_work
        # Run the same candidate validators as Arm A, then add the ordinary
        # replay's conventional comparison checks.
        conventional = validate_execution(candidate, proposal_input)
        # Ordinary replay checks use the same public semantic and observer
        # consistency checks; a divergence is detected rather than hidden.
        if semantic_state(replayed) != semantic_state(world):
            conventional["reasons"].append("ordinary_replay_divergence")
        if public_world(replayed)["observer_outputs"] != candidate["observer_outputs"]:
            conventional["reasons"].append("ordinary_observer_divergence")
        if public_world(replayed) != shared_inputs["checkpoint"]:
            conventional["reasons"].append("checkpoint_replay_mismatch")
        try:
            if shared_inputs["ledger"] != public_world(replayed)["ledger"]:
                conventional["reasons"].append("ledger_replay_mismatch")
        except (KeyError, TypeError):
            conventional["reasons"].append("ledger_replay_mismatch")
        conventional["validation_steps"] += 5  # checkpoint/ledger replay checks
        work_kind = "ordinary_checkpoint_ledger_replay"
    elif arm == "closure_aware":
        package = _return_package(candidate, initial_state)
        package = _apply_return_fault(package, scenario)
        return_check = validate_return_package(package, candidate)
        try:
            reconstruction = _reconstruct_beginning(initial_state, package)
            replayed, replay_work = _replay_proposals(reconstruction, proposals)
            replay_steps = replay_work
            closure = validate_closure(candidate, public_world(replayed),
                                       return_check)
            closure["reasons"] = sorted(set(
                closure["reasons"] + proposal_check["reasons"]))
            closure["detected"] = bool(closure["reasons"])
            closure["closure_pass"] = not closure["detected"]
            # Closure uses the same proposal validator as the enhanced
            # ordinary replay, in addition to its return checks.
            closure["validation_steps"] += proposal_check["proposals"][
                "validation_steps"]
        except (KeyError, TypeError, ValueError) as exc:
            closure = {
                "closure_pass": False, "detected": True,
                "reasons": ["reconstruction_failure", str(exc)],
                "first_divergence": "reconstructed_beginning",
                "semantic_state_mismatch_count": 1,
                "observer_output_mismatch_count": 0,
                "validation_steps": return_check["validation_steps"] +
                proposal_check["proposals"]["validation_steps"],
            }
        conventional = closure
        work_kind = "ending_return_reconstruction_replay"
    reasons = sorted(set(conventional["reasons"]))
    detected = bool(reasons)
    closure_pass = (conventional.get("closure_pass")
                    if arm == "closure_aware" else None)
    # Real deterministic work is derived from loops/validators, not assigned
    # as an outcome.  The enhanced baseline's conventional work is measured
    # from its ordinary replay and is intentionally comparable to closure.
    deterministic_work = (
        len(proposals) + proposal_check["validation_steps"] +
        conventional.get("validation_steps", 0) + replay_steps)
    info_digest = checksum({
        "observations": schedule["observations"], "proposals": proposals,
        "horizon": REPLAY_HORIZON, "midpoint_tick": MIDPOINT_TICK,
    })
    return {
        "arm": arm, "information_digest": info_digest,
        "model_schedule": schedule, "proposals": proposal_input,
        "candidate": candidate, "invariant_validation": proposal_check,
        "shared_schedule_match": schedule_match,
        "executed_trace_digest": checksum({
            "proposals": proposals, "candidate": candidate,
        }),
        "detected": detected, "failure_reasons": reasons,
        "closure_pass": closure_pass,
        "first_divergence": conventional.get("first_divergence") or
        (reasons[0] if reasons else None),
        "score": _score({"detected": detected, "reasons": reasons}),
        "return_package": package, "reconstructed_beginning": reconstruction,
        "return_validation": return_check,
        "metrics": {
            "identity_divergence_count": proposal_check["invariant"][
                "identity_divergence_count"],
            "obligation_divergence_count": proposal_check["invariant"][
                "obligation_divergence_count"],
            "unsupported_provenance_count": proposal_check["invariant"][
                "unsupported_provenance_count"],
            "semantic_state_mismatch_count": conventional.get(
                "semantic_state_mismatch_count", 0),
            "observer_output_mismatch_count": conventional.get(
                "observer_output_mismatch_count", 0),
            "deterministic_work_units": deterministic_work,
            "storage_bytes": len(canonical_bytes(candidate)) +
            len(canonical_bytes(proposal_input)),
            "validation_steps": conventional.get("validation_steps", 0),
            "replay_steps": replay_steps,
            "replay_horizon": REPLAY_HORIZON,
        },
        "validator_version": VALIDATOR_VERSION,
        "scoring_version": SCORING_VERSION,
        "diagnostic_budget": DIAGNOSTIC_BUDGET,
        "work_kind": work_kind,
        "truth_label_exposed_to_validator": False,
        "arm_label_exposed_to_validator": False,
    }

def public_inputs(seed: int, fixture: str = "valid", swap: bool = True) -> dict[str, Any]:
    """Build a self-contained public package; fixture is not an execution input."""
    validate_seed(seed)
    scenario = scenario_for_label(fixture)
    initial_state = initial_world(seed)
    shared_world, shared_proposals, shared_schedule = _run_forward(
        initial_state, swap=swap)
    # The schedule is a public parity witness and replay input, not hidden
    # process state.  Each arm independently regenerates and checks it.
    return {
        "schema_version": SCHEMA_VERSION, "protocol_version": SCHEMA_VERSION,
        "scoring_version": SCORING_VERSION,
        "seed_metadata": {"development_seed": seed},
        "initial_state": initial_state,
        "scenario_record": scenario,
        "action_schedule": shared_proposals,
        "checkpoint": public_world(shared_world),
        "ledger": shared_world["ledger"],
        "horizon": REPLAY_HORIZON, "midpoint_tick": MIDPOINT_TICK,
        "swap": bool(swap),
        "protocol_digest": checksum({
            "schema": SCHEMA_VERSION, "scoring": SCORING_VERSION,
            "horizon": REPLAY_HORIZON, "midpoint": MIDPOINT_TICK,
        }),
    }

def _label_for_result(scenario: dict[str, Any]) -> str:
    aliases = {
        "dev-valid": "valid", "dev-identity": "identity_change",
        "dev-obligation": "obligation_drop", "dev-provenance": "missing_provenance",
        "dev-ledger": "ledger_tamper", "dev-semantic": "semantic_state",
        "dev-observer": "observer_output", "dev-unauthorized": "unauthorized_fields",
        "dev-duplicate": "duplicate_proposals", "dev-stale-digest": "stale_digest",
        "dev-unauthorized-proposal": "unauthorized_proposals",
    }
    return aliases[scenario["scenario_id"]]

def run_episode(seed: int, fixture: str = "valid", swap: bool = True) -> dict[str, Any]:
    inputs = public_inputs(seed, fixture, swap)
    scenario = inputs["scenario_record"]
    initial_state = copy.deepcopy(inputs["initial_state"])
    arms = [
        _arm_result(arm, initial_state, inputs, scenario, swap)
        for arm in ARMS
    ]
    # Join arm outcomes to oracle metadata only after blinded execution.
    oracle = join_blinded_outcomes(arms, scenario)
    result = {
        "schema_version": SCHEMA_VERSION, "mode": "development",
        "non_confirmatory": True, "public_inputs": inputs,
        "seed": seed, "fixture": _label_for_result(scenario),
        "scenario_id": scenario["scenario_id"], "agent_ids": list(AGENT_IDS),
        "horizon": REPLAY_HORIZON, "midpoint_tick": MIDPOINT_TICK,
        "swap": bool(swap), "initial_state": initial_state,
        "authoritative_ledger": inputs["ledger"], "checkpoint": inputs["checkpoint"],
        "arms": arms, "oracle": oracle,
        "paired_information_equal": len({a["information_digest"] for a in arms}) == 1,
        "paired_failure_detection": oracle["observed_category"],
        "deviations": [], "status": "development_non_confirmatory",
        "replay_command": "python -m persistent_closure_benchmark.replay_worker INPUT OUTPUT",
    }
    result["result_checksum"] = result_checksum(result)
    return result

def run_arm(seed: int, arm: str, fixture: str = "valid",
            swap: bool = True) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")
    return next(a for a in run_episode(seed, fixture, swap)["arms"]
                if a["arm"] == arm)

def validate_episode(result: dict[str, Any]) -> bool:
    if result.get("result_checksum") != result_checksum(result):
        raise ValueError("result checksum mismatch")
    expected = replay_public_inputs(result["public_inputs"])
    if expected != result:
        raise ValueError("episode does not recompute from public package")
    return True

def run_benchmark(seeds: tuple[int, ...] = DEVELOPMENT_SEEDS,
                  fixtures: tuple[str, ...] | None = None,
                  swap: bool | None = None) -> dict[str, Any]:
    for seed in seeds:
        validate_seed(seed)
    labels = fixtures or (
        "valid", "identity_change", "obligation_drop", "missing_provenance",
        "ledger_tamper", "semantic_state", "observer_output",
        "unauthorized_fields", "duplicate_proposals", "unauthorized_proposals",
        "stale_digest",
    )
    swaps = (True, False) if swap is None else (bool(swap),)
    episodes = [run_episode(seed, label, replacement)
                for seed in seeds for replacement in swaps for label in labels]
    executed = sorted({e["seed"] for e in episodes})
    result = {
        "schema_version": SCHEMA_VERSION, "mode": "development",
        "non_confirmatory": True,
        "reserved_seeds_not_run": not any(seed in executed
                                         for seed in range(52000, 52020)),
        "development_seed_allowlist": list(DEVELOPMENT_SEEDS),
        "development_scenario_ids": list(DEVELOPMENT_SCENARIO_IDS),
        "protocol": {"arms": list(ARMS), "agent_ids": list(AGENT_IDS),
                     "seeds": executed, "fixtures": list(labels),
                     "horizon": REPLAY_HORIZON, "midpoint_tick": MIDPOINT_TICK,
                     "strata": ["swap", "no_swap"] if len(swaps) == 2 else
                     ["swap" if swaps[0] else "no_swap"]},
        "episodes": episodes, "deviations": [],
        "status": "development_non_confirmatory",
    }
    result["result_checksum"] = result_checksum(result)
    return result

def replay_public_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Recompute from initial state, scenario, schedule, and checkpoint bytes."""
    required = {"schema_version", "protocol_version", "scoring_version",
                "seed_metadata", "initial_state", "scenario_record",
                "action_schedule", "checkpoint", "ledger", "horizon",
                "midpoint_tick", "swap", "protocol_digest"}
    if not isinstance(inputs, dict) or set(inputs) != required:
        raise ValueError("self-contained public package schema mismatch")
    if inputs["schema_version"] != SCHEMA_VERSION:
        raise ValueError("protocol version mismatch")
    if inputs["horizon"] != REPLAY_HORIZON or inputs["midpoint_tick"] != MIDPOINT_TICK:
        raise ValueError("replay horizon mismatch")
    validate_seed(inputs["seed_metadata"]["development_seed"])
    validate_scenario(inputs["scenario_record"])
    protocol_digest = checksum({
        "schema": SCHEMA_VERSION, "scoring": SCORING_VERSION,
        "horizon": REPLAY_HORIZON, "midpoint": MIDPOINT_TICK,
    })
    if inputs["protocol_digest"] != protocol_digest:
        raise ValueError("protocol digest mismatch")
    initial_state = copy.deepcopy(inputs["initial_state"])
    # The schedule, checkpoint, and ledger are verified as serialized public
    # artifacts before any arm is recomputed.
    scheduled, _ = _replay_proposals(initial_state, inputs["action_schedule"])
    if public_world(scheduled) != inputs["checkpoint"]:
        raise ValueError("checkpoint/action schedule mismatch")
    if scheduled["ledger"] != inputs["ledger"]:
        raise ValueError("ledger/action schedule mismatch")
    scenario = inputs["scenario_record"]
    arms = [_arm_result(arm, initial_state, inputs, scenario, bool(inputs["swap"]))
            for arm in ARMS]
    oracle = join_blinded_outcomes(arms, scenario)
    result = {
        "schema_version": SCHEMA_VERSION, "mode": "development",
        "non_confirmatory": True, "public_inputs": inputs,
        "seed": inputs["seed_metadata"]["development_seed"],
        "fixture": _label_for_result(scenario),
        "scenario_id": scenario["scenario_id"], "agent_ids": list(AGENT_IDS),
        "horizon": REPLAY_HORIZON, "midpoint_tick": MIDPOINT_TICK,
        "swap": bool(inputs["swap"]), "initial_state": initial_state,
        "authoritative_ledger": inputs["ledger"], "checkpoint": inputs["checkpoint"],
        "arms": arms, "oracle": oracle,
        "paired_information_equal": len({a["information_digest"] for a in arms}) == 1,
        "paired_failure_detection": oracle["observed_category"],
        "deviations": [], "status": "development_non_confirmatory",
        "replay_command": "python -m persistent_closure_benchmark.replay_worker INPUT OUTPUT",
    }
    result["result_checksum"] = result_checksum(result)
    return result

def fresh_process_replay(inputs: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        source, target = os.path.join(directory, "inputs.json"), os.path.join(
            directory, "result.json")
        with open(source, "wb") as handle:
            handle.write(canonical_bytes(inputs))
        subprocess.run([sys.executable, "-m",
                        "persistent_closure_benchmark.replay_worker",
                        source, target], check=True)
        with open(target, "rb") as handle:
            return deserialize_result(handle.read())