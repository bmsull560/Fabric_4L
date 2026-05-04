"""Shared audit compatibility API."""
from .emitter import emit_audit_event, emitted_events, validate_audit_config
from .models import AuditAction, AuditEvent, AuditOutcome, PolicyDecisionRecord, PrivilegedAccessDetails

__all__ = [
    "AuditAction",
    "AuditEvent",
    "AuditOutcome",
    "PolicyDecisionRecord",
    "PrivilegedAccessDetails",
    "emit_audit_event",
    "emitted_events",
    "validate_audit_config",
]
