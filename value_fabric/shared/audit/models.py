"""Shared audit event and policy decision compatibility models.

These models intentionally keep a small dependency footprint so release-policy and
agent production gates can import the public audit contract without requiring the
full service runtime.  The schema mirrors the platform-contract gate policy
record used by release validation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AuditAction(str, Enum):
    """Common audit action vocabulary used by layer4 compatibility routes."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    POLICY_DECISION = "policy_decision"
    TOOL_INVOCATION = "tool_invocation"
    TENANT_PROVISION = "tenant_provision"
    CROSS_TENANT_ACCESS = "cross_tenant_access"
    UNKNOWN = "unknown"


class AuditOutcome(str, Enum):
    """Common audit outcome vocabulary."""

    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    ERROR = "error"


@dataclass(slots=True)
class PolicyDecisionRecord:
    """Runtime policy decision record matching the release schema contract."""

    decision: bool
    reason: str
    obligations: list[str] = field(default_factory=list)
    policy_bundle_hash: str = ""

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PrivilegedAccessDetails:
    """Structured details for audited super-admin cross-tenant access.

    The mandatory security regression gate requires this shape to remain
    serialisable and deterministic so privileged operations can be reviewed
    without relying on ad-hoc dictionaries.
    """

    reason: str
    accessed_tenant_ids: list[str] = field(default_factory=list)
    resource_types: list[str] = field(default_factory=list)
    session_duration_seconds: int = 0
    approval_ticket: str | None = None
    query_count: int = 0
    data_exported: bool = False

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AuditEvent:
    """Minimal audit event envelope used by compatibility services."""

    action: str | AuditAction
    outcome: str | AuditOutcome
    tenant_id: str | None = None
    actor_id: str | None = None
    resource: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def model_dump(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["action"] = self.action.value if isinstance(self.action, Enum) else self.action
        payload["outcome"] = self.outcome.value if isinstance(self.outcome, Enum) else self.outcome
        return payload
