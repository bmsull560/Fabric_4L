"""Shared audit compatibility API."""
from .emitter import AuditEmitter, emit_audit_event, emitted_events, validate_audit_config
from .models import AuditAction, AuditEvent, AuditOutcome, PolicyDecisionRecord, PrivilegedAccessDetails

__all__ = [
    "AuditAction",
    "AuditEvent",
    "AuditOutcome",
    "AuditEmitter",
    "PolicyDecisionRecord",
    "PrivilegedAccessDetails",
    "emit_audit_event",
    "emitted_events",
    "validate_audit_config",
]
