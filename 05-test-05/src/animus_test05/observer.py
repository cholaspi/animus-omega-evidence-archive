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
from .hashing import hash_obj

WINDOW = 2

# Frozen thresholds (declared before any history is executed or observed),
# per protocol v1.2.0-dev3 section 14. The primary claim requires BOTH
# statistics to clear their bound; the positive control requires EITHER.
INDISTINGUISHABILITY_TV_THRESHOLD = 0.05  # primary observer: TV <= this
INDISTINGUISHABILITY_ACCURACY_THRESHOLD = 0.55  # primary observer: Bayes accuracy <= this
POSITIVE_CONTROL_TV_THRESHOLD = 0.25  # full-state observer: TV >= this, or...
POSITIVE_CONTROL_ACCURACY_THRESHOLD = 0.75  # ...Bayes accuracy >= this
MIN_MATCHED_OBSERVATIONS_PER_CLASS = 200  # below this without exact enumeration -> inconclusive
MIN_MATCHING_COVERAGE = 0.90  # fraction of boundary windows needing an eligible interior match


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


PRIMARY_OBSERVER_SPEC: dict = {
    "observer_id": "primary_bounded_observer",
    "radius": "radius-one (own state plus the single ring edge it directly participates in)",
    "memory_ticks": WINDOW,
    "information_access": ["own_identity", "own_balance", "direct_relationship_edge", "own_current_obligation_status"],
    "excluded_information": [
        "global_clock", "absolute_cycle_position", "boundary_marker",
        "full_state", "unrestricted_full_ledger_access", "other_agents_state",
    ],
    "frozen_before_execution": True,
}

# Computed once at import time, before any world family is evaluated, so
# this hash is the same for every run of this protocol version regardless
# of which world families or seeds are used -- it depends only on the
# frozen observer specification above.
_PRIMARY_OBSERVER_SPEC_HASH = hash_obj(PRIMARY_OBSERVER_SPEC)


def _percept_primary_bounded_observer(states: list[dict], config: W.WorldConfig) -> tuple:
    """The single frozen primary bounded-observer claim (protocol v2,
    update B): radius-one local state access, two ticks of memory, its own
    identity, its direct (ring) relationship, and its current obligation
    status. No global clock, no absolute cycle position, no boundary
    marker, no full-state access, and no ledger access at all."""
    aid = config.agent_ids()[0]
    n = config.num_agents
    target = config.agent_ids()[1 % n]
    owned = [oid for oid, o in states[-1]["obligations"].items() if o["owner"] == aid]
    owned_id = owned[0] if owned else None
    out = []
    for s in states:
        out.append(
            (
                aid,  # own identity (constant, but genuinely read, never a boundary marker)
                s["agents"][aid]["balance"],
                s["relationships"].get(f"{aid}->{target}"),  # direct relationship edge only
                s["obligations"][owned_id]["status"] if owned_id else None,
            )
        )
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


ROLE_PRIMARY = "primary"
ROLE_SENSITIVITY = "sensitivity_analysis"
ROLE_POSITIVE_CONTROL = "positive_control"

