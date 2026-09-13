import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from persistent_closure_benchmark import (
    AGENT_IDS, ARMS, canonical_json, fresh_process_replay, run_episode,
)
from persistent_closure_benchmark.ledger import Ledger
from persistent_closure_benchmark.benchmark import public_inputs, replay_public_inputs
from persistent_closure_benchmark.serialization import (
    deserialize_result, result_checksum, serialize_result,
)


class PersistentClosureBenchmarkTests(unittest.TestCase):
    def test_six_stable_agents_and_three_arms(self):
        result = run_episode(51000)
        self.assertEqual(tuple(result["agent_ids"]), AGENT_IDS)
        self.assertEqual(tuple(a["arm"] for a in result["arms"]), ARMS)
        self.assertTrue(result["paired_information_equal"])

    def test_determinism_and_checksum(self):
        first = run_episode(51000, "semantic_state")
        second = run_episode(51000, "semantic_state")
        self.assertEqual(first, second)
        self.assertEqual(first["result_checksum"], result_checksum(first))
        self.assertEqual(serialize_result(first), serialize_result(second))

    def test_hash_chained_ledger_tampering(self):
        result = run_episode(51000)
        ledger = copy.deepcopy(result["authoritative_ledger"])
        ledger[-1]["payload"] = {"forged": True}
        self.assertFalse(Ledger(tuple(ledger)).verify()["ok"])

    def test_model_swap_continuity(self):
        result = run_episode(51000)
        schedule = result["arms"][0]["model_schedule"]
        self.assertEqual(schedule["versions"][0], "deterministic-adapter-v1")
        self.assertEqual(schedule["versions"][-1], "deterministic-adapter-v2")
        self.assertTrue(schedule["swap_occurred"])
        no_swap = run_episode(51000, swap=False)
        self.assertFalse(no_swap["arms"][0]["model_schedule"]["swap_occurred"])

    def test_valid_specificity_and_diagnostic_separation(self):
        result = run_episode(51000, "valid")
        self.assertTrue(result["arms"][2]["closure_pass"])
        self.assertFalse(any(a["detected"] for a in result["arms"]))
        self.assertEqual(result["paired_failure_detection"], "no_failure")
        invalid = run_episode(51000, "semantic_state")
        closure = invalid["arms"][2]
        self.assertFalse(closure["closure_pass"])
        self.assertTrue(closure["detected"])
        self.assertEqual(invalid["oracle"]["closure_relevant"], True)

    def test_nonclosure_and_closure_failure_categories(self):
        nonclosure = run_episode(51000, "identity_change")
        self.assertTrue(nonclosure["arms"][0]["detected"])
        self.assertTrue(nonclosure["arms"][2]["detected"])
        self.assertEqual(nonclosure["paired_failure_detection"], "both_detect")
        closure_only = run_episode(51000, "observer_output")
        # Observer consistency is an ordinary check in every arm; the fixture
        # must not manufacture a closure-only advantage.
        self.assertTrue(closure_only["arms"][0]["detected"])
        self.assertTrue(closure_only["arms"][2]["detected"])
        self.assertEqual(closure_only["paired_failure_detection"], "both_detect")

    def test_return_package_reconstructs_and_rejects_unauthorized_fields(self):
        valid = run_episode(51000)
        closure = valid["arms"][2]
        package = closure["return_package"]
        self.assertTrue(closure["return_validation"]["ok"])
        self.assertTrue(package["immediate_round_trip"])
        self.assertEqual(closure["reconstructed_beginning"],
                         valid["initial_state"])
        unauthorized = run_episode(51000, "unauthorized_fields")
        self.assertIn("return_schema", unauthorized["arms"][2]["failure_reasons"])

    def test_enhanced_arm_performs_real_replay_checks(self):
        result = run_episode(51000, "semantic_state")
        enhanced = result["arms"][1]
        self.assertGreater(enhanced["metrics"]["replay_steps"], 0)
        self.assertIn("semantic_digest_stale", enhanced["failure_reasons"])
        self.assertEqual(enhanced["validator_version"],
                         result["arms"][2]["validator_version"])

    def test_seed_allowlist_and_self_contained_tamper_rejection(self):
        from persistent_closure_benchmark.protocol import validate_seed
        with self.assertRaises(ValueError):
            validate_seed(52000)
        with self.assertRaises(ValueError):
            validate_seed(1)
        inputs = public_inputs(51000)
        tampered = copy.deepcopy(inputs)
        tampered["initial_state"]["positions"][0] += 1
        with self.assertRaises(ValueError):
            replay_public_inputs(tampered)

    def test_ledger_ownership_and_duplicate_proposals(self):
        duplicate = run_episode(51000, "duplicate_proposals")
        self.assertTrue(all(a["detected"] for a in duplicate["arms"]))
        ledger = run_episode(51000, "ledger_tamper")
        self.assertTrue(all("ledger_tamper" in a["failure_reasons"]
                            for a in ledger["arms"]))

    def test_public_serialization_and_fresh_process(self):
        inputs = public_inputs(51000, "observer_output")
        local = replay_public_inputs(inputs)
        fresh = fresh_process_replay(inputs)
        self.assertEqual(local, fresh)
        with self.assertRaises(ValueError):
            replay_public_inputs({**inputs, "horizon": 999})

    def test_runner_writes_explicit_safe_output(self):
        from persistent_closure_benchmark.runner import main
        with tempfile.TemporaryDirectory() as directory:
            output = main(["--output-dir", directory])
            self.assertEqual(output, Path(directory))
            self.assertTrue((output / "results.json").exists())
            self.assertTrue((output / "DEV_NON_CONFIRMATORY").exists())
            self.assertTrue((output / "SHA256SUMS").exists())
            result = json.loads((output / "results.json").read_text())
            self.assertEqual(result["status"], "development_non_confirmatory")
            recorded = {
                line.split("  ", 1)[1]: line.split("  ", 1)[0]
                for line in (output / "SHA256SUMS").read_text().splitlines()
            }
            for filename in ("DEV_NON_CONFIRMATORY", "results.json"):
                actual = hashlib.sha256((output / filename).read_bytes()).hexdigest()
                self.assertEqual(recorded[filename], actual)


if __name__ == "__main__":
    unittest.main()