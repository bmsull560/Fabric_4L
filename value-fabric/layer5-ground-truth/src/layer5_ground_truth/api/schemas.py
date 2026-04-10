"""
Pydantic request/response schemas for the Layer 5 Ground Truth API.

Follows the same style as Layer 3's src/api/models.py:
  - Separate Request / Response models
  - Strict field validation with Field() descriptors
  - Enum imports from models (single source of truth)
"""

import uuid
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# Re-export enums so API consumers only need to import from schemas
from ..models.truth_object import (
    ClaimType,
    DisputeReason,
    MaturityLevel,
    SourceType,
    TruthStatus,
)

__all__ = [
    "ClaimType",
    "DisputeReason",
    "MaturityLevel",
    "SourceType",
    "TruthStatus",
    # Request models
    "TruthSourceCreate",
    "TruthObjectCreate",
    "ValidateRequest",
    "AddSourceRequest",
    # Response models
    "TruthSourceResponse",
    "ValidationEventResponse",
    "MaturityHistoryResponse",
    "TruthObjectResponse",
    "TruthObjectSummary",
    "TruthObjectListResponse",
    "ValidateResponse",
    "HealthResponse",
    "MaturityLadderResponse",
]


# ---------------------------------------------------------------------------
# Source schemas
# ---------------------------------------------------------------------------

class TruthSourceCreate(BaseModel):
    """Schema for creating a new TruthSource."""

    source_type: SourceType = Field(
        default=SourceType.OTHER,
        description="Category of evidence",
    )
    source_url: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="URL or URI of the source document",
    )
    source_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Internal document / asset ID",
    )
    source_title: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Human-readable title of the source",
    )
    excerpt: Optional[str] = Field(
        default=None,
        description="Verbatim excerpt supporting the claim",
    )
    excerpt_location: Optional[str] = Field(
        default=None,
        max_length=255,
        description='Location within source, e.g. "page 3, paragraph 2"',
    )
    confidence_contribution: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Contribution to overall confidence (0.0–1.0)",
    )
    source_date: Optional[datetime] = Field(
        default=None,
        description="Date the source was published or captured",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class TruthSourceResponse(TruthSourceCreate):
    """Schema for a TruthSource in API responses."""

    id: UUID
    truth_object_id: UUID
    organization_id: UUID
    created_at: datetime
    created_by: Optional[str] = None
    # Map from SQLAlchemy's extra_metadata column
    metadata: dict[str, Any] = Field(default_factory=dict, alias="extra_metadata")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator("metadata", mode="before")
    @classmethod
    def extract_metadata(cls, v: Any) -> dict[str, Any]:
        """Handle both dict values and SQLAlchemy MetaData objects."""
        if isinstance(v, dict):
            return v
        if v is None:
            return {}
        # Handle case where SQLAlchemy's MetaData is returned instead
        return {}


# ---------------------------------------------------------------------------
# Validation event schemas
# ---------------------------------------------------------------------------

class ValidationEventResponse(BaseModel):
    """Schema for a ValidationEvent in API responses."""

    id: UUID
    from_status: Optional[str] = None
    to_status: str
    from_maturity: Optional[int] = None
    to_maturity: int
    actor: Optional[str] = None
    actor_type: str
    confidence_at_transition: Optional[float] = None
    source_count_at_transition: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Maturity history schemas
# ---------------------------------------------------------------------------

class MaturityHistoryResponse(BaseModel):
    """Schema for a MaturityHistory entry in API responses."""

    id: UUID
    from_level: Optional[int] = None
    to_level: int
    trigger: Optional[str] = None
    triggered_by: Optional[str] = None
    context: Optional[dict[str, Any]] = None
    recorded_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# TruthObject create schema
# ---------------------------------------------------------------------------

class TruthObjectCreate(BaseModel):
    """
    Schema for POST /truths — create a new TruthObject.

    The organization_id is injected from the auth context in the router;
    it is not accepted from the request body.
    """

    claim: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description='Natural-language claim, e.g. "20 hrs/month reconciling invoices"',
        examples=["Manual reporting costs 12 hours/week per analyst"],
    )
    claim_type: ClaimType = Field(
        default=ClaimType.OTHER,
        description="Semantic category of the claim",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Extraction model confidence score",
        examples=[0.82],
    )
    value: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Structured value: {amount, unit, currency, period} "
            "e.g. {amount: 20, unit: 'hours', period: 'month'}"
        ),
        examples=[{"amount": 20, "unit": "hours", "period": "month"}],
    )
    applies_to: Optional[dict[str, Any]] = Field(
        default=None,
        description="Scope: {opportunity_id, account_id, industry, product_line, geography}",
        examples=[{"opportunity_id": "opp-123", "account_id": "acct-456"}],
    )
    extraction_job_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Layer 2 extraction job that produced this claim",
    )
    extraction_model: Optional[str] = Field(
        default=None,
        max_length=128,
        description="LLM / model version used for extraction",
    )
    raw_extraction_data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Original extraction payload for reproducibility",
    )
    sources: list[TruthSourceCreate] = Field(
        default_factory=list,
        description="Initial evidence sources (optional — can be added later via POST /truths/{id}/sources)",
    )

    @field_validator("claim")
    @classmethod
    def claim_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("claim must not be blank")
        return v.strip()


