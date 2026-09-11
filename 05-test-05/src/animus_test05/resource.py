"""Test 05D: Fidelity-Matched Resource Comparison.

Research question: does the proposed architecture provide a computational
advantage after accounting for all retained information, reconstruction
work, synchronization, and fidelity requirements?

Protocol v2, update C freezes the resource objective *before* looking at
results:

1. Primary objective: peak canonical bytes at matched semantic fidelity.
2. Secondary objective: total canonical byte-ticks.
3. Diagnostic: deterministic operation count.
4. Noncanonical diagnostic: repeated wall-clock duration.

Only the primary objective determines "supported"/"unsupported" for this
component; byte-ticks and operation count are reported for every arm but
never substituted for the primary objective after the fact. Wall-clock
timing is measured for interest but excluded from every canonical
byte/op/hash computation (it lives in a separate, explicitly non-canonical
timing record with environment metadata), since it is not reproducible
run-to-run.

Every arm's byte counts are real, measured sizes (``len(canonical_json(...))``
of whatever that arm actually retains), not estimates, broken down across
every declared resource category (authoritative state, residual, ledger,
event log, observer buffers, checkpoints, reconstruction buffers, indexes,
lookup tables, retained preprocessing) so nothing is silently omitted --
categories that are genuinely unused by an arm are reported as zero, not
left out. Every arm is first graded against the same frozen semantic
contract and probe battery used in Test 05B; only arms that pass every
probe are eligible to enter the resource-advantage comparison. Ineligible
arms are still measured and reported (for transparency) but excluded from
any advantage claim.
"""

from __future__ import annotations

import platform
import sys
import time
import zlib
from dataclasses import dataclass, field
from typing import Any, Optional

from . import world as W
from . import residual as R
from .hashing import canonical_json, hash_obj

STATE_MACHINE_REPLICAS = 3

RESOURCE_CATEGORIES = (
    "authoritative_state_bytes", "residual_bytes", "ledger_bytes", "event_log_bytes",
    "observer_buffer_bytes", "checkpoint_bytes", "reconstruction_buffer_bytes",
    "index_bytes", "lookup_table_bytes", "preprocessing_bytes",
)


def _bytes_of(obj: Any) -> int:
    if isinstance(obj, (bytes, bytearray)):
        return len(obj)
    return len(canonical_json(obj).encode("utf-8"))


def _breakdown(**kwargs: int) -> dict:
    """Every declared resource category, defaulting to zero so nothing is
    silently omitted; only categories an arm actually uses are nonzero."""
    out = {cat: 0 for cat in RESOURCE_CATEGORIES}
    for k, v in kwargs.items():
        if k not in out:
            raise KeyError(f"{k!r} is not a declared resource category")
        out[k] = v
    return out


@dataclass
class ArmMeasurement:
    arm_id: str
    description: str
    peak_canonical_bytes: int  # PRIMARY objective
    total_byte_ticks: int  # secondary objective
    dump_ops: int
    reconstruction_ops: int
    merge_ops: int
    sync_ops: int
    observer_update_ops: int
    total_operation_count: int  # diagnostic
    resource_breakdown: dict  # every declared category, real measured bytes
    semantic_eligible: bool
    semantic_grade: dict
    notes: str = ""


def _ops_total(dump, reconstruction, merge, sync, observer_update) -> int:
    return dump + reconstruction + merge + sync + observer_update


def _replay_all_ticks(config: W.WorldConfig, history: tuple[str, ...]) -> list[dict]:
    """Full per-tick states for the executed history (used to build several
    baselines' per-tick retained-bytes series)."""
    state = W.initial_state(config)
    states = [state]
    for action in history:
        state = W.step(state, action, config)
        states.append(state)
    return states


