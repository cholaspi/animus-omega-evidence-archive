"""Test 05, sections 5 and 13: the seed-based execution matrix.

For each friendly seed, one unfaulted execution is recorded. For each
adversarial seed, ten executions are recorded: one unfaulted baseline plus
the nine required fault mutations. Every execution records seed, execution
ID, mutation ID, before/after hashes of the mutated (residual, ledger)
pair, the concrete mutated field paths (from a real structural diff, not a
label), a frozen predicted failure declared before the mutation is applied,
and the observed failure actually computed by grading against the same
probe battery Test 05B uses.

Mutation *construction* here is deliberately independent of Test 05B's
``run_controls`` (which exists for the semantic-continuity report): this
module exists to produce individually addressable execution records for
the protocol's required matrix, even though several mutations are
structurally the same perturbation.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any, Callable

from . import residual as R
from . import world as W
from .hashing import hash_obj

# Frozen before any execution: what each mutation is predicted to do. Every
# mutation is predicted, at minimum, to cause the unfaulted probe battery to
# stop passing in full; several have a specific probe identified as the one
# expected to flip.
FAULT_PREDICTIONS: dict[str, dict] = {
    "identity_substitution": {
        "description": "Swap the balances of the generated substitution pair in the residual.",
        "expect_all_pass": False,
        "expect_probe_flip": "identity_substitution_challenges",
    },
    "obligation_deletion": {
        "description": "Remove the first obligation entirely from the residual.",
        "expect_all_pass": False,
        "expect_probe_flip": "obligation_ownership",
    },
    "contradictory_ledger": {
        "description": "Flip the first ledger entry's recorded effect to a value inconsistent with its (tick, action).",
        "expect_all_pass": False,
        "expect_probe_flip": "ledger_effects_consistent",
    },
    "missing_provenance": {
        "description": "Remove the provenance field from the first obligation.",
        "expect_all_pass": False,
        "expect_probe_flip": "provenance",
    },
    "stale_event": {
        "description": "Replace the ledger with an empty (stale/earlier-point) ledger.",
        "expect_all_pass": False,
        "expect_probe_flip": "identity_substitution_challenges",
    },
    "duplicate_event": {
        "description": "Duplicate the first ledger entry at the end of the ledger.",
        "expect_all_pass": False,
        "expect_probe_flip": None,
    },
    "causal_reorder": {
        "description": "Reverse the order of the relevant ledger's entries.",
        "expect_all_pass": False,
        "expect_probe_flip": "identity_substitution_challenges",
    },
    "no_ledger": {
        "description": "Supply an empty ledger alongside the true residual.",
        "expect_all_pass": False,
        "expect_probe_flip": "identity_substitution_challenges",
    },
    "random_reconstruction": {
        "description": "Replace residual balances and obligation owner/status with random values.",
        "expect_all_pass": False,
        "expect_probe_flip": None,
    },
}

MUTATION_IDS = tuple(FAULT_PREDICTIONS.keys())
assert len(MUTATION_IDS) == 9, "protocol requires exactly 9 named fault mutations"


def _causally_significant_reorder(ledger_obj: list[dict], config: W.WorldConfig) -> tuple[list[dict], bool]:
    """Finds two "resolve" ledger entries where the later one's obligation
    causally depends *directly* on the earlier one's (immediate predecessor
    in the dependency chain, not merely an earlier position in the overall
    obligation ordering), and swaps only their positions -- putting the
    dependent resolution before its prerequisite, a genuine causal-order
    violation, rather than a blanket reversal that may be semantically
    inert (e.g. reversing two independent "move" entries).

    Protocol v1.3.0-dev4, corrections 11-12: v1.2.0-dev3's version of this
    function accepted ANY pair with obligation_order.index(oi) <
    obligation_order.index(oj), not only an immediately-dependent pair.
    Mechanical investigation of the 2 (of 30) adversarial executions whose
    observed outcome did not match its frozen prediction under v1.2.0-dev3
    found the root cause here: with a 3-obligation chain (o0<-o1<-o2), the
    old code could pick the non-adjacent pair (o0, o2) instead of an
    adjacent one. Swapping o0 and o2's positions does not violate o2's
    *actual* gating dependency (o1, whose own resolve entry is untouched
    and stays correctly ordered), so replay_with_recomputed_effects()
    recomputes the identical "resolved" effect for both moved entries and
    every probe still passes -- an inert reorder, not a real causal-order
    violation, even though a pair with "an earlier index" was found. This
    was an implementation defect in the swap-pair selection, not a genuine
    counterexample to the fault-control prediction, so it is fixed here
    rather than weakening the frozen prediction (do not relax
    expect_all_pass for causal_reorder merely to obtain a match).

    Returns (new_ledger, applicable): ``applicable`` is False when no
    immediately-dependent resolve pair exists in this particular ledger
    (e.g. a 1-obligation family, or a ledger where the dependency's own
    resolve never occurred), so the caller can report the mutation as
    not_applicable for that execution instead of asserting a prediction it
    cannot actually test."""
    obligation_order = config.obligation_ids()
    resolve_positions = [i for i, e in enumerate(ledger_obj) if e.get("action") == "resolve"]
    for i in resolve_positions:
        for j in resolve_positions:
            if i == j:
                continue
            oi, oj = ledger_obj[i].get("obligation"), ledger_obj[j].get("obligation")
            if oi is None or oj is None:
                continue
            oj_idx = obligation_order.index(oj)
            if oj_idx == 0:
                continue
            immediate_dependency = obligation_order[oj_idx - 1]
            if oi != immediate_dependency:
                continue
            # oi is oj's direct prerequisite, and oi's resolve currently
            # precedes oj's (the correct causal order): swap their
            # positions so oj's resolve is recorded before the one entry
            # its own gating check actually reads.
            if i < j:
                new_ledger = list(ledger_obj)
                new_ledger[i], new_ledger[j] = new_ledger[j], new_ledger[i]
                return new_ledger, True
    return list(reversed(ledger_obj)), False


def _duplicate_a_resolve_entry(ledger_obj: list[dict]) -> tuple[list[dict], bool]:
    """Duplicates the FIRST "resolve" entry (appending a copy at the end),
    not unconditionally ``ledger_obj[0]``. Protocol v1.3.0-dev4, corrections
    11-12: mechanical investigation of an unpredicted duplicate_event pass
    (found empirically against the corrected world dimensions) showed
    v1.2.0-dev3's unconditional ``ledger_obj[0]`` duplication is not
    guaranteed detectable -- if entry 0 is a "move" whose preconditions
    (mover balance, ring permission) happen to still hold when it is
    reprocessed at the end of the ledger,
    world.replay_with_recomputed_effects() recomputes the identical
    "transferred" effect both times and probe_ledger_effects_consistent
    never flips, so an inert duplicate can slip through. Duplicating a
    "resolve" entry instead is unconditionally detectable: reprocessing an
    already-closed obligation's resolve always recomputes "already_closed",
    which can never equal the original stored "resolved" effect. Returns
    (new_ledger, applicable); applicable is False only when the ledger
    contains no resolve entry at all, in which case the caller falls back
    to duplicating entry 0 (as before) and reports the mutation as not
    applicable rather than asserting an untestable prediction."""
    resolve_idx = next((i for i, e in enumerate(ledger_obj) if e.get("action") == "resolve" and e.get("effect") == "resolved"), None)
    if resolve_idx is None:
        new_ledger = list(ledger_obj)
        if new_ledger:
            new_ledger.append(dict(new_ledger[0]))
        return new_ledger, False
    new_ledger = list(ledger_obj)
    new_ledger.append(dict(new_ledger[resolve_idx]))
    return new_ledger, True


def _apply_mutation(mutation_id: str, residual_obj: dict, ledger_obj: list[dict], config: W.WorldConfig, rng: random.Random) -> tuple[dict, list[dict], bool]:
    """Returns (mutated_residual, mutated_ledger, applicable). ``applicable``
    is False only for mutations that can decline to apply for a specific
    execution (currently just causal_reorder, when no dependent resolve
    pair exists); every other mutation is always applicable. Pure function
    of the inputs and an explicit rng (never of a label)."""
    res = copy.deepcopy(residual_obj)
    ledg = [dict(e) for e in ledger_obj]
    applicable = True

    if mutation_id == "identity_substitution":
        instances = R.generate_delayed_probe_instances(res, ledg, config)
        a, b = instances["substitution_pair"]
        res["agents"][a], res["agents"][b] = res["agents"][b], res["agents"][a]
    elif mutation_id == "obligation_deletion":
        first_obl = config.obligation_ids()[0]
        res["obligations"].pop(first_obl, None)
    elif mutation_id == "contradictory_ledger":
        if ledg:
            ledg[0]["effect"] = "resolved" if ledg[0]["effect"] != "resolved" else "blocked_dependency"
    elif mutation_id == "missing_provenance":
        first_obl = config.obligation_ids()[0]
        if first_obl in res["obligations"]:
            res["obligations"][first_obl].pop("provenance", None)
    elif mutation_id == "stale_event":
        ledg = []
    elif mutation_id == "duplicate_event":
        ledg, applicable = _duplicate_a_resolve_entry(ledg)
    elif mutation_id == "causal_reorder":
        ledg, applicable = _causally_significant_reorder(ledg, config)
    elif mutation_id == "no_ledger":
        ledg = []
    elif mutation_id == "random_reconstruction":
        for aid in res["agents"]:
            res["agents"][aid]["balance"] = rng.randint(0, config.total_resource)
        for obl in res["obligations"].values():
            obl["status"] = rng.choice(["open", "closed"])
            obl["owner"] = rng.choice(config.agent_ids())
    else:
        raise ValueError(f"unknown mutation_id {mutation_id!r}")

    return res, ledg, applicable


def _mutated_field_paths(before: Any, after: Any, path: str = "") -> list[str]:
    """Every top-level-and-nested path that differs between two structures
    (a real structural diff, not a declared label)."""
    paths: list[str] = []
    if isinstance(before, dict) and isinstance(after, dict):
        for k in sorted(set(before.keys()) | set(after.keys())):
            paths.extend(_mutated_field_paths(before.get(k), after.get(k), f"{path}.{k}" if path else str(k)))
    elif isinstance(before, list) and isinstance(after, list):
        for i in range(max(len(before), len(after))):
            b = before[i] if i < len(before) else "<missing>"
            a = after[i] if i < len(after) else "<missing>"
            paths.extend(_mutated_field_paths(b, a, f"{path}[{i}]"))
    else:
        if before != after:
            paths.append(path)
    return paths


@dataclass
class ExecutionRecord:
    seed: int
    execution_id: str
    mutation_id: str  # "unfaulted" for the baseline
    family: str
    reference_history: list
    before_hash: str
    after_hash: str
    mutated_fields: list
    predicted_failure: dict
    observed_failure: dict
    prediction_matched: bool


def _grade_and_observe(residual_obj: dict, ledger_obj: list[dict], true_ending: dict, config: W.WorldConfig) -> dict:
    grade = R._grade(residual_obj, ledger_obj, true_ending, config)
    failing_probes = [pid for pid, ok in grade["grades"].items() if not ok]
    return {
        "all_pass": grade["all_pass"],
        "pass_count": grade["pass_count"],
        "total": grade["total"],
        "failing_probes": failing_probes,
    }


def run_adversarial_seed(config: W.WorldConfig, seed: int, family: str) -> list[ExecutionRecord]:
    """Ten executions for one adversarial seed: one unfaulted baseline plus
    the nine required fault mutations, each built from that same seed's
    selected reference history."""
    rng = random.Random(seed)
    histories = W.enumerate_histories(config)
    closing = [h for h in histories if W.resolved_count(W.run_history(config, h)) >= 1]
    reference_history = rng.choice(closing) if closing else histories[0]

    true_ending = W.run_history(config, reference_history)
    base_residual = R.build_residual(true_ending, config)
    base_ledger = R.build_ledger(true_ending)

    records: list[ExecutionRecord] = []

    # Unfaulted baseline.
    before_hash = hash_obj({"residual": base_residual, "ledger": base_ledger})
    observed = _grade_and_observe(base_residual, base_ledger, true_ending, config)
    records.append(
        ExecutionRecord(
            seed=seed,
            execution_id=f"{family}-seed{seed}-unfaulted",
            mutation_id="unfaulted",
            family=family,
            reference_history=list(reference_history),
            before_hash=before_hash,
            after_hash=before_hash,  # no mutation applied
            mutated_fields=[],
            predicted_failure={"expect_all_pass": True, "description": "unfaulted baseline; no mutation applied"},
            observed_failure=observed,
            prediction_matched=observed["all_pass"] is True,
        )
    )

    # Nine fault executions, each mutating a fresh copy of the same baseline.
    for mutation_id in MUTATION_IDS:
        mutation_rng = random.Random(hash_obj({"seed": seed, "mutation_id": mutation_id})[:8])
        mutated_residual, mutated_ledger, applicable = _apply_mutation(mutation_id, base_residual, base_ledger, config, mutation_rng)
        b_hash = hash_obj({"residual": base_residual, "ledger": base_ledger})
        a_hash = hash_obj({"residual": mutated_residual, "ledger": mutated_ledger})
        mutated_fields = _mutated_field_paths(
            {"residual": base_residual, "ledger": base_ledger},
            {"residual": mutated_residual, "ledger": mutated_ledger},
        )
        observed = _grade_and_observe(mutated_residual, mutated_ledger, true_ending, config)
        prediction = dict(FAULT_PREDICTIONS[mutation_id])
        if not applicable:
            # Declared honestly, not folded into the pass/fail count: this
            # specific execution's ledger contained no pair this mutation's
            # *targeted* mechanism could act on (causal_reorder needs at
            # least two dependent "resolve" entries), so it fell back to a
            # full reversal. The general prediction (at least one probe
            # fails) is still checked against whatever that fallback
            # actually produced -- "not applicable" is a diagnostic label,
            # not an automatic pass.
            prediction["not_applicable_for_targeted_mechanism"] = True
        prediction_matched = observed["all_pass"] == prediction["expect_all_pass"]
        records.append(
            ExecutionRecord(
                seed=seed,
                execution_id=f"{family}-seed{seed}-{mutation_id}",
                mutation_id=mutation_id,
                family=family,
                reference_history=list(reference_history),
                before_hash=b_hash,
                after_hash=a_hash,
                mutated_fields=mutated_fields,
                predicted_failure=prediction,
                observed_failure=observed,
                prediction_matched=prediction_matched,
            )
        )

    return records


def run_friendly_seed(config: W.WorldConfig, seed: int, family: str) -> ExecutionRecord:
    """One unfaulted execution for a friendly seed: no fault matrix (the
    protocol only requires the fault matrix for adversarial seeds)."""
    rng = random.Random(seed)
    histories = W.enumerate_histories(config)
    closing = [h for h in histories if W.resolved_count(W.run_history(config, h)) >= 1]
    reference_history = rng.choice(closing) if closing else histories[0]

    true_ending = W.run_history(config, reference_history)
    residual_obj = R.build_residual(true_ending, config)
    ledger_obj = R.build_ledger(true_ending)
    h = hash_obj({"residual": residual_obj, "ledger": ledger_obj})
    observed = _grade_and_observe(residual_obj, ledger_obj, true_ending, config)
    return ExecutionRecord(
        seed=seed,
        execution_id=f"{family}-seed{seed}-unfaulted",
        mutation_id="unfaulted",
        family=family,
        reference_history=list(reference_history),
        before_hash=h,
        after_hash=h,
        mutated_fields=[],
        predicted_failure={"expect_all_pass": True, "description": "unfaulted baseline; no mutation applied"},
        observed_failure=observed,
        prediction_matched=observed["all_pass"] is True,
    )


def run_family_matrix(wf, seeds: list[int]) -> dict:
    """Runs the full execution matrix for one world family across its
    assigned seeds. Adversarial families (declared via ``wf.adversarial``
    being non-empty) get the full 10-execution-per-seed fault matrix;
    friendly families get one unfaulted execution per seed."""
    config = wf.config
    is_adversarial = len(wf.adversarial) > 0
    executions: list[ExecutionRecord] = []
    for seed in seeds:
        if is_adversarial:
            executions.extend(run_adversarial_seed(config, seed, wf.family_id))
        else:
            executions.append(run_friendly_seed(config, seed, wf.family_id))

    unexpected = [e.execution_id for e in executions if not e.prediction_matched]
    return {
        "family_id": wf.family_id,
        "is_adversarial": is_adversarial,
        "seeds": seeds,
        "execution_count": len(executions),
        "executions": [vars(e) for e in executions],
        "unexpected_predictions": unexpected,
        "all_predictions_matched": len(unexpected) == 0,
        "status": "supported" if len(unexpected) == 0 else "unsupported",
    }


def run_component(world_families, seeds_by_family: dict[str, list[int]]) -> dict:
    per_family = {}
    for wf in world_families:
        seeds = seeds_by_family.get(wf.family_id, [])
        per_family[wf.family_id] = run_family_matrix(wf, seeds)
    statuses = [r["status"] for r in per_family.values()]
    overall = "supported" if statuses and all(s == "supported" for s in statuses) else (
        "unsupported" if statuses else "invalid"
    )
    return {
        "status": overall,
        "reason": (
            "every declared fault mutation produced its frozen predicted failure in every family"
            if overall == "supported"
            else "at least one execution's observed failure did not match its frozen prediction"
        ),
        "per_world_family": per_family,
    }
