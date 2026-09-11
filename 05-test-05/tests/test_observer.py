import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import observer as O
from animus_test05 import world as W
from animus_test05.worlds import WorldFamily
from test_world import tiny_config


def observer_family(num_agents=2, history_length=5, num_obligations=1, total_resource=2) -> WorldFamily:
    std = tiny_config(
        world_id="obs-test", num_agents=num_agents, num_obligations=num_obligations,
        history_length=4, total_resource=total_resource,
    )
    obs = tiny_config(
        world_id="obs-test-observer", num_agents=num_agents, num_obligations=num_obligations,
        history_length=history_length, total_resource=total_resource,
    )
    return WorldFamily(family_id="obs-test", description="test", standard_config=std, observer_config=obs, loss_profile="standard")


class TestPhaseMatching(unittest.TestCase):
    def test_boundary_and_interior_are_phase_matched(self):
        cfg = tiny_config(num_agents=2, history_length=5)
        b, i = O.boundary_and_interior_starts(cfg)
        self.assertGreaterEqual(i, 0)
        self.assertLess(i, b)
        self.assertEqual(b % cfg.num_agents, i % cfg.num_agents)

    def test_no_interior_window_reports_negative_one(self):
        cfg = tiny_config(num_agents=5, history_length=2)  # too short for any interior window
        b, i = O.boundary_and_interior_starts(cfg)
        self.assertEqual(i, -1)


class TestExactDistributions(unittest.TestCase):
    def test_distribution_sums_to_one(self):
        cfg = tiny_config(num_agents=2, history_length=5)
        b, i = O.boundary_and_interior_starts(cfg)
        p, n = O.exact_distribution(cfg, b, O._percept_full_state)
        self.assertAlmostEqual(sum(p.values()), 1.0, places=9)
        self.assertEqual(n, len(W.enumerate_histories(cfg)))

    def test_tv_distance_zero_for_identical_distributions(self):
        p = {("a",): 0.5, ("b",): 0.5}
        self.assertEqual(O.total_variation_distance(p, p), 0.0)

    def test_tv_distance_one_for_disjoint_supports(self):
        p = {("a",): 1.0}
        q = {("b",): 1.0}
        self.assertEqual(O.total_variation_distance(p, q), 1.0)

    def test_bayes_accuracy_is_half_at_zero_tv(self):
        self.assertAlmostEqual(O.bayes_optimal_accuracy(0.0), 0.5)

    def test_bayes_accuracy_is_one_at_full_tv(self):
        self.assertAlmostEqual(O.bayes_optimal_accuracy(1.0), 1.0)

    def test_mutual_information_zero_for_identical_distributions(self):
        p = {("a",): 0.3, ("b",): 0.7}
        self.assertAlmostEqual(O.mutual_information(p, p), 0.0, places=9)


class TestPrimaryObserverFrozen(unittest.TestCase):
    def test_primary_observer_spec_hash_is_stable(self):
        import hashlib
        from animus_test05.hashing import hash_obj

        self.assertEqual(O._PRIMARY_OBSERVER_SPEC_HASH, hash_obj(O.PRIMARY_OBSERVER_SPEC))

    def test_primary_observer_excludes_forbidden_information(self):
        excluded = O.PRIMARY_OBSERVER_SPEC["excluded_information"]
        for forbidden in ("global_clock", "full_state", "unrestricted_full_ledger_access"):
            self.assertIn(forbidden, excluded)

    def test_primary_observer_percept_never_includes_tick(self):
        cfg = tiny_config(num_agents=2, history_length=5)
        state = W.initial_state(cfg)
        states = [W.step(state, "move", cfg)]
        obs = O._percept_primary_bounded_observer(states, cfg)
        # tick numbers are ints that would appear as the sole element only
        # in the full-state percept, which always leads with (tick, ...).
        self.assertNotIsInstance(obs[0][0], int)


class TestLadderRoles(unittest.TestCase):
    def test_exactly_one_primary_and_one_positive_control(self):
        roles = [role for (_id, _desc, _fn, role) in O.OBSERVER_LADDER]
        self.assertEqual(roles.count(O.ROLE_PRIMARY), 1)
        self.assertEqual(roles.count(O.ROLE_POSITIVE_CONTROL), 1)
        self.assertGreaterEqual(roles.count(O.ROLE_SENSITIVITY), 1)


class TestEvaluateWorldFamily(unittest.TestCase):
    def test_positive_control_detects_boundary(self):
        wf = observer_family()
        result = O.evaluate_world_family(wf)
        self.assertEqual(result["positive_control_result"]["conclusion"], "positive_control_valid")

    def test_status_never_supported_when_positive_control_fails(self):
        # Construct a pathological config where the observer window can't
        # even be phase-matched -- must report inconclusive, not "supported".
        wf = observer_family(history_length=2)
        result = O.evaluate_world_family(wf)
        self.assertIn(result["status"], ("inconclusive", "invalid"))


if __name__ == "__main__":
    unittest.main()
