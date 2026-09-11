"""Test 05C: Observer Boundary Detection.

Research question: can a specified bounded observer distinguish boundary
observations from phase-matched interior observations?

Everything that must be frozen before execution (per the protocol) is
declared as module-level constants and pure functions below: the observer
ladder, the boundary/interior window definitions, the phase-matching rule,
the test statistic, the null model, and the two thresholds (one for
bounded-observer indistinguishability, one for positive-control
sensitivity). Because every world family here is small enough to enumerate
exactly, P(observation | boundary) and P(observation | interior) are exact
histograms over the full admissible-history space under a frozen null model
(histories uniformly likely) rather than samples, so no sampling-uncertainty
procedure is needed; this is recorded explicitly in the result.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

from . import world as W

WINDOW = 2

# Frozen thresholds (declared before any history is executed or observed).
INDISTINGUISHABILITY_TV_THRESHOLD = 0.05  # bounded observer: TV below this -> "supported"
POSITIVE_CONTROL_TV_THRESHOLD = 0.20  # full-state observer: TV above this -> control valid


def boundary_and_interior_starts(config: W.WorldConfig) -> tuple[int, int]:
    """Frozen window definition: boundary window is the last WINDOW ticks
    of the history; interior window is the phase-matched window (same
    tick-mod-num_agents position) that starts earliest while remaining
    strictly before the boundary window. This is a pure function of
    config, fixed before any history executes."""
    n = config.num_agents
    boundary_start = config.history_length - WINDOW
    phase = boundary_start % n
    candidates = [s for s in range(0, boundary_start) if s % n == phase]
    if not candidates:
        return boundary_start, -1  # no phase-matched interior window exists
    interior_start = max(candidates)
    return boundary_start, interior_start


def _window_states(config: W.WorldConfig, history: tuple[str, ...], start: int) -> list[dict]:
    """The sequence of WINDOW full states observed *after* each action in
    [start, start+WINDOW), replaying only that prefix of the history."""
    state = W.initial_state(config)
    states = []
    for i, action in enumerate(history):
        state = W.step(state, action, config)
        if start <= i < start + WINDOW:
            states.append(state)
        if i >= start + WINDOW - 1:
            break
    return states


# ---------------------------------------------------------------------------
# Observer ladder (frozen: information access, memory, window)
# ---------------------------------------------------------------------------

def _percept_radius_one_local(states: list[dict], config: W.WorldConfig) -> tuple:
    """Sees only its own (agent a0) balance, and only at the final tick of
    the window (memory capacity: 1 tick)."""
    aid = config.agent_ids()[0]
    last = states[-1]
    return (last["agents"][aid]["balance"],)


def _percept_local_short_memory(states: list[dict], config: W.WorldConfig) -> tuple:
    """Sees only agent a0's balance, but across the whole window (memory
    capacity: WINDOW ticks)."""
    aid = config.agent_ids()[0]
    return tuple(s["agents"][aid]["balance"] for s in states)


def _percept_local_relationship_memory(states: list[dict], config: W.WorldConfig) -> tuple:
    """Adds, at each tick, whether the last recorded event's actor was a0
    (a purely local relationship/interaction signal)."""
    aid = config.agent_ids()[0]
    out = []
    for s in states:
        bal = s["agents"][aid]["balance"]
        was_actor = bool(s["event_log"]) and s["event_log"][-1]["actor"] == aid
        out.append((bal, was_actor))
    return tuple(out)


def _percept_local_obligation_history(states: list[dict], config: W.WorldConfig) -> tuple:
    """Adds the status of the one obligation owned by a0 (if any)."""
    aid = config.agent_ids()[0]
    owned = [oid for oid, o in states[-1]["obligations"].items() if o["owner"] == aid]
    owned_id = owned[0] if owned else None
    out = []
    for s in states:
        bal = s["agents"][aid]["balance"]
        was_actor = bool(s["event_log"]) and s["event_log"][-1]["actor"] == aid
        status = s["obligations"][owned_id]["status"] if owned_id else None
        out.append((bal, was_actor, status))
    return tuple(out)


def _percept_bounded_longer_memory(states: list[dict], config: W.WorldConfig) -> tuple:
    """Wider in space (sees every agent's balance) rather than time: still
    only the window ticks, but not restricted to a single agent."""
    out = []
    for s in states:
        out.append(tuple(s["agents"][aid]["balance"] for aid in config.agent_ids()))
    return tuple(out)


def _percept_full_state(states: list[dict], config: W.WorldConfig) -> tuple:
    """Positive control: everything, including tick number and obligation
    status for every obligation."""
    out = []
    for s in states:
        out.append(
            (
                s["tick"],
                tuple(s["agents"][aid]["balance"] for aid in config.agent_ids()),
                tuple((oid, s["obligations"][oid]["status"]) for oid in config.obligation_ids()),
            )
        )
    return tuple(out)


OBSERVER_LADDER: list[tuple[str, str, Callable[[list[dict], W.WorldConfig], tuple]]] = [
    ("radius_one_local", "Radius-one local observer (own balance, last tick only).", _percept_radius_one_local),
    ("local_short_memory", "Local observer with short memory (own balance across the window).", _percept_local_short_memory),
    ("local_relationship_memory", "Local observer with relationship memory (own balance + was-actor).", _percept_local_relationship_memory),
    ("local_obligation_history", "Local observer with obligation history (adds own obligation status).", _percept_local_obligation_history),
    ("bounded_longer_memory", "Bounded observer with longer (wider) memory (all balances, window ticks).", _percept_bounded_longer_memory),
    ("full_state_positive_control", "Full-state observer (positive control): tick + all balances + all obligation statuses.", _percept_full_state),
]


# ---------------------------------------------------------------------------
# Exact distributions and statistics
# ---------------------------------------------------------------------------

def exact_distribution(config: W.WorldConfig, start: int, percept_fn) -> dict[tuple, float]:
    histories = W.enumerate_histories(config)
    counts: dict[tuple, int] = {}
    for h in histories:
        states = _window_states(config, h, start)
        obs = percept_fn(states, config)
        counts[obs] = counts.get(obs, 0) + 1
    total = len(histories)
    return {k: v / total for k, v in counts.items()}, total


def total_variation_distance(p: dict[tuple, float], q: dict[tuple, float]) -> float:
    keys = set(p.keys()) | set(q.keys())
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def bayes_optimal_accuracy(tv: float) -> float:
    return 0.5 * (1 + tv)


def mutual_information(p_boundary: dict[tuple, float], p_interior: dict[tuple, float]) -> float:
    keys = set(p_boundary.keys()) | set(p_interior.keys())
    mi = 0.0
    for k in keys:
        pb = p_boundary.get(k, 0.0)
        pi = p_interior.get(k, 0.0)
        p_o = 0.5 * pb + 0.5 * pi
        if p_o <= 0:
            continue
        if pb > 0:
            mi += 0.5 * pb * math.log2(pb / p_o)
        if pi > 0:
            mi += 0.5 * pi * math.log2(pi / p_o)
    return mi


def likelihood_ratio_summary(p_boundary: dict[tuple, float], p_interior: dict[tuple, float]) -> dict:
    keys = set(p_boundary.keys()) | set(p_interior.keys())
    ratios = {}
    for k in keys:
        pb = p_boundary.get(k, 0.0)
        pi = p_interior.get(k, 0.0)
        if pi == 0 and pb == 0:
            continue
        if pi == 0:
            ratios[repr(k)] = math.inf
        else:
            ratios[repr(k)] = pb / pi
    finite = [v for v in ratios.values() if math.isfinite(v)]
    return {
        "max_finite_ratio": max(finite) if finite else None,
        "min_finite_ratio": min(finite) if finite else None,
        "boundary_only_observations": sum(1 for v in ratios.values() if v == math.inf),
        "num_distinct_observations": len(ratios),
    }


@dataclass
class ObserverResult:
    observer_id: str
    description: str
    total_variation_distance: float
    bayes_optimal_accuracy: float
    mutual_information_bits: float
    likelihood_ratio_summary: dict
    enumeration_count: int
    is_positive_control: bool
    conclusion: str


def evaluate_world_family(wf, seed: int | None = None) -> dict:
    config = wf.config
    boundary_start, interior_start = boundary_and_interior_starts(config)
    if interior_start < 0:
        return {
            "world_id": config.world_id,
            "status": "inconclusive",
            "reason": "no phase-matched interior window exists for this world family's history length",
            "boundary_start": boundary_start,
            "interior_start": None,
        }

    results: list[ObserverResult] = []
    for observer_id, desc, fn in OBSERVER_LADDER:
        p_boundary, n_enum = exact_distribution(config, boundary_start, fn)
        p_interior, _ = exact_distribution(config, interior_start, fn)
        tv = total_variation_distance(p_boundary, p_interior)
        acc = bayes_optimal_accuracy(tv)
        mi = mutual_information(p_boundary, p_interior)
        lr = likelihood_ratio_summary(p_boundary, p_interior)
        is_control = observer_id == "full_state_positive_control"
        if is_control:
            conclusion = "positive_control_valid" if tv > POSITIVE_CONTROL_TV_THRESHOLD else "positive_control_failed"
        else:
            conclusion = "supported" if tv < INDISTINGUISHABILITY_TV_THRESHOLD else "unsupported"
        results.append(
            ObserverResult(
                observer_id=observer_id,
                description=desc,
                total_variation_distance=round(tv, 6),
                bayes_optimal_accuracy=round(acc, 6),
                mutual_information_bits=round(mi, 6),
                likelihood_ratio_summary=lr,
                enumeration_count=n_enum,
                is_positive_control=is_control,
                conclusion=conclusion,
            )
        )

    control = next(r for r in results if r.is_positive_control)
    bounded = [r for r in results if not r.is_positive_control]

    if control.conclusion == "positive_control_failed":
        status = "invalid"
        reason = "full-state positive control failed to detect the boundary; the setup lacks sensitivity"
    elif any(r.conclusion == "unsupported" for r in bounded):
        status = "unsupported"
        reason = "a qualifying distinction was detected for at least one bounded observer class"
    else:
        status = "supported"
        reason = "no bounded observer class exceeded the frozen indistinguishability threshold"

    return {
        "world_id": config.world_id,
        "config": config.to_dict(),
        "window": WINDOW,
        "boundary_start": boundary_start,
        "interior_start": interior_start,
        "null_model": "histories uniformly likely over the full enumerated admissible-history space (exact, no sampling)",
        "indistinguishability_tv_threshold": INDISTINGUISHABILITY_TV_THRESHOLD,
        "positive_control_tv_threshold": POSITIVE_CONTROL_TV_THRESHOLD,
        "observers": [vars(r) for r in results],
        "status": status,
        "reason": reason,
    }


def run_component(observer_world_families) -> dict:
    per_family = {}
    for wf in observer_world_families:
        per_family[wf.family_id] = evaluate_world_family(wf)
    statuses = [r["status"] for r in per_family.values()]
    if not statuses:
        overall = "invalid"
    elif any(s == "invalid" for s in statuses):
        overall = "invalid"
    elif all(s == "supported" for s in statuses):
        overall = "supported"
    elif any(s == "unsupported" for s in statuses):
        overall = "unsupported"
    else:
        overall = "inconclusive"
    return {"status": overall, "per_world_family": per_family}
