"""Shared audit log package for Value Fabric.

Provides:
- AuditAction  — canonical enum of auditable actions
- AuditEvent   — Pydantic model for an audit record
- AuditEmitter — async emitter; writes via FastAPI BackgroundTasks
"""

from .emitter import AuditEmitter, emit_audit_event
from .models import AuditAction, AuditEvent

__all__ = [
    "AuditAction",
    "AuditEvent",
    "AuditEmitter",
    "emit_audit_event",
]
