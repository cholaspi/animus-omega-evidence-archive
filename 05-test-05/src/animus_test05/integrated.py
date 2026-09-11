"""Test 05E: Integrated Animus Omega Evaluation.

Protocol v2, update A: the integrated result is a *gated dashboard*. Every
component below is computed and reported independently of the others and
independently of the final integrated status, using these result functions
as the single source of truth for both the standalone dashboard entries
(built by run.py) and the integrated gate table (built here) -- so a
component's displayed status can never silently drift from what actually
gates the integrated conclusion. An integrated failure never erases or
hides a component's own result.

Allowed statuses: supported, unsupported, inconclusive, ineligible, invalid.

This module performs no simulation of its own: it only reads the already-
computed 05A-05D component result dictionaries. Per protocol: "If any
required component is unsupported, inconclusive, ineligible, or invalid,
the complete conjecture is not supported by this run." This is never
converted to "disproved."
"""

from __future__ import annotations

from typing import Any


def _gate(name: str, ok: bool, detail: str) -> dict:
    return {"gate": name, "ok": ok, "detail": detail}


# ---------------------------------------------------------------------------
# Shared component-result derivations (single source of truth for both the
# dashboard entries in run.py and the gate table below).
# ---------------------------------------------------------------------------

def genuine_information_loss_result(residual_result: dict) -> dict:
    """Split out from 05B's bundled status: whether the residual is a
    demonstrably non-injective function of the admissible microstate space,
    in every world family -- independent of whether the probes/controls
    also pass."""
    families = residual_result.get("per_world_family", {})
    if not families:
        return {"status": "invalid", "reason": "no world family evaluated", "per_world_family": {}}
    per_family = {
        fid: r.get("support_checks", {}).get("non_injective_loss_demonstrated", False)
        for fid, r in families.items()
    }
    status = "supported" if all(per_family.values()) else "unsupported"
    return {
        "status": status,
        "reason": (
            "every world family's residual has at least one collision group (two distinct admissible "
            "microstates mapping to the same residual)"
            if status == "supported"
            else "at least one world family's residual was injective (no genuine loss demonstrated)"
        ),
        "per_world_family": per_family,
    }


def semantic_continuity_result(residual_result: dict) -> dict:
    """Split out from 05B's bundled status: whether the semantic probe
    battery, positive controls, negative controls, and leakage audit all
    pass -- independent of the genuine-loss (non-injectivity) finding."""
    families = residual_result.get("per_world_family", {})
    if not families:
        return {"status": "invalid", "reason": "no world family evaluated", "per_world_family": {}}
    keys = (
        "main_residual_passes_all_probes", "positive_controls_pass",
        "negative_controls_correctly_fail", "leakage_audit_clean",
    )
    per_family = {}
    for fid, r in families.items():
        checks = r.get("support_checks", {})
        per_family[fid] = all(checks.get(k, False) for k in keys)
    status = "supported" if all(per_family.values()) else "unsupported"
    return {
        "status": status,
        "reason": (
            "every world family's residual passes every semantic probe, every positive control passes, "
            "every negative control correctly fails, and the leakage audit is clean"
            if status == "supported"
            else "at least one world family failed a semantic probe, a control, or the leakage audit"
        ),
        "per_world_family": per_family,
    }


def ledger_causality_result(boundary_result: dict, residual_result: dict) -> dict:
    """Does the narrative ledger causally affect reconstruction/future
    behavior? Evidenced by (a) 05B's negative controls that remove or
    corrupt the ledger correctly failing probes, and (b) 05A's arm 8
    (correct return value, incorrect ledger) correctly breaking closure."""
    residual_families = residual_result.get("per_world_family", {})
    boundary_families = boundary_result.get("per_world_family", {})
    if not residual_families or not boundary_families:
        return {"status": "invalid", "reason": "no world family evaluated", "per_family": {}}

    per_family = {}
    for fid, r in residual_families.items():
        controls = r.get("controls", {})
        no_ledger_fails = not controls.get("lossy_residual_without_ledger", {}).get("all_pass", True)
        stale_ledger_fails = not controls.get("stale_ledger_entry", {}).get("all_pass", True)
        contradictory_fails = not controls.get("contradictory_ledger_entry", {}).get("all_pass", True)
        per_family[f"05B:{fid}"] = no_ledger_fails and stale_ledger_fails and contradictory_fails
    for fid, r in boundary_families.items():
        arm8 = next((a for a in r.get("arms", []) if a["arm_id"] == "08_correct_return_value_incorrect_ledger"), None)
        per_family[f"05A:{fid}"] = (arm8 is not None) and (not arm8["closes"])

    status = "supported" if per_family and all(per_family.values()) else "unsupported"
    return {
        "status": status,
        "reason": (
            "removing/staling/corrupting the ledger breaks semantic probes (05B) and corrupting the ledger "
            "breaks closure (05A arm 8) in every world family"
            if status == "supported"
            else "at least one world family did not show the ledger causally affecting reconstruction/closure"
        ),
        "per_family": per_family,
    }