# Protocol v2, update B: exactly one observer class carries the
# supported/unsupported bounded-observer claim (role=primary). Every other
# bounded class is a sensitivity analysis only -- informative, but never an
# alternate opportunity to obtain "supported" if the primary class fails.
# The full-state observer remains a mandatory positive control.
OBSERVER_LADDER: list[tuple[str, str, Callable[[list[dict], W.WorldConfig], tuple], str]] = [
    ("primary_bounded_observer", "PRIMARY: radius-one, 2-tick memory, own identity/relationship/obligation only.", _percept_primary_bounded_observer, ROLE_PRIMARY),
    ("radius_one_local", "Sensitivity analysis: own balance, last tick only (less information than primary).", _percept_radius_one_local, ROLE_SENSITIVITY),
    ("local_short_memory", "Sensitivity analysis: own balance across the window, no relationship/obligation field.", _percept_local_short_memory, ROLE_SENSITIVITY),
    ("local_relationship_memory", "Sensitivity analysis: own balance + was-actor interaction signal.", _percept_local_relationship_memory, ROLE_SENSITIVITY),
    ("local_obligation_history", "Sensitivity analysis: own balance + was-actor + own obligation status.", _percept_local_obligation_history, ROLE_SENSITIVITY),
    ("bounded_longer_memory", "Sensitivity analysis: wider in space (all agents' balances) rather than deeper in local detail.", _percept_bounded_longer_memory, ROLE_SENSITIVITY),
    ("full_state_positive_control", "MANDATORY POSITIVE CONTROL: tick + all balances + all obligation statuses.", _percept_full_state, ROLE_POSITIVE_CONTROL),
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
    role: str
    total_variation_distance: float
    bayes_optimal_accuracy: float
    mutual_information_bits: float
    likelihood_ratio_summary: dict
    enumeration_count: int
    is_positive_control: bool
    conclusion: str
    # Window/coverage bookkeeping (protocol v1.2.0-dev3 section 14). Exact
    # enumeration pairs every history with exactly one boundary window and
    # one phase-matched interior window, so coverage is 100% and
    # multiplicity is 1 by construction -- this is recorded explicitly
    # rather than left implicit.
    num_boundary_windows: int = 0
    num_interior_windows: int = 0
    matching_coverage: float = 1.0
    unmatched_windows: int = 0
    match_multiplicity: int = 1
    weighting_procedure: str = "uniform over enumerated admissible histories"
    notes: str = ""


def evaluate_world_family(wf, seed: int | None = None) -> dict:
    # 05C always uses this family's *observer* configuration (same agent
    # count / obligation structure, longer history) rather than the short
    # standard_config used by 05A/05B/05D, so a phase-matched interior
    # window exists.
    config = wf.observer_config
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
    for observer_id, desc, fn, role in OBSERVER_LADDER:
        p_boundary, n_enum = exact_distribution(config, boundary_start, fn)
        p_interior, _ = exact_distribution(config, interior_start, fn)
        tv = total_variation_distance(p_boundary, p_interior)
        acc = bayes_optimal_accuracy(tv)
        mi = mutual_information(p_boundary, p_interior)
        lr = likelihood_ratio_summary(p_boundary, p_interior)
        is_control = role == ROLE_POSITIVE_CONTROL
        if is_control:
            conclusion = (
                "positive_control_valid"
                if (tv >= POSITIVE_CONTROL_TV_THRESHOLD or acc >= POSITIVE_CONTROL_ACCURACY_THRESHOLD)
                else "positive_control_failed"
            )
        else:
            conclusion = (
                "supported"
                if (tv <= INDISTINGUISHABILITY_TV_THRESHOLD and acc <= INDISTINGUISHABILITY_ACCURACY_THRESHOLD)
                else "unsupported"
            )
        # Exact enumeration pairs every one of the n_enum admissible
        # histories with exactly one boundary window and one phase-matched
        # interior window, so coverage is 100% (0 unmatched, multiplicity
        # 1) by construction, not by assertion.
        results.append(
            ObserverResult(
                observer_id=observer_id,
                description=desc,
                role=role,
                total_variation_distance=round(tv, 6),
                bayes_optimal_accuracy=round(acc, 6),
                mutual_information_bits=round(mi, 6),
                likelihood_ratio_summary=lr,
                enumeration_count=n_enum,
                is_positive_control=is_control,
                conclusion=conclusion,
                num_boundary_windows=n_enum,
                num_interior_windows=n_enum,
                matching_coverage=1.0,
                unmatched_windows=0,
                match_multiplicity=1,
            )
        )

    # The "primary observer with eight ticks of memory" sensitivity rung
    # (protocol section 14's ladder item 3) is mathematically intractable
    # to enumerate exactly: with a shared window size of 8 the boundary and
    # a non-overlapping phase-matched interior window require
    # history_length >= 2*8 + num_agents, giving an admissible-history
    # space of alphabet_size**history_length >= 4**24 (~2.8e14), far past
    # the protocol's 1,000,000-history exhaustion bound. Rather than
    # quietly substitute sampling for this one diagnostic rung, it is
    # reported as inconclusive with the arithmetic shown, per "mark
    # exhaustion inconclusive... do not quietly replace enumeration with
    # sampling."
    required_history_length_for_8_tick_window = 2 * 8 + config.num_agents
    infeasible_history_count = len(W.ACTIONS) ** required_history_length_for_8_tick_window
    results.append(
        ObserverResult(
            observer_id="primary_with_eight_tick_memory",
            description="Sensitivity analysis: primary observer fields with an 8-tick window (ladder item 3).",
            role=ROLE_SENSITIVITY,
            total_variation_distance=None,
            bayes_optimal_accuracy=None,
            mutual_information_bits=None,
            likelihood_ratio_summary={},
            enumeration_count=0,
            is_positive_control=False,
            conclusion="inconclusive",
            num_boundary_windows=0,
            num_interior_windows=0,
            matching_coverage=0.0,
            unmatched_windows=0,
            match_multiplicity=0,
            weighting_procedure="not applicable: not computed",
            notes=(
                f"not computed: exact enumeration would require history_length="
                f"{required_history_length_for_8_tick_window}, i.e. "
                f"{infeasible_history_count:.3e} admissible histories, exceeding the "
                "protocol's 1,000,000-history exhaustion bound; not sampled because this "
                "protocol requires exact enumeration or an explicit inconclusive mark, "
                "never a quiet sampling substitution"
            ),
        )
    )

    control = next(r for r in results if r.role == ROLE_POSITIVE_CONTROL)
    primary = next(r for r in results if r.role == ROLE_PRIMARY)
    sensitivity = [r for r in results if r.role == ROLE_SENSITIVITY]

    # Protocol v1.2.0-dev3, section 14: only the primary observer's result
    # and the positive control determine status. Sensitivity-analysis
    # classes are reported for context but are never an alternate path to
    # "supported" and never independently downgrade it either.
    if control.conclusion == "positive_control_failed":
        status = "invalid"
        reason = "full-state positive control failed to detect the boundary; the setup lacks sensitivity"
    elif primary.conclusion == "unsupported":
        status = "unsupported"
        reason = "the frozen primary bounded observer detected a qualifying distinction (TV or accuracy over threshold)"
    else:
        status = "supported"
        reason = "the frozen primary bounded observer stayed under both the TV and accuracy indistinguishability thresholds"

    return {
        "world_id": config.world_id,
        "config": config.to_dict(),
        "primary_observer_spec": PRIMARY_OBSERVER_SPEC,
        "primary_observer_spec_hash": _PRIMARY_OBSERVER_SPEC_HASH,
        "window": WINDOW,
        "boundary_start": boundary_start,
        "interior_start": interior_start,
        "null_model": "histories uniformly likely over the full enumerated admissible-history space (exact, no sampling)",
        "indistinguishability_tv_threshold": INDISTINGUISHABILITY_TV_THRESHOLD,
        "indistinguishability_accuracy_threshold": INDISTINGUISHABILITY_ACCURACY_THRESHOLD,
        "positive_control_tv_threshold": POSITIVE_CONTROL_TV_THRESHOLD,
        "positive_control_accuracy_threshold": POSITIVE_CONTROL_ACCURACY_THRESHOLD,
        "matching_coverage": 1.0,
        "matching_coverage_meets_minimum": 1.0 >= MIN_MATCHING_COVERAGE,
        "observers": [vars(r) for r in results],
        "primary_result": vars(primary),
        "positive_control_result": vars(control),
        "sensitivity_analysis_results": [vars(r) for r in sensitivity],
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
