"""Audit event emitter."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from .models import AuditAction, AuditEvent, AuditOutcome

logger = logging.getLogger(__name__)


class AuditEmitter:
    """Emitter for audit events."""

    def __init__(self) -> None:
        self._handlers: list[Any] = []

    def add_handler(self, handler: Any) -> None:
        """Add an audit event handler."""
        self._handlers.append(handler)

    async def emit(self, event: AuditEvent) -> None:
        """Emit an audit event to all handlers."""
        # Log to structured logging
        logger.info(
            "audit_event",
            event_id=str(event.id),
            action=event.action.value,
            outcome=event.outcome.value,
            actor_id=str(event.actor_id) if event.actor_id else None,
            tenant_id=str(event.tenant_id) if event.tenant_id else None,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
        )

        # Send to handlers
        for handler in self._handlers:
            try:
                if hasattr(handler, "handle"):
                    await handler.handle(event)
                elif callable(handler):
                    await handler(event)
            except Exception as e:
                logger.error(f"Audit handler failed: {e}")


# Global emitter instance
_global_emitter = AuditEmitter()


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
    )


async def emit_audit_event(
    action: AuditAction,
    outcome: AuditOutcome,
    resource_type: str,
    resource_id: str | None = None,
    actor_id: UUID | None = None,
    tenant_id: UUID | None = None,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Emit an audit event (async version).

    Use this in async contexts or with FastAPI BackgroundTasks.
    For synchronous contexts, use emit_audit_event_sync().

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
        # In async endpoint:
        await emit_audit_event(...)

        # In FastAPI endpoint with background tasks:
        background_tasks.add_task(emit_audit_event, ...)
    """
    event = _create_audit_event(
        action, outcome, resource_type, resource_id,
        actor_id, tenant_id, request_id, details
    )
    await _global_emitter.emit(event)


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
