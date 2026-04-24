# Canonical agent output envelope for Fabric 4L.
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class AgentErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    node_id: str | None = Field(None, description="Workflow node where error occurred")
    retryable: bool = Field(False, description="Whether the error may resolve on retry")
    details: dict[str, Any] | None = Field(None, description="Additional error context")


class AgentResultMetadata(BaseModel):
    trace_id: str = Field(..., description="OpenTelemetry trace ID or X-Request-ID fallback")
    workflow_id: str = Field(..., description="Unique workflow instance ID")
    tenant_id: str = Field(..., description="Tenant identifier")
    agent_type: str = Field(..., description="Agent type identifier")
    started_at: datetime = Field(..., description="Workflow start timestamp")
    completed_at: datetime = Field(..., description="Workflow completion timestamp")
    duration_ms: int = Field(..., description="Total execution time in milliseconds")
    node_path: list[str] = Field(default_factory=list, description="Ordered list of nodes executed")


class AgentResultEnvelope(BaseModel):
    """Canonical envelope for all agent API responses."""
    status: Literal["success", "error", "paused"]
    data: dict[str, Any] | None = None
    error: AgentErrorDetail | None = None
    metadata: AgentResultMetadata
