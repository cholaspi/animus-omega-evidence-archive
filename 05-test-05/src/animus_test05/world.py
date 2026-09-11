"""Shared deterministic "story world" used by every Test 05 component.

This is intentionally small and exactly enumerable rather than large and
opaque (per the run procedure's instruction to prefer exhaustive analysis
over large random simulation). A world instance has:

- a fixed number of agents arranged in a ring of transfer relationships;
- a fixed number of obligations forming a causal-dependency chain;
- a per-agent private nuisance field (``internal_seed`` / ``private_trace``)
  that is genuinely irrelevant to every public/semantic quantity and exists
  specifically so information loss and irrelevant-intervention claims can be
  demonstrated rather than asserted;
- a deterministic transition function over a small action alphabet, so the
  full admissible-history space is exactly enumerable for small
  ``history_length``.

Nothing here depends on arm names, expected outcomes, or test labels: the
transition function only ever looks at the action symbol, the current state,
and (for RNG-bearing actions used elsewhere in the suite) an explicit seed.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field, asdict
from typing import Any

from . import hashing

# The full action alphabet. "move" and "resolve" are causally relevant to
# every public/semantic quantity (balances, obligations, the return value).
# "noop_x" / "noop_y" are causally irrelevant to all public/semantic
# quantities: they only churn a private per-agent nuisance field. Having two
# distinct irrelevant symbols lets an "irrelevant mutation" arm change the
# executed symbol at a tick without becoming a relevant-action mutation.
ACTIONS: tuple[str, ...] = ("move", "resolve", "noop_x", "noop_y")
RELEVANT_ACTIONS = ("move", "resolve")
IRRELEVANT_ACTIONS = ("noop_x", "noop_y")


@dataclass(frozen=True)
class WorldConfig:
    world_id: str
    num_agents: int
    num_obligations: int
    history_length: int
    total_resource: int
    reconstruction_algorithm: str = "faithful_replay"  # or "lossy_replay"
    ledger_capacity: int = 64

    def agent_ids(self) -> list[str]:
        return [f"a{i}" for i in range(self.num_agents)]

    def obligation_ids(self) -> list[str]:
        return [f"o{i}" for i in range(self.num_obligations)]

    def to_dict(self) -> dict:
        return asdict(self)

    def config_hash(self) -> str:
        return hashing.hash_obj(self.to_dict())


def initial_state(config: WorldConfig) -> dict:
    agents = config.agent_ids()
    n = config.num_agents
    agent_state = {}
    for i, aid in enumerate(agents):
        agent_state[aid] = {
            "balance": config.total_resource if i == 0 else 0,
            # Private nuisance field: genuinely irrelevant to every public
            # quantity. Seeded deterministically from the world id and index
            # only (never from an outcome, and never from Python's
            # process-randomized builtin hash()), so it is reproducible
            # across processes and machines.
            "internal_seed": _stable_seed(f"{config.world_id}:{aid}"),
            "private_trace": [],
        }

    relationships = {}
    for i in range(n):
        a, b = agents[i], agents[(i + 1) % n]
        relationships[f"{a}->{b}"] = 1

    obligations = {}
    causal_deps = {}
    for i, oid in enumerate(config.obligation_ids()):
        owner = agents[i % n]
        target = agents[(i + 1) % n]
        obligations[oid] = {
            "owner": owner,
            "target": target,
            "resource": 1,
            "deadline": config.history_length - i,
            "status": "open",
            "provenance": f"genesis:{i}",
        }
        causal_deps[oid] = config.obligation_ids()[i - 1] if i > 0 else None

    return {
        "tick": 0,
        "agents": agent_state,
        "obligations": obligations,
        "relationships": relationships,
        "causal_deps": causal_deps,
        "event_log": [],
    }


def _stable_seed(text: str) -> int:
    """Deterministic replacement for builtin hash() (which is randomized per
    process via PYTHONHASHSEED). Uses sha256 so it is stable across
    processes, machines, and Python versions."""
    import hashlib

    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16) & 0x7FFFFFFF


def _lcg_next(x: int) -> int:
    return (1103515245 * x + 12345) & 0x7FFFFFFF


def _apply_action_effect(new_state: dict, action: str, tick: int, config: WorldConfig) -> dict:
    """Mutates ``new_state`` in place applying ``action`` as if it were the
    action executed at logical clock value ``tick``, and returns the event
    record. ``tick`` is an explicit parameter (never read from
    ``new_state["tick"]``) so this same logic can be used both for live,
    sequential execution and for replaying a sparse ledger whose entries
    carry their own original tick numbers with gaps where irrelevant actions
    were skipped."""
    n = config.num_agents
    agents = config.agent_ids()
    mover = agents[tick % n]
    event: dict[str, Any] = {"tick": tick, "action": action, "actor": mover}

    if action == "move":
        target = agents[(tick + 1) % n]
        rel_key = f"{mover}->{target}"
        if new_state["relationships"].get(rel_key) == 1 and new_state["agents"][mover]["balance"] > 0:
            new_state["agents"][mover]["balance"] -= 1
            new_state["agents"][target]["balance"] += 1
            event["effect"] = "transferred"
            event["target"] = target
        else:
            event["effect"] = "blocked_no_balance_or_permission"
            event["target"] = target
    elif action == "resolve":
        oid = config.obligation_ids()[tick % config.num_obligations]
        obl = new_state["obligations"][oid]
        dep = new_state["causal_deps"][oid]
        dep_ok = dep is None or new_state["obligations"][dep]["status"] == "closed"
        event["obligation"] = oid
        if obl["status"] == "closed":
            event["effect"] = "already_closed"
        elif not dep_ok:
            event["effect"] = "blocked_dependency"
        elif new_state["agents"][obl["owner"]]["balance"] >= obl["resource"]:
            new_state["agents"][obl["owner"]]["balance"] -= obl["resource"]
            obl["status"] = "closed"
            event["effect"] = "resolved"
        else:
            event["effect"] = "blocked_resource"
    elif action in IRRELEVANT_ACTIONS:
        # Touches only the private nuisance field of the current mover.
        # Never reads or writes balances, obligations, or relationships.
        cur = new_state["agents"][mover]["internal_seed"]
        bump = 1 if action == "noop_x" else 7
        nxt = _lcg_next(cur + bump)
        new_state["agents"][mover]["internal_seed"] = nxt
        new_state["agents"][mover]["private_trace"].append(nxt)
        event["effect"] = f"private_churn:{action}"
    else:
        raise ValueError(f"unknown action {action!r}")

    return event


def step(state: dict, action: str, config: WorldConfig) -> dict:
    """Pure function: returns a *new* state dict. Never mutates ``state``."""
    import copy

    new_state = copy.deepcopy(state)
    tick = new_state["tick"]
    event = _apply_action_effect(new_state, action, tick, config)
    new_state["event_log"].append(event)
    new_state["tick"] = tick + 1
    return new_state


def run_history(config: WorldConfig, history: tuple[str, ...]) -> dict:
    state = initial_state(config)
    for action in history:
        state = step(state, action, config)
    return state


def enumerate_histories(config: WorldConfig) -> list[tuple[str, ...]]:
    return list(itertools.product(ACTIONS, repeat=config.history_length))


def public_fields(state: dict) -> dict:
    """The portion of state that is semantically meaningful (as opposed to
    the private nuisance fields), used for equality checks that must not be
    sensitive to irrelevant internal churn."""
    return {
        "tick": state["tick"],
        "agents": {
            aid: {"balance": a["balance"]} for aid, a in state["agents"].items()
        },
        "obligations": state["obligations"],
        "relationships": state["relationships"],
    }


def relevant_ledger(state: dict) -> list[dict]:
    """Policy-declared projection of the full event log: drop irrelevant
    (noop_x/noop_y) entries and drop the private-trace payload they would
    otherwise carry. This is a structural policy fixed by action *type*,
    never by outcome, label, or arm identity."""
    out = []
    for ev in state["event_log"]:
        if ev["action"] in IRRELEVANT_ACTIONS:
            continue
        out.append(dict(ev))
    return out


def primary_holder(state: dict) -> str:
    """Deterministic: the agent with the strictly largest balance, ties
    broken by lowest agent index."""
    agents = sorted(state["agents"].keys())
    return max(agents, key=lambda aid: (state["agents"][aid]["balance"], -int(aid[1:])))


def resolved_count(state: dict) -> int:
    return sum(1 for o in state["obligations"].values() if o["status"] == "closed")


def return_value_of(state: dict) -> dict:
    """R(ending_state): the ending-derived quantity that must round-trip
    into the next beginning. Depends only on public/relevant fields."""
    return {
        "primary_holder": primary_holder(state),
        "resolved_count": resolved_count(state),
        "ledger_root": hashing.hash_obj(relevant_ledger(state)),
    }


def replay(config: WorldConfig, ledger: list[dict], algorithm: str | None = None) -> dict:
    """Reconstruct public state fields by replaying a relevant ledger onto a
    fresh copy of the initial state. This is the "reconstructed_state"
    referenced throughout Test 05A/E: a pure function of (config, ledger)
    that never sees the true final microstate directly.

    ``algorithm`` selects a world-family reconstruction variant:
    - "faithful_replay": replays every ledger entry exactly (lossless w.r.t.
      public fields).
    - "lossy_replay": deliberately drops "blocked_*" entries during replay
      (a lossier reconstruction used by some world families to show that
      not every reconstruction algorithm yields a closing history).
    """
    algo = algorithm or config.reconstruction_algorithm
    state = initial_state(config)
    # The relevant ledger is sparse: entries carry their own original tick
    # number, with gaps where irrelevant (noop_x/noop_y) actions were
    # skipped. Replay must apply each entry at *its own* recorded tick
    # (never a locally re-incremented counter) so agent/obligation selection
    # matches the original execution exactly.
    for ev in ledger:
        if algo == "lossy_replay" and ev["action"] == "resolve":
            # A deliberately lossier reconstruction algorithm: it discards
            # all obligation-resolution detail during replay (a declared,
            # world-family-level policy, not a per-history special case).
            # This makes some natural histories fail to reconstruct their
            # true public ending exactly, which is the point of this world
            # family: reconstruction fidelity depends on the reconstruction
            # algorithm, not merely on the existence of a ledger.
            continue
        _apply_action_effect(state, ev["action"], ev["tick"], config)
    # The final tick is always known from configuration (every admissible
    # history in this world has the same declared length): reconstruction is
    # permitted to know the protocol's history length, but never the
    # specific history that produced the ledger.
    state["tick"] = config.history_length
    return state


def replay_with_recomputed_effects(config: WorldConfig, ledger: list[dict]) -> list[dict]:
    """Replays a ledger step by step (always with the faithful algorithm)
    and returns, for each entry, the effect that a fresh deterministic
    recomputation produces at that entry's own tick. Used to detect a
    ledger entry whose stored "effect" field has been tampered with
    independently of the (tick, action) pair that determines the true
    effect -- something ``replay`` itself cannot catch, since it recomputes
    effects from (tick, action) and never reads the stored effect field."""
    state = initial_state(config)
    recomputed = []
    for ev in ledger:
        fresh_event = _apply_action_effect(state, ev["action"], ev["tick"], config)
        recomputed.append(fresh_event)
    return recomputed


def first_mismatch(a: dict, b: dict, path: str = "") -> tuple[str, Any, Any] | None:
    """Return (path, value_in_a, value_in_b) for the first field that
    differs between two canonical JSON-able structures, walking dict keys in
    sorted order and lists by index. Returns None if equal."""
    if isinstance(a, dict) and isinstance(b, dict):
        keys = sorted(set(a.keys()) | set(b.keys()))
        for k in keys:
            if k not in a:
                return (f"{path}.{k}" if path else k, "<missing>", b[k])
            if k not in b:
                return (f"{path}.{k}" if path else k, a[k], "<missing>")
            sub = first_mismatch(a[k], b[k], f"{path}.{k}" if path else k)
            if sub is not None:
                return sub
        return None
    if isinstance(a, list) and isinstance(b, list):
        for i in range(max(len(a), len(b))):
            av = a[i] if i < len(a) else "<missing>"
            bv = b[i] if i < len(b) else "<missing>"
            sub = first_mismatch(av, bv, f"{path}[{i}]")
            if sub is not None:
                return sub
        return None
    if a != b:
        return (path, a, b)
    return None
