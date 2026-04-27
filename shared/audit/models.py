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
    FEATURE_FLAG_CREATED = "feature_flag_created"
    FEATURE_FLAG_UPDATED = "feature_flag_updated"
    FEATURE_FLAG_DELETED = "feature_flag_deleted"
    MODEL_REGISTERED = "model_registered"
    MODEL_PROMOTED = "model_promoted"
    MODEL_DEPRECATED = "model_deprecated"
    MODEL_EVALUATED = "model_evaluated"
    OIDC_LOGIN = "oidc_login"
    OIDC_LOGIN_FAILED = "oidc_login_failed"
    # Task 3.1: Tenant resolution audit logging
    TENANT_RESOLVED = "tenant_resolved"
    TENANT_CONTEXT_SET = "tenant_context_set"
    # Phase 3: Usage tracking audit actions
    API_CALL = "api_call"
    LLM_USAGE = "llm_usage"
    AGENT_EXECUTION = "agent_execution"
    # Task 2: Multi-Tenancy Hardening - Super-admin bypass audit
    CROSS_TENANT_ACCESS = "cross_tenant_access"
    # Phase 2: Provisioning pipeline audit actions
    TENANT_PROVISIONED = "tenant_provisioned"
    TENANT_PROVISIONING_FAILED = "tenant_provisioning_failed"
    TENANT_PROVISIONING_STEP_COMPLETE = "tenant_provisioning_step_complete"
    TENANT_PROVISIONING_ROLLBACK = "tenant_provisioning_rollback"
    TENANT_PROVISIONED_WEBHOOK = "tenant_provisioned_webhook"
    TENANT_STATUS_CHANGED = "tenant_status_changed"
    INFISICAL_PATH_CREATED = "infisical_path_created"
    INFISICAL_SECRET_SEEDED = "infisical_secret_seeded"
    # GATE Framework actions
    TOOL_INVOCATION = "tool_invocation"
    POLICY_DECISION = "policy_decision"
    LEDGER_COMMIT = "ledger_commit"
    MEMORY_ACCESS = "memory_access"
    REPLAY_SNAPSHOT = "replay_snapshot"


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
    # GATE Phase 1 — hash-chain ledger fields (all optional for backward compat)
    previous_hash: str | None = Field(None, description="Hash of previous event in chain")
    event_hash: str | None = Field(None, description="Hash of this event's canonical payload")
    canonical_payload: dict[str, Any] | None = Field(None, description="Canonical JSON payload used for hashing")
    chain_id: str | None = Field(None, description="Logical chain identifier (e.g., tenant_id:tool_name)")
    sequence_number: int | None = Field(None, description="Monotonic sequence within chain_id")

    class Config:
        from_attributes = True


class TenantResolvedDetails(BaseModel):
    """Structured details for TENANT_RESOLVED audit events (Task 3.1).

    Provides a standardized schema for tenant resolution events without
    fragmenting the audit model into separate types.
    """

    resolution_source: str = Field(
        ...,
        description="How tenant was resolved: jwt_claim | api_key | service_account | unknown"
    )
    resolved_tenant_id: str | None = Field(
        None,
        description="Final tenant_id that was resolved"
    )
    requested_tenant_id: str | None = Field(
        None,
        description="Tenant_id that was originally requested (if different)"
    )
    user_id: str | None = Field(
        None,
        description="User ID if JWT authentication"
    )
    api_key_id: str | None = Field(
        None,
        description="API key ID if API key authentication"
    )
    service_account_id: str | None = Field(
        None,
        description="Service account ID if service account authentication"
    )
    auth_method: str = Field(
        ...,
        description="Authentication method: jwt | api_key | service_account | none"
    )
    has_org_id: bool = Field(
        default=False,
        description="Whether org_id was present in claims"
    )
    org_id: str | None = Field(
        None,
        description="Organization ID if present in claims"
    )
    tenant_role: str | None = Field(
        None,
        description="User's role within tenant context"
    )
    isolation_tier: str = Field(
        default="shared",
        description="Tenant isolation tier: shared | schema | database"
    )
    roles: list[str] = Field(
        default_factory=list,
        description="Roles assigned to the actor"
    )
    is_super_admin: bool = Field(
        default=False,
        description="Whether actor has super admin privileges"
    )
    bypass: bool = Field(
        default=False,
        description="Whether tenant context was bypassed (privileged access)"
    )
    bypass_reason: str | None = Field(
        None,
        description="Reason for bypass if applicable"
    )
    outcome: str = Field(
        default="success",
        description="Resolution outcome: success | failure | denied"
    )
    failure_reason: str | None = Field(
        None,
        description="Reason for failure if outcome is not success"
    )
    request_path: str | None = Field(
        None,
        description="API path being accessed"
    )
    request_method: str | None = Field(
        None,
        description="HTTP method of the request"
    )

    class Config:
        from_attributes = True


