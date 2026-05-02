"""Shared observability utilities (path normalization, metrics access control).

These helpers are reused across all layers (L1–L6) to avoid drift in metric
cardinality controls and `/metrics` endpoint authorization.
"""

from .metrics_access import is_internal_ip, verify_metrics_access
from .path_normalization import PathNormalizer

__all__ = [
    "PathNormalizer",
    "is_internal_ip",
    "verify_metrics_access",
]
