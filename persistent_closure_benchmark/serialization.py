"""Canonical public serialization and checksums."""

from __future__ import annotations

import hashlib
import json
from typing import Any

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)

def canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def checksum(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))

def result_checksum(result: dict[str, Any]) -> str:
    """Hash a result without trusting an embedded checksum field."""
    unsigned = {k: v for k, v in result.items() if k != "result_checksum"}
    return checksum(unsigned)

def serialize_result(result: dict[str, Any]) -> bytes:
    """Return canonical bytes and verify any embedded checksum."""
    expected = result_checksum(result)
    if "result_checksum" in result and result["result_checksum"] != expected:
        raise ValueError("result checksum mismatch")
    return canonical_bytes(result)

def deserialize_result(data: bytes | str) -> dict[str, Any]:
    if isinstance(data, str):
        data = data.encode("utf-8")
    try:
        result = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid result JSON") from exc
    if canonical_bytes(result) != data:
        raise ValueError("result is not canonical JSON")
    if not isinstance(result, dict):
        raise ValueError("result must be an object")
    if result.get("result_checksum") != result_checksum(result):
        raise ValueError("result checksum mismatch")
    return result