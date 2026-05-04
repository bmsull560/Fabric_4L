"""Audit event emitter.

Design (per review feedback — no Celery):
- Primary path: structured JSON log to stdout via ``logging``.  In production
  this is captured by the log aggregator (e.g., Loki, Datadog, CloudWatch)
  and can be ingested into the audit_events table by a log-router sidecar.
- Secondary path (optional): if a ``db_session_factory`` is provided at
  construction time, events are also persisted directly to ``audit_events``
  via a FastAPI ``BackgroundTask`` (fire-and-forget, zero latency on the
  hot path).

The dual-path approach means audit logging works immediately without
requiring any additional infrastructure, and the DB write is a progressive
enhancement.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, Optional, Set
from uuid import UUID

try:
    from prometheus_client import Counter
    _AUDIT_WRITE_FAILURES = Counter(
        "value_fabric_audit_write_failures_total",
        "Total number of audit event write failures",
        ["failure_type"]
    )
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False
    _AUDIT_WRITE_FAILURES = None

from .models import AuditAction, AuditEvent, AuditOutcome
from value_fabric.shared.models.typed_dict import TypedDictModel


class _scrub_detailsResult(TypedDictModel):
    pass

logger = logging.getLogger("vf.audit")

# Keys that must never appear in the structured log (scrubbed from ``details``).
_SENSITIVE_KEYS: Set[str] = {
    "password",
    "hashed_password",
    "secret",
    "token",
    "api_key",
    "key_hash",
    "access_token",
    "refresh_token",
    "private_key",
    "client_secret",
}


def _scrub_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of *details* with sensitive keys replaced by '[REDACTED]'."""
    # Keep the public emitter contract as a plain mapping.  The lightweight
    # TypedDictModel wrapper is useful for generated typing, but AuditEvent and
    # downstream DB serialization expect a concrete dict.
    return {
        k: "[REDACTED]" if k.lower() in _SENSITIVE_KEYS else v
        for k, v in details.items()
    }


# ---------------------------------------------------------------------------
# Global helper — call this from any layer
# ---------------------------------------------------------------------------


def emit_audit_event(
    action: AuditAction,
    *,
    tenant_id: Optional[UUID] = None,
    user_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    outcome: AuditOutcome = AuditOutcome.SUCCESS,
    details: Optional[Dict[str, Any]] = None,
    chain_id: Optional[str] = None,
) -> AuditEvent:
    """Create and emit an audit event.

    The event is written to the structured audit logger immediately.
    Returns the :class:`AuditEvent` so callers can pass it to the DB writer
    via a BackgroundTask if desired.

    Example::

        from value_fabric.shared.audit import emit_audit_event, AuditAction

        event = emit_audit_event(
            AuditAction.TENANT_CREATED,
            tenant_id=new_tenant.id,
            user_id=ctx.user_id,
            resource_type="Tenant",
            resource_id=str(new_tenant.id),
        )
        background_tasks.add_task(AuditEmitter.write_to_db, event, get_db)
    """
    safe_details = _scrub_details(details or {})

    event = AuditEvent(
        action=action,
        tenant_id=tenant_id,
        user_id=user_id,
        api_key_id=api_key_id,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        outcome=outcome,
        details=safe_details,
    )

    # Write to structured log (always).  Sensitive keys are scrubbed above.
    logger.info(
        json.dumps(
            {
                "audit": True,
                "event_id": str(event.id),
                "action": event.action,
                "tenant_id": str(event.tenant_id) if event.tenant_id else None,
                "user_id": event.user_id,
                "api_key_id": event.api_key_id,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "outcome": event.outcome,
                "ip_address": event.ip_address,
                "request_id": event.request_id,
                "timestamp": event.timestamp.isoformat(),
                "details": event.details,
                "chain_id": chain_id,
            }
        )
    )

    return event


# ---------------------------------------------------------------------------
# AuditEmitter — optional DB persistence via BackgroundTask
# ---------------------------------------------------------------------------


