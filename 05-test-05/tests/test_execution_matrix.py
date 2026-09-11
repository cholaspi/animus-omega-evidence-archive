import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import execution_matrix as EM
from animus_test05.worlds import WorldFamily
from test_world import tiny_config


def adversarial_family(**overrides):
    cfg = tiny_config(world_id="exec-matrix-test", **overrides)
    return WorldFamily(
        family_id="exec-matrix-test", description="test", standard_config=cfg,
        observer_config=cfg, loss_profile="standard", adversarial=("identity_substitution",),
    )


def friendly_family(**overrides):
    cfg = tiny_config(world_id="exec-matrix-friendly-test", **overrides)
    return WorldFamily(
        family_id="exec-matrix-friendly-test", description="test", standard_config=cfg,
        observer_config=cfg, loss_profile="standard",
    )


class TestMutationCount(unittest.TestCase):
    def test_exactly_nine_mutations_declared(self):
        self.assertEqual(len(EM.MUTATION_IDS), 9)
        self.assertEqual(len(EM.FAULT_PREDICTIONS), 9)


class TestAdversarialSeedExecution(unittest.TestCase):
    def test_ten_executions_per_seed(self):
        wf = adversarial_family()
        records = EM.run_adversarial_seed(wf.config, seed=14001, family=wf.family_id)
        self.assertEqual(len(records), 10)
        mutation_ids = {r.mutation_id for r in records}
        self.assertEqual(mutation_ids, {"unfaulted"} | set(EM.MUTATION_IDS))

    def test_unfaulted_execution_passes_all_probes(self):
        wf = adversarial_family()
        records = EM.run_adversarial_seed(wf.config, seed=14001, family=wf.family_id)
        unfaulted = next(r for r in records if r.mutation_id == "unfaulted")
        self.assertTrue(unfaulted.observed_failure["all_pass"])

    def test_before_after_hash_differ_when_mutation_applies(self):
        wf = adversarial_family()
        records = EM.run_adversarial_seed(wf.config, seed=14001, family=wf.family_id)
        identity_sub = next(r for r in records if r.mutation_id == "identity_substitution")
        self.assertNotEqual(identity_sub.before_hash, identity_sub.after_hash)
        self.assertTrue(len(identity_sub.mutated_fields) > 0)

    def test_deterministic_given_same_seed(self):
        wf = adversarial_family()
        r1 = EM.run_adversarial_seed(wf.config, seed=14001, family=wf.family_id)
        r2 = EM.run_adversarial_seed(wf.config, seed=14001, family=wf.family_id)
        self.assertEqual([r.after_hash for r in r1], [r.after_hash for r in r2])

    def test_most_fault_mutations_flip_all_pass_to_false(self):
        wf = adversarial_family()
        records = EM.run_adversarial_seed(wf.config, seed=14001, family=wf.family_id)
        non_reorder = [r for r in records if r.mutation_id not in ("unfaulted", "causal_reorder")]
        self.assertTrue(all(not r.observed_failure["all_pass"] for r in non_reorder))


class TestFriendlySeedExecution(unittest.TestCase):
    def test_one_unfaulted_execution_per_seed(self):
        wf = friendly_family()
        record = EM.run_friendly_seed(wf.config, seed=13001, family=wf.family_id)
        self.assertEqual(record.mutation_id, "unfaulted")
        self.assertTrue(record.observed_failure["all_pass"])


class TestFamilyMatrix(unittest.TestCase):
    def test_adversarial_family_runs_full_matrix(self):
        wf = adversarial_family()
        result = EM.run_family_matrix(wf, [14001, 14002])
        self.assertEqual(result["execution_count"], 20)
        self.assertTrue(result["is_adversarial"])

    def test_friendly_family_runs_baseline_only(self):
        wf = friendly_family()
        result = EM.run_family_matrix(wf, [13001, 13002, 13003])
        self.assertEqual(result["execution_count"], 3)
        self.assertFalse(result["is_adversarial"])


if __name__ == "__main__":
    unittest.main()
