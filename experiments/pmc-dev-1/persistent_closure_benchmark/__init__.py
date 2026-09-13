"""Development-only paired benchmark for persistent multi-agent closure.

The package is intentionally independent from ``narrative_closure`` (Test 05).
It provides a small, deterministic software harness; it is not a scientific
result and does not access external model providers.
"""

from .protocol import (
    AGENT_IDS,
    ARMS,
    DEVELOPMENT_SEEDS,
    DEVELOPMENT_SEED_ALLOWLIST,
    MIDPOINT_TICK,
    REPLAY_HORIZON,
    RESERVED_SEEDS,
)
from .benchmark import (
    run_arm, run_episode,
    run_benchmark,
    replay_public_inputs,
    fresh_process_replay,
    validate_episode,
)
from .serialization import canonical_json, result_checksum, serialize_result

__all__ = [
    "AGENT_IDS", "ARMS", "DEVELOPMENT_SEEDS", "DEVELOPMENT_SEED_ALLOWLIST",
    "MIDPOINT_TICK",
    "REPLAY_HORIZON", "RESERVED_SEEDS", "run_arm", "run_episode",
    "run_benchmark", "replay_public_inputs", "fresh_process_replay",
    "validate_episode", "canonical_json", "result_checksum",
    "serialize_result",
]