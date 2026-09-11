import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import world as W


def tiny_config(**overrides) -> W.WorldConfig:
    base = dict(
        world_id="test-tiny",
        num_agents=3,
        num_obligations=2,
        history_length=4,
        total_resource=3,
        reconstruction_algorithm="faithful_replay",
        ledger_capacity=64,
    )
    base.update(overrides)
    return W.WorldConfig(**base)


class TestDeterminism(unittest.TestCase):
    def test_run_history_is_deterministic_across_calls(self):
        cfg = tiny_config()
        history = ("move", "resolve", "noop_x", "move")
        r1 = W.run_history(cfg, history)
        r2 = W.run_history(cfg, history)
        self.assertEqual(r1, r2)

    def test_initial_state_seed_is_process_stable(self):
        # Guards against the earlier bug of using builtin hash() (which is
        # randomized per-process via PYTHONHASHSEED) for internal_seed.
        cfg = tiny_config()
        s1 = W.initial_state(cfg)
        s2 = W.initial_state(cfg)
        for aid in cfg.agent_ids():
            self.assertEqual(s1["agents"][aid]["internal_seed"], s2["agents"][aid]["internal_seed"])

    def test_step_does_not_mutate_input_state(self):
        cfg = tiny_config()
        s0 = W.initial_state(cfg)
        import copy
        s0_copy = copy.deepcopy(s0)
        W.step(s0, "move", cfg)
        self.assertEqual(s0, s0_copy)


class TestExhaustiveEnumeration(unittest.TestCase):
    def test_enumeration_count_matches_alphabet_power_length(self):
        cfg = tiny_config(history_length=3)
        histories = W.enumerate_histories(cfg)
        self.assertEqual(len(histories), len(W.ACTIONS) ** 3)
        self.assertEqual(len(set(histories)), len(histories))  # no duplicates


class TestReplayFidelity(unittest.TestCase):
    def test_faithful_replay_matches_every_history_publicly(self):
        cfg = tiny_config()
        mismatches = 0
        for h in W.enumerate_histories(cfg):
            end = W.run_history(cfg, h)
            ledger = W.relevant_ledger(end)
            reconstructed = W.replay(cfg, ledger)
            if W.first_mismatch(W.public_fields(end), W.public_fields(reconstructed)) is not None:
                mismatches += 1
        self.assertEqual(mismatches, 0, "faithful_replay must reproduce public fields for every history")

    def test_lossy_replay_can_diverge_on_resolve_histories(self):
        cfg = tiny_config(reconstruction_algorithm="lossy_replay")
        found_divergence = False
        for h in W.enumerate_histories(cfg):
            end = W.run_history(cfg, h)
            ledger = W.relevant_ledger(end)
            reconstructed = W.replay(cfg, ledger)
            if W.first_mismatch(W.public_fields(end), W.public_fields(reconstructed)) is not None:
                found_divergence = True
                break
        self.assertTrue(found_divergence, "lossy_replay must diverge for at least one history containing a real resolve")

    def test_relevant_ledger_excludes_irrelevant_actions(self):
        cfg = tiny_config()
        end = W.run_history(cfg, ("noop_x", "noop_y", "move", "resolve"))
        ledger = W.relevant_ledger(end)
        actions = {e["action"] for e in ledger}
        self.assertTrue(actions.issubset(set(W.RELEVANT_ACTIONS)))

    def test_replay_with_recomputed_effects_matches_true_execution(self):
        cfg = tiny_config()
        end = W.run_history(cfg, ("move", "move", "resolve", "move"))
        ledger = W.relevant_ledger(end)
        recomputed = W.replay_with_recomputed_effects(cfg, ledger)
        for stored, fresh in zip(ledger, recomputed):
            self.assertEqual(stored["effect"], fresh["effect"])
            self.assertEqual(stored["action"], fresh["action"])


class TestFirstMismatch(unittest.TestCase):
    def test_identical_structures_report_no_mismatch(self):
        a = {"x": 1, "y": [1, 2, {"z": 3}]}
        b = {"x": 1, "y": [1, 2, {"z": 3}]}
        self.assertIsNone(W.first_mismatch(a, b))

    def test_reports_first_differing_path(self):
        a = {"x": 1, "y": [1, 2, {"z": 3}]}
        b = {"x": 1, "y": [1, 2, {"z": 4}]}
        path, av, bv = W.first_mismatch(a, b)
        self.assertEqual(path, "y[2].z")
        self.assertEqual((av, bv), (3, 4))


if __name__ == "__main__":
    unittest.main()