class TenantContextSetDetails(BaseModel):
    """Structured details for TENANT_CONTEXT_SET audit events (Task 3.1).

    Emitted when database session is configured with RLS tenant context.
    """

    tenant_id: str | None = Field(
        None,
        description="Tenant ID set for RLS context (empty string for bypass)"
    )
    isolation_tier: str = Field(
        default="shared",
        description="Isolation tier from request context"
    )
    bypass: bool = Field(
        default=False,
        description="Whether this is a super-admin bypass"
    )
    bypass_reason: str | None = Field(
        None,
        description="Reason for bypass if applicable"
    )
    context_source: str = Field(
        default="request_context",
        description="Source of tenant context: request_context | explicit_param | job_queue"
    )


# ═══════════════════════════════════════════════════════════════════════════
# GATE Framework — Structured Detail Records
# ═══════════════════════════════════════════════════════════════════════════


class ToolInvocationRecord(BaseModel):
    """Structured details for TOOL_INVOCATION audit events (GATE Phase 1)."""

    tool_name: str
    tool_version: str | None = None
    tool_manifest_hash: str | None = None
    request_hash: str
    response_hash: str | None = None
    policy_decision: str | None = None  # "allowed" | "denied" | "invariant_blocked"
    invariant_checks: list[str] = Field(default_factory=list)
    execution_time_ms: int | None = None
    tenant_id: str | None = None
    actor_id: str | None = None
    trace_id: str | None = None


class LedgerCommitDetails(BaseModel):
    """Details for ledger commit events linking to previous state (GATE Phase 1)."""

    chain_head_hash: str | None = None
    commit_type: str  # "tool_invocation" | "policy_decision" | "agent_execution"
    bundle_hash: str | None = None  # Hash of policy/invariant bundle evaluated


class PolicyDecisionRecord(BaseModel):
    """Structured details for POLICY_DECISION audit events (GATE Phase 2)."""

    decision: bool
    reason: str | None = None
    obligations: list[str] = Field(default_factory=list)
    policy_bundle_hash: str | None = None


class MemoryAccessRecord(BaseModel):
    """Structured details for MEMORY_ACCESS audit events (GATE Phase 3)."""

    query: str
    tenant_id: str
    agent_id: str | None = None
    content_hash: str
    source_lineage: list[dict[str, Any]] = Field(default_factory=list)
    entity_count: int = 0
    relationship_count: int = 0
    trace_id: str | None = None


class ReplaySnapshotRecord(BaseModel):
    """Structured details for REPLAY_SNAPSHOT audit events (GATE Phase 3)."""

    agent_id: str
    agent_type: str | None = None
    manifest_hash: str | None = None
    snapshot_hash: str
    tool_invocation_count: int = 0
    memory_access_count: int = 0
    tenant_id: str | None = None
    trace_id: str | None = None


class PrivilegedAccessDetails(BaseModel):
    """Structured details for CROSS_TENANT_ACCESS audit events (Task 2).
    
    Captures comprehensive information about super-admin bypass operations
    for compliance and security monitoring.
    
    Example usage:
        details = PrivilegedAccessDetails(
            accessed_tenant_ids=["tenant-a", "tenant-b"],
            resource_types=["Entity", "Relationship"],
            session_duration_seconds=45,
            reason="Emergency data recovery for customer incident #12345",
            approval_ticket="JIRA-SEC-9876"
        )
        
        await emit_audit_event(
            action=AuditAction.CROSS_TENANT_ACCESS,
            outcome=AuditOutcome.SUCCESS,
            actor_id=admin_user_id,
            details=details.model_dump()
        )
    """
    
    accessed_tenant_ids: list[str] = Field(
        default_factory=list,
        description="List of tenant IDs accessed during privileged session"
    )
    resource_types: list[str] = Field(
        default_factory=list,
        description="Types of resources accessed (Entity, Relationship, etc.)"
    )
    session_duration_seconds: int = Field(
        default=0,
        description="Duration of privileged session in seconds"
    )
    reason: str = Field(
        ...,
        description="Justification for cross-tenant access (from X-Privileged-Reason header)"
    )
    approval_ticket: str | None = Field(
        None,
        description="Optional approval ticket/incident number"
    )
    query_count: int = Field(
        default=0,
        description="Number of cross-tenant queries executed"
    )
    data_exported: bool = Field(
        default=False,
        description="Whether data was exported/downloaded"
    )
