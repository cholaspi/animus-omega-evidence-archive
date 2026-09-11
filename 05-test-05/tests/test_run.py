import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import run as run_module


class TestSourceAndProtocolHashing(unittest.TestCase):
    def test_source_hash_is_deterministic(self):
        a = run_module.compute_source_hash()
        b = run_module.compute_source_hash()
        self.assertEqual(a["source_hash"], b["source_hash"])

    def test_source_hash_covers_every_module(self):
        record = run_module.compute_source_hash()
        for name in ("boundary.py", "residual.py", "observer.py", "resource.py", "integrated.py", "world.py", "worlds.py", "seeds.py", "hashing.py", "label_audit.py", "validator.py", "run.py"):
            rel = f"src/animus_test05/{name}"
            self.assertIn(rel, record["files"], f"{rel} missing from source_hash file list")

    def test_protocol_hash_is_deterministic_and_matches_current_document(self):
        from animus_test05 import hashing
        pilot_path, current_path, digest = run_module.compute_protocol_hash()
        full_path = run_module._project_root() / current_path
        self.assertEqual(digest, hashing.hash_file(full_path))
        self.assertNotEqual(pilot_path, current_path)

    def test_protocol_version_matches_requested_scheme(self):
        self.assertEqual(run_module.PROTOCOL_VERSION, "1.2.0-dev3")

    def test_output_path_is_under_repo_root_evidence_test05(self):
        out = run_module._repo_root() / "evidence" / "test05" / "revised_development_v1.2.0-dev3"
        self.assertTrue(str(out).endswith("evidence/test05/revised_development_v1.2.0-dev3"))
        self.assertFalse(str(out).startswith(str(run_module._project_root())))


if __name__ == "__main__":
    unittest.main()
