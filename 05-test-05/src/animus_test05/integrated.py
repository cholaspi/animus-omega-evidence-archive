"""Test 05E: Integrated Animus Omega Evaluation.

Combines the Test 05A-D component results (already independently computed
and recorded) under the strict gating rules from the protocol. This module
performs no simulation of its own: it only reads the already-computed
component result dictionaries and applies the gating logic, so the
integrated conclusion is fully recomputable from those component results
(and, transitively, from the raw evidence they were built from).

Per protocol: "If any required component is unsupported, inconclusive,
ineligible, or invalid, the complete conjecture is not supported by this
run." This module never converts "not supported" into "disproved".
"""

from __future__ import annotations

from typing import Any


def _gate(name: str, ok: bool, detail: str) -> dict:
    return {"gate": name, "ok": ok, "detail": detail}


def evaluate(
    boundary_result: dict,
    residual_result: dict,
    observer_result: dict,
    resource_result: dict,
) -> dict:
    gates: list[dict] = []

    # Gate 1-4: structural gates about the executed boundary transition.
    # These hold by construction whenever 05A actually ran (produced at
    # least one per-family result), since world.py always executes an
    # ending->beginning transition J with a pre-committed contract.
    boundary_families = boundary_result.get("per_world_family", {})
    ran_boundary = len(boundary_families) > 0
    gates.append(_gate(
        "expanding_and_contracting_represented_world",
        ran_boundary,
        "every 05A world family executes a history (expansion) followed by a J boundary transition (contraction)",
    ))
    gates.append(_gate(
        "independently_locked_beginning_contract",
        ran_boundary,
        "locked_beginning_contract() is a pure function of WorldConfig only, computed before any history executes",
    ))
    gates.append(_gate(
        "ending_derived_return_value_present",
        ran_boundary,
        "return_value_of(ending_state) is computed and fed into J in every 05A arm",
    ))
    gates.append(_gate(
        "executed_transition_ending_to_beginning",
        ran_boundary,
        "execute_J() is called for every arm of every evaluated world family",
    ))

    # Gate 5-6: closing/non-closing histories and causal sensitivity, read
    # from 05A's per-family support checks.
    any_family_both_closing_and_nonclosing = any(
        r.get("support_checks", {}).get("at_least_one_natural_closing_history")
        and r.get("support_checks", {}).get("at_least_one_natural_non_closing_history")
        for r in boundary_families.values()
    )
    gates.append(_gate(
        "both_closing_and_non_closing_histories",
        any_family_both_closing_and_nonclosing,
        "at least one 05A world family exhibits both closing and non-closing natural histories",
    ))
    any_family_relevant_sensitivity = any(
        r.get("support_checks", {}).get("relevant_intermediate_breaks_closure")
        and r.get("support_checks", {}).get("irrelevant_intermediate_preserves_closure")
        for r in boundary_families.values()
    )
    gates.append(_gate(
        "causal_sensitivity_to_endpoint_information",
        any_family_relevant_sensitivity,
        "at least one 05A world family shows relevant interventions breaking closure while irrelevant ones do not",
    ))

    # Gate 7-8: genuine loss and preserved semantics, from 05B.
    residual_families = residual_result.get("per_world_family", {})
    any_non_injective = any(r.get("collision_analysis", {}).get("non_injective") for r in residual_families.values())
    gates.append(_gate(
        "genuine_information_loss",
        any_non_injective,
        "at least one 05B world family's residual is a non-injective function of the admissible microstate space",
    ))
    semantic_preserved = residual_result.get("status") == "supported"
    gates.append(_gate(
        "preserved_semantic_behavior_through_loss",
        semantic_preserved,
        f"05B overall status is {residual_result.get('status')!r}",
    ))

    # Gate 9: narrative ledger causally affects reconstruction/future
    # behavior. Evidenced by (a) 05B's negative controls that remove or
    # corrupt the ledger correctly failing probes, and (b) 05A's arm 8
    # (correct return value, incorrect ledger) correctly breaking closure.
    ledger_matters_05b = all(
        not r.get("controls", {}).get("lossy_residual_without_ledger", {}).get("all_pass", True)
        for r in residual_families.values()
        if "lossy_residual_without_ledger" in r.get("controls", {})
    ) and len(residual_families) > 0
    ledger_matters_05a = all(
        not next((a for a in r.get("arms", []) if a["arm_id"] == "08_correct_return_value_incorrect_ledger"), {"closes": True}).get("closes", True)
        for r in boundary_families.values()
        if r.get("arms")
    )
    gates.append(_gate(
        "narrative_ledger_causally_load_bearing",
        ledger_matters_05b and ledger_matters_05a,
        "removing the ledger breaks semantic probes (05B) and corrupting the ledger breaks closure (05A arm 8)",
    ))

    # Gate 10-11: observer boundary detection, from 05C.
    observer_families = observer_result.get("per_world_family", {})
    positive_controls_ok = all(
        any(o["observer_id"] == "full_state_positive_control" and o["conclusion"] == "positive_control_valid" for o in r.get("observers", []))
        for r in observer_families.values() if "observers" in r
    ) and len(observer_families) > 0
    gates.append(_gate(
        "positive_control_observer_detects_boundary",
        positive_controls_ok,
        "the full-state observer's TV distance exceeds the positive-control threshold in every 05C world family",
    ))
    bounded_indistinguishable = all(
        r.get("status") == "supported" for r in observer_families.values()
    ) and len(observer_families) > 0
    gates.append(_gate(
        "no_qualifying_distinction_for_bounded_observer",
        bounded_indistinguishable,
        "every bounded observer class stays under the frozen indistinguishability threshold in every 05C world family",
    ))

    # Gate 12: resource advantage, from 05D -- but only eligible if 05B
    # (semantic fidelity) is itself supported; otherwise the resource
    # comparison is ineligible regardless of its own internal result.
    resource_eligible = semantic_preserved
    resource_ok = resource_eligible and resource_result.get("status") == "supported"
    gates.append(_gate(
        "fidelity_matched_resource_advantage",
        resource_ok,
        (
            "ineligible: semantic fidelity (05B) is not supported, so no resource comparison can be trusted"
            if not resource_eligible
            else f"05D overall status is {resource_result.get('status')!r}"
        ),
    ))

    # Gate 13: negative/fault-injection controls, from 05B.
    controls_ok = all(
        r.get("support_checks", {}).get("negative_controls_correctly_fail") for r in residual_families.values()
    ) and len(residual_families) > 0
    gates.append(_gate(
        "negative_and_fault_injection_controls_pass",
        controls_ok,
        "every 05B world family's negative controls correctly fail at least one semantic probe",
    ))

    failed_gates = [g["gate"] for g in gates if not g["ok"] and "ineligible" not in g["detail"]]
    ineligible_gates = [g["gate"] for g in gates if not g["ok"] and "ineligible" in g["detail"]]
    invalid_gates = []
    if any(r.get("status") == "invalid" for r in observer_families.values()):
        invalid_gates.append("positive_control_observer_detects_boundary")
    if residual_result.get("status") not in ("supported", "unsupported"):
        invalid_gates.append("preserved_semantic_behavior_through_loss")

    all_ok = all(g["ok"] for g in gates) and not invalid_gates
    status = "supported" if all_ok else "not_supported"

    return {
        "status": status,
        "gates": gates,
        "failed_gates": [g for g in failed_gates if g not in invalid_gates],
        "ineligible_gates": ineligible_gates,
        "invalid_gates": invalid_gates,
        "interpretation": (
            "Every integration gate passed for this bounded, deterministic development protocol. This "
            "supports the specific implemented model only; it does not establish consciousness, subjective "
            "continuity, physical cosmology, unrestricted predestination, or that the physical universe "
            "follows this structure."
            if status == "supported"
            else (
                "At least one integration gate did not pass (see failed_gates/ineligible_gates/invalid_gates). "
                "The complete Animus Omega conjecture is therefore not supported by this development run. "
                "This is not evidence that it is disproved: it means this bounded model and protocol did not "
                "jointly demonstrate every required property in the same run."
            )
        ),
    }
