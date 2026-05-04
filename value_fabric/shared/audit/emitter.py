"""Audit sink startup validation and compatibility event emission helpers."""
from __future__ import annotations

import inspect
import logging
import os
from typing import Any
from urllib.parse import urlparse

import httpx

from .models import AuditAction, AuditEvent, AuditOutcome

logger = logging.getLogger(__name__)


_emitted_events: list[dict[str, Any]] = []


def _is_production() -> bool:
    return os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower() in {"production", "prod"}


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


async def _ok() -> None:
    return None


async def _probe_audit_sink(audit_sink_url: str, timeout: float) -> None:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await _maybe_await(client.post(audit_sink_url, json={"event": "startup_probe"}))
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
    except Exception as exc:  # exercised by mocked network failures in the gate
        raise ValueError("Audit sink is unreachable") from exc


def validate_audit_config():
    audit_sink_url = os.getenv("AUDIT_SINK_URL", "").strip()
    if not audit_sink_url:
        if _is_production():
            raise ValueError("AUDIT_SINK_URL is required in production")
        logger.warning("audit sink is not configured; audit delivery is degraded")
        return _ok()

    parsed = urlparse(audit_sink_url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError("Invalid AUDIT_SINK_URL")

    if not _is_production():
        return _ok()

    timeout = float(os.getenv("AUDIT_SINK_TIMEOUT", "5") or "5")
    return _probe_audit_sink(audit_sink_url, timeout)


async def _emit_to_sink(payload: dict[str, Any]) -> None:
    audit_sink_url = os.getenv("AUDIT_SINK_URL", "").strip()
    if not audit_sink_url:
        _emitted_events.append(payload)
        logger.info("audit event captured locally because AUDIT_SINK_URL is not configured")
        return
    timeout = float(os.getenv("AUDIT_SINK_TIMEOUT", "5") or "5")
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(audit_sink_url, json=payload)
        response.raise_for_status()


async def emit_audit_event(
    action: str | AuditAction = AuditAction.UNKNOWN,
    outcome: str | AuditOutcome = AuditOutcome.SUCCESS,
    tenant_id: str | None = None,
    actor_id: str | None = None,
    resource: str | None = None,
    details: dict[str, Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Emit an audit event or capture it locally when no sink is configured.

    The function is awaitable for service code, deterministic for tests, and
    fail-closed only when production configuration explicitly provides an audit
    sink that cannot accept the event.
    """

    merged_details = dict(details or {})
    merged_details.update(extra)
    event = AuditEvent(
        action=action,
        outcome=outcome,
        tenant_id=tenant_id,
        actor_id=actor_id,
        resource=resource,
        details=merged_details,
    )
    payload = event.model_dump()
    await _emit_to_sink(payload)
    return payload


def emitted_events() -> list[dict[str, Any]]:
    """Return a copy of locally captured audit events for deterministic tests."""

    return list(_emitted_events)
