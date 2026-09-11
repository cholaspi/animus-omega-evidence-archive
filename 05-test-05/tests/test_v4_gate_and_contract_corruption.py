"""Protocol v1.3.0-dev4, correction 8: corruption tests that remove each
integrated gate individually, flip each gate individually, remove each
mandatory beginning-contract field individually, and prove that integrated
support is impossible when any required gate fails.

Reuses the same real freeze()+execute() baseline pattern as
test_validator_corruption.py (generated once for the whole module).
"""

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from animus_test05 import hashing
from animus_test05 import run as run_module
from animus_test05 import validator
from animus_test05.validator import _GATE_ORDER, _REQUIRED_CONTRACT_FIELD_TYPES

_BASELINE_DIR: Path = None


def setUpModule():
    global _BASELINE_DIR
    _BASELINE_DIR = Path(tempfile.mkdtemp(prefix="animus_test05_v4_gate_baseline_"))
    run_module.freeze(_BASELINE_DIR)
    run_module.execute(_BASELINE_DIR)


def tearDownModule():
    if _BASELINE_DIR is not None:
        shutil.rmtree(_BASELINE_DIR, ignore_errors=True)


def _copy_baseline(name: str) -> Path:
    dst = Path(tempfile.mkdtemp(prefix=f"animus_test05_v4_corrupt_{name}_"))
    shutil.rmtree(dst)
    shutil.copytree(_BASELINE_DIR, dst)
    return dst


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


class TestBaselineHas16Gates(unittest.TestCase):
    def test_exactly_16_gates_present(self):
        gates = _load(_BASELINE_DIR / "runs" / "integrated_gates.json")["gates"]
        self.assertEqual(len(gates), 16)
        self.assertEqual({g["gate"] for g in gates}, set(_GATE_ORDER))

    def test_all_18_contract_fields_present_in_every_family(self):
        for path in sorted((_BASELINE_DIR / "runs" / "boundary").glob("*.json")):
            data = _load(path)["beginning_commitment"]["data"]
            for field_name in _REQUIRED_CONTRACT_FIELD_TYPES:
                self.assertIn(field_name, data, f"{path.name} missing {field_name}")


class TestPerGateRemoval(unittest.TestCase):
    """For every one of the 16 required gates, removing it from
    runs/integrated_gates.json's gates list must be rejected."""


def _make_removal_test(gate_name: str):
    def test(self):
        d = _copy_baseline(f"remove_gate_{gate_name}")
        p = d / "runs" / "integrated_gates.json"
        obj = _load(p)
        obj["gates"] = [g for g in obj["gates"] if g["gate"] != gate_name]
        _save(p, obj)
        report = validator.validate(d, components=("integrated",))
        self.assertFalse(report.valid, f"removing gate {gate_name!r} was not rejected")
        self.assertTrue(
            any(v.check == "all_16_gates_present_and_individually_match" for v in report.violations),
            f"removing gate {gate_name!r} did not trigger the gate-completeness check",
        )
        shutil.rmtree(d, ignore_errors=True)

    return test


for _gate_name in _GATE_ORDER:
    setattr(TestPerGateRemoval, f"test_removing_{_gate_name}_is_rejected", _make_removal_test(_gate_name))


class TestPerGateFlip(unittest.TestCase):
    """For every one of the 16 required gates, flipping its "ok" boolean
    (without correspondingly updating status/failed_gates) must be
    rejected."""


def _make_flip_test(gate_name: str):
    def test(self):
        d = _copy_baseline(f"flip_gate_{gate_name}")
        p = d / "runs" / "integrated_gates.json"
        obj = _load(p)
        for g in obj["gates"]:
            if g["gate"] == gate_name:
                g["ok"] = not g["ok"]
        _save(p, obj)
        report = validator.validate(d, components=("integrated",))
        self.assertFalse(report.valid, f"flipping gate {gate_name!r} was not rejected")
        self.assertTrue(
            any(v.check == "all_16_gates_present_and_individually_match" for v in report.violations),
            f"flipping gate {gate_name!r} did not trigger the per-gate match check",
        )
        shutil.rmtree(d, ignore_errors=True)

    return test


