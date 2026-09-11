import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import integrated as I


def _boundary_family(closes_all=True, has_relevant=True, has_irrelevant=True):
    arms = [
        {"arm_id": "01_correct_return_value", "closes": True, "return_value_used": True},
        {
            "arm_id": "06_relevant_intermediate_mutation",
            "closes": not closes_all,  # relevant intervention breaks closure
            "notes": "" if has_relevant else "ineligible",
            "causal_path_diff": {"any_stage_differs": True},
        },
        {
            "arm_id": "07_irrelevant_intermediate_mutation",
            "closes": closes_all,  # irrelevant intervention preserves closure
            "notes": "" if has_irrelevant else "ineligible",
            "causal_path_diff": {"any_stage_differs": False},
        },
        {"arm_id": "08_correct_return_value_incorrect_ledger", "closes": False},
        {"arm_id": "11_open_chain_no_return_transition", "closes": False, "contract_fail_reason": "no_transition_executed"},
    ]
    return {
        "status": "supported" if closes_all else "unsupported",
        "beginning_commitment": {"consumed": False, "content_hash": "deadbeef"},
        "arms": arms,
        "support_checks": {
            "at_least_one_natural_closing_history": True,
            "at_least_one_natural_non_closing_history": True,
            "relevant_intermediate_breaks_closure": True,
            "irrelevant_intermediate_preserves_closure": True,
            "relevant_intermediate_modifies_causal_path": True,
            "irrelevant_intermediate_does_not_modify_causal_path": True,
        },
    }


def make_boundary_result(all_supported=True):
    return {"status": "supported" if all_supported else "unsupported", "per_world_family": {"fam1": _boundary_family(closes_all=True)}}


def _residual_family(all_pass=True):
    return {
        "support_checks": {
            "non_injective_loss_demonstrated": all_pass,
            "main_residual_passes_all_probes": all_pass,
            "positive_controls_pass": all_pass,
            "negative_controls_correctly_fail": all_pass,
            "leakage_audit_clean": all_pass,
        },
        "main_probe_grade": {
            "scoring": {
                "required_core": {"total": 9, "all_pass": all_pass},
                "delayed": {"total": 8, "all_pass": all_pass},
            },
        },
        "controls": {
            "lossy_residual_without_ledger": {"all_pass": not all_pass},
            "stale_ledger_entry": {"all_pass": not all_pass},
            "contradictory_ledger_entry": {"all_pass": not all_pass},
        },
    }


def make_residual_result(all_supported=True):
    return {
        "status": "supported" if all_supported else "unsupported",
        "per_world_family": {"fam1": _residual_family(all_supported)},
    }


def _observer_family(primary_supported=True, positive_control_valid=True):
    return {
        "status": "supported" if primary_supported else "unsupported",
        "positive_control_result": {"conclusion": "positive_control_valid" if positive_control_valid else "positive_control_failed"},
        "observers": [{"observer_id": "full_state_positive_control", "conclusion": "positive_control_valid" if positive_control_valid else "positive_control_failed"}],
    }


def make_observer_result(primary_supported=True, positive_control_valid=True):
    return {"status": "supported" if primary_supported else "unsupported", "per_world_family": {"fam1": _observer_family(primary_supported, positive_control_valid)}}


def make_resource_result(status="supported"):
    return {"status": status, "per_world_family": {"fam1": {"status": status}}}


def make_expansion_result(supported=True):
    return {"status": "supported" if supported else "unsupported", "per_world_family": {"fam1": {"status": "supported" if supported else "unsupported"}}}


def make_execution_matrix_result(all_matched=True):
    return {
        "status": "supported" if all_matched else "unsupported",
        "per_world_family": {"fam1": {"all_predictions_matched": all_matched}},
    }


def _evaluate(boundary=None, residual=None, observer=None, resource=None, expansion=None, execution_matrix=None):
    return I.evaluate(
        boundary if boundary is not None else make_boundary_result(True),
        residual if residual is not None else make_residual_result(True),
        observer if observer is not None else make_observer_result(True, True),
        resource if resource is not None else make_resource_result("supported"),
        expansion if expansion is not None else make_expansion_result(True),
        execution_matrix if execution_matrix is not None else make_execution_matrix_result(True),
    )


