"""Frozen development protocol values.

These values are deliberately modest so development fixtures are quick.  The
reserved range is never used by the development runner.
"""

from __future__ import annotations

AGENT_IDS = ("agent-0", "agent-1", "agent-2", "agent-3", "agent-4", "agent-5")
ARMS = ("standard_forward_only", "enhanced_forward_matched", "closure_aware")
DEVELOPMENT_SEEDS = (51000, 51001, 51002)
DEVELOPMENT_SEED_ALLOWLIST = frozenset(DEVELOPMENT_SEEDS)
RESERVED_SEEDS = tuple(range(52000, 52020))
REPLAY_HORIZON = 8
MIDPOINT_TICK = REPLAY_HORIZON // 2
WORLD_SIZE = 12
MODEL_VERSIONS = ("deterministic-adapter-v1", "deterministic-adapter-v2")
SCHEMA_VERSION = "persistent-closure-v1"
VALIDATOR_VERSION = "invariant-validator-v1"
SCORING_VERSION = "paired-outcome-v1"
DIAGNOSTIC_BUDGET = 64
FAULTS = (
    "valid",
    "identity_change",
    "obligation_drop",
    "missing_provenance",
    "ledger_tamper",
    "semantic_state",
    "observer_output",
)

def validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if seed not in DEVELOPMENT_SEED_ALLOWLIST:
        if seed in RESERVED_SEEDS:
            raise ValueError(f"reserved development seed: {seed}")
        raise ValueError(f"seed is not in the development allow-list: {seed}")