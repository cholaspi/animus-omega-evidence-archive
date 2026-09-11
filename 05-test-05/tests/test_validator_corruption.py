"""Corruption tests for validator.py (protocol v2, update I).

Generates one real baseline evidence set with the actual development
pipeline (this is the expensive part -- run once for the whole module),
then for each named rejection condition, copies the baseline, corrupts
exactly one thing, and asserts the validator's report is invalid with a
matching violation. Uses ``components=`` to skip expensive unrelated
recomputation (05C's exact observer enumeration in particular) so each
individual corruption test stays fast.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import run as run_module
from animus_test05 import validator

_BASELINE_DIR: Path = None


def setUpModule():
    global _BASELINE_DIR
    _BASELINE_DIR = Path(tempfile.mkdtemp(prefix="animus_test05_validator_baseline_"))
    run_module.run(_BASELINE_DIR)


def tearDownModule():
    if _BASELINE_DIR is not None:
        shutil.rmtree(_BASELINE_DIR, ignore_errors=True)


def _copy_baseline(name: str) -> Path:
    dst = Path(tempfile.mkdtemp(prefix=f"animus_test05_corrupt_{name}_"))
    shutil.rmtree(dst)
    shutil.copytree(_BASELINE_DIR, dst)
    return dst


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


class TestBaselineIsValid(unittest.TestCase):
    def test_uncorrupted_baseline_passes_full_validation(self):
        report = validator.validate(_BASELINE_DIR)
        self.assertTrue(report.valid, report.to_dict()["violations"])


class TestStructuralCorruption(unittest.TestCase):
    def test_missing_evidence_file_is_rejected(self):
        d = _copy_baseline("missing_evidence")
        (d / "evidence" / "boundary" / "friendly.json").unlink()
        report = validator.validate(d, components=("boundary",))
        self.assertFalse(report.valid)
        self.assertTrue(any("missing" in v.detail for v in report.violations))

    def test_modified_evidence_hash_is_rejected(self):
        d = _copy_baseline("modified_hash")
        p = d / "evidence" / "residual" / "friendly.json"
        obj = _load(p)
        obj["status"] = "supported" if obj["status"] != "supported" else "unsupported"
        _save(p, obj)
        report = validator.validate(d, components=("residual",))
        self.assertFalse(report.valid)
        self.assertTrue(any(v.check == "evidence_manifest_files_exist_and_hash" for v in report.violations))

    def test_forbidden_reserved_seed_is_rejected(self):
        d = _copy_baseline("reserved_seed")
        p = d / "results" / "test05_development_result.json"
        obj = _load(p)
        obj["development_seeds"].append(58000)
        _save(p, obj)
        report = validator.validate(d, components=())
        self.assertFalse(report.valid)
        self.assertTrue(any(v.check == "no_reserved_seed_used" for v in report.violations))

    def test_unregistered_seed_is_rejected(self):
        d = _copy_baseline("unregistered_seed")
        p = d / "results" / "test05_development_result.json"
        obj = _load(p)
        obj["development_seeds"].append(1)
        _save(p, obj)
        report = validator.validate(d, components=())
        self.assertFalse(report.valid)
        self.assertTrue(any(v.check == "no_reserved_seed_used" for v in report.violations))


class TestBoundaryCorruption(unittest.TestCase):
    def test_post_hoc_modified_beginning_contract_is_rejected(self):
        d = _copy_baseline("modified_contract")
        p = d / "evidence" / "boundary" / "friendly.json"
        obj = _load(p)
        obj["beginning_commitment"]["data"]["min_resolutions"] = 999  # tamper after the hash was computed
        _save(p, obj)
        report = validator.validate(d, components=("boundary",))
        self.assertFalse(report.valid)
        self.assertTrue(any("content_hash" in v.detail or "modified" in v.detail for v in report.violations))

    def test_contract_marked_consumed_in_evidence_record_is_rejected(self):
        d = _copy_baseline("consumed_evidence_contract")
        p = d / "evidence" / "boundary" / "friendly.json"
        obj = _load(p)
        obj["beginning_commitment"]["consumed"] = True
        _save(p, obj)
        report = validator.validate(d, components=("boundary",))
        self.assertFalse(report.valid)

    def test_ignored_return_value_silently_marked_fine_is_rejected(self):
        d = _copy_baseline("ignored_rv")
        p = d / "evidence" / "boundary" / "friendly.json"
        obj = _load(p)
        for arm in obj["arms"]:
            if arm["arm_id"] == "13_ignored_return_value_control":
                arm["closes"] = True
                arm["notes"] = "ignored_return_value_detected=False"
        _save(p, obj)
        report = validator.validate(d, components=("boundary",))
        self.assertFalse(report.valid)
        self.assertTrue(any("ignored_return_value" in v.check for v in report.violations))

    def test_fake_relevant_intervention_with_unchanged_causal_path_is_rejected(self):
        d = _copy_baseline("fake_intervention")
        p = d / "evidence" / "boundary" / "friendly.json"
        obj = _load(p)
        for arm in obj["arms"]:
            if arm["arm_id"] == "06_relevant_intermediate_mutation" and arm.get("causal_path_diff"):
                arm["causal_path_diff"]["any_stage_differs"] = False  # claim relevance but show no real change
        _save(p, obj)
        report = validator.validate(d, components=("boundary",))
        self.assertFalse(report.valid)
        self.assertTrue(any("arm06" in v.check for v in report.violations))

    def test_shortcut_arm_falsely_marked_as_consuming_contract_is_rejected(self):
        d = _copy_baseline("fake_shortcut_pass")
        p = d / "evidence" / "boundary" / "friendly.json"
        obj = _load(p)
        for arm in obj["arms"]:
            if arm["arm_id"] == "12_directly_copied_beginning":
                arm["contract_fail_reason"] = None
                arm["contract_satisfied"] = True
        _save(p, obj)
        report = validator.validate(d, components=("boundary",))
        self.assertFalse(report.valid)


class TestResidualLeakageAndCounts(unittest.TestCase):
    def test_leaked_answer_key_in_residual_is_rejected(self):
        d = _copy_baseline("leakage")
        p = d / "evidence" / "residual" / "friendly.json"
        obj = _load(p)
        obj["residual_snapshot"]["expected_answer"] = "a0"  # inject a banned meta-key
        obj["leakage_audit"] = {"violations": [], "clean": True}  # falsely claim clean
        _save(p, obj)
        report = validator.validate(d, components=("residual",))
        self.assertFalse(report.valid)
        self.assertTrue(any(v.check == "residual[friendly]_leakage_audit_reverified" for v in report.violations))

    def test_incorrect_collision_count_is_rejected(self):
        d = _copy_baseline("collision_counts")
        p = d / "evidence" / "residual" / "friendly.json"
        obj = _load(p)
        obj["collision_analysis"]["max_preimage_size"] = 999999
        _save(p, obj)
        report = validator.validate(d, components=("residual",))
        self.assertFalse(report.valid)
        self.assertTrue(any(v.check == "residual[friendly]_collision_counts_match" for v in report.violations))

    def test_non_injective_falsely_claimed_true_is_rejected(self):
        d = _copy_baseline("non_injective_lie")
        p = d / "evidence" / "residual" / "friendly.json"
        obj = _load(p)
        obj["collision_analysis"]["non_injective"] = not obj["collision_analysis"]["non_injective"]
        _save(p, obj)
        report = validator.validate(d, components=("residual",))
        self.assertFalse(report.valid)


class TestResourceEligibilityAndBuffers(unittest.TestCase):
    def test_ineligible_arm_admitted_into_pareto_comparison_is_rejected(self):
        d = _copy_baseline("fidelity_ineligible_admitted")
        p = d / "evidence" / "resource" / "friendly.json"
        obj = _load(p)
        obj["pareto"]["eligible_arms"].append("open_chain_execution")  # known ineligible arm
        _save(p, obj)
        report = validator.validate(d, components=("resource",))
        self.assertFalse(report.valid)
        self.assertTrue(any(v.check == "resource[friendly]_eligibility_consistent" for v in report.violations))

    def test_omitted_resource_category_is_rejected(self):
        d = _copy_baseline("omitted_category")
        p = d / "evidence" / "resource" / "friendly.json"
        obj = _load(p)
        first_arm = next(iter(obj["arms"]))
        del obj["arms"][first_arm]["resource_breakdown"]["lookup_table_bytes"]
        _save(p, obj)
        report = validator.validate(d, components=("resource",))
        self.assertFalse(report.valid)
        self.assertTrue(any(v.check == "resource[friendly]_no_omitted_categories" for v in report.violations))

    def test_incorrect_peak_bytes_is_rejected(self):
        d = _copy_baseline("wrong_peak_bytes")
        p = d / "evidence" / "resource" / "friendly.json"
        obj = _load(p)
        first_arm = next(iter(obj["arms"]))
        obj["arms"][first_arm]["peak_canonical_bytes"] = 123456789
        _save(p, obj)
        report = validator.validate(d, components=("resource",))
        self.assertFalse(report.valid)


class TestIntegratedCorruption(unittest.TestCase):
    def test_integrated_support_with_failed_gate_is_rejected(self):
        d = _copy_baseline("fake_integrated_support")
        p = d / "results" / "test05_development_result.json"
        obj = _load(p)
        obj["integrated_result"]["status"] = "supported"
        # leave failed_gates non-empty (from the real not_supported run) if any
        _save(p, obj)
        report = validator.validate(d, components=())
        self.assertFalse(report.valid)

    def test_integrated_evidence_disagrees_with_recompute_is_rejected(self):
        d = _copy_baseline("integrated_evidence_tamper")
        p = d / "evidence" / "integrated.json"
        obj = _load(p)
        obj["status"] = "supported"
        obj["failed_gates"] = []
        obj["ineligible_gates"] = []
        obj["invalid_gates"] = []
        _save(p, obj)
        report = validator.validate(d, components=("integrated",))
        self.assertFalse(report.valid)


class TestObserverCorruption(unittest.TestCase):
    def test_falsely_valid_positive_control_is_rejected(self):
        d = _copy_baseline("fake_positive_control")
        p = d / "evidence" / "observer" / "friendly.json"
        obj = _load(p)
        obj["positive_control_result"]["conclusion"] = "positive_control_valid"
        obj["positive_control_result"]["total_variation_distance"] = 0.0  # inconsistent with "valid"
        _save(p, obj)
        report = validator.validate(d, components=("observer",))
        self.assertFalse(report.valid)


if __name__ == "__main__":
    unittest.main()
