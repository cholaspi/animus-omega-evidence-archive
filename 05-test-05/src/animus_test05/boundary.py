"""Test 05A: Reciprocal Boundary Necessity.

Research question: does information produced at the ending participate
causally and necessarily in constructing the next beginning?

This module implements an explicit, executed boundary transition ``J``:

    S_next_beginning = J(reconstructed_state, ledger, return_value, contract)

``reconstructed_state`` is produced by replaying the relevant ledger (see
``world.replay``) -- it is a pure function of (config, ledger) and never
sees the true final microstate directly. ``contract`` is committed before
any history executes (it is a pure function of ``WorldConfig`` only). The
12 required intervention arms, plus an additional "ignored return value"
control, are all defined as perturbations of J's four inputs relative to one
naturally-closing reference history per world family, so every arm's result
is recomputed from actually-executed data rather than asserted.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional

from . import world as W
from .hashing import hash_obj

AGENT_ID_RE_PREFIX = "a"


class TrackedReturnValue:
    """Wraps a return-value dict and records which fields were actually
    read. Used to detect a return value that is computed but never
    consumed by the executed transition."""

    def __init__(self, value: Optional[dict]):
        self._value = value
        self.accessed_fields: set[str] = set()

    def get(self, field_name: str):
        if self._value is None:
            return None
        self.accessed_fields.add(field_name)
        return self._value.get(field_name)

    @property
    def is_present(self) -> bool:
        return self._value is not None


def locked_beginning_contract(config: W.WorldConfig) -> dict:
    """Committed before any history executes; a pure function of config
    only. Never selected or revised after observing an ending."""
    return {
        "total_conserved_invariant": config.total_resource,
        "min_resolutions": 1,
    }


def execute_J(
    reconstructed_state: dict,
    ledger: list[dict],
    return_value: Optional[dict],
    config: W.WorldConfig,
    use_endpoint: bool = True,
) -> tuple[dict, TrackedReturnValue]:
    """The executed boundary transition. Builds the next beginning's public
    fields from the three inputs. Returns (next_beginning, tracked_rv) so
    callers can check whether the return value was actually read."""
    tracked = TrackedReturnValue(return_value if use_endpoint else None)
    primary_holder = tracked.get("primary_holder") if use_endpoint else None
    resolved_count_hint = tracked.get("resolved_count") if use_endpoint else None
    next_beginning = {
        "total": sum(a["balance"] for a in reconstructed_state["agents"].values()),
        "primary_holder": primary_holder,
        "resolved_count_hint": resolved_count_hint,
        "ledger_root": hash_obj(ledger),
    }
    return next_beginning, tracked


def _valid_agent_id(value: Any, config: W.WorldConfig) -> bool:
    return isinstance(value, str) and value in config.agent_ids()


def contract_satisfied(next_beginning: dict, contract: dict, config: W.WorldConfig) -> tuple[bool, Optional[str]]:
    """Structural check only: does next_beginning satisfy the pre-committed
    contract, using only the values actually present in next_beginning (no
    access to the true ending)? Returns (ok, first_fail_reason)."""
    if not _valid_agent_id(next_beginning.get("primary_holder"), config):
        return False, "primary_holder_missing_or_invalid"
    rc = next_beginning.get("resolved_count_hint")
    if not isinstance(rc, int) or rc < 0:
        return False, "resolved_count_missing_or_invalid"
    if next_beginning.get("total") is None:
        return False, "total_missing"
    if next_beginning["total"] + rc != contract["total_conserved_invariant"]:
        return False, "total_conservation_violated"
    if rc < contract["min_resolutions"]:
        return False, "min_resolutions_not_met"
    if not next_beginning.get("ledger_root"):
        return False, "ledger_root_missing"
    return True, None


def exact_closure(
    next_beginning: dict,
    true_ending_state: dict,
    config: W.WorldConfig,
) -> tuple[bool, Optional[str], Optional[dict]]:
    """Compares next_beginning against the true ending's independently
    computed ground truth (never against a label or expectation). Returns
    (ok, first_mismatch_field, detail)."""
    true_rv = W.return_value_of(true_ending_state)
    true_ledger = W.relevant_ledger(true_ending_state)
    checks = [
        ("primary_holder", next_beginning.get("primary_holder"), true_rv["primary_holder"]),
        ("resolved_count_hint", next_beginning.get("resolved_count_hint"), true_rv["resolved_count"]),
        ("ledger_root", next_beginning.get("ledger_root"), hash_obj(true_ledger)),
        (
            "total",
            next_beginning.get("total"),
            sum(a["balance"] for a in true_ending_state["agents"].values()),
        ),
    ]
    for name, got, want in checks:
        if got != want:
            return False, name, {"got": got, "want": want}
    return True, None, None


@dataclass
class ArmResult:
    arm_id: str
    description: str
    closes: bool
    contract_satisfied: bool
    contract_fail_reason: Optional[str]
    exact_closure_fail_field: Optional[str]
    exact_closure_detail: Optional[dict]
    return_value_used: bool
    notes: str = ""


def _base_natural_inputs(config: W.WorldConfig, history: tuple[str, ...]):
    true_ending = W.run_history(config, history)
    true_ledger = W.relevant_ledger(true_ending)
    reconstructed = W.replay(config, true_ledger)
    true_rv = W.return_value_of(true_ending)
    return true_ending, true_ledger, reconstructed, true_rv


def _run_arm(
    arm_id: str,
    description: str,
    reconstructed_state: dict,
    ledger: list[dict],
    return_value: Optional[dict],
    true_ending_state: dict,
    config: W.WorldConfig,
    use_endpoint: bool = True,
    notes: str = "",
) -> ArmResult:
    contract = locked_beginning_contract(config)
    next_beginning, tracked = execute_J(reconstructed_state, ledger, return_value, config, use_endpoint)
    c_ok, c_fail = contract_satisfied(next_beginning, contract, config)
    e_ok, e_fail_field, e_detail = exact_closure(next_beginning, true_ending_state, config)
    rv_used = ("primary_holder" in tracked.accessed_fields) or ("resolved_count" in tracked.accessed_fields)
    return ArmResult(
        arm_id=arm_id,
        description=description,
        closes=bool(e_ok),
        contract_satisfied=bool(c_ok),
        contract_fail_reason=c_fail,
        exact_closure_fail_field=e_fail_field,
        exact_closure_detail=e_detail,
        return_value_used=rv_used,
        notes=notes,
    )


def find_reference_history(
    config: W.WorldConfig,
    contract: dict,
) -> tuple[Optional[tuple[str, ...]], list[tuple[str, ...]], list[tuple[str, ...]]]:
    """Enumerate all admissible histories and classify natural closure.
    Returns (reference_history_or_None, closing_histories, non_closing_histories).
    The reference history is the first closing history (in enumeration
    order) that also contains at least one relevant-action tick beyond the
    minimum and at least one irrelevant-action tick, so arms 6/7 are both
    constructible; if no such "rich" history exists, falls back to the
    first closing history."""
    closing: list[tuple[str, ...]] = []
    non_closing: list[tuple[str, ...]] = []
    rich_candidate = None
    plain_candidate = None
    for history in W.enumerate_histories(config):
        ending = W.run_history(config, history)
        ledger = W.relevant_ledger(ending)
        reconstructed = W.replay(config, ledger)
        rv = W.return_value_of(ending)
        next_beginning, _ = execute_J(reconstructed, ledger, rv, config)
        c_ok, _ = contract_satisfied(next_beginning, contract, config)
        e_ok, _, _ = exact_closure(next_beginning, ending, config)
        if c_ok and e_ok:
            closing.append(history)
            if plain_candidate is None:
                plain_candidate = history
            has_relevant = any(a in W.RELEVANT_ACTIONS for a in history)
            has_irrelevant = any(a in W.IRRELEVANT_ACTIONS for a in history)
            if rich_candidate is None and has_relevant and has_irrelevant:
                rich_candidate = history
        else:
            non_closing.append(history)
    reference = rich_candidate or plain_candidate
    return reference, closing, non_closing


def run_intervention_arms(
    config: W.WorldConfig,
    reference_history: tuple[str, ...],
    rng_seed: int,
) -> list[ArmResult]:
    contract = locked_beginning_contract(config)
    true_ending, true_ledger, reconstructed, true_rv = _base_natural_inputs(config, reference_history)
    rng = random.Random(rng_seed)
    arms: list[ArmResult] = []

    # Arm 1: correct ending-derived return value.
    arms.append(
        _run_arm(
            "01_correct_return_value",
            "Feed the true return value derived from this history's own ending.",
            reconstructed, true_ledger, true_rv, true_ending, config,
        )
    )

    # Arm 2: missing return value.
    arms.append(
        _run_arm(
            "02_missing_return_value",
            "Return value is None.",
            reconstructed, true_ledger, None, true_ending, config,
        )
    )

    # Arm 3: random return value (primary_holder randomized to a different
    # agent than the true one; resolved_count kept faithful so the
    # structural contract can still be satisfied, isolating exactly what
    # exact-closure catches that contract-satisfaction does not).
    agents = config.agent_ids()
    other_agents = [a for a in agents if a != true_rv["primary_holder"]]
    random_holder = rng.choice(other_agents) if other_agents else true_rv["primary_holder"]
    random_rv = {
        "primary_holder": random_holder,
        "resolved_count": true_rv["resolved_count"],
        "ledger_root": true_rv["ledger_root"],
    }
    arms.append(
        _run_arm(
            "03_random_return_value",
            "Return value's primary_holder field replaced with a random different agent id.",
            reconstructed, true_ledger, random_rv, true_ending, config,
            notes=f"true_holder={true_rv['primary_holder']} random_holder={random_holder}",
        )
    )

    # Arm 4: return value taken from a different history (first enumerated
    # history whose true primary_holder differs from this one's).
    swap_rv = None
    swap_history = None
    for h2 in W.enumerate_histories(config):
        if h2 == reference_history:
            continue
        end2 = W.run_history(config, h2)
        rv2 = W.return_value_of(end2)
        if rv2["primary_holder"] != true_rv["primary_holder"]:
            swap_rv = rv2
            swap_history = h2
            break
    arms.append(
        _run_arm(
            "04_return_value_from_different_history",
            "Return value taken from a different admissible history's true ending.",
            reconstructed, true_ledger, swap_rv, true_ending, config,
            notes=f"donor_history={swap_history}",
        )
    )

    # Arm 5: one-symbol endpoint mutation -- flip a single obligation's
    # status field (open<->closed) in a copy of the true ending before
    # computing the return value fed into J. This is a minimal one-field
    # mutation that is guaranteed to change resolved_count by exactly one
    # regardless of this world family's specific balance arithmetic (unlike
    # perturbing a balance by one unit, which can leave primary_holder
    # unchanged when the true holder has a wide margin).
    import copy

    mutated_ending = copy.deepcopy(true_ending)
    first_obligation_id = config.obligation_ids()[0]
    obl = mutated_ending["obligations"][first_obligation_id]
    obl["status"] = "open" if obl["status"] == "closed" else "closed"
    mutated_rv = W.return_value_of(mutated_ending)
    arms.append(
        _run_arm(
            "05_endpoint_mutation",
            "Return value recomputed from a one-unit endpoint mutation of the true ending.",
            reconstructed, true_ledger, mutated_rv, true_ending, config,
        )
    )

    # Arm 6: mutation of a causally relevant intermediate action.
    relevant_positions = [i for i, a in enumerate(reference_history) if a in W.RELEVANT_ACTIONS]
    if relevant_positions:
        pos = relevant_positions[0]
        cur = reference_history[pos]
        replacement = "resolve" if cur == "move" else "move"
        mutated_history = reference_history[:pos] + (replacement,) + reference_history[pos + 1 :]
        mutated_end, mutated_ledger, mutated_reconstructed, mutated_rv2 = _base_natural_inputs(
            config, mutated_history
        )
        # Key test: keep the ORIGINAL true return value (as if the endpoint
        # information were never updated to reflect the mutated execution)
        # together with the mutated execution's own ledger/reconstruction,
        # and check both against the ORIGINAL reference history's true
        # ending (the ground truth the beginning contract actually committed
        # against). A causally relevant mutation should make the mutated
        # ledger/reconstruction disagree with that ground truth.
        arms.append(
            _run_arm(
                "06_relevant_intermediate_mutation",
                f"Action at tick {pos} changed {cur!r}->{replacement!r}; original return value held stale "
                "against the mutated execution's ledger/reconstruction, checked against the original "
                "reference history's true ending.",
                mutated_reconstructed, mutated_ledger, true_rv, true_ending, config,
                notes=f"mutated_history={mutated_history} own_true_rv={mutated_rv2}",
            )
        )
    else:
        arms.append(
            ArmResult(
                "06_relevant_intermediate_mutation",
                "No relevant-action tick available in the reference history for this world family.",
                closes=False, contract_satisfied=False, contract_fail_reason="not_applicable",
                exact_closure_fail_field="not_applicable", exact_closure_detail=None,
                return_value_used=False, notes="ineligible",
            )
        )

    # Arm 7: mutation of a causally irrelevant intermediate action.
    irrelevant_positions = [i for i, a in enumerate(reference_history) if a in W.IRRELEVANT_ACTIONS]
    if irrelevant_positions:
        pos = irrelevant_positions[0]
        cur = reference_history[pos]
        replacement = "noop_y" if cur == "noop_x" else "noop_x"
        mutated_history = reference_history[:pos] + (replacement,) + reference_history[pos + 1 :]
        mutated_end, mutated_ledger, mutated_reconstructed, mutated_rv2 = _base_natural_inputs(
            config, mutated_history
        )
        arms.append(
            _run_arm(
                "07_irrelevant_intermediate_mutation",
                f"Action at tick {pos} changed {cur!r}->{replacement!r} (irrelevant-class swap); "
                "original return value re-used against the mutated execution's ledger/reconstruction, "
                "checked against the original reference history's true ending.",
                mutated_reconstructed, mutated_ledger, true_rv, true_ending, config,
                notes=f"mutated_history={mutated_history} own_true_rv={mutated_rv2}",
            )
        )
    else:
        arms.append(
            ArmResult(
                "07_irrelevant_intermediate_mutation",
                "No irrelevant-action tick available in the reference history for this world family.",
                closes=False, contract_satisfied=False, contract_fail_reason="not_applicable",
                exact_closure_fail_field="not_applicable", exact_closure_detail=None,
                return_value_used=False, notes="ineligible",
            )
        )

    # Arm 8: correct return value, incorrect ledger (flip one entry's effect
    # field, which changes the ledger's hash root without changing the
    # reconstructed state that was computed from the *true* ledger).
    corrupted_ledger = [dict(e) for e in true_ledger]
    if corrupted_ledger:
        corrupted_ledger[0] = dict(corrupted_ledger[0])
        corrupted_ledger[0]["effect"] = "CORRUPTED:" + str(corrupted_ledger[0].get("effect"))
    arms.append(
        _run_arm(
            "08_correct_return_value_incorrect_ledger",
            "Ledger's first entry corrupted; return value and reconstruction left correct.",
            reconstructed, corrupted_ledger, true_rv, true_ending, config,
        )
    )

    # Arm 9: correct ledger, incorrect reconstruction (corrupt one agent's
    # reconstructed balance).
    corrupted_reconstructed = copy.deepcopy(reconstructed)
    any_agent = agents[0]
    corrupted_reconstructed["agents"][any_agent]["balance"] += 5
    arms.append(
        _run_arm(
            "09_correct_ledger_incorrect_reconstruction",
            f"Reconstructed balance for {any_agent} corrupted (+5); ledger and return value left correct.",
            corrupted_reconstructed, true_ledger, true_rv, true_ending, config,
        )
    )

    # Arm 10: beginning constructed without endpoint information at all (a
    # distinct code path that never receives a return value, as opposed to
    # arm 2's explicit None).
    arms.append(
        _run_arm(
            "10_no_endpoint_information",
            "J executed via the no-endpoint code path (return_value parameter never supplied).",
            reconstructed, true_ledger, None, true_ending, config,
            use_endpoint=False,
        )
    )

    # Arm 11: open-chain control -- no return transition executed at all.
    arms.append(
        ArmResult(
            "11_open_chain_no_return_transition",
            "No J transition executed; there is no next beginning to compare against the contract.",
            closes=False, contract_satisfied=False, contract_fail_reason="no_transition_executed",
            exact_closure_fail_field="no_transition_executed", exact_closure_detail=None,
            return_value_used=False, notes="control: closure is vacuously absent by construction",
        )
    )

    # Arm 12: directly copied beginning (ignore the ending entirely; the
    # "next beginning" is just the pristine initial public state).
    initial_public = W.public_fields(W.initial_state(config))
    copied_next_beginning = {
        "total": sum(a["balance"] for a in initial_public["agents"].values()),
        "primary_holder": W.primary_holder(W.initial_state(config)),
        "resolved_count_hint": 0,
        "ledger_root": hash_obj([]),
    }
    contract2 = locked_beginning_contract(config)
    c_ok, c_fail = contract_satisfied(copied_next_beginning, contract2, config)
    e_ok, e_field, e_detail = exact_closure(copied_next_beginning, true_ending, config)
    arms.append(
        ArmResult(
            "12_directly_copied_beginning",
            "Next beginning is the untouched initial state, ignoring the executed ending entirely.",
            closes=bool(e_ok), contract_satisfied=bool(c_ok), contract_fail_reason=c_fail,
            exact_closure_fail_field=e_field, exact_closure_detail=e_detail,
            return_value_used=False,
            notes="shortcut/no-copy-explains-result control",
        )
    )

    # Additional control (beyond the 12 numbered arms): a J implementation
    # that computes the return value's fields but never reads them when
    # building next_beginning (they are always overwritten with a fixed
    # default that ignores whatever was read). This must be caught as an
    # "ignored return value", distinct from every arm above where the
    # value, if present, is genuinely propagated into the output. The
    # default is deliberately an invalid sentinel (never a real agent id)
    # so detection does not depend on this world family's particular true
    # holder happening to differ from a hardcoded guess.
    tracked = TrackedReturnValue(true_rv)
    read_value = tracked.get("primary_holder")  # computed...
    IGNORED_SENTINEL = None
    broken_next_beginning = {
        "total": sum(a["balance"] for a in reconstructed["agents"].values()),
        "primary_holder": IGNORED_SENTINEL,  # ...but ignored: never propagated
        "resolved_count_hint": true_rv["resolved_count"],
        "ledger_root": hash_obj(true_ledger),
    }
    ignored_flag = (
        "primary_holder" in tracked.accessed_fields
        and broken_next_beginning["primary_holder"] != read_value
    )
    c_ok, c_fail = contract_satisfied(broken_next_beginning, contract, config)
    e_ok, e_field, e_detail = exact_closure(broken_next_beginning, true_ending, config)
    arms.append(
        ArmResult(
            "13_ignored_return_value_control",
            "Return value is read (accessed_fields is non-empty) but the output field is hardcoded "
            "regardless of what was read: this must be flagged as an ignored return value.",
            closes=bool(e_ok) and not ignored_flag,
            contract_satisfied=bool(c_ok),
            contract_fail_reason=c_fail,
            exact_closure_fail_field=e_field if not (e_ok and ignored_flag) else "ignored_return_value_detected",
            exact_closure_detail=e_detail,
            return_value_used=not ignored_flag,
            notes=f"ignored_return_value_detected={ignored_flag}",
        )
    )

    return arms


def evaluate_world_family(config: W.WorldConfig, rng_seed: int) -> dict:
    contract = locked_beginning_contract(config)
    reference, closing, non_closing = find_reference_history(config, contract)
    result: dict[str, Any] = {
        "world_id": config.world_id,
        "config": config.to_dict(),
        "contract": contract,
        "total_histories": len(closing) + len(non_closing),
        "closing_count": len(closing),
        "non_closing_count": len(non_closing),
        "closing_examples": [list(h) for h in closing[:5]],
        "non_closing_examples": [list(h) for h in non_closing[:5]],
        "reference_history": list(reference) if reference else None,
    }
    if reference is None:
        result["status"] = "unsupported"
        result["reason"] = "no natural history satisfies both the locked contract and exact closure"
        result["arms"] = []
        return result

    arms = run_intervention_arms(config, reference, rng_seed)
    result["arms"] = [vars(a) for a in arms]

    relevant_arm = next(a for a in arms if a.arm_id == "06_relevant_intermediate_mutation")
    irrelevant_arm = next(a for a in arms if a.arm_id == "07_irrelevant_intermediate_mutation")
    natural_arm = next(a for a in arms if a.arm_id == "01_correct_return_value")
    ignored_arm = next(a for a in arms if a.arm_id == "13_ignored_return_value_control")

    disrupting_arm_ids = [
        "02_missing_return_value", "03_random_return_value", "04_return_value_from_different_history",
        "05_endpoint_mutation", "08_correct_return_value_incorrect_ledger",
        "09_correct_ledger_incorrect_reconstruction", "10_no_endpoint_information",
        "12_directly_copied_beginning",
    ]
    all_disruptions_broke = all(not next(a for a in arms if a.arm_id == aid).closes for aid in disrupting_arm_ids)
    relevant_broke = relevant_arm.notes != "ineligible" and not relevant_arm.closes
    irrelevant_preserved = irrelevant_arm.notes != "ineligible" and irrelevant_arm.closes
    ignored_detected = "ignored_return_value_detected=True" in ignored_arm.notes

    result["support_checks"] = {
        "at_least_one_natural_closing_history": len(closing) >= 1,
        "at_least_one_natural_non_closing_history": len(non_closing) >= 1,
        "natural_reference_closes": natural_arm.closes,
        "all_disrupting_arms_break_closure": all_disruptions_broke,
        "relevant_intermediate_arm_applicable": relevant_arm.notes != "ineligible",
        "relevant_intermediate_breaks_closure": relevant_broke,
        "irrelevant_intermediate_arm_applicable": irrelevant_arm.notes != "ineligible",
        "irrelevant_intermediate_preserves_closure": irrelevant_preserved,
        "ignored_return_value_detected_and_rejected": ignored_detected and not ignored_arm.closes,
    }
    checks = result["support_checks"]
    core_ok = (
        checks["at_least_one_natural_closing_history"]
        and checks["at_least_one_natural_non_closing_history"]
        and checks["natural_reference_closes"]
        and checks["all_disrupting_arms_break_closure"]
        and checks["ignored_return_value_detected_and_rejected"]
    )
    if not core_ok:
        result["status"] = "unsupported"
    elif not (checks["relevant_intermediate_arm_applicable"] and checks["irrelevant_intermediate_arm_applicable"]):
        result["status"] = "inconclusive"
        result["reason"] = "relevant/irrelevant intermediate-action arms not both constructible for this world family"
    elif not checks["relevant_intermediate_breaks_closure"] or not checks["irrelevant_intermediate_preserves_closure"]:
        result["status"] = "unsupported"
    else:
        result["status"] = "supported"
    return result


def run_component(world_families, seed_base: int) -> dict:
    per_family = {}
    for i, wf in enumerate(world_families):
        per_family[wf.family_id] = evaluate_world_family(wf.config, seed_base + i)
    statuses = [r["status"] for r in per_family.values()]
    if any(s == "supported" for s in statuses):
        overall = "supported" if all(s in ("supported", "inconclusive") for s in statuses) else "supported"
    else:
        overall = "unsupported" if statuses else "invalid"
    if not per_family:
        overall = "invalid"
    return {
        "status": overall,
        "reason": (
            "at least one world family demonstrates natural closing and non-closing histories, "
            "all disruptive interventions breaking closure, the relevant/irrelevant distinction holding, "
            "and ignored-return-value detection working"
            if overall == "supported"
            else "no world family satisfied every reciprocal-closure support check"
        ),
        "per_world_family": per_family,
    }
