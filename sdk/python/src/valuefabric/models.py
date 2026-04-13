"""Lightweight Pydantic models for the Value Fabric SDK."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, FrozenSet, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Tenant(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class User(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    display_name: Optional[str] = None
    role: str
    status: str
    last_login_at: Optional[datetime] = None
    invited_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class APIKey(BaseModel):
    key_id: str
    tenant_id: UUID
    user_id: Optional[UUID] = None
    name: str
    prefix: str
    role: str
    permissions: FrozenSet[str] = Field(default_factory=frozenset)
    enabled: bool = True
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    rate_limit_per_minute: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class APIKeyCreateResult(BaseModel):
    key_id: str
    tenant_id: UUID
    name: str
    api_key: str
    prefix: str
    role: str
    permissions: FrozenSet[str] = Field(default_factory=frozenset)
    expires_at: Optional[datetime] = None
    rate_limit_per_minute: Optional[int] = None
    created_at: datetime


class Workflow(BaseModel):
    workflow_instance_id: str
    workflow_type: str
    status: str
    current_state: Optional[str] = None
    current_node: Optional[str] = None
    progress_percentage: float = 0.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_count: int = 0
    has_output: bool = False
    results: Optional[Dict[str, Any]] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    priority: Optional[int] = None
    scheduler_status: Optional[str] = None


class WorkflowTypeInfo(BaseModel):
    type: str
    name: str
    description: str


class ModelVersion(BaseModel):
    id: UUID
    tenant_id: UUID
    provider: str
    model_name: str
    model_version: str
    stage: str
    promoted_by: Optional[UUID] = None
    eval_score: Optional[float] = None
    eval_run_id: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class FeatureFlag(BaseModel):
    id: UUID
    tenant_id: Optional[UUID] = None
    flag_key: str
    enabled: bool
    rollout_percentage: int = 0
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    updated_by: Optional[UUID] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    executor_ready: bool
    uptime_seconds: float
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