class AuditEmitter:
    """Handles optional DB persistence of audit events.

    Usage in a FastAPI route::

        @router.post("/v1/tenants")
        async def create_tenant(
            request: TenantCreateRequest,
            background_tasks: BackgroundTasks,
            ctx = Depends(require_super_admin),
            db: AsyncSession = Depends(get_db_from_context),
        ):
            tenant = await service.create_tenant(db, request)
            event = emit_audit_event(
                AuditAction.TENANT_CREATED,
                tenant_id=tenant.id,
                user_id=ctx.user_id,
                resource_type="Tenant",
                resource_id=str(tenant.id),
            )
            background_tasks.add_task(AuditEmitter.write_to_db, event, get_db_from_context)
            return tenant
    """

    @staticmethod
    async def write_to_db(event: AuditEvent, db_factory: Callable) -> None:
        """Persist an audit event to the ``audit_events`` table.

        Called as a BackgroundTask — failures are logged but do not affect
        the main request.

        Args:
            event:      The :class:`AuditEvent` to persist.
            db_factory: An async context manager factory (e.g. ``get_db``
                        from ``layer4-agents/src/database.py``).
        """
        try:
            async with db_factory() as session:
                from sqlalchemy import text

                await session.execute(
                    text(
                        """
                        INSERT INTO audit_events (
                            id, tenant_id, user_id, api_key_id,
                            action, resource_type, resource_id,
                            ip_address, user_agent, request_id,
                            outcome, details, timestamp
                        ) VALUES (
                            :id, :tenant_id, :user_id, :api_key_id,
                            :action, :resource_type, :resource_id,
                            :ip_address, :user_agent, :request_id,
                            :outcome, :details::jsonb, :timestamp
                        )
                        """
                    ),
                    {
                        "id": event.id,
                        "tenant_id": event.tenant_id,
                        "user_id": event.user_id,
                        "api_key_id": event.api_key_id,
                        "action": event.action,
                        "resource_type": event.resource_type,
                        "resource_id": event.resource_id,
                        "ip_address": event.ip_address,
                        "user_agent": event.user_agent,
                        "request_id": event.request_id,
                        "outcome": event.outcome,
                        "details": json.dumps(event.details),
                        "timestamp": event.timestamp,
                    },
                )
                await session.commit()
        except Exception as exc:
            logger.error(
                "Failed to persist audit event %s to DB: %s",
                event.id,
                exc,
                exc_info=True,
            )
            if _METRICS_AVAILABLE and _AUDIT_WRITE_FAILURES is not None:
                _AUDIT_WRITE_FAILURES.labels(failure_type="db_write").inc()

# Merged from root shared/audit/emitter.py
class AuditEmitterError(Exception):
    """Raised when audit emission fails in fail-closed mode."""
    pass

def get_emitter() -> AuditEmitter:
    """Get the global audit emitter."""
    return _global_emitter

def _create_audit_event(
    action: AuditAction,
    outcome: AuditOutcome,
    resource_type: str,
    resource_id: str | None = None,
    actor_id: UUID | None = None,
    tenant_id: UUID | None = None,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
    chain_id: str | None = None,
) -> AuditEvent:
    """Create an AuditEvent instance with standard fields populated."""
    return AuditEvent(
        id=uuid4(),
        timestamp=datetime.now(UTC).isoformat(),
        action=action,
        outcome=outcome,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_id=tenant_id,
        request_id=request_id,
        details=details,
        chain_id=chain_id,
    )

def emit_audit_event_sync(
    action: AuditAction,
    outcome: AuditOutcome,
    resource_type: str,
    resource_id: str | None = None,
    actor_id: UUID | None = None,
    tenant_id: UUID | None = None,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Emit an audit event (synchronous version).

    Use this in synchronous contexts where async/await is not available.
    Schedules the async emit via asyncio.create_task if an event loop is running,
    otherwise logs a warning and returns without emitting.

    Args:
        action: The action performed
        outcome: Outcome of the action
        resource_type: Type of resource affected
        resource_id: ID of resource (optional)
        actor_id: Actor ID (optional)
        tenant_id: Tenant ID (optional)
        request_id: Request correlation ID (optional)
        details: Additional details (optional)

    Example:
        # In synchronous code:
        emit_audit_event_sync(...)
    """
    event = _create_audit_event(
        action, outcome, resource_type, resource_id,
        actor_id, tenant_id, request_id, details
    )

    try:
        loop = asyncio.get_running_loop()
        # Schedule in background - don't block and don't wait for result
        loop.create_task(_global_emitter.emit(event))
    except RuntimeError:
        # No event loop running - log warning but don't crash
        logger.warning(
            "Cannot emit audit event: no event loop running. "
            "Use emit_audit_event() in async contexts."
        )
