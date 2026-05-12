"""Deterministic canonical JSON encoding and hashing."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def canonical_json_encode(value: Any) -> str:
    """Encode a value as deterministic canonical JSON."""

    normalized = _normalize(value)
    return json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def canonical_hash(value: Any, *, algorithm: str = "sha256") -> str:
    """Hash a value after canonical JSON encoding."""

    if algorithm != "sha256":
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    encoded = canonical_json_encode(value).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Cannot canonicalize non-finite float")
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, set):
        return sorted(_normalize(item) for item in value)
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    raise TypeError(f"Object of type {type(value).__name__} is not canonicalizable")