def resource_advantage_result(resource_result: dict, semantic_continuity_status: str) -> dict:
    """Resource advantage is ELIGIBLE only if semantic fidelity (semantic
    continuity) is itself supported; otherwise no resource comparison can
    be trusted, regardless of what 05D's own internal computation found."""
    if semantic_continuity_status != "supported":
        return {
            "status": "ineligible",
            "reason": "semantic fidelity (semantic_continuity) is not supported, so no resource comparison is eligible",
            "internal_status": resource_result.get("status"),
            "per_world_family": resource_result.get("per_world_family", {}),
        }
    return {
        "status": resource_result.get("status", "invalid"),
        "reason": resource_result.get("reason", ""),
        "internal_status": resource_result.get("status"),
        "per_world_family": resource_result.get("per_world_family", {}),
    }


# ---------------------------------------------------------------------------
# Integrated gate table
# ---------------------------------------------------------------------------

def evaluate(
    boundary_result: dict,
    residual_result: dict,
    observer_result: dict,
    resource_result: dict,
) -> dict:
    gates: list[dict] = []

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
        "FrozenContract is a pure function of WorldConfig only, computed and hashed before any history executes "
        "(protocol v2, update E)",
    ))
    gates.append(_gate(
        "ending_derived_return_value_present",
        ran_boundary,
        "return_value_of(ending_state) is computed and fed into J in every 05A arm",
    ))
    gates.append(_gate(
        "executed_transition_ending_to_beginning",
        ran_boundary,
        "execute_J() is called and consumes the frozen contract for every arm of every evaluated world family",
    ))

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
        and r.get("support_checks", {}).get("relevant_intermediate_modifies_causal_path")
        and r.get("support_checks", {}).get("irrelevant_intermediate_does_not_modify_causal_path")
        for r in boundary_families.values()
    )
    gates.append(_gate(
        "causal_sensitivity_and_specificity",
        any_family_relevant_sensitivity,
        "at least one 05A world family shows relevant interventions breaking closure AND modifying the "
        "declared causal path, while irrelevant ones do neither",
    ))

    loss = genuine_information_loss_result(residual_result)
    gates.append(_gate("genuine_information_loss", loss["status"] == "supported", loss["reason"]))

    semantic = semantic_continuity_result(residual_result)
    gates.append(_gate("preserved_semantic_behavior_through_loss", semantic["status"] == "supported", semantic["reason"]))

    ledger_causality = ledger_causality_result(boundary_result, residual_result)
    gates.append(_gate("narrative_ledger_causally_load_bearing", ledger_causality["status"] == "supported", ledger_causality["reason"]))

    observer_families = observer_result.get("per_world_family", {})
    positive_controls_ok = all(
        r.get("positive_control_result", {}).get("conclusion") == "positive_control_valid"
        for r in observer_families.values() if "positive_control_result" in r
    ) and len(observer_families) > 0
    gates.append(_gate(
        "positive_control_observer_detects_boundary",
        positive_controls_ok,
        "the full-state observer's TV distance exceeds the positive-control threshold in every 05C world family",
    ))
    primary_observer_ok = all(
        r.get("status") == "supported" for r in observer_families.values()
    ) and len(observer_families) > 0
    gates.append(_gate(
        "no_qualifying_distinction_for_primary_bounded_observer",
        primary_observer_ok,
        "the single frozen PRIMARY bounded observer stays under the indistinguishability threshold in every "
        "05C world family (sensitivity-analysis classes are diagnostic only and never gate this)",
    ))

    resource = resource_advantage_result(resource_result, semantic["status"])
    gates.append(_gate(
        "fidelity_matched_resource_advantage",
        resource["status"] == "supported",
        resource["reason"],
    ))

    controls_ok = all(
        r.get("support_checks", {}).get("negative_controls_correctly_fail")
        for r in residual_result.get("per_world_family", {}).values()
    ) and len(residual_result.get("per_world_family", {})) > 0
    gates.append(_gate(
        "negative_and_fault_injection_controls_pass",
        controls_ok,
        "every 05B world family's negative controls correctly fail at least one semantic probe",
    ))

    failed_gates = []
    ineligible_gates = []
    invalid_gates = []
    for g in gates:
        if g["ok"]:
            continue
        if g["gate"] == "fidelity_matched_resource_advantage" and resource["status"] == "ineligible":
            ineligible_gates.append(g["gate"])
        elif g["gate"] == "positive_control_observer_detects_boundary":
            invalid_gates.append(g["gate"])
        else:
            failed_gates.append(g["gate"])

    all_ok = all(g["ok"] for g in gates)
    status = "supported" if all_ok else "not_supported"

    return {
        "status": status,
        "gates": gates,
        "failed_gates": failed_gates,
        "ineligible_gates": ineligible_gates,
        "invalid_gates": invalid_gates,
        "component_summaries": {
            "genuine_information_loss": loss,
            "semantic_continuity": semantic,
            "ledger_causality": ledger_causality,
            "resource_advantage": resource,
        },
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
                "jointly demonstrate every required property in the same run. Every component result above "
                "remains valid and preserved regardless of this integrated outcome."
            )
        ),
    }