# ---------------------------------------------------------------------------
# TruthObject response schemas
# ---------------------------------------------------------------------------

class TruthObjectResponse(BaseModel):
    """
    Full TruthObject response including related sources and audit trail.
    """

    id: UUID
    organization_id: UUID
    claim: str
    claim_type: str
    value: Optional[dict[str, Any]] = None
    confidence: float
    status: str
    maturity_level: int
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    freshness: datetime
    expires_at: Optional[datetime] = None
    is_stale: bool
    applies_to: Optional[dict[str, Any]] = None
    dispute_reason: Optional[str] = None
    dispute_notes: Optional[str] = None
    disputed_by: Optional[str] = None
    disputed_at: Optional[datetime] = None
    kg_node_id: Optional[str] = None
    kg_synced_at: Optional[datetime] = None
    extraction_job_id: Optional[str] = None
    extraction_model: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Related records
    sources: list[TruthSourceResponse] = Field(default_factory=list)
    validation_events: list[ValidationEventResponse] = Field(default_factory=list)
    maturity_history: list[MaturityHistoryResponse] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat() if v else None,
        },
    }


class TruthObjectSummary(BaseModel):
    """Lightweight summary for list responses."""

    id: UUID
    claim: str
    claim_type: str
    confidence: float
    status: str
    maturity_level: int
    is_stale: bool
    source_count: int = 0
    approved_by: Optional[str] = None
    freshness: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class TruthObjectListResponse(BaseModel):
    """Paginated list of TruthObjects."""

    items: list[TruthObjectSummary]
    total: int
    limit: int
    offset: int
    has_more: bool


# ---------------------------------------------------------------------------
# Validate request/response
# ---------------------------------------------------------------------------

class ValidateRequest(BaseModel):
    """
    Schema for POST /truths/{id}/validate — trigger a state transition.

    action values:
      advance_supported     — EXTRACTED → SUPPORTED
      advance_corroborated  — SUPPORTED → CORROBORATED
      approve               — CORROBORATED → APPROVED (requires actor)
      dispute               — ANY → DISPUTED (requires dispute_reason)
      resolve_dispute       — DISPUTED → CORROBORATED
      operationalize        — APPROVED → maturity 5 (status stays APPROVED)
    """

    action: str = Field(
        ...,
        description=(
            "Transition to apply: advance_supported | advance_corroborated | "
            "approve | dispute | resolve_dispute | operationalize"
        ),
        examples=["approve"],
    )
    actor: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User ID or service name triggering the transition",
        examples=["john.doe@company.com"],
    )
    actor_type: str = Field(
        default="human",
        description="'human' | 'system' | 'agent'",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional notes for the audit trail",
    )
    dispute_reason: Optional[DisputeReason] = Field(
        default=None,
        description="Required when action == 'dispute'",
    )

    @model_validator(mode="after")
    def validate_dispute_fields(self) -> "ValidateRequest":
        if self.action == "dispute" and not self.dispute_reason:
            raise ValueError("dispute_reason is required when action is 'dispute'")
        return self


class ValidateResponse(BaseModel):
    """Response after a validation action."""

    truth_object_id: UUID
    previous_status: str
    new_status: str
    previous_maturity: int
    new_maturity: int
    actor: str
    transition_allowed: bool = True
    message: str


# ---------------------------------------------------------------------------
# Add source request
# ---------------------------------------------------------------------------

class AddSourceRequest(TruthSourceCreate):
    """Schema for POST /truths/{id}/sources."""
    pass


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: datetime
    database: str
    layer3_connected: bool
    layer3_url: str


# ---------------------------------------------------------------------------
# Maturity ladder reference
# ---------------------------------------------------------------------------

class MaturityLevelDetail(BaseModel):
    level: int
    name: str
    description: str
    required_status: str
    advancement_trigger: str


class MaturityLadderResponse(BaseModel):
    """Reference endpoint — returns the full maturity ladder definition."""
    levels: list[MaturityLevelDetail]
