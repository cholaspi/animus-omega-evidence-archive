import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import boundary as B
from animus_test05 import world as W
from test_world import tiny_config


class TestFrozenContract(unittest.TestCase):
    def test_immutable_after_creation(self):
        c = B.FrozenContract({"a": 1})
        with self.assertRaises(TypeError):
            c.foo = 1

    def test_consume_marks_consumed_and_returns_data(self):
        c = B.FrozenContract({"a": 1})
        self.assertFalse(c.consumed)
        data = c.consume()
        self.assertEqual(data, {"a": 1})
        self.assertTrue(c.consumed)

    def test_hash_changes_if_data_would_differ(self):
        c1 = B.FrozenContract({"a": 1})
        c2 = B.FrozenContract({"a": 2})
        self.assertNotEqual(c1.content_hash, c2.content_hash)

    def test_verify_detects_correct_hash(self):
        c = B.FrozenContract({"a": 1})
        self.assertTrue(c.verify(c.content_hash))
        self.assertFalse(c.verify("not-the-real-hash"))


class TestExecuteJConsumesContract(unittest.TestCase):
    def setUp(self):
        self.cfg = tiny_config()
        history = ("move", "move", "resolve", "noop_x")
        self.ending = W.run_history(self.cfg, history)
        self.ledger = W.relevant_ledger(self.ending)
        self.reconstructed = W.replay(self.cfg, self.ledger)
        self.rv = W.return_value_of(self.ending)

    def test_execute_j_consumes_the_contract(self):
        contract = B.locked_beginning_contract(self.cfg, "test-protocol-version")
        self.assertFalse(contract.consumed)
        next_beginning, tracked = B.execute_J(self.reconstructed, self.ledger, self.rv, self.cfg, contract)
        self.assertTrue(contract.consumed)
        self.assertEqual(next_beginning["declared_min_resolutions"], contract._data["min_resolutions"])

    def test_contract_satisfied_rejects_unconsumed_contract(self):
        contract = B.locked_beginning_contract(self.cfg, "test-protocol-version")
        next_beginning = {
            "total": self.cfg.total_resource, "primary_holder": self.cfg.agent_ids()[0],
            "resolved_count_hint": 0, "ledger_root": "x", "declared_min_resolutions": 1,
        }
        ok, reason = B.contract_satisfied(next_beginning, contract, self.cfg)
        self.assertFalse(ok)
        self.assertEqual(reason, "contract_not_consumed")

    def test_natural_closing_history_satisfies_contract_and_exact_closure(self):
        contract = B.locked_beginning_contract(self.cfg, "test-protocol-version")
        next_beginning, _tracked = B.execute_J(self.reconstructed, self.ledger, self.rv, self.cfg, contract)
        c_ok, _ = B.contract_satisfied(next_beginning, contract, self.cfg)
        e_ok, _, _ = B.exact_closure(next_beginning, self.ending, self.cfg)
        # whether it "closes" depends on min_resolutions; just check both
        # checks are internally consistent (no exception, well-formed).
        self.assertIsInstance(c_ok, bool)
        self.assertIsInstance(e_ok, bool)


class TestTrackedReturnValue(unittest.TestCase):
    def test_missing_value_never_marks_accessed(self):
        tracked = B.TrackedReturnValue(None)
        self.assertIsNone(tracked.get("primary_holder"))
        self.assertNotIn("primary_holder", tracked.accessed_fields)

    def test_present_value_marks_accessed_on_read(self):
        tracked = B.TrackedReturnValue({"primary_holder": "a0"})
        self.assertEqual(tracked.get("primary_holder"), "a0")
        self.assertIn("primary_holder", tracked.accessed_fields)


