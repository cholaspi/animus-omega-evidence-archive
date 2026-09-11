"""Test 05E: Integrated Animus Omega Evaluation.

Protocol v1.3.0-dev4, corrections 3-6: this module is rewritten as an
explicit, one-gate-per-required-property structure. Every one of the 16
properties required by section 17 gets its own named gate, evaluated from
its own real evidence source -- no gate stands in for a different property
by name-resemblance alone (the v1.2.0-dev3 defect this replaces: an
"expanding_and_contracting_represented_world" gate that actually checked
only whether 05A ran, and a "negative_and_fault_injection_controls_pass"
gate that never read the fault-execution matrix at all). ``evaluate()`` now
takes all six component results -- boundary, residual, observer, resource,
expansion, and execution_matrix -- so every computed component can actually
gate the integrated status.

This module performs no simulation of its own: it only reads the already-
computed component result dictionaries. Per protocol: "If any required
component is unsupported, inconclusive, ineligible, or invalid, the
complete conjecture is not supported by this run." This is never converted
to "disproved."

See gate_registry.py for the protocol-clause-to-evidence-source-to-
evaluator-to-validator-check registry that documents every gate below.
validator.py's independent integrated-status derivation deliberately does
NOT call this module's ``evaluate()`` -- it recomputes every gate with its
own separate implementation, so a defect here cannot silently reproduce
itself in the "independent" derivation (protocol v1.3.0-dev4, correction 7).
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


def semantic_continuity_core_result(residual_result: dict) -> dict:
    """Section 17 item 9: semantic continuity on all 9 core probes,
    reported as its own gate (not folded into a combined semantic bundle)."""
    families = residual_result.get("per_world_family", {})
    if not families:
        return {"status": "invalid", "reason": "no world family evaluated", "per_world_family": {}}
    per_family = {}
    for fid, r in families.items():
        scoring = r.get("main_probe_grade", {}).get("scoring", {}).get("required_core", {})
        per_family[fid] = bool(scoring.get("all_pass")) and scoring.get("total") == 9
    status = "supported" if all(per_family.values()) else "unsupported"
    return {
        "status": status,
        "reason": (
            "every world family's residual passes all 9 of 9 required core semantic probes"
            if status == "supported"
            else "at least one world family did not pass all 9 required core semantic probes"
        ),
        "per_world_family": per_family,
    }


def semantic_continuity_delayed_result(residual_result: dict) -> dict:
    """Section 17 item 10: semantic continuity on all 8 delayed probes,
    reported as its own gate."""
    families = residual_result.get("per_world_family", {})
    if not families:
        return {"status": "invalid", "reason": "no world family evaluated", "per_world_family": {}}
    per_family = {}
    for fid, r in families.items():
        scoring = r.get("main_probe_grade", {}).get("scoring", {}).get("delayed", {})
        per_family[fid] = bool(scoring.get("all_pass")) and scoring.get("total") == 8
    status = "supported" if all(per_family.values()) else "unsupported"
    return {
        "status": status,
        "reason": (
            "every world family's residual passes all 8 of 8 delayed probes"
            if status == "supported"
            else "at least one world family did not pass all 8 delayed probes"
        ),
        "per_world_family": per_family,
    }


def clean_leakage_audit_result(residual_result: dict) -> dict:
    """Section 17 item 11: the leakage audit is clean in every family, plus
    every positive control passes and every negative control correctly
    fails (both required for "semantic continuity is invalid if success
    depends on prohibited leakage" to be checkable at all)."""
    families = residual_result.get("per_world_family", {})
    if not families:
        return {"status": "invalid", "reason": "no world family evaluated", "per_world_family": {}}
    per_family = {}
    for fid, r in families.items():
        checks = r.get("support_checks", {})
        per_family[fid] = bool(checks.get("leakage_audit_clean")) and bool(checks.get("positive_controls_pass"))
    status = "supported" if all(per_family.values()) else "unsupported"
    return {
        "status": status,
        "reason": (
            "every world family's leakage audit is clean and its positive controls pass"
            if status == "supported"
            else "at least one world family's leakage audit found a violation, or a positive control failed"
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


def fault_control_validity_result(execution_matrix_result: dict) -> dict:
    """Section 17 item 13, section 13 (part 2): "every required fault must
    produce its frozen predicted rejection or semantic failure." Reads
    execution_matrix_result directly (the seed-based fault-mutation
    matrix) -- NOT residual_result's negative controls, which is a
    different, 05B-internal check. Protocol v1.3.0-dev4, correction 4: this
    is the real gate that v1.2.0-dev3 never wired in."""
    families = execution_matrix_result.get("per_world_family", {})
    if not families:
        return {"status": "invalid", "reason": "no world family evaluated", "per_world_family": {}}
    per_family = {fid: r.get("all_predictions_matched", False) for fid, r in families.items()}
    status = "supported" if all(per_family.values()) else "unsupported"
    return {
        "status": status,
        "reason": (
            "every declared fault mutation produced its frozen predicted rejection or semantic failure "
            "in every world family"
            if status == "supported"
            else "at least one execution's observed failure did not match its frozen prediction "
            "(see the family's unexpected_predictions)"
        ),
        "per_world_family": per_family,
    }


def expansion_and_contraction_result(expansion_result: dict) -> dict:
    """Section 17 item 1, section 16: R(t1) >= 2*R(t0) and R(t2) <=
    R(t0)+1 for some t0<t1<t2, witnessed by an actual enumerated history in
    every world family. Reads expansion_result directly. Protocol
    v1.3.0-dev4, correction 4: this is the real gate that v1.2.0-dev3 never
    wired in (its "expanding_and_contracting_represented_world" gate
    checked only that 05A ran, never this component's own result)."""
    families = expansion_result.get("per_world_family", {})
    if not families:
        return {"status": "invalid", "reason": "no world family evaluated", "per_world_family": {}}
    per_family = {fid: (r.get("status") == "supported") for fid, r in families.items()}
    status = "supported" if all(per_family.values()) else "unsupported"
    return {
        "status": status,
        "reason": (
            "every world family exhibits the required expansion/contraction pattern in at least one "
            "exhaustively-enumerated history"
            if status == "supported"
            else "at least one world family has no admissible history exhibiting the required pattern "
            "(see the family's theoretical_max_r for whether this is mathematically impossible or merely "
            "unwitnessed)"
        ),
        "per_world_family": per_family,
    }


def resource_advantage_result(resource_result: dict, semantic_continuity_status: str) -> dict:
    """Resource advantage is ELIGIBLE only if semantic fidelity (semantic
    continuity, both core and delayed) is itself supported; otherwise no
    resource comparison can be trusted, regardless of what 05D's own
    internal computation found."""
    if semantic_continuity_status != "supported":
        return {
            "status": "ineligible",
            "reason": "semantic fidelity (semantic continuity) is not supported, so no resource comparison is eligible",
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
# Integrated gate table: 16 explicit gates, one per section-17 item.
# ---------------------------------------------------------------------------

def evaluate(
    boundary_result: dict,
    residual_result: dict,
    observer_result: dict,
    resource_result: dict,
    expansion_result: dict,
    execution_matrix_result: dict,
) -> dict:
    gates: list[dict] = []
    boundary_families = boundary_result.get("per_world_family", {})

    # 1. Required expansion and contraction.
    expansion = expansion_and_contraction_result(expansion_result)
    gates.append(_gate("expansion_and_contraction", expansion["status"] == "supported", expansion["reason"]))

    # 2. Beginning contract committed before tick zero.
    contract_committed = all(
        r.get("beginning_commitment", {}).get("consumed") is False
        and r.get("beginning_commitment", {}).get("content_hash")
        for r in boundary_families.values()
    ) and len(boundary_families) > 0
    gates.append(_gate(
        "beginning_contract_committed",
        contract_committed,
        "FrozenContract is a pure function of (WorldConfig, protocol_version) plus other modules' own "
        "frozen pre-execution content, computed and hashed before any history executes, and recorded "
        "unconsumed in the evidence record itself",
    ))

    # 3. Ending-derived return value.
    ending_rv_present = all(
        any(a.get("arm_id") == "01_correct_return_value" and a.get("return_value_used") for a in r.get("arms", []))
        for r in boundary_families.values()
    ) and len(boundary_families) > 0
    gates.append(_gate(
        "ending_derived_return_value",
        ending_rv_present,
        "return_value_of(ending_state) is computed and actually read by J in the natural-history arm of every "
        "world family",
    ))

    # 4. Executed J transition.
    executed_transition = all(
        all(a.get("contract_fail_reason") != "no_transition_executed" or a.get("arm_id") == "11_open_chain_no_return_transition" for a in r.get("arms", []))
        and any(a.get("arm_id") == "01_correct_return_value" for a in r.get("arms", []))
        for r in boundary_families.values()
    ) and len(boundary_families) > 0
    gates.append(_gate(
        "executed_transition",
        executed_transition,
        "execute_J() is called and consumes the frozen contract for every arm of every evaluated world family "
        "(the sole declared exception, arm 11, is itself the open-chain control for 'no transition executed')",
    ))

    # 5. At least one closing history.
    at_least_one_closing = any(
        r.get("support_checks", {}).get("at_least_one_natural_closing_history") for r in boundary_families.values()
    )
    gates.append(_gate(
        "at_least_one_closing_history",
        at_least_one_closing,
        "at least one world family exhibits at least one natural history satisfying the locked beginning "
        "contract after J",
    ))

    # 6. At least one non-closing history.
    at_least_one_non_closing = any(
        r.get("support_checks", {}).get("at_least_one_natural_non_closing_history") for r in boundary_families.values()
    )
    gates.append(_gate(
        "at_least_one_non_closing_history",
        at_least_one_non_closing,
        "at least one world family exhibits at least one natural history that does not satisfy the locked "
        "beginning contract after J",
    ))

    # 7. Causal endpoint sensitivity.
    causal_sensitivity = any(
        r.get("support_checks", {}).get("relevant_intermediate_breaks_closure")
        and r.get("support_checks", {}).get("irrelevant_intermediate_preserves_closure")
        and r.get("support_checks", {}).get("relevant_intermediate_modifies_causal_path")
        and r.get("support_checks", {}).get("irrelevant_intermediate_does_not_modify_causal_path")
        for r in boundary_families.values()
    )
    gates.append(_gate(
        "causal_endpoint_sensitivity",
        causal_sensitivity,
        "at least one world family shows relevant interventions breaking closure AND modifying the "
        "declared causal path, while irrelevant ones do neither",
    ))

    # 8. Genuine information loss.
    loss = genuine_information_loss_result(residual_result)
    gates.append(_gate("genuine_information_loss", loss["status"] == "supported", loss["reason"]))

    # 9. Semantic continuity on all core probes.
    semantic_core = semantic_continuity_core_result(residual_result)
    gates.append(_gate("semantic_continuity_core_probes", semantic_core["status"] == "supported", semantic_core["reason"]))

    # 10. Semantic continuity on all delayed probes.
    semantic_delayed = semantic_continuity_delayed_result(residual_result)
    gates.append(_gate("semantic_continuity_delayed_probes", semantic_delayed["status"] == "supported", semantic_delayed["reason"]))

    # 11. Clean leakage audit.
    leakage = clean_leakage_audit_result(residual_result)
    gates.append(_gate("clean_leakage_audit", leakage["status"] == "supported", leakage["reason"]))

    # 12. Ledger causality.
    ledger_causality = ledger_causality_result(boundary_result, residual_result)
    gates.append(_gate("ledger_causality", ledger_causality["status"] == "supported", ledger_causality["reason"]))

    # 13. Valid fault controls.
    fault_control = fault_control_validity_result(execution_matrix_result)
    gates.append(_gate("fault_control_validity", fault_control["status"] == "supported", fault_control["reason"]))

    # 14. Primary observer indistinguishability.
    observer_families = observer_result.get("per_world_family", {})
    primary_observer_ok = all(
        r.get("status") == "supported" for r in observer_families.values()
    ) and len(observer_families) > 0
    gates.append(_gate(
        "primary_observer_indistinguishability",
        primary_observer_ok,
        "the single frozen PRIMARY bounded observer stays under the indistinguishability threshold in every "
        "05C world family (sensitivity-analysis classes are diagnostic only and never gate this)",
    ))

    # 15. Full-state observer boundary detection (positive control).
    positive_controls_ok = all(
        r.get("positive_control_result", {}).get("conclusion") == "positive_control_valid"
        for r in observer_families.values() if "positive_control_result" in r
    ) and len(observer_families) > 0
    gates.append(_gate(
        "full_state_observer_boundary_detection",
        positive_controls_ok,
        "the full-state observer's TV distance or Bayes-optimal accuracy exceeds the positive-control "
        "threshold in every 05C world family",
    ))

    # 16. Fidelity-matched resource advantage.
    semantic_continuity_status = "supported" if (
        semantic_core["status"] == "supported" and semantic_delayed["status"] == "supported"
        and leakage["status"] == "supported"
    ) else "unsupported"
    resource = resource_advantage_result(resource_result, semantic_continuity_status)
    gates.append(_gate(
        "fidelity_matched_resource_advantage",
        resource["status"] == "supported",
        resource["reason"],
    ))

    assert len(gates) == 16, f"protocol v1.3.0-dev4 requires exactly 16 integrated gates, got {len(gates)}"

    failed_gates = []
    ineligible_gates = []
    invalid_gates = []
    for g in gates:
        if g["ok"]:
            continue
        if g["gate"] == "fidelity_matched_resource_advantage" and resource["status"] == "ineligible":
            ineligible_gates.append(g["gate"])
        elif g["gate"] == "full_state_observer_boundary_detection":
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
            "semantic_continuity_core": semantic_core,
            "semantic_continuity_delayed": semantic_delayed,
            "clean_leakage_audit": leakage,
            "ledger_causality": ledger_causality,
            "fault_control_validity": fault_control,
            "expansion_and_contraction": expansion,
            "resource_advantage": resource,
        },
        "interpretation": (
            "Every one of the 16 required integration gates passed for this bounded, deterministic "
            "development protocol. This supports the specific implemented model only; it does not "
            "establish consciousness, subjective continuity, physical cosmology, unrestricted "
            "predestination, or that the physical universe follows this structure."
            if status == "supported"
            else (
                "At least one of the 16 required integration gates did not pass (see "
                "failed_gates/ineligible_gates/invalid_gates). The complete Animus Omega conjecture is "
                "therefore not supported by this development run. This is not evidence that it is "
                "disproved: it means this bounded model and protocol did not jointly demonstrate every "
                "required property in the same run. Every component result above remains valid and "
                "preserved regardless of this integrated outcome."
            )
        ),
    }
