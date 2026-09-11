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
#
# PROTOCOL_V1_DEVELOPMENT_SEED_BANDS were used only by the superseded
# development pilot (see 05-test-05/superseded-development-pilot-2026-09-11/).
# They are kept here, unchanged, for provenance/audit purposes, but the
# revised (v2) protocol uses a disjoint band so no seed is reused across
# protocol versions.
PROTOCOL_V1_DEVELOPMENT_SEED_BANDS: dict[str, range] = {
    "05A": range(55000, 55020),
    "05B": range(55100, 55120),
    "05C": range(55200, 55220),
    "05D": range(55300, 55320),
    "05E": range(55400, 55420),
}

PROTOCOL_V2_DEVELOPMENT_SEED_BANDS: dict[str, range] = {
    "05A": range(57000, 57020),
    "05B": range(57100, 57120),
    "05C": range(57200, 57220),
    "05D": range(57300, 57320),
    "05E": range(57400, 57420),
}

# Protocol v1.2.0-dev3 (the exact governing document): seeds are keyed by
# world family, not by sub-test -- the same seed drives every component
# (05A-05D) for that family, plus (for the adversarial family) the full
# fault-execution matrix. These are the ONLY seeds ``run.py`` uses for
# v1.2.0-dev3.
PROTOCOL_V3_DEVELOPMENT_SEEDS: dict[str, list[int]] = {
    "friendly": [13001, 13002, 13003],
    "adversarial": [14001, 14002, 14003],
}

# Seeds actually touched by exploratory/tuning work while building this
# implementation (unit-test fixtures, ad hoc smoke checks, and the
# superseded v1/v2 draft bands above) -- recorded so "not a tuning seed"
# can be checked mechanically rather than asserted. None of these overlap
# 13001-13003 / 14001-14003.
TUNING_SEEDS_USED: set[int] = (
    {1, 55000, 55100, 55300}
    | set(PROTOCOL_V1_DEVELOPMENT_SEED_BANDS["05A"])
    | set(PROTOCOL_V2_DEVELOPMENT_SEED_BANDS["05A"])
    | set(PROTOCOL_V2_DEVELOPMENT_SEED_BANDS["05B"])
    | set(PROTOCOL_V2_DEVELOPMENT_SEED_BANDS["05D"])
)

# Active band used by the current protocol version's entrypoint
# (``run.py``). Kept as a separate name so a future protocol version can be
# added without editing the bands above.
DEVELOPMENT_SEED_BANDS: dict[str, range] = PROTOCOL_V2_DEVELOPMENT_SEED_BANDS


def all_v3_development_seeds() -> set[int]:
    out: set[int] = set()
    for seed_list in PROTOCOL_V3_DEVELOPMENT_SEEDS.values():
        out.update(seed_list)
    return out


def check_v3_seed_eligibility() -> dict:
    """Verifies, for every v1.2.0-dev3 seed, that it: was not used by the
    pilot; is not a reserved confirmatory seed; is not a recorded tuning
    seed; and is not already claimed by an earlier protocol version's
    development band. Returns a structured, evidence-grade report rather
    than raising, so it can be embedded directly in the preflight record."""
    pilot_seeds: set[int] = set()
    for band in PROTOCOL_V1_DEVELOPMENT_SEED_BANDS.values():
        pilot_seeds.update(band)
    reserved = all_reserved_seeds()
    earlier_bands: set[int] = set()
    for band in PROTOCOL_V2_DEVELOPMENT_SEED_BANDS.values():
        earlier_bands.update(band)

    per_seed = {}
    all_ok = True
    for family, seed_list in PROTOCOL_V3_DEVELOPMENT_SEEDS.items():
        for seed in seed_list:
            checks = {
                "not_used_by_pilot": seed not in pilot_seeds,
                "not_reserved_confirmatory": seed not in reserved,
                "not_a_tuning_seed": seed not in TUNING_SEEDS_USED,
                "not_in_earlier_protocol_band": seed not in earlier_bands,
            }
            ok = all(checks.values())
            all_ok = all_ok and ok
            per_seed[str(seed)] = {"family": family, "checks": checks, "eligible": ok}
    return {"eligible": all_ok, "per_seed": per_seed}

RESERVED_CONFIRMATORY_SEED_BANDS: dict[str, range] = {
    "05A": range(58000, 58020),
    "05B": range(58100, 58120),
    "05C": range(58200, 58220),
    "05D": range(58300, 58320),
    "05E": range(58400, 58420),
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
    """All seeds ever registered as development seeds, across every
    protocol version (v1 included), so historical/superseded evidence is
    never misclassified as having used a reserved seed."""
    out: set[int] = set()
    for band in PROTOCOL_V1_DEVELOPMENT_SEED_BANDS.values():
        out.update(band)
    for band in PROTOCOL_V2_DEVELOPMENT_SEED_BANDS.values():
        out.update(band)
    for seed_list in PROTOCOL_V3_DEVELOPMENT_SEEDS.values():
        out.update(seed_list)
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
