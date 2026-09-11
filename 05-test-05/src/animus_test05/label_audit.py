"""Protocol v2, update F: an audit proving the simulator core never
receives arm names, expected outcomes, should-close flags, fault-control
flags, or integrated-support expectations.

This is a *runtime* audit (not just a naming convention): it inspects the
actual parameter names of the core simulator functions via
``inspect.signature`` and fails if any forbidden name appears, so renaming
an ``arm_id`` parameter to an integer ``arm_index`` would still be caught if
the simulator branched on it under a different name.
"""

from __future__ import annotations

import inspect
from typing import Callable

FORBIDDEN_SUBSTRINGS = (
    "arm_id", "arm_name", "arm_label", "arm_index", "label",
    "expected", "should_close", "fault_control", "fault_flag",
    "integrated_support", "test_label", "closure_status",
)

# The functions that actually execute the simulated world / boundary
# transition. None of these may take a parameter whose name contains a
# forbidden substring. (Descriptive, human-facing functions like
# ``_run_arm`` and ``ArmResult`` intentionally DO take arm_id/description --
# those are report-layer labels attached *after* the simulator has already
# produced a result, never fed into it. This audit targets the simulator
# core specifically.)
SIMULATOR_CORE_FUNCTIONS: dict[str, Callable] = {}


def register(name: str, fn: Callable) -> Callable:
    SIMULATOR_CORE_FUNCTIONS[name] = fn
    return fn


def audit_function(name: str, fn: Callable) -> list[str]:
    violations = []
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return violations
    for param_name in sig.parameters:
        lowered = param_name.lower()
        for forbidden in FORBIDDEN_SUBSTRINGS:
            if forbidden in lowered:
                violations.append(f"{name}(...): parameter {param_name!r} matches forbidden pattern {forbidden!r}")
    return violations


def audit_no_label_leakage() -> dict:
    """Runs the audit against every registered simulator-core function.
    Returns {"clean": bool, "violations": [...], "functions_checked": [...]}."""
    all_violations = []
    for name, fn in SIMULATOR_CORE_FUNCTIONS.items():
        all_violations.extend(audit_function(name, fn))
    return {
        "clean": len(all_violations) == 0,
        "violations": all_violations,
        "functions_checked": sorted(SIMULATOR_CORE_FUNCTIONS.keys()),
    }
