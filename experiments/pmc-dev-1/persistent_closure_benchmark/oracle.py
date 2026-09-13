"""Independent post-execution oracle labels.

The oracle consumes sealed scenario records and arm outcomes only after
execution.  Its labels are never passed into proposal, invariant, or closure
validators.
"""

from __future__ import annotations

from typing import Any

from .faults import validate_scenario

_EXPECTED = {
    "dev-valid": ("valid", "none"),
    "dev-identity": ("invalid", "both"),
    "dev-obligation": ("invalid", "both"),
    "dev-provenance": ("invalid", "both"),
    "dev-ledger": ("invalid", "both"),
    "dev-semantic": ("invalid", "both"),
    "dev-observer": ("invalid", "both"),
    "dev-unauthorized": ("invalid", "B-only"),
    "dev-duplicate": ("invalid", "both"),
    "dev-stale-digest": ("invalid", "both"),
    "dev-unauthorized-proposal": ("invalid", "both"),
}

CAPABILITY_CATEGORIES = ("valid", "A-only", "B-only", "both", "neither")

def label_scenario(record: dict[str, Any]) -> dict[str, Any]:
    validate_scenario(record)
    validity, capability = _EXPECTED[record["scenario_id"]]
    return {
        "scenario_id": record["scenario_id"], "validity": validity,
        "expected_capability": capability,
        "capability_categories": list(CAPABILITY_CATEGORIES),
        "closure_relevant": record["scenario_id"] in {
            "dev-semantic", "dev-observer", "dev-unauthorized",
        },
        "truth_generated_after_execution": True,
    }

def join_blinded_outcomes(arms: list[dict[str, Any]],
                          record: dict[str, Any]) -> dict[str, Any]:
    """Only this post-execution join may inspect oracle metadata."""
    label = label_scenario(record)
    detected = {a["arm"]: bool(a["detected"]) for a in arms}
    if label["validity"] == "valid":
        category = "no_failure"
    elif detected.get("standard_forward_only") and detected.get("closure_aware"):
        category = "both_detect"
    elif detected.get("closure_aware"):
        category = "only_closure_detects"
    elif detected.get("standard_forward_only"):
        category = "only_forward_detects"
    else:
        category = "neither_detects"
    return {**label, "observed_category": category}