class TestGenuineInformationLossSplit(unittest.TestCase):
    def test_supported_when_all_families_non_injective(self):
        r = I.genuine_information_loss_result(make_residual_result(True))
        self.assertEqual(r["status"], "supported")

    def test_unsupported_when_any_family_injective(self):
        residual_result = make_residual_result(True)
        residual_result["per_world_family"]["fam1"]["support_checks"]["non_injective_loss_demonstrated"] = False
        r = I.genuine_information_loss_result(residual_result)
        self.assertEqual(r["status"], "unsupported")

    def test_invalid_when_no_families(self):
        r = I.genuine_information_loss_result({"per_world_family": {}})
        self.assertEqual(r["status"], "invalid")


class TestResourceEligibility(unittest.TestCase):
    def test_ineligible_when_semantic_continuity_not_supported(self):
        r = I.resource_advantage_result(make_resource_result("supported"), semantic_continuity_status="unsupported")
        self.assertEqual(r["status"], "ineligible")
        self.assertEqual(r["internal_status"], "supported")

    def test_eligible_and_passthrough_when_semantic_continuity_supported(self):
        r = I.resource_advantage_result(make_resource_result("supported"), semantic_continuity_status="supported")
        self.assertEqual(r["status"], "supported")


class TestExpansionAndFaultControlGates(unittest.TestCase):
    """Protocol v1.3.0-dev4, corrections 3-4: these two gates must read
    their own real component result, not a same-named-but-different
    surrogate (the exact defect the v1.2.0-dev3 post-run audit found)."""

    def test_unsupported_expansion_fails_its_own_gate(self):
        result = _evaluate(expansion=make_expansion_result(False))
        self.assertEqual(result["status"], "not_supported")
        self.assertIn("expansion_and_contraction", result["failed_gates"])

    def test_unsupported_fault_control_fails_its_own_gate(self):
        result = _evaluate(execution_matrix=make_execution_matrix_result(False))
        self.assertEqual(result["status"], "not_supported")
        self.assertIn("fault_control_validity", result["failed_gates"])


class TestIntegratedGating(unittest.TestCase):
    def test_all_gates_pass_yields_supported(self):
        result = _evaluate()
        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["failed_gates"], [])
        self.assertEqual(result["ineligible_gates"], [])
        self.assertEqual(result["invalid_gates"], [])
        self.assertEqual(len(result["gates"]), 16)

    def test_failed_observer_primary_makes_it_not_supported(self):
        result = _evaluate(observer=make_observer_result(primary_supported=False, positive_control_valid=True))
        self.assertEqual(result["status"], "not_supported")
        self.assertIn("primary_observer_indistinguishability", result["failed_gates"])

    def test_failed_positive_control_is_invalid_not_failed(self):
        result = _evaluate(observer=make_observer_result(primary_supported=True, positive_control_valid=False))
        self.assertEqual(result["status"], "not_supported")
        self.assertIn("full_state_observer_boundary_detection", result["invalid_gates"])

    def test_unsupported_semantic_continuity_makes_resource_ineligible_not_failed(self):
        result = _evaluate(residual=make_residual_result(False))
        self.assertEqual(result["status"], "not_supported")
        self.assertIn("fidelity_matched_resource_advantage", result["ineligible_gates"])

    def test_never_reports_supported_with_nonempty_gate_lists(self):
        # Paranoid invariant check across a grid of inputs.
        for b in (True, False):
            for rr in (True, False):
                for o in (True, False):
                    result = _evaluate(
                        boundary=make_boundary_result(b), residual=make_residual_result(rr),
                        observer=make_observer_result(o, True),
                        resource=make_resource_result("supported" if rr else "unsupported"),
                    )
                    if result["status"] == "supported":
                        self.assertEqual(result["failed_gates"], [])
                        self.assertEqual(result["ineligible_gates"], [])
                        self.assertEqual(result["invalid_gates"], [])

    def test_component_summaries_present_for_dashboard_reuse(self):
        result = _evaluate()
        self.assertEqual(
            set(result["component_summaries"].keys()),
            {
                "genuine_information_loss", "semantic_continuity_core", "semantic_continuity_delayed",
                "clean_leakage_audit", "ledger_causality", "fault_control_validity",
                "expansion_and_contraction", "resource_advantage",
            },
        )

    def test_not_supported_explicitly_disclaims_disproof(self):
        result = _evaluate(
            boundary=make_boundary_result(False), residual=make_residual_result(False),
            observer=make_observer_result(False, True), resource=make_resource_result("unsupported"),
        )
        interpretation = result["interpretation"].lower()
        self.assertIn("not_supported", result["status"])
        # "not supported" must never be silently upgraded to "disproved";
        # the interpretation must say so explicitly.
        self.assertIn("not evidence that it is disproved", interpretation)


if __name__ == "__main__":
    unittest.main()
