"""Structured telemetry helpers for legacy auth/tenant fallback paths."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

_REMOVAL_WINDOW_DAYS = int(os.getenv("LEGACY_FALLBACK_REMOVAL_WINDOW_DAYS", "30"))


def _flag_env_name(fallback_key: str) -> str:
    normalized = fallback_key.upper().replace(".", "_").replace("-", "_")
    return f"LEGACY_FALLBACK_{normalized}_ENABLED"


def fallback_enabled(fallback_key: str, default: bool = True) -> bool:
    """Return whether a specific fallback path is enabled."""
    raw = os.getenv(_flag_env_name(fallback_key))
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def enforce_fallback_enabled(fallback_key: str, *, default: bool = True) -> None:
    """Raise if a fallback path is disabled by a staged feature flag."""
    if not fallback_enabled(fallback_key, default=default):
        raise RuntimeError(f"Fallback '{fallback_key}' is disabled by feature flag.")


def record_fallback_usage(
    fallback_key: str,
    *,
    tenant_id: Any | None,
    client_id: str | None,
    service: str,
    path: str | None = None,
) -> None:
    """Emit a structured telemetry counter event for fallback usage."""
    logger.info(
        "legacy_fallback_usage",
        extra={
            "event": "legacy_fallback_usage",
            "counter": "legacy_auth_tenant_fallback_total",
            "fallback_key": fallback_key,
            "tenant_id": str(tenant_id) if tenant_id is not None else "unknown",
            "client_id": client_id or "unknown",
            "service": service,
            "path": path or "unknown",
            "removal_criteria_days_zero_usage": _REMOVAL_WINDOW_DAYS,
            "disable_flag": _flag_env_name(fallback_key),
            "observed_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def removal_cutoff_utc() -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=_REMOVAL_WINDOW_DAYS)
    return cutoff.isoformat()