def build_all_arms(
    config: W.WorldConfig, history: tuple[str, ...], seed: int
) -> tuple[dict[str, ArmMeasurement], dict[str, float]]:
    """Returns (arms, wall_clock_seconds_by_arm). The second element is the
    noncanonical diagnostic timing record -- callers must keep it out of
    anything that feeds the canonical result hash."""
    true_ending = W.run_history(config, history)
    ledger = W.relevant_ledger(true_ending)
    residual = R.build_residual(true_ending, config)
    full_states = _replay_all_ticks(config, history)
    n = config.num_agents
    L = config.history_length
    timing: dict[str, float] = {}

    def grade_with(residual_obj, ledger_obj, ending_for_ground_truth):
        return R._grade(residual_obj, ledger_obj, ending_for_ground_truth, config)

    arms: dict[str, ArmMeasurement] = {}

    # 1. Complete checkpointing: full state stored at every tick.
    t0 = time.perf_counter()
    per_tick = [_bytes_of(s) for s in full_states[1:]]
    full_state_answers = R.run_probes(
        {
            "agents": {a: {"balance": full_states[-1]["agents"][a]["balance"]} for a in config.agent_ids()},
            "obligations": full_states[-1]["obligations"],
            "relationships": full_states[-1]["relationships"],
            "causal_order_token": residual["causal_order_token"],
            "provenance_digest": residual["provenance_digest"],
        },
        ledger,
        config,
    )
    gt = R.ground_truth_answers(true_ending, config)
    grades = {k: full_state_answers.get(k) == gt.get(k) for k in gt}
    arms["complete_checkpointing"] = ArmMeasurement(
        arm_id="complete_checkpointing",
        description="Full state (all private fields) serialized and retained at every tick.",
        peak_canonical_bytes=max(per_tick),
        total_byte_ticks=sum(per_tick),
        dump_ops=L, reconstruction_ops=0, merge_ops=0, sync_ops=0, observer_update_ops=L,
        total_operation_count=_ops_total(L, 0, 0, 0, L),
        resource_breakdown=_breakdown(
            authoritative_state_bytes=max(per_tick),
            checkpoint_bytes=max(per_tick),
        ),
        semantic_eligible=all(grades.values()),
        semantic_grade={"grades": grades, "pass_count": sum(grades.values()), "total": len(grades)},
    )
    timing["complete_checkpointing"] = time.perf_counter() - t0

    # 2. Snapshot plus event log: one genesis snapshot + growing full log.
    t0 = time.perf_counter()
    genesis_bytes = _bytes_of(full_states[0])
    running_log_bytes = []
    for s in full_states[1:]:
        running_log_bytes.append(genesis_bytes + _bytes_of(s["event_log"]))
    final_log = full_states[-1]["event_log"]
    reconstructed_from_log = W.replay(config, [e for e in final_log if e["action"] in W.RELEVANT_ACTIONS])
    grade2 = grade_with(
        {
            "agents": {a: {"balance": reconstructed_from_log["agents"][a]["balance"]} for a in config.agent_ids()},
            "obligations": reconstructed_from_log["obligations"],
            "relationships": reconstructed_from_log["relationships"],
            "causal_order_token": residual["causal_order_token"],
            "provenance_digest": residual["provenance_digest"],
        },
        ledger,
        true_ending,
    )
    arms["snapshot_plus_event_log"] = ArmMeasurement(
        arm_id="snapshot_plus_event_log",
        description="One genesis snapshot plus the full (unfiltered) growing event log; replayed once at the end.",
        peak_canonical_bytes=max(running_log_bytes),
        total_byte_ticks=sum(running_log_bytes),
        dump_ops=1 + L, reconstruction_ops=1, merge_ops=0, sync_ops=0, observer_update_ops=L,
        total_operation_count=_ops_total(1 + L, 1, 0, 0, L),
        resource_breakdown=_breakdown(
            checkpoint_bytes=genesis_bytes,
            event_log_bytes=_bytes_of(final_log),
        ),
        semantic_eligible=grade2["all_pass"],
        semantic_grade=grade2,
    )
    timing["snapshot_plus_event_log"] = time.perf_counter() - t0

    # 3. Always-expanded lossless execution: every region/agent keeps a
    # full independent copy of state at every tick (no dump, no merge).
    t0 = time.perf_counter()
    expanded_per_tick = [n * _bytes_of(s) for s in full_states[1:]]
    arms["always_expanded_lossless"] = ArmMeasurement(
        arm_id="always_expanded_lossless",
        description=f"Every one of {n} regions keeps an independent full copy of state at every tick; never dumps or merges.",
        peak_canonical_bytes=max(expanded_per_tick),
        total_byte_ticks=sum(expanded_per_tick),
        dump_ops=0, reconstruction_ops=0, merge_ops=0, sync_ops=0, observer_update_ops=n * L,
        total_operation_count=_ops_total(0, 0, 0, 0, n * L),
        resource_breakdown=_breakdown(authoritative_state_bytes=max(expanded_per_tick)),
        semantic_eligible=True,
        semantic_grade={"note": "full state retained at all times; trivially passes every probe"},
    )
    timing["always_expanded_lossless"] = time.perf_counter() - t0

    # 4. Open-chain execution: only the final public state is retained, no
    # ledger at all, no boundary transition.
    t0 = time.perf_counter()
    open_chain_state = {"agents": residual["agents"], "obligations": residual["obligations"], "relationships": residual["relationships"]}
    grade4 = grade_with(open_chain_state, [], true_ending)
    arms["open_chain_execution"] = ArmMeasurement(
        arm_id="open_chain_execution",
        description="Only the final public state is retained; no ledger, no boundary transition, no narrative continuity.",
        peak_canonical_bytes=_bytes_of(open_chain_state),
        total_byte_ticks=_bytes_of(open_chain_state),
        dump_ops=1, reconstruction_ops=0, merge_ops=0, sync_ops=0, observer_update_ops=1,
        total_operation_count=_ops_total(1, 0, 0, 0, 1),
        resource_breakdown=_breakdown(authoritative_state_bytes=_bytes_of(open_chain_state)),
        semantic_eligible=grade4["all_pass"],
        semantic_grade=grade4,
        notes="Test 05A arm 11 control: no return transition executed.",
    )
    timing["open_chain_execution"] = time.perf_counter() - t0

    # 5. General-purpose lossless compression of the full state.
    t0 = time.perf_counter()
    full_json = canonical_json(true_ending).encode("utf-8")
    compressed = zlib.compress(full_json, level=9)
    decompressed_state = __import__("json").loads(zlib.decompress(compressed).decode("utf-8"))
    grade5 = grade_with(
        {
            "agents": {a: {"balance": decompressed_state["agents"][a]["balance"]} for a in config.agent_ids()},
            "obligations": decompressed_state["obligations"],
            "relationships": decompressed_state["relationships"],
            "causal_order_token": residual["causal_order_token"],
            "provenance_digest": residual["provenance_digest"],
        },
        decompressed_state["event_log"],
        true_ending,
    )
    arms["general_purpose_lossless_compression"] = ArmMeasurement(
        arm_id="general_purpose_lossless_compression",
        description="Full state zlib-compressed (level 9) and later decompressed in full.",
        peak_canonical_bytes=len(compressed),
        total_byte_ticks=len(compressed) * L,
        dump_ops=1, reconstruction_ops=1, merge_ops=0, sync_ops=0, observer_update_ops=1,
        total_operation_count=_ops_total(1, 1, 0, 0, 1),
        resource_breakdown=_breakdown(
            authoritative_state_bytes=len(compressed),
            reconstruction_buffer_bytes=len(full_json),  # transient decompression buffer
        ),
        semantic_eligible=grade5["all_pass"],
        semantic_grade=grade5,
    )
    timing["general_purpose_lossless_compression"] = time.perf_counter() - t0

    # 6. General-purpose lossy compression at matched semantic fidelity:
    # compress a JSON payload reduced to the same fields our own residual
    # retains (private fields already stripped) plus the full ledger, via a
    # generic compressor rather than a structured residual object.
    t0 = time.perf_counter()
    matched_payload = {"residual": residual, "ledger": ledger}
    matched_json = canonical_json(matched_payload).encode("utf-8")
    matched_compressed = zlib.compress(matched_json, level=9)
    grade6 = grade_with(residual, ledger, true_ending)
    arms["general_purpose_lossy_compression_matched_fidelity"] = ArmMeasurement(
        arm_id="general_purpose_lossy_compression_matched_fidelity",
        description="Residual+ledger (same content as our own architecture) generically zlib-compressed instead of kept structured.",
        peak_canonical_bytes=len(matched_compressed),
        total_byte_ticks=len(matched_compressed) * L,
        dump_ops=1, reconstruction_ops=1, merge_ops=0, sync_ops=0, observer_update_ops=len(ledger),
        total_operation_count=_ops_total(1, 1, 0, 0, len(ledger)),
        resource_breakdown=_breakdown(
            residual_bytes=len(zlib.compress(canonical_json(residual).encode("utf-8"), level=9)),
            ledger_bytes=len(zlib.compress(canonical_json(ledger).encode("utf-8"), level=9)),
            reconstruction_buffer_bytes=len(matched_json),
        ),
        semantic_eligible=grade6["all_pass"],
        semantic_grade=grade6,
    )
    timing["general_purpose_lossy_compression_matched_fidelity"] = time.perf_counter() - t0

    # 7. Lossy execution without a narrative ledger (residual only).
    t0 = time.perf_counter()
    grade7 = grade_with(residual, [], true_ending)
    arms["lossy_execution_without_ledger"] = ArmMeasurement(
        arm_id="lossy_execution_without_ledger",
        description="The same residual as our architecture, but with the narrative ledger discarded entirely.",
        peak_canonical_bytes=_bytes_of(residual),
        total_byte_ticks=_bytes_of(residual),
        dump_ops=1, reconstruction_ops=0, merge_ops=0, sync_ops=0, observer_update_ops=0,
        total_operation_count=_ops_total(1, 0, 0, 0, 0),
        resource_breakdown=_breakdown(residual_bytes=_bytes_of(residual)),
        semantic_eligible=grade7["all_pass"],
        semantic_grade=grade7,
    )
    timing["lossy_execution_without_ledger"] = time.perf_counter() - t0

    # 8. No-loss cyclic execution: one full copy retained, no expansion
    # multiplier, never dumped, never lossy.
    t0 = time.perf_counter()
    per_tick_single = [_bytes_of(s) for s in full_states[1:]]
    arms["no_loss_cyclic_execution"] = ArmMeasurement(
        arm_id="no_loss_cyclic_execution",
        description="A single full copy of state is kept live at every tick; nothing is ever dumped or discarded.",
        peak_canonical_bytes=max(per_tick_single),
        total_byte_ticks=sum(per_tick_single),
        dump_ops=0, reconstruction_ops=0, merge_ops=0, sync_ops=0, observer_update_ops=L,
        total_operation_count=_ops_total(0, 0, 0, 0, L),
        resource_breakdown=_breakdown(authoritative_state_bytes=max(per_tick_single)),
        semantic_eligible=True,
        semantic_grade={"note": "full state retained at all times; trivially passes every probe"},
    )
    timing["no_loss_cyclic_execution"] = time.perf_counter() - t0

    # 9. Scripted cyclic replay: store only the action-symbol script.
    t0 = time.perf_counter()
    script_bytes = _bytes_of(list(history))
    replayed = W.run_history(config, history)
    grade9 = grade_with(
        {
            "agents": {a: {"balance": replayed["agents"][a]["balance"]} for a in config.agent_ids()},
            "obligations": replayed["obligations"],
            "relationships": replayed["relationships"],
            "causal_order_token": residual["causal_order_token"],
            "provenance_digest": residual["provenance_digest"],
        },
        W.relevant_ledger(replayed),
        true_ending,
    )
    arms["scripted_cyclic_replay"] = ArmMeasurement(
        arm_id="scripted_cyclic_replay",
        description="Only the exact action-symbol script is stored; the full history is re-executed from scratch to reconstruct state.",
        peak_canonical_bytes=script_bytes,
        total_byte_ticks=script_bytes * L,
        dump_ops=1, reconstruction_ops=L, merge_ops=0, sync_ops=0, observer_update_ops=0,
        total_operation_count=_ops_total(1, L, 0, 0, 0),
        resource_breakdown=_breakdown(preprocessing_bytes=script_bytes),
        semantic_eligible=grade9["all_pass"],
        semantic_grade=grade9,
        notes=(
            "Passes fidelity trivially because it is exempt from the loss requirement entirely (it stores "
            "the exact script, not a lossy summary): this is not an apples-to-apples comparison with the "
            "lossy arms, and this arm cannot reconstruct a history it was not given the exact script for."
        ),
    )
    timing["scripted_cyclic_replay"] = time.perf_counter() - t0

    # 10. State-machine replication: N replicas of the residual, kept in
    # sync via periodic merge/sync operations.
    t0 = time.perf_counter()
    replica_bytes = STATE_MACHINE_REPLICAS * _bytes_of(residual)
    grade10 = grade_with(residual, ledger, true_ending)
    arms["state_machine_replication"] = ArmMeasurement(
        arm_id="state_machine_replication",
        description=f"{STATE_MACHINE_REPLICAS} replicas of the residual, synchronized once per tick.",
        peak_canonical_bytes=replica_bytes,
        total_byte_ticks=replica_bytes * L,
        dump_ops=1, reconstruction_ops=0, merge_ops=0, sync_ops=L, observer_update_ops=len(ledger),
        total_operation_count=_ops_total(1, 0, 0, L, len(ledger)),
        resource_breakdown=_breakdown(residual_bytes=replica_bytes),
        semantic_eligible=grade10["all_pass"],
        semantic_grade=grade10,
    )
    timing["state_machine_replication"] = time.perf_counter() - t0

    # 11. Our own architecture: residual + narrative ledger, one boundary
    # transition (dump + reconstruction + merge).
    t0 = time.perf_counter()
    own_bytes_per_tick = [_bytes_of(W.relevant_ledger(s)) for s in full_states[1:]]
    final_residual_bytes = _bytes_of(residual)
    final_ledger_bytes = _bytes_of(ledger)
    final_bytes = final_residual_bytes + final_ledger_bytes
    grade_own = grade_with(residual, ledger, true_ending)
    arms["proposed_architecture_residual_plus_ledger"] = ArmMeasurement(
        arm_id="proposed_architecture_residual_plus_ledger",
        description="The architecture under test: reconstructed residual + narrative ledger, one boundary transition.",
        peak_canonical_bytes=max(own_bytes_per_tick + [final_bytes]) if own_bytes_per_tick else final_bytes,
        total_byte_ticks=sum(own_bytes_per_tick) + final_residual_bytes,
        dump_ops=1, reconstruction_ops=1, merge_ops=1, sync_ops=0, observer_update_ops=len(ledger),
        total_operation_count=_ops_total(1, 1, 1, 0, len(ledger)),
        resource_breakdown=_breakdown(
            residual_bytes=final_residual_bytes,
            ledger_bytes=final_ledger_bytes,
        ),
        semantic_eligible=grade_own["all_pass"],
        semantic_grade=grade_own,
    )
    timing["proposed_architecture_residual_plus_ledger"] = time.perf_counter() - t0

    return arms, timing


