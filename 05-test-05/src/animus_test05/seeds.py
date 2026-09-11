"""Development vs. reserved confirmatory seed controls for Test 05.

Following the convention established by Test 04 (frozen manifest + atomic
started/completed markers, reserved seeds treated as burned once accessed),
Test 05 declares two disjoint, explicit seed bands. Development seeds are the
only seeds this module will ever let ordinary code execute. Reserved
confirmatory seeds can be executed only by a separate, explicit path that
requires all of:

1. a frozen protocol file whose hash matches ``RESERVED_PROTOCOL_HASH_REQUIRED``
   (set only once a confirmatory protocol is actually frozen -- it is
   deliberately left as a sentinel that can never match today, so reserved
   execution is impossible until a human freezes a real protocol file and
   updates this constant in a reviewed change);
2. the literal token ``I_UNDERSTAND_THIS_BURNS_A_RESERVED_SEED`` passed to
   ``confirm_reserved_execution``;
3. an atomic ``confirmatory.started.json`` marker written before any
   simulation work begins.

No code path in this development run calls ``confirm_reserved_execution``.
This module exists so that attempting to smuggle a reserved seed into a
development run fails loudly rather than silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

# Disjoint from Test 04's reserved bands (42000-42019, 43000-43019) and from
# each other. These are declared, not derived, so they can be audited by eye.
DEVELOPMENT_SEED_BANDS: dict[str, range] = {
    "05A": range(55000, 55020),
    "05B": range(55100, 55120),
    "05C": range(55200, 55220),
    "05D": range(55300, 55320),
    "05E": range(55400, 55420),
}

RESERVED_CONFIRMATORY_SEED_BANDS: dict[str, range] = {
    "05A": range(56000, 56020),
    "05B": range(56100, 56120),
    "05C": range(56200, 56220),
    "05D": range(56300, 56320),
    "05E": range(56400, 56420),
}

# Deliberately unsatisfiable until a human freezes a real confirmatory
# protocol and edits this constant in a reviewed, dated change.
RESERVED_PROTOCOL_HASH_REQUIRED = "UNFROZEN-NO-CONFIRMATORY-PROTOCOL-EXISTS-YET"

_CONFIRM_TOKEN = "I_UNDERSTAND_THIS_BURNS_A_RESERVED_SEED"


class ReservedSeedError(RuntimeError):
    pass


def all_reserved_seeds() -> set[int]:
    out: set[int] = set()
    for band in RESERVED_CONFIRMATORY_SEED_BANDS.values():
        out.update(band)
    return out


def all_development_seeds() -> set[int]:
    out: set[int] = set()
    for band in DEVELOPMENT_SEED_BANDS.values():
        out.update(band)
    return out


def is_reserved(seed: int) -> bool:
    return seed in all_reserved_seeds()


def is_development(seed: int) -> bool:
    return seed in all_development_seeds()


def require_development_seeds(seeds: Sequence[int]) -> None:
    """Raise ``ReservedSeedError`` if any seed is reserved or unregistered."""
    for seed in seeds:
        if is_reserved(seed):
            raise ReservedSeedError(
                f"seed {seed} is a reserved confirmatory seed; refusing to run "
                "it in a development context"
            )
        if not is_development(seed):
            raise ReservedSeedError(
                f"seed {seed} is not a registered development seed for Test 05"
            )


@dataclass(frozen=True)
class ConfirmatoryAuthorization:
    protocol_path: Path
    protocol_hash: str
    marker_path: Path


def confirm_reserved_execution(
    seeds: Sequence[int],
    confirm_token: str,
    frozen_protocol_path: Path,
) -> ConfirmatoryAuthorization:
    """Gate for confirmatory (reserved-seed) execution. Not called anywhere in
    this development run. Left implemented (rather than a stub) so tests can
    prove it actually refuses, instead of merely asserting it is absent."""
    from . import hashing

    if confirm_token != _CONFIRM_TOKEN:
        raise ReservedSeedError("confirmatory execution requires the exact confirmation token")

    if not frozen_protocol_path.exists():
        raise ReservedSeedError("no frozen confirmatory protocol file exists")

    protocol_hash = hashing.hash_file(frozen_protocol_path)
    if protocol_hash != RESERVED_PROTOCOL_HASH_REQUIRED:
        raise ReservedSeedError(
            "frozen protocol hash does not match the hash pinned in seeds.py; "
            "a confirmatory run requires a reviewed change that pins the exact "
            "frozen protocol before any reserved seed may be touched"
        )

    for seed in seeds:
        if not is_reserved(seed):
            raise ReservedSeedError(f"seed {seed} is not in a reserved confirmatory band")

    marker_path = frozen_protocol_path.parent / "confirmatory.started.json"
    if marker_path.exists():
        raise ReservedSeedError(
            "a confirmatory.started.json marker already exists; reserved seeds "
            "are treated as burned and this run must not be resumed or repeated"
        )
    marker_path.write_text(
        hashing.canonical_json({"status": "started", "protocol_hash": protocol_hash}) + "\n",
        encoding="utf-8",
    )
    return ConfirmatoryAuthorization(
        protocol_path=frozen_protocol_path,
        protocol_hash=protocol_hash,
        marker_path=marker_path,
    )
