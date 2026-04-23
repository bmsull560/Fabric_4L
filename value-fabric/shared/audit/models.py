"""Audit event model and action enum.

Audit records are append-only — no UPDATE or DELETE operations are ever
issued against the audit_events table (enforced at the DB level via a
trigger in production; enforced in application code by design).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AuditAction(str, Enum):
    """Canonical set of auditable actions across all layers."""

    # ── Identity / auth ────────────────────────────────────────────────────
    USER_INVITED = "user.invited"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    USER_LOGIN = "user.login"
    USER_LOGIN_FAILED = "user.login_failed"

    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    API_KEY_USED = "api_key.used"

    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_SUSPENDED = "tenant.suspended"
    TENANT_DELETED = "tenant.deleted"

    # ── Data lifecycle ──────────────────────────────────────────────────────
    DOCUMENT_INGESTED = "document.ingested"
    EXTRACTION_RUN = "extraction.run"
    KG_NODE_CREATED = "kg.node_created"
    KG_NODE_UPDATED = "kg.node_updated"
    KG_NODE_DELETED = "kg.node_deleted"

    # ── OIDC ────────────────────────────────────────────────────────────────
    OIDC_LOGIN = "oidc.login"
    OIDC_LOGIN_FAILED = "oidc.login_failed"

    # ── Model registry ──────────────────────────────────────────────────────
    MODEL_REGISTERED = "model.registered"
    MODEL_PROMOTED = "model.promoted"
    MODEL_DEPRECATED = "model.deprecated"
    MODEL_EVALUATED = "model.evaluated"

    # ── Feature flags ───────────────────────────────────────────────────────
    FEATURE_FLAG_CREATED = "feature_flag.created"
    FEATURE_FLAG_UPDATED = "feature_flag.updated"
    FEATURE_FLAG_DELETED = "feature_flag.deleted"

    # ── Agent / workflow ────────────────────────────────────────────────────
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    BUSINESS_CASE_GENERATED = "business_case.generated"
    ROI_CALCULATED = "roi.calculated"
    EXPORT_REQUESTED = "export.requested"
    EXPORT_PACKAGE_GENERATED = "export.package_generated"
    EXPORT_DOWNLOAD_ACCESSED = "export.download_accessed"

    # ── Integrations ─────────────────────────────────────────────────────────
    WEBHOOK_RECEIVED = "webhook.received"
    WEBHOOK_PROCESSING_FAILED = "webhook.processing_failed"


class AuditOutcome(str, Enum):
    """Outcome of the audited action."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class AuditEvent(BaseModel):
    """Immutable audit record.

    Fields mirror the ``audit_events`` DB table column-for-column so that
    the emitter can serialize directly to SQL without any transformation.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique event ID")
    tenant_id: Optional[UUID] = Field(None, description="Owning tenant (None for platform actions)")
    user_id: Optional[str] = Field(None, description="Acting user")
    api_key_id: Optional[str] = Field(None, description="API key used, if any")
    action: AuditAction
    resource_type: Optional[str] = Field(None, description="e.g. 'Tenant', 'User', 'Workflow'")
    resource_id: Optional[str] = Field(None, description="Primary key of the affected resource")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    details: Dict[str, Any] = Field(default_factory=dict, description="Action-specific metadata")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(use_enum_values=True)
