"""Deterministic stand-in for model proposals.

The adapter is intentionally not authoritative: it returns proposals only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .protocol import AGENT_IDS, MODEL_VERSIONS
from .serialization import canonical_json

@dataclass(frozen=True)
class Proposal:
    agent_id: str
    tick: int
    action: str
    model_version: str
    request_digest: str
    token_count: int = 8

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id, "tick": self.tick,
            "action": self.action, "model_version": self.model_version,
            "request_digest": self.request_digest, "token_count": self.token_count,
        }

class AdapterInterface:
    """Small stable interface implemented by replaceable adapter instances."""

    version = ""

    def __init__(self, seed: int):
        self.seed = seed
        self.calls = 0
        self.tokens = 0

    def propose(self, agent_id: str, tick: int, observation: dict[str, Any]) -> Proposal:
        if agent_id not in AGENT_IDS:
            raise ValueError("unknown agent")
        request = {"seed": self.seed, "agent": agent_id, "tick": tick,
                   "version": self.version, "observation": observation}
        digest = hashlib.sha256(canonical_json(request).encode()).hexdigest()
        value = int(digest[:8], 16) % 5
        action = ("move" if value in (0, 1) else "gather" if value == 2 else "hold")
        proposal = Proposal(agent_id, tick, action, self.version, digest)
        self.calls += 1
        self.tokens += proposal.token_count
        return proposal

class DeterministicAdapterV1(AdapterInterface):
    version = MODEL_VERSIONS[0]

class DeterministicAdapterV2(AdapterInterface):
    version = MODEL_VERSIONS[1]

def make_adapter(seed: int, version: str) -> AdapterInterface:
    """Construct a fresh adapter instance behind the stable interface."""
    classes = {
        MODEL_VERSIONS[0]: DeterministicAdapterV1,
        MODEL_VERSIONS[1]: DeterministicAdapterV2,
    }
    try:
        return classes[version](seed)
    except KeyError as exc:
        raise ValueError(f"unknown adapter version: {version}") from exc

class DeterministicModelAdapter(AdapterInterface):
    """Compatibility adapter for callers that need one fixed version."""

    def __init__(self, seed: int, swap: bool = True):
        super().__init__(seed)
        self.version = MODEL_VERSIONS[1] if not swap else MODEL_VERSIONS[0]