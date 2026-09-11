import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import resource as RS
from animus_test05 import world as W
from test_world import tiny_config


class TestResourceBreakdownCompleteness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg = tiny_config()
        histories = W.enumerate_histories(cfg)
        history = next(h for h in histories if W.resolved_count(W.run_history(cfg, h)) >= 1)
        cls.canonical, cls.timing = RS.evaluate_world_family(cfg, history, seed=1)

    def test_every_arm_declares_every_resource_category(self):
        for aid, arm in self.canonical["arms"].items():
            with self.subTest(arm=aid):
                self.assertEqual(set(arm["resource_breakdown"].keys()), set(RS.RESOURCE_CATEGORIES))

    def test_timing_is_kept_out_of_canonical_result(self):
        self.assertNotIn("noncanonical_timing", self.canonical)
        self.assertNotIn("wall_clock_seconds", str(self.canonical["arms"]))

    def test_ten_arms_plus_focal_are_present(self):
        expected = {
            "complete_checkpointing", "snapshot_plus_event_log", "always_expanded_lossless",
            "open_chain_execution", "general_purpose_lossless_compression",
            "general_purpose_lossy_compression_matched_fidelity", "lossy_execution_without_ledger",
            "no_loss_cyclic_execution", "scripted_cyclic_replay", "state_machine_replication",
            "proposed_architecture_residual_plus_ledger",
        }
        self.assertEqual(set(self.canonical["arms"].keys()), expected)


class TestFidelityEligibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg = tiny_config()
        histories = W.enumerate_histories(cfg)
        history = next(h for h in histories if W.resolved_count(W.run_history(cfg, h)) >= 1)
        cls.canonical, _timing = RS.evaluate_world_family(cfg, history, seed=1)

    def test_open_chain_and_no_ledger_arms_are_ineligible(self):
        self.assertFalse(self.canonical["arms"]["open_chain_execution"]["semantic_eligible"])
        self.assertFalse(self.canonical["arms"]["lossy_execution_without_ledger"]["semantic_eligible"])

    def test_proposed_architecture_is_eligible(self):
        self.assertTrue(self.canonical["arms"]["proposed_architecture_residual_plus_ledger"]["semantic_eligible"])

    def test_ineligible_arms_excluded_from_pareto_comparison(self):
        eligible = set(self.canonical["pareto"]["eligible_arms"])
        self.assertNotIn("open_chain_execution", eligible)
        self.assertNotIn("lossy_execution_without_ledger", eligible)

    def test_pareto_status_is_a_declared_status(self):
        self.assertIn(self.canonical["status"], ("supported", "unsupported", "ineligible", "invalid"))


class TestByteAccounting(unittest.TestCase):
    def test_bytes_of_uses_real_canonical_json_length(self):
        obj = {"a": 1, "b": [1, 2, 3]}
        from animus_test05.hashing import canonical_json
        self.assertEqual(RS._bytes_of(obj), len(canonical_json(obj).encode("utf-8")))

    def test_scripted_replay_has_smallest_peak_bytes_of_all_arms(self):
        cfg = tiny_config()
        histories = W.enumerate_histories(cfg)
        history = next(h for h in histories if W.resolved_count(W.run_history(cfg, h)) >= 1)
        canonical, _timing = RS.evaluate_world_family(cfg, history, seed=1)
        script_bytes = canonical["arms"]["scripted_cyclic_replay"]["peak_canonical_bytes"]
        for aid, arm in canonical["arms"].items():
            if aid == "scripted_cyclic_replay":
                continue
            self.assertLessEqual(script_bytes, arm["peak_canonical_bytes"])


if __name__ == "__main__":
    unittest.main()