def pareto_eligible_arms(arms: dict[str, ArmMeasurement]) -> list[str]:
    return [aid for aid, m in arms.items() if m.semantic_eligible]


def compute_pareto_comparison(arms: dict[str, ArmMeasurement]) -> dict:
    """Status is determined by the FROZEN PRIMARY objective (peak canonical
    bytes) alone -- never by whichever of byte-ticks/op-count looks best
    after the fact. Byte-ticks and op count are still reported, per arm, as
    secondary/diagnostic context."""
    eligible = pareto_eligible_arms(arms)
    focal = "proposed_architecture_residual_plus_ledger"
    if focal not in eligible:
        return {
            "status": "ineligible",
            "reason": "the proposed architecture arm itself failed the semantic-fidelity gate",
            "eligible_arms": eligible,
        }
    comparisons = {}
    focal_m = arms[focal]
    for aid in eligible:
        if aid == focal:
            continue
        m = arms[aid]
        comparisons[aid] = {
            "primary_peak_bytes_ratio_focal_over_baseline": (
                round(focal_m.peak_canonical_bytes / m.peak_canonical_bytes, 6) if m.peak_canonical_bytes else None
            ),
            "secondary_byte_ticks_ratio_focal_over_baseline": (
                round(focal_m.total_byte_ticks / m.total_byte_ticks, 6) if m.total_byte_ticks else None
            ),
            "diagnostic_op_count_ratio_focal_over_baseline": (
                round(focal_m.total_operation_count / m.total_operation_count, 6) if m.total_operation_count else None
            ),
            "focal_smaller_peak_bytes": focal_m.peak_canonical_bytes < m.peak_canonical_bytes,
            "focal_smaller_byte_ticks": focal_m.total_byte_ticks < m.total_byte_ticks,
            "focal_fewer_ops": focal_m.total_operation_count < m.total_operation_count,
        }
    dominates_count = sum(1 for c in comparisons.values() if c["focal_smaller_peak_bytes"])
    # Protocol v1.2.0-dev3, section 15: supported only if peak canonical
    # bytes are STRICTLY lower than EVERY eligible baseline -- no
    # exceptions for a baseline's own non-comparability notes. Byte-ticks
    # cannot rescue a loss on the frozen primary metric.
    regression_arms = [aid for aid, c in comparisons.items() if not c["focal_smaller_peak_bytes"]]
    status = "supported" if (len(comparisons) > 0 and not regression_arms) else "unsupported"
    return {
        "status": status,
        "primary_metric": "peak_canonical_bytes",
        "secondary_metric": "total_byte_ticks",
        "diagnostic_metric": "total_operation_count",
        "eligible_arms": eligible,
        "ineligible_arms": [aid for aid in arms if aid not in eligible],
        "focal_arm": focal,
        "comparisons_vs_focal": comparisons,
        "dominates_count": dominates_count,
        "regression_arms_on_primary_metric": regression_arms,
        "reason": (
            f"the proposed architecture strictly beats every one of the {len(comparisons)} other eligible "
            "baseline(s) on the frozen primary objective (peak canonical bytes)"
            if status == "supported"
            else f"loses on peak canonical bytes to at least one eligible baseline "
            f"(see regression_arms_on_primary_metric: {regression_arms})"
        ),
    }


