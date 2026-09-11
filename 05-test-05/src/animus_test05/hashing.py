"""Canonical hashing utilities for Test 05.

Every hash in this project is a SHA-256 hex digest computed over a
canonical JSON encoding (sorted keys, compact separators, UTF-8) unless the
input is already raw bytes (source files), in which case the file bytes are
hashed directly. This module is imported by both the experiment runner and
the independent validator so the two never disagree about what a hash means.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def canonical_json(obj: Any) -> str:
    """Deterministic JSON encoding used as the input to every content hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def hash_obj(obj: Any) -> str:
    """SHA-256 hex digest of the canonical JSON encoding of ``obj``."""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    return hash_bytes(path.read_bytes())


def hash_source_tree(root: Path, relative_paths: Iterable[str]) -> dict:
    """Hash a declared, explicit list of source files (never a directory scan).

    Returns a dict with per-file hashes and a combined ``source_hash`` that is
    the hash of the sorted mapping, so any change to any listed file, or to
    the declared file list itself, changes ``source_hash``.
    """
    files = {}
    for rel in sorted(relative_paths):
        files[rel] = hash_file(root / rel)
    return {"files": files, "source_hash": hash_obj(files)}


def write_json(path: Path, obj: Any) -> str:
    """Write canonical JSON to ``path`` (pretty for humans) and return its hash
    computed over the canonical (non-pretty) encoding, so the stored hash is
    stable regardless of formatting."""
    digest = hash_obj(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return digest


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_json_hash(path: Path, expected_hash: str) -> bool:
    obj = read_json(path)
    return hash_obj(obj) == expected_hash
