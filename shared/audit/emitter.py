"""Audit event emitter."""

from __future__ import annotations

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
    """Emit an audit event.

    Args:
        action: The action performed
        outcome: Outcome of the action
        resource_type: Type of resource affected
        resource_id: ID of resource (optional)
        actor_id: Actor ID (optional)
        tenant_id: Tenant ID (optional)
        request_id: Request correlation ID (optional)
        details: Additional details (optional)
    """
    event = AuditEvent(
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
    
    await _global_emitter.emit(event)
