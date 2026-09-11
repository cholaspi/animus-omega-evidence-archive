import shutil
import sys
import tempfile
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

    def test_protocol_doc_path_is_deterministic_and_hashable(self):
        from animus_test05 import hashing
        path = run_module._protocol_doc_path()
        self.assertTrue(path.exists())
        h1 = hashing.hash_file(path)
        h2 = hashing.hash_file(path)
        self.assertEqual(h1, h2)

    def test_protocol_version_matches_requested_scheme(self):
        self.assertEqual(run_module.PROTOCOL_VERSION, "1.2.0-dev3")

    def test_output_path_is_under_repo_root_evidence_test05(self):
        out = run_module._repo_root() / "evidence" / "test05" / "revised_development_v1.2.0-dev3"
        self.assertTrue(str(out).endswith("evidence/test05/revised_development_v1.2.0-dev3"))
        self.assertFalse(str(out).startswith(str(run_module._project_root())))


class TestFreezeExecuteOrdering(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="animus_test05_run_test_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_execute_refuses_before_freeze(self):
        with self.assertRaises(RuntimeError):
            run_module.execute(self.tmp)

    def test_freeze_writes_no_execution_evidence(self):
        run_module.freeze(self.tmp)
        self.assertFalse((self.tmp / "runs").exists() and any((self.tmp / "runs").iterdir()))
        self.assertFalse((self.tmp / "results").exists() and any((self.tmp / "results").iterdir()))
        self.assertTrue((self.tmp / "hashes" / "companion_file_manifest.json").exists())

    def test_freeze_refuses_if_runs_already_populated(self):
        (self.tmp / "runs").mkdir(parents=True)
        (self.tmp / "runs" / "marker.json").write_text("{}")
        with self.assertRaises(RuntimeError):
            run_module.freeze(self.tmp)

    def test_freeze_checklist_ready_after_freeze(self):
        run_module.freeze(self.tmp)
        checklist = run_module.freeze_checklist(self.tmp)
        self.assertTrue(checklist["ready_pending_test_results"])
        for key, value in checklist["items"].items():
            if key in ("unit_tests_pass", "validator_corruption_tests_pass"):
                continue
            self.assertTrue(value, f"{key} was not true after freeze()")


if __name__ == "__main__":
    unittest.main()
