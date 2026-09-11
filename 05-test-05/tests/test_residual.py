import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import residual as R
from animus_test05 import world as W
from animus_test05.worlds import WorldFamily
from test_world import tiny_config


def tiny_family(**overrides) -> WorldFamily:
    cfg = tiny_config(**overrides)
    return WorldFamily(
        family_id=cfg.world_id,
        description="test family",
        standard_config=cfg,
        observer_config=cfg,
        loss_profile="standard",
    )


class TestFieldClassification(unittest.TestCase):
    def test_classification_has_all_four_categories(self):
        classes = set(R.declared_field_classification().values())
        self.assertEqual(
            classes,
            {"copied", "reconstructed", "derived_through_later_execution", "intentionally_discarded"},
        )


class TestGenuineLoss(unittest.TestCase):
    def test_non_injective_with_at_least_one_real_collision_example(self):
        cfg = tiny_config()
        analysis = R.collision_analysis(cfg)
        self.assertTrue(analysis["non_injective"])
        self.assertGreaterEqual(analysis["max_preimage_size"], 2)
        example = analysis["example_collision"]
        self.assertIsNotNone(example)
        self.assertNotEqual(example["microstate_a"]["microstate_hash"], example["microstate_b"]["microstate_hash"])

    def test_microstate_count_equals_history_count_for_this_world(self):
        # In this construction every history yields a distinct full
        # microstate (private nuisance churn differs per noop choice).
        cfg = tiny_config()
        analysis = R.collision_analysis(cfg)
        self.assertEqual(analysis["admissible_microstate_count"], len(W.enumerate_histories(cfg)))

    def test_residual_space_is_strictly_smaller_than_microstate_space(self):
        cfg = tiny_config()
        analysis = R.collision_analysis(cfg)
        self.assertLess(analysis["distinct_residual_count"], analysis["admissible_microstate_count"])


class TestCoreAndDelayedProbes(unittest.TestCase):
    def test_core_and_delayed_probe_ids_are_disjoint(self):
        core_ids = {p[0] for p in R.CORE_PROBE_SPECS}
        delayed_ids = {p[0] for p in R.DELAYED_PROBE_SPECS}
        self.assertEqual(core_ids & delayed_ids, set())

    def test_nine_core_categories_present(self):
        core_ids = {p[0] for p in R.CORE_PROBE_SPECS}
        required = {
            "identity_continuity", "obligation_ownership", "relationship_permissions",
            "causal_ordering", "provenance", "deadline_behavior",
            "resource_allocation_commitments", "permitted_future_actions",
            "observer_visible_consequences",
        }
        self.assertTrue(required.issubset(core_ids))

    def test_five_delayed_categories_present(self):
        delayed_ids = {p[0] for p in R.DELAYED_PROBE_SPECS}
        required = {
            "new_counterfactual_actions", "unseen_obligation_queries", "new_resource_disputes",
            "identity_substitution_challenges", "causal_prerequisite_challenges",
        }
        self.assertEqual(delayed_ids, required)

    def test_delayed_generator_output_depends_on_residual_content(self):
        cfg = tiny_config()
        history_a = ("move", "move", "resolve", "noop_x")
        history_b = ("noop_x", "noop_y", "noop_x", "noop_y")
        end_a = W.run_history(cfg, history_a)
        end_b = W.run_history(cfg, history_b)
        residual_a = R.build_residual(end_a, cfg)
        residual_b = R.build_residual(end_b, cfg)
        inst_a = R.generate_delayed_probe_instances(residual_a, R.build_ledger(end_a), cfg)
        inst_b = R.generate_delayed_probe_instances(residual_b, R.build_ledger(end_b), cfg)
        # At least one instance parameter must differ between two very
        # different histories -- otherwise the generator isn't actually
        # reading the committed residual.
        self.assertNotEqual(inst_a, inst_b)

    def test_dispute_pair_prefers_nonzero_balance_difference(self):
        cfg = tiny_config(total_resource=3)
        history = ("move", "move", "resolve", "noop_x")
        end = W.run_history(cfg, history)
        residual = R.build_residual(end, cfg)
        ledger = R.build_ledger(end)
        instances = R.generate_delayed_probe_instances(residual, ledger, cfg)
        a, b = instances["dispute_pair"]
        balances = residual["agents"]
        # If any pair has a nonzero difference, the chosen pair must too.
        agents = cfg.agent_ids()
        any_nonzero = any(
            balances[x]["balance"] != balances[y]["balance"]
            for i, x in enumerate(agents) for y in agents[i + 1:]
        )
        if any_nonzero:
            self.assertNotEqual(balances[a]["balance"], balances[b]["balance"])


class TestLeakageAudit(unittest.TestCase):
    def test_clean_residual_and_ledger_pass(self):
        cfg = tiny_config()
        end = W.run_history(cfg, ("move", "resolve", "noop_x", "move"))
        residual = R.build_residual(end, cfg)
        ledger = R.build_ledger(end)
        audit = R.leakage_audit(residual, ledger)
        self.assertTrue(audit["clean"])

    def test_banned_key_is_detected(self):
        cfg = tiny_config()
        end = W.run_history(cfg, ("move", "resolve", "noop_x", "move"))
        residual = R.build_residual(end, cfg)
        residual = dict(residual)
        residual["expected_answer"] = "a0"  # simulate a leaked meta-key
        ledger = R.build_ledger(end)
        audit = R.leakage_audit(residual, ledger)
        self.assertFalse(audit["clean"])
        self.assertTrue(any("expected_answer" in v for v in audit["violations"]))


class TestControlsFailAppropriately(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = tiny_family(world_id="test-residual-controls")
        cls.result = R.evaluate_world_family(cls.wf, rng_seed=1)

    def test_main_residual_passes_all_probes(self):
        self.assertTrue(self.result["main_probe_grade"]["all_pass"])

    def test_positive_controls_pass(self):
        self.assertTrue(self.result["controls"]["complete_checkpoint"]["all_pass"])
        self.assertTrue(self.result["controls"]["lossless_event_log"]["all_pass"])

    def test_negative_controls_all_fail_at_least_one_probe(self):
        negative_ids = [
            "lossy_residual_without_ledger", "shuffled_identities", "deleted_obligation",
            "changed_causal_dependency", "contradictory_ledger_entry", "missing_provenance",
            "stale_ledger_entry", "duplicate_event", "random_reconstructed_payload",
        ]
        for cid in negative_ids:
            with self.subTest(control=cid):
                self.assertFalse(self.result["controls"][cid]["all_pass"], f"{cid} unexpectedly passed all probes")

    def test_generic_lossless_compression_control_passes(self):
        self.assertTrue(self.result["controls"]["general_purpose_compressed_baseline"]["all_pass"])

    def test_status_is_supported(self):
        self.assertEqual(self.result["status"], "supported")


if __name__ == "__main__":
    unittest.main()
