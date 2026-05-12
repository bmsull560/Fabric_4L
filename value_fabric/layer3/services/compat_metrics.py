"""Compatibility metrics for deprecated Layer 3 usage."""

from __future__ import annotations

from collections import Counter

try:
    from prometheus_client import Counter as PromCounter
except Exception:  # pragma: no cover
    PromCounter = None

_DEPRECATED_ROUTE_HITS: Counter[tuple[str, str, str]] = Counter()
_DEPRECATED_LEGACY_FIELD_HITS: Counter[tuple[str, str, str]] = Counter()

if PromCounter is not None:
    _ROUTE_COUNTER = PromCounter(
        "layer3_deprecated_route_hits_total",
        "Deprecated Layer 3 route hits",
        ["route", "tenant_id", "app_client"],
    )
    _FIELD_COUNTER = PromCounter(
        "layer3_legacy_field_usage_total",
        "Legacy field usage in Layer 3 compatibility paths",
        ["field", "tenant_id", "app_client"],
    )
else:
    _ROUTE_COUNTER = None
    _FIELD_COUNTER = None


def record_deprecated_route_hit(route: str, *, tenant_id: str, app_client: str) -> None:
    key = (route, tenant_id or "unknown", app_client or "unknown")
    _DEPRECATED_ROUTE_HITS[key] += 1
    if _ROUTE_COUNTER is not None:
        _ROUTE_COUNTER.labels(route=key[0], tenant_id=key[1], app_client=key[2]).inc()


def record_deprecated_legacy_field_usage(field: str, *, tenant_id: str, app_client: str) -> None:
    key = (field, tenant_id or "unknown", app_client or "unknown")
    _DEPRECATED_LEGACY_FIELD_HITS[key] += 1
    if _FIELD_COUNTER is not None:
        _FIELD_COUNTER.labels(field=key[0], tenant_id=key[1], app_client=key[2]).inc()


def get_compat_metrics_snapshot() -> dict[str, dict[str, int]]:
    return {
        "route_hits": {"|".join(key): value for key, value in _DEPRECATED_ROUTE_HITS.items()},
        "legacy_field_hits": {"|".join(key): value for key, value in _DEPRECATED_LEGACY_FIELD_HITS.items()},
    }
