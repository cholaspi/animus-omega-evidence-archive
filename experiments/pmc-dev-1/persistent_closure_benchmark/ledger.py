"""Authoritative append-only hash-chained event ledger."""

from __future__ import annotations

from dataclasses import dataclass
import copy
from typing import Any

from .serialization import canonical_bytes, checksum

GENESIS_HASH = "0" * 64

def _event_body(sequence: int, tick: int, actor: str, kind: str,
                payload: Any, previous_hash: str) -> dict[str, Any]:
    return {"sequence": sequence, "tick": tick, "actor": actor, "kind": kind,
            "payload": payload, "previous_hash": previous_hash}

def make_event(sequence: int, tick: int, actor: str, kind: str,
               payload: Any, previous_hash: str) -> dict[str, Any]:
    # Canonical round-tripping prevents callers from retaining a mutable
    # reference to a payload already committed to the append-only log.
    frozen_payload = __import__("json").loads(canonical_bytes(payload))
    body = _event_body(sequence, tick, actor, kind, frozen_payload, previous_hash)
    return {**body, "hash": checksum(body)}

@dataclass(frozen=True)
class Ledger:
    events: tuple[dict[str, Any], ...] = ()

    @property
    def tip(self) -> str:
        return self.events[-1]["hash"] if self.events else GENESIS_HASH

    def append(self, tick: int, actor: str, kind: str, payload: Any) -> "Ledger":
        event = make_event(len(self.events), tick, actor, kind, payload, self.tip)
        return Ledger(tuple(copy.deepcopy(self.events)) + (event,))

    def verify(self) -> dict[str, Any]:
        previous = GENESIS_HASH
        for index, event in enumerate(self.events):
            if set(event) != {"sequence", "tick", "actor", "kind", "payload",
                               "previous_hash", "hash"}:
                return {"ok": False, "reason": "ledger_schema", "index": index}
            body = {k: event[k] for k in (
                "sequence", "tick", "actor", "kind", "payload", "previous_hash")}
            if event["sequence"] != index:
                return {"ok": False, "reason": "ledger_sequence", "index": index}
            if event["previous_hash"] != previous:
                return {"ok": False, "reason": "ledger_link", "index": index}
            if event["hash"] != checksum(body):
                return {"ok": False, "reason": "ledger_hash", "index": index}
            previous = event["hash"]
        return {"ok": True, "reason": "ok", "index": None, "tip": previous}

    def to_list(self) -> list[dict[str, Any]]:
        return copy.deepcopy(list(self.events))

    @classmethod
    def from_list(cls, events: list[dict[str, Any]]) -> "Ledger":
        if not isinstance(events, list):
            raise ValueError("ledger must be a list")
        ledger = cls(tuple(copy.deepcopy(dict(event)) for event in events))
        if not ledger.verify()["ok"]:
            raise ValueError("invalid ledger")
        return ledger