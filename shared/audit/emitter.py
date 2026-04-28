"""Audit event emitter."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import httpx

from .models import AuditAction, AuditEvent, AuditOutcome

logger = logging.getLogger(__name__)


class AuditEmitterError(Exception):
    """Raised when audit emission fails in fail-closed mode."""
    pass


class AuditEmitter:
    """Emitter for audit events.

    SECURITY: Fail-closed mode enabled via AUDIT_FAIL_CLOSED=true environment variable.
    When enabled, audit handler failures block the operation (raise AuditEmitterError).
    """

    def __init__(self) -> None:
        self._handlers: list[Any] = []
        self._fail_closed = os.getenv("AUDIT_FAIL_CLOSED", "").lower() in ("true", "1", "yes")

    def add_handler(self, handler: Any) -> None:
        """Add an audit event handler."""
        self._handlers.append(handler)

    async def emit(self, event: AuditEvent) -> None:
        """Emit an audit event to all handlers.

        SECURITY: In fail-closed mode, any handler failure raises AuditEmitterError.
        This ensures operations cannot proceed without audit logging.
        """
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
        handler_errors: list[tuple[Any, Exception]] = []
        for handler in self._handlers:
            try:
                if hasattr(handler, "handle"):
                    await handler.handle(event)
                elif callable(handler):
                    await handler(event)
            except Exception as e:
                logger.error(f"Audit handler failed: {e}")
                handler_errors.append((handler, e))
                if self._fail_closed:
                    # F-12 FIX: Fail-closed mode blocks operation
                    raise AuditEmitterError(
                        f"Audit logging failed in fail-closed mode: {e}"
                    ) from e

        # Log summary if any handlers failed (in warn mode)
        if handler_errors and not self._fail_closed:
            logger.warning(f"{len(handler_errors)} audit handler(s) failed but fail-closed is disabled")


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


async def emit_audit_event(
    action: AuditAction,
    outcome: AuditOutcome,
    resource_type: str,
    resource_id: str | None = None,
    actor_id: UUID | None = None,
    tenant_id: UUID | None = None,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
    chain_id: str | None = None,
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
        chain_id: Logical chain identifier for ledger tracking (optional)

    Example:
        # In async endpoint:
        await emit_audit_event(...)

        # In FastAPI endpoint with background tasks:
        background_tasks.add_task(emit_audit_event, ...)
    """
    event = _create_audit_event(
        action, outcome, resource_type, resource_id,
        actor_id, tenant_id, request_id, details, chain_id
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


# ═══════════════════════════════════════════════════════════════════════════
# Startup Validation
# ═══════════════════════════════════════════════════════════════════════════


async def validate_audit_config() -> None:
    """Validate audit sink configuration for production safety.
    
    Raises:
        ValueError: If audit sink is misconfigured in production
    """
    environment = os.getenv("ENVIRONMENT", "").lower()
    audit_sink_url = os.getenv("AUDIT_SINK_URL", "")
    audit_sink_timeout = int(os.getenv("AUDIT_SINK_TIMEOUT", "5"))
    
    if environment == "production":
        if not audit_sink_url:
            raise ValueError(
                "AUDIT_SINK_URL is required in production. "
                "Privileged operations must be audited for compliance."
            )
        
        # Test connectivity to audit sink
        try:
            async with httpx.AsyncClient(timeout=audit_sink_timeout) as client:
                response = await client.get(f"{audit_sink_url}/health")
                if response.status_code >= 500:
                    raise ValueError(
                        f"Audit sink is unreachable: HTTP {response.status_code}. "
                        "Cannot start without functional audit logging."
                    )
        except httpx.RequestError as e:
            raise ValueError(
                f"Audit sink is unreachable: {e}. "
                "Cannot start without functional audit logging."
            )
    elif environment == "development" and not audit_sink_url:
        logger.warning(
            "AUDIT_SINK_URL is not configured in development mode. "
            "Audit events will be logged locally only. "
            "This is not compliant for production."
        )

    # GATE Phase 1: Register ledger handler if enabled
    ledger_mode = os.getenv("AUDIT_LEDGER_MODE", "disabled")
    if ledger_mode == "enabled":
        from .ledger import LedgerCommitHandler

        handler = LedgerCommitHandler()
        _global_emitter.add_handler(handler)
        logger.info("GATE ledger handler registered (AUDIT_LEDGER_MODE=enabled)")
