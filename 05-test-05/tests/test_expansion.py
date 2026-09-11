import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import expansion as E
from test_world import tiny_config


class TestRSeries(unittest.TestCase):
    def test_r_series_length_matches_history_plus_one(self):
        cfg = tiny_config(history_length=4)
        series = E.r_series(cfg, ("move", "resolve", "noop_x", "move"))
        self.assertEqual(len(series), 5)

    def test_genesis_r_equals_one_plus_obligations(self):
        cfg = tiny_config(num_obligations=2, history_length=4)
        series = E.r_series(cfg, ("noop_x", "noop_x", "noop_x", "noop_x"))
        self.assertEqual(series[0], 1 + 2)


class TestPatternSearch(unittest.TestCase):
    def test_finds_pattern_when_present(self):
        series = [2, 5, 2]  # R(0)=2, R(1)=5>=4, R(2)=2<=3
        pattern = E.find_expansion_contraction_pattern(series)
        self.assertIsNotNone(pattern)
        self.assertEqual((pattern["t0"], pattern["t1"], pattern["t2"]), (0, 1, 2))

    def test_no_pattern_when_absent(self):
        series = [2, 3, 2]  # 3 < 2*2=4, never expands enough
        self.assertIsNone(E.find_expansion_contraction_pattern(series))

    def test_zero_genesis_r_is_skipped(self):
        series = [0, 5, 0]
        self.assertIsNone(E.find_expansion_contraction_pattern(series))


class TestTheoreticalCeiling(unittest.TestCase):
    def test_ceiling_matches_hand_computation(self):
        cfg = tiny_config(num_agents=3, num_obligations=2)
        ceiling = E.theoretical_max_r(cfg)
        self.assertEqual(ceiling["r_at_genesis"], 3)
        self.assertEqual(ceiling["provable_ceiling"], 5)
        self.assertEqual(ceiling["required_for_expansion"], 6)
        self.assertFalse(ceiling["expansion_mathematically_possible"])

    def test_evaluate_world_family_explains_impossibility(self):
        cfg = tiny_config(num_agents=3, num_obligations=2, history_length=4)
        result = E.evaluate_world_family(cfg)
        self.assertEqual(result["status"], "unsupported")
        self.assertIn("provable ceiling", result["reason"])
        self.assertEqual(result["histories_checked"], 4 ** 4)


if __name__ == "__main__":
    unittest.main()