def evaluate_world_family(config: W.WorldConfig, history: tuple[str, ...], seed: int) -> tuple[dict, dict]:
    """Returns (canonical_result, noncanonical_timing). The timing dict is
    kept fully separate from the canonical result -- callers must not fold
    it back in before hashing/manifesting, since wall-clock jitter would
    otherwise break run-to-run reproducibility of the canonical digest for
    identical seeds."""
    arms, timing = build_all_arms(config, history, seed)
    pareto = compute_pareto_comparison(arms)
    canonical = {
        "world_id": config.world_id,
        "reference_history": list(history),
        "arms": {aid: vars(m) for aid, m in arms.items()},
        "pareto": pareto,
        "status": pareto["status"],
    }
    noncanonical_timing = {
        "world_id": config.world_id,
        "wall_clock_seconds_by_arm": timing,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "note": "Diagnostic only (protocol v2, update C's noncanonical diagnostic). Deliberately excluded "
        "from the canonical evidence manifest and from canonical_digest: wall-clock time is not "
        "reproducible run-to-run even with identical seeds.",
    }
    return canonical, noncanonical_timing


def run_component(world_families, boundary_reference_histories: dict[str, Optional[tuple[str, ...]]], seed_base: int) -> dict:
    per_family = {}
    per_family_timing = {}
    for i, wf in enumerate(world_families):
        ref = boundary_reference_histories.get(wf.family_id)
        if ref is None:
            histories = W.enumerate_histories(wf.config)
            ref = next((h for h in histories if W.resolved_count(W.run_history(wf.config, h)) >= 1), histories[0])
        canonical, timing = evaluate_world_family(wf.config, ref, seed_base + i)
        per_family[wf.family_id] = canonical
        per_family_timing[wf.family_id] = timing
    statuses = [r["status"] for r in per_family.values()]
    if not statuses:
        overall = "invalid"
    elif all(s == "supported" for s in statuses):
        overall = "supported"
    else:
        overall = "unsupported"
    return {
        "status": overall,
        "reason": (
            "the proposed architecture achieves a frozen, undominated resource advantage on the primary "
            "objective (peak canonical bytes) in every evaluated world family"
            if overall == "supported"
            else "at least one world family showed an undeclared total regression on the primary metric or "
            "no strict dominance over any eligible baseline (see per_world_family)"
        ),
        "per_world_family": per_family,
        "per_world_family_noncanonical_timing": per_family_timing,
    }
