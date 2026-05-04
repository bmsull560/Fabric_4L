"""RFC 8785 Canonical JSON hashing utility.

Provides deterministic JSON serialization and SHA-256 hashing for audit
ledger integrity.  All hash-chained audit events, tool invocation records,
and replay snapshots MUST use these functions to guarantee cross-platform
hash stability.

References:
    - RFC 8785: JSON Canonicalization Scheme (JCS)
    - GATE Framework §1.1 — Canonical JSON Hashing Utility
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def canonical_json_encode(obj: Any) -> str:
    """Serialize *obj* to canonical JSON per RFC 8785.

    Rules enforced:
    - Lexicographic key sorting (Unicode code-point order)
    - No insignificant whitespace
    - UTF-8 encoding (``ensure_ascii=False``)
    - Floats rendered as shortest decimal representation
    - ``bytes`` values decoded as UTF-8 strings

    Args:
        obj: Any JSON-serializable Python object.

    Returns:
        Canonical JSON string.

    Raises:
        TypeError: If *obj* contains a type that cannot be canonicalized.
    """
    _check_non_finite_floats(obj)
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",",":"),
        ensure_ascii=False,
        default=_canonical_default,
    )


def _check_non_finite_floats(obj: Any) -> None:
    """Recursively check for non-finite floats before serialization."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError(f"Cannot canonicalize non-finite float: {obj}")
    elif isinstance(obj, dict):
        for v in obj.values():
            _check_non_finite_floats(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _check_non_finite_floats(item)


def _canonical_default(obj: Any) -> Any:
    """Handle non-standard types during canonical serialization."""
    if isinstance(obj, bytes):
        return obj.decode("utf-8")
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not canonicalizable")


def canonical_hash(obj: Any, algorithm: str = "sha256") -> str:
    """Return hex digest of the canonical JSON serialization of *obj*.

    Args:
        obj: Any JSON-serializable Python object.
        algorithm: Hash algorithm (only ``"sha256"`` supported).

    Returns:
        Lowercase hex digest string.

    Raises:
        ValueError: If *algorithm* is not supported.
    """
    payload = canonical_json_encode(obj).encode("utf-8")
    if algorithm == "sha256":
        return hashlib.sha256(payload).hexdigest()
    raise ValueError(f"Unsupported hash algorithm: {algorithm}")
