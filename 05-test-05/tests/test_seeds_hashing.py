import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import hashing
from animus_test05 import seeds


class TestHashing(unittest.TestCase):
    def test_hash_obj_is_deterministic(self):
        obj = {"b": 2, "a": 1, "nested": [3, 2, 1]}
        self.assertEqual(hashing.hash_obj(obj), hashing.hash_obj(dict(obj)))

    def test_hash_obj_is_order_independent_for_dict_keys(self):
        a = {"x": 1, "y": 2}
        b = {"y": 2, "x": 1}
        self.assertEqual(hashing.hash_obj(a), hashing.hash_obj(b))

    def test_hash_obj_changes_on_content_change(self):
        self.assertNotEqual(hashing.hash_obj({"x": 1}), hashing.hash_obj({"x": 2}))

    def test_write_json_hash_matches_hash_obj(self, tmp_path=Path("/tmp/animus_test05_hash_test.json")):
        obj = {"x": [1, 2, 3]}
        digest = hashing.write_json(tmp_path, obj)
        self.assertEqual(digest, hashing.hash_obj(obj))
        tmp_path.unlink(missing_ok=True)

    def test_verify_json_hash(self, tmp_path=Path("/tmp/animus_test05_hash_test2.json")):
        obj = {"y": 42}
        digest = hashing.write_json(tmp_path, obj)
        self.assertTrue(hashing.verify_json_hash(tmp_path, digest))
        self.assertFalse(hashing.verify_json_hash(tmp_path, "wrong"))
        tmp_path.unlink(missing_ok=True)


class TestSeeds(unittest.TestCase):
    def test_development_and_reserved_bands_are_disjoint(self):
        dev = seeds.all_development_seeds()
        res = seeds.all_reserved_seeds()
        self.assertEqual(dev & res, set())

    def test_v1_and_v2_bands_are_disjoint(self):
        v1 = set()
        for band in seeds.PROTOCOL_V1_DEVELOPMENT_SEED_BANDS.values():
            v1.update(band)
        v2 = set()
        for band in seeds.PROTOCOL_V2_DEVELOPMENT_SEED_BANDS.values():
            v2.update(band)
        self.assertEqual(v1 & v2, set())

    def test_require_development_seeds_accepts_valid_seeds(self):
        seeds.require_development_seeds([57000, 57100, 57300])  # no exception

    def test_require_development_seeds_rejects_reserved_seed(self):
        with self.assertRaises(seeds.ReservedSeedError):
            seeds.require_development_seeds([58000])

    def test_require_development_seeds_rejects_unregistered_seed(self):
        with self.assertRaises(seeds.ReservedSeedError):
            seeds.require_development_seeds([1])

    def test_confirm_reserved_execution_refuses_without_frozen_protocol(self):
        with self.assertRaises(seeds.ReservedSeedError):
            seeds.confirm_reserved_execution(
                [58000],
                "I_UNDERSTAND_THIS_BURNS_A_RESERVED_SEED",
                Path("/nonexistent/frozen_protocol.json"),
            )

    def test_confirm_reserved_execution_refuses_with_wrong_token(self):
        with self.assertRaises(seeds.ReservedSeedError):
            seeds.confirm_reserved_execution([58000], "wrong-token", Path("/nonexistent"))

    def test_confirm_reserved_execution_refuses_even_with_a_real_file_since_hash_is_unpinned(self, tmp_path=Path("/tmp/animus_test05_fake_protocol.md")):
        tmp_path.write_text("not the real frozen confirmatory protocol")
        try:
            with self.assertRaises(seeds.ReservedSeedError):
                seeds.confirm_reserved_execution(
                    [58000], "I_UNDERSTAND_THIS_BURNS_A_RESERVED_SEED", tmp_path,
                )
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
