"""SQLAlchemy models for account-scoped review requests and gates.

Provides persistence for the review/gate workflow that the frontend
exposes via ReviewQueuePage and account-gate UIs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ReviewStatus(str, PyEnum):
    """Lifecycle states for a review request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ReviewScope(str, PyEnum):
    """What kind of artifact is under review."""

    BUSINESS_CASE = "business_case"
    VALUE_MODEL = "value_model"
    NARRATIVE = "narrative"
    HYPOTHESIS = "hypothesis"


class ReviewRequest(Base):
    """Account-scoped review request with comments.

    Mirrors the frontend's ReviewRequest shape so that
    GET /accounts/{id}/reviews can be served directly.
    """

    __tablename__ = "review_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Account scoping
    account_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="External account identifier (matches CRM provider_record_id or internal UUID)",
    )

    tenant_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="default", index=True,
        comment="Tenant identifier for RLS isolation",
    )

    # Request metadata
    requester_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="User ID who created the review",
    )
    reviewer_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Assigned reviewer user ID",
    )

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ReviewStatus.PENDING.value,
        comment="Current review status",
    )
    scope: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ReviewScope.BUSINESS_CASE.value,
        comment="What is being reviewed",
    )
    target_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="ID of the artifact under review (business_case_id, etc.)",
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When the review reached a terminal state (approved/rejected)",
    )

    # Comments stored as JSONB array
    comments: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list,
        comment="Embedded comments: [{id, author_id, text, created_at}]",
    )

    __table_args__ = (
        Index("ix_reviews_account_tenant", "account_id", "tenant_id", "status"),
        Index("ix_reviews_target", "target_id", "scope"),
        Index("ix_reviews_status", "status", "created_at"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to frontend-compatible shape."""
        return {
            "id": str(self.id),
            "account_id": self.account_id,
            "tenant_id": self.tenant_id,
            "requester_id": self.requester_id,
            "reviewer_id": self.reviewer_id,
            "status": self.status,
            "scope": self.scope,
            "target_id": self.target_id,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    def __repr__(self) -> str:
        return f"<ReviewRequest(id={self.id}, account={self.account_id}, status={self.status})>"
