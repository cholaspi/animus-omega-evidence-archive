"""Bounded authoritative world and distinct observer projections."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .ledger import Ledger
from .model_adapter import Proposal
from .protocol import AGENT_IDS, MIDPOINT_TICK, WORLD_SIZE
from .serialization import checksum

def initial_world(seed: int) -> dict[str, Any]:
    obligations = [
        {"id": "obligation-0", "debtor": AGENT_IDS[0], "creditor": AGENT_IDS[1],
         "due_tick": 4, "status": "open", "provenance": None},
        {"id": "obligation-1", "debtor": AGENT_IDS[2], "creditor": AGENT_IDS[3],
         "due_tick": 7, "status": "open", "provenance": None},
    ]
    ledger = Ledger().append(0, "system", "genesis",
                             {"seed": seed, "identities": list(AGENT_IDS)})
    return {
        "seed": seed, "tick": 0, "identities": list(AGENT_IDS),
        "positions": [(seed + 2 * i) % WORLD_SIZE for i in range(6)],
        "energy": [20] * 6, "inventory": [0] * 6,
        "obligations": obligations, "ledger": ledger.to_list(),
        "semantic_counter": 0, "observer_outputs": {a: [] for a in AGENT_IDS},
        "authority": {
            "writer": "authoritative-merge",
            "protected_fields": ["identities", "obligations", "ledger",
                                 "authority"],
            "permissions": {a: ["propose", "observe-own-view"] for a in AGENT_IDS},
        },
    }

def observation(world: dict[str, Any], agent_index: int) -> dict[str, Any]:
    """A bounded, identity-specific view; no global state or full ledger."""
    aid = AGENT_IDS[agent_index]
    return {
        "agent_id": aid, "tick": world["tick"],
        "own_position": world["positions"][agent_index],
        "own_energy": world["energy"][agent_index],
        "own_inventory": world["inventory"][agent_index],
        "nearby_positions": [
            world["positions"][i] for i in range(6)
            if i != agent_index and abs(world["positions"][i] -
                                       world["positions"][agent_index]) <= 1
        ],
        "open_obligation_count": sum(
            o["status"] == "open" and o["debtor"] == aid
            for o in world["obligations"]),
    }

def _ledger(world: dict[str, Any]) -> Ledger:
    return Ledger.from_list(world["ledger"])

def apply_proposals(world: dict[str, Any], proposals: list[Proposal]) -> None:
    """Authoritative merge; proposals cannot directly mutate protected state."""
    if {p.agent_id for p in proposals} != set(AGENT_IDS):
        raise ValueError("proposal set must contain exactly six agents")
    if any(p.tick != world["tick"] + 1 for p in proposals):
        raise ValueError("proposal tick mismatch")
    ordered = sorted(proposals, key=lambda p: AGENT_IDS.index(p.agent_id))
    ledger = _ledger(world)
    tick = world["tick"] + 1
    world["tick"] = tick
    for index, proposal in enumerate(ordered):
        if proposal.action == "move":
            world["positions"][index] = (world["positions"][index] + 1) % WORLD_SIZE
        elif proposal.action == "gather":
            world["inventory"][index] += 1
        world["energy"][index] = max(0, world["energy"][index] - 1)
        ledger = ledger.append(tick, proposal.agent_id, "action",
                              {"action": proposal.action,
                               "model_version": proposal.model_version})
    if tick in (4, 7):
        obligation_index = 0 if tick == 4 else 1
        obligation = world["obligations"][obligation_index]
        if obligation["status"] == "open":
            obligation["status"] = "fulfilled"
            ledger = ledger.append(tick, obligation["debtor"], "fulfilment",
                                  {"obligation_id": obligation["id"]})
            obligation["provenance"] = ledger.events[-1]["hash"]
    world["semantic_counter"] += sum(p.action == "move" for p in ordered)
    world["ledger"] = ledger.to_list()
    for index, aid in enumerate(AGENT_IDS):
        world["observer_outputs"][aid].append(observation(world, index))

def semantic_state(world: dict[str, Any]) -> dict[str, Any]:
    return {
        "tick": world["tick"], "identities": list(world["identities"]),
        "positions": list(world["positions"]), "energy": list(world["energy"]),
        "inventory": list(world["inventory"]),
        "obligations": deepcopy(world["obligations"]),
        "semantic_counter": world["semantic_counter"],
        "ledger_tip": Ledger.from_list(world["ledger"]).tip,
        "authority": deepcopy(world["authority"]),
    }

def semantic_digest(world: dict[str, Any]) -> str:
    return checksum(semantic_state(world))

def public_world(world: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed": world["seed"], "tick": world["tick"],
        "identities": list(world["identities"]),
        "positions": list(world["positions"]), "energy": list(world["energy"]),
        "inventory": list(world["inventory"]),
        "obligations": deepcopy(world["obligations"]),
        "semantic_counter": world["semantic_counter"],
        "ledger": deepcopy(world["ledger"]),
        "observer_outputs": deepcopy(world["observer_outputs"]),
        "semantic_digest": semantic_digest(world),
        "authority": deepcopy(world["authority"]),
    }