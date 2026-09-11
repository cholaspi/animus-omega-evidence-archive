"""Test 05, section 16: expansion and contraction.

Defines the represented-world size

    R(t) = live entities + live represented-region cells

for this implemented model as:

    live entities            = number of agents currently holding a
                                nonzero balance (an "active participant"
                                proxy -- an agent with zero balance holds
                                no live stake in the represented world)
    live represented-region cells = number of obligations still open
                                (outstanding narrative structure not yet
                                folded back into the trunk)

This is a declared, honest mapping onto a world model that does not have a
separate spatial "region cell" concept: an obligation is the model's unit
of represented, not-yet-resolved structure, and an agent's non-zero holding
is the model's unit of a "live", currently-participating entity. Both
counts are read directly from executed state at each tick, never asserted.

Support requires ticks t0 < t1 < t2 with R(t1) >= 2*R(t0) and
R(t2) <= R(t0) + 1, computed by exhaustively enumerating admissible
histories and searching for at least one that exhibits the pattern (rather
than checking only a single hand-picked reference history).
"""

from __future__ import annotations

from . import world as W


def live_entities(state: dict) -> int:
    return sum(1 for a in state["agents"].values() if a["balance"] > 0)


def live_region_cells(state: dict) -> int:
    return sum(1 for o in state["obligations"].values() if o["status"] == "open")


def r_series(config: W.WorldConfig, history: tuple[str, ...]) -> list[int]:
    """R(t) for t = 0..history_length, replaying the history tick by tick."""
    state = W.initial_state(config)
    series = [live_entities(state) + live_region_cells(state)]
    for action in history:
        state = W.step(state, action, config)
        series.append(live_entities(state) + live_region_cells(state))
    return series


def find_expansion_contraction_pattern(series: list[int]) -> dict | None:
    """Searches for t0 < t1 < t2 with R(t1) >= 2*R(t0) and R(t2) <= R(t0)+1.
    Returns the first such triple found (by t0, then t1, then t2, in
    increasing order) or None."""
    n = len(series)
    for t0 in range(n):
        r0 = series[t0]
        if r0 <= 0:
            continue  # 2*0 = 0 would make "expansion" vacuous
        for t1 in range(t0 + 1, n):
            if series[t1] < 2 * r0:
                continue
            for t2 in range(t1 + 1, n):
                if series[t2] <= r0 + 1:
                    return {"t0": t0, "t1": t1, "t2": t2, "r_t0": r0, "r_t1": series[t1], "r_t2": series[t2]}
    return None


def theoretical_max_r(config: W.WorldConfig) -> dict:
    """The provable ceiling on R(t) for this config, independent of which
    history is chosen: at most every agent holds nonzero balance
    (num_agents) and no obligation has yet resolved (num_obligations).
    Reported so an "unsupported" result is explained by exact arithmetic
    rather than left as an unexplained exhaustive-search failure."""
    r0 = 1 + config.num_obligations  # genesis: one holder, no resolutions yet
    r_max = config.num_agents + config.num_obligations
    return {
        "r_at_genesis": r0,
        "provable_ceiling": r_max,
        "required_for_expansion": 2 * r0,
        "expansion_mathematically_possible": r_max >= 2 * r0,
    }


def evaluate_world_family(config: W.WorldConfig) -> dict:
    """Exhaustively searches every admissible history for at least one that
    exhibits the required expansion/contraction pattern."""
    best_example = None
    checked = 0
    for history in W.enumerate_histories(config):
        checked += 1
        series = r_series(config, history)
        pattern = find_expansion_contraction_pattern(series)
        if pattern is not None:
            best_example = {"history": list(history), "r_series": series, "pattern": pattern}
            break
    status = "supported" if best_example is not None else "unsupported"
    ceiling = theoretical_max_r(config)
    if status == "unsupported" and not ceiling["expansion_mathematically_possible"]:
        reason = (
            f"no admissible history can exhibit the pattern: R(genesis)={ceiling['r_at_genesis']}, so "
            f"2x expansion would require R>={ceiling['required_for_expansion']}, but this config's provable "
            f"ceiling (every agent holding balance, no obligation yet resolved) is only {ceiling['provable_ceiling']}"
        )
    elif status == "unsupported":
        reason = "expansion is mathematically possible for this config, but no enumerated history achieved it"
    else:
        reason = "at least one admissible history exhibits R(t1) >= 2*R(t0) and R(t2) <= R(t0)+1 for some t0<t1<t2"
    return {
        "world_id": config.world_id,
        "definition": "R(t) = agents with nonzero balance + obligations still open",
        "histories_checked": checked,
        "theoretical_max_r": ceiling,
        "status": status,
        "reason": reason,
        "example": best_example,
    }


def preflight_feasibility_check(world_families) -> dict:
    """Protocol v1.3.0-dev4, correction 10: a mechanical, non-bypassable
    preflight gate for the section-16 expansion/contraction requirement.
    Actually runs the same exhaustive search evaluate_world_family() uses
    (not just the ceiling arithmetic) against every family's configured
    dimensions, before any seed executes or any evidence is frozen. If the
    configured maximum represented-world size cannot satisfy the required
    inequality -- either because it is mathematically impossible (the
    ceiling never reaches 2*R(t0)) or because it is merely never witnessed
    by an actual enumerated history within the configured history_length --
    this returns feasible: False so the caller (run.freeze()) can refuse to
    freeze rather than silently seal a protocol version that repeats
    v1.2.0-dev3's failure mode."""
    per_family = {}
    for wf in world_families:
        result = evaluate_world_family(wf.config)
        per_family[wf.family_id] = {
            "status": result["status"],
            "theoretical_max_r": result["theoretical_max_r"],
            "witnessed_by_history": result["example"] is not None,
        }
    feasible = all(r["status"] == "supported" for r in per_family.values()) and bool(per_family)
    return {
        "feasible": feasible,
        "per_world_family": per_family,
        "reason": (
            "every world family's configured dimensions admit at least one exhaustively-enumerated "
            "history satisfying R(t1) >= 2*R(t0) and R(t2) <= R(t0)+1"
            if feasible
            else "at least one world family's configured dimensions cannot satisfy the expansion/contraction "
            "inequality (see per_world_family for which, and whether it is mathematically impossible or "
            "merely unwitnessed by the configured history_length)"
        ),
    }


def run_component(world_families) -> dict:
    per_family = {}
    for wf in world_families:
        per_family[wf.family_id] = evaluate_world_family(wf.config)
    statuses = [r["status"] for r in per_family.values()]
    overall = "supported" if statuses and all(s == "supported" for s in statuses) else (
        "unsupported" if statuses else "invalid"
    )
    return {
        "status": overall,
        "reason": (
            "both world families exhibit the required expansion/contraction pattern in at least one "
            "admissible history"
            if overall == "supported"
            else "at least one world family has no admissible history exhibiting the required pattern"
        ),
        "per_world_family": per_family,
    }
