import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import integrated as I


def _boundary_family(closes_all=True, has_relevant=True, has_irrelevant=True):
    arms = [
        {"arm_id": "01_correct_return_value", "closes": True},
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
    ]
    return {
        "status": "supported" if closes_all else "unsupported",
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


class TestIntegratedGating(unittest.TestCase):
    def test_all_gates_pass_yields_supported(self):
        result = I.evaluate(
            make_boundary_result(True), make_residual_result(True),
            make_observer_result(True, True), make_resource_result("supported"),
        )
        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["failed_gates"], [])
        self.assertEqual(result["ineligible_gates"], [])
        self.assertEqual(result["invalid_gates"], [])

    def test_failed_observer_primary_makes_it_not_supported(self):
        result = I.evaluate(
            make_boundary_result(True), make_residual_result(True),
            make_observer_result(primary_supported=False, positive_control_valid=True),
            make_resource_result("supported"),
        )
        self.assertEqual(result["status"], "not_supported")
        self.assertIn("no_qualifying_distinction_for_primary_bounded_observer", result["failed_gates"])

    def test_failed_positive_control_is_invalid_not_failed(self):
        result = I.evaluate(
            make_boundary_result(True), make_residual_result(True),
            make_observer_result(primary_supported=True, positive_control_valid=False),
            make_resource_result("supported"),
        )
        self.assertEqual(result["status"], "not_supported")
        self.assertIn("positive_control_observer_detects_boundary", result["invalid_gates"])

    def test_unsupported_semantic_continuity_makes_resource_ineligible_not_failed(self):
        result = I.evaluate(
            make_boundary_result(True), make_residual_result(False),
            make_observer_result(True, True), make_resource_result("supported"),
        )
        self.assertEqual(result["status"], "not_supported")
        self.assertIn("fidelity_matched_resource_advantage", result["ineligible_gates"])

    def test_never_reports_supported_with_nonempty_gate_lists(self):
        # Paranoid invariant check across a grid of inputs.
        for b in (True, False):
            for rr in (True, False):
                for o in (True, False):
                    result = I.evaluate(
                        make_boundary_result(b), make_residual_result(rr),
                        make_observer_result(o, True), make_resource_result("supported" if rr else "unsupported"),
                    )
                    if result["status"] == "supported":
                        self.assertEqual(result["failed_gates"], [])
                        self.assertEqual(result["ineligible_gates"], [])
                        self.assertEqual(result["invalid_gates"], [])

    def test_component_summaries_present_for_dashboard_reuse(self):
        result = I.evaluate(
            make_boundary_result(True), make_residual_result(True),
            make_observer_result(True, True), make_resource_result("supported"),
        )
        self.assertEqual(
            set(result["component_summaries"].keys()),
            {"genuine_information_loss", "semantic_continuity", "ledger_causality", "resource_advantage"},
        )

    def test_not_supported_explicitly_disclaims_disproof(self):
        result = I.evaluate(
            make_boundary_result(False), make_residual_result(False),
            make_observer_result(False, True), make_resource_result("unsupported"),
        )
        interpretation = result["interpretation"].lower()
        self.assertIn("not_supported", result["status"])
        # "not supported" must never be silently upgraded to "disproved";
        # the interpretation must say so explicitly.
        self.assertIn("not evidence that it is disproved", interpretation)


if __name__ == "__main__":
    unittest.main()