for _gate_name in _GATE_ORDER:
    setattr(TestPerGateFlip, f"test_flipping_{_gate_name}_is_rejected", _make_flip_test(_gate_name))


class TestPerContractFieldRemoval(unittest.TestCase):
    """For every one of the 18 mandatory section-8 contract fields,
    removing it from a family's beginning_commitment.data (with the
    content_hash recomputed to match, isolating the missing-field defect
    from a simple hash mismatch) must be rejected."""


def _make_field_removal_test(field_name: str):
    def test(self):
        d = _copy_baseline(f"remove_field_{field_name}")
        p = d / "runs" / "boundary" / "friendly.json"
        obj = _load(p)
        data = obj["beginning_commitment"]["data"]
        del data[field_name]
        # Recompute the hash to match the tampered (field-missing) data, so
        # the ONLY defect this fixture introduces is the missing mandatory
        # field -- not an incidental hash mismatch that a cruder check
        # would also catch for an unrelated reason.
        obj["beginning_commitment"]["content_hash"] = hashing.hash_obj(data)
        _save(p, obj)
        report = validator.validate(d, components=("boundary",))
        self.assertFalse(report.valid, f"removing contract field {field_name!r} was not rejected")
        self.assertTrue(
            any(v.check == "boundary[friendly]_contract_fields_complete_and_typed" for v in report.violations),
            f"removing contract field {field_name!r} did not trigger the contract-completeness check",
        )
        shutil.rmtree(d, ignore_errors=True)

    return test


for _field_name in _REQUIRED_CONTRACT_FIELD_TYPES:
    setattr(TestPerContractFieldRemoval, f"test_removing_{_field_name}_is_rejected", _make_field_removal_test(_field_name))


class TestIntegratedSupportImpossibleWithFailedGate(unittest.TestCase):
    """Proves mechanically that forcing runs/integrated_gates.json to
    claim full success (status=supported, every gate ok=True, empty
    failed/ineligible/invalid lists) is still rejected when the underlying
    raw evidence contains a genuine failure -- i.e. tampering only the
    aggregation layer can never manufacture "supported"."""

    def test_forcing_full_success_over_a_real_failure_is_rejected(self):
        # The real baseline genuinely fails primary_observer_indistinguishability
        # (the frozen primary observer detects the boundary in this bounded
        # model) -- confirm that premise, then try to paper over it.
        real_gates = _load(_BASELINE_DIR / "runs" / "integrated_gates.json")
        self.assertIn("primary_observer_indistinguishability", real_gates["failed_gates"])

        d = _copy_baseline("forced_full_success")
        p = d / "runs" / "integrated_gates.json"
        obj = _load(p)
        obj["status"] = "supported"
        obj["failed_gates"] = []
        obj["ineligible_gates"] = []
        obj["invalid_gates"] = []
        for g in obj["gates"]:
            g["ok"] = True
        _save(p, obj)

        report = validator.validate(d, components=("integrated",))
        self.assertFalse(report.valid, "forcing integrated_gates.json to claim full success over a real failure was not rejected")
        self.assertTrue(
            any(v.check == "all_16_gates_present_and_individually_match" for v in report.violations),
            "forced full success did not trigger the per-gate independent-recompute mismatch",
        )
        # And the authoritative determination this validate() call would
        # derive (had it not already been rejected) is computed fresh from
        # raw evidence every time -- it is never read back from the
        # tampered file, so it is unaffected by this tampering.
        determination_path = d / "results" / "integrated_determination.json"
        if determination_path.exists():
            determination = _load(determination_path)
            self.assertEqual(determination["status"], "not_supported")
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
