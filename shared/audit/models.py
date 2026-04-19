"""Audit event models."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    """Audit action types."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_FAIL = "workflow_fail"


class AuditOutcome(str, Enum):
    """Audit outcome types."""

    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    ERROR = "error"


class AuditEvent(BaseModel):
    """Audit event model."""

    id: UUID = Field(..., description="Event ID")
    timestamp: str = Field(..., description="ISO timestamp")
    action: AuditAction = Field(..., description="Action performed")
    outcome: AuditOutcome = Field(..., description="Outcome of action")
    actor_id: UUID | None = Field(None, description="User or API key ID")
    actor_type: str = Field("user", description="Type of actor")
    tenant_id: UUID | None = Field(None, description="Tenant ID")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: str | None = Field(None, description="ID of resource")
    request_id: str | None = Field(None, description="Request correlation ID")
    ip_address: str | None = Field(None, description="Client IP")
    user_agent: str | None = Field(None, description="User agent")
    details: dict[str, Any] | None = Field(None, description="Additional details")

    class Config:
        from_attributes = True
