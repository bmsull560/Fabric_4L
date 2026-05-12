"""Shared observability utilities (path normalization, probes, middleware).

These helpers are reused across all layers (L1–L6) to avoid drift in metric
cardinality controls and `/metrics` endpoint authorization.
"""

from .metrics_access import is_internal_ip, verify_metrics_access
from .probes import configure_observability
from .path_normalization import PathNormalizer
from .trace_context import (
    ALL_TRACE_HEADERS,
    CANONICAL_TRACE_HEADER,
    TRACE_HEADER_ALIASES,
    canonical_trace_headers,
    resolve_trace_context,
)

__all__ = [
    "PathNormalizer",
    "configure_observability",
    "is_internal_ip",
    "verify_metrics_access",
    "ALL_TRACE_HEADERS",
    "CANONICAL_TRACE_HEADER",
    "TRACE_HEADER_ALIASES",
    "canonical_trace_headers",
    "resolve_trace_context",
]