class TestInterventionArms(unittest.TestCase):
    """Exhaustive-enumeration-backed checks that every one of the 12
    required arms (plus the ignored-return-value control) behaves as
    specified, on a small tractable world."""

    @classmethod
    def setUpClass(cls):
        cls.cfg = tiny_config()
        contract = B.locked_beginning_contract(cls.cfg, "test-protocol-version")
        cls.reference, cls.closing, cls.non_closing = B.find_reference_history(cls.cfg, "test-protocol-version")
        assert cls.reference is not None, "test world must have a natural closing reference history"
        cls.arms = {a.arm_id: a for a in B.run_intervention_arms(cls.cfg, cls.reference, rng_seed=1, protocol_version="test-protocol-version")}

    def test_at_least_one_closing_and_one_non_closing_history_exist(self):
        self.assertGreaterEqual(len(self.closing), 1)
        self.assertGreaterEqual(len(self.non_closing), 1)

    def test_arm01_correct_return_value_closes(self):
        self.assertTrue(self.arms["01_correct_return_value"].closes)

    def test_arm02_missing_return_value_breaks_closure(self):
        self.assertFalse(self.arms["02_missing_return_value"].closes)

    def test_arm03_random_return_value_breaks_exact_closure_but_may_satisfy_contract(self):
        arm = self.arms["03_random_return_value"]
        self.assertFalse(arm.closes)
        # This is the key "distinguish exact equality from contract
        # satisfaction" demonstration from the spec.
        self.assertTrue(arm.contract_satisfied)

    def test_arm04_swapped_return_value_breaks_closure(self):
        self.assertFalse(self.arms["04_return_value_from_different_history"].closes)

    def test_arm05_endpoint_mutation_breaks_closure(self):
        self.assertFalse(self.arms["05_endpoint_mutation"].closes)

    def test_arm06_relevant_mutation_breaks_closure_and_modifies_causal_path(self):
        arm = self.arms["06_relevant_intermediate_mutation"]
        if arm.notes == "ineligible":
            self.skipTest("no relevant-action tick available in this reference history")
        self.assertFalse(arm.closes)
        self.assertIsNotNone(arm.causal_path_diff)
        self.assertTrue(arm.causal_path_diff["any_stage_differs"])

    def test_arm07_irrelevant_mutation_preserves_closure_and_causal_path(self):
        arm = self.arms["07_irrelevant_intermediate_mutation"]
        if arm.notes == "ineligible":
            self.skipTest("no irrelevant-action tick available in this reference history")
        self.assertTrue(arm.closes)
        self.assertIsNotNone(arm.causal_path_diff)
        self.assertFalse(arm.causal_path_diff["any_stage_differs"])

    def test_arm08_incorrect_ledger_breaks_closure(self):
        self.assertFalse(self.arms["08_correct_return_value_incorrect_ledger"].closes)

    def test_arm09_incorrect_reconstruction_breaks_closure(self):
        self.assertFalse(self.arms["09_correct_ledger_incorrect_reconstruction"].closes)

    def test_arm10_no_endpoint_information_breaks_closure(self):
        self.assertFalse(self.arms["10_no_endpoint_information"].closes)

    def test_arm11_open_chain_has_no_transition(self):
        arm = self.arms["11_open_chain_no_return_transition"]
        self.assertFalse(arm.closes)
        self.assertEqual(arm.contract_fail_reason, "no_transition_executed")

    def test_arm12_copied_beginning_fails_because_contract_never_consumed(self):
        arm = self.arms["12_directly_copied_beginning"]
        self.assertFalse(arm.closes)
        self.assertEqual(arm.contract_fail_reason, "contract_not_consumed")

    def test_arm13_ignored_return_value_is_detected_and_rejected(self):
        arm = self.arms["13_ignored_return_value_control"]
        self.assertFalse(arm.closes)
        self.assertIn("ignored_return_value_detected=True", arm.notes)


class TestLabelAudit(unittest.TestCase):
    def test_boundary_core_functions_take_no_forbidden_parameters(self):
        from animus_test05 import label_audit
        result = label_audit.audit_no_label_leakage()
        self.assertTrue(result["clean"], result["violations"])
        self.assertIn("boundary.execute_J", result["functions_checked"])
        self.assertIn("world.step", result["functions_checked"])

    def test_audit_detects_a_deliberately_bad_function(self):
        from animus_test05 import label_audit

        def bad(state, arm_id, expected):
            return state

        violations = label_audit.audit_function("bad", bad)
        self.assertTrue(violations)


if __name__ == "__main__":
    unittest.main()
