"""Shared correlation ID contract for headers, request context keys, and log fields."""

from __future__ import annotations

CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"
CANONICAL_CORRELATION_HEADERS: tuple[str, ...] = (REQUEST_ID_HEADER, CORRELATION_ID_HEADER)

REQUEST_STATE_TRACE_ID_KEY = "trace_id"
REQUEST_STATE_CORRELATION_ID_KEY = "correlation_id"

LOG_FIELD_CORRELATION_ID = "correlation_id"
LOG_FIELD_TRACE_ID = "trace_id"
