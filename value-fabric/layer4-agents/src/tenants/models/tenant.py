"""SQLAlchemy model for Tenant."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...database import Base


class TenantStatus(str, Enum):
    """Tenant lifecycle status with transition validation."""

    PENDING = "pending"  # Initial state after registration
    ACTIVE = "active"    # Fully operational
    SUSPENDED = "suspended"  # Access blocked but data preserved
    DELETED = "deleted"  # Soft-deleted (purged after retention period)


# Valid status transitions
# Format: {current_status: {allowed_next_statuses}}
VALID_STATUS_TRANSITIONS = {
    TenantStatus.PENDING: {TenantStatus.ACTIVE, TenantStatus.DELETED},
    TenantStatus.ACTIVE: {TenantStatus.SUSPENDED, TenantStatus.DELETED},
    TenantStatus.SUSPENDED: {TenantStatus.ACTIVE, TenantStatus.DELETED},
    TenantStatus.DELETED: set(),  # Terminal state - no transitions allowed
}


class IsolationTier(str, Enum):
    """Tenant data isolation tiers for future-proofing (Task 4.1).

    Tiers:
    - SHARED: Shared schema with RLS (current implementation)
    - SCHEMA: Dedicated schema per tenant (future)
    - DATABASE: Dedicated database per tenant (future)
    """

    SHARED = "shared"
    SCHEMA = "schema"
    DATABASE = "database"


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validate if a status transition is allowed.

    Args:
        current_status: Current tenant status
        new_status: Requested new status

    Returns:
        True if transition is valid, False otherwise
    """
    try:
        current = TenantStatus(current_status)
        new = TenantStatus(new_status)
    except ValueError:
        return False

    return new in VALID_STATUS_TRANSITIONS.get(current, set())


class Tenant(Base):
    """A customer organisation that owns its own isolated data partition.

    All other governance tables (User, APIKey) and all content tables
    (accounts, KG nodes, etc.) reference ``tenant_id`` pointing here.
    """

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Internal tenant UUID",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Display name (e.g. 'Acme Corp')",
    )

    slug: Mapped[str] = mapped_column(
        String(63),
        nullable=False,
        unique=True,
        comment="URL-safe unique identifier (lowercase kebab-case)",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TenantStatus.PENDING.value,
        comment="Lifecycle status: pending | active | suspended | deleted",
    )

    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {"isolation_tier": IsolationTier.SHARED.value},
        comment="Tenant-level configuration blob (rate limits, feature flags, isolation_tier, etc.)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationship to tier history (Task 4.1)
    tier_history: Mapped[list["TenantIsolationTierHistory"]] = relationship(
        "TenantIsolationTierHistory",
        back_populates="tenant",
        order_by="desc(TenantIsolationTierHistory.changed_at)",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("slug", name="uix_tenant_slug"),
        Index("ix_tenants_status", "status"),
        Index("ix_tenants_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, slug={self.slug!r}, status={self.status!r})>"

    # -------------------------------------------------------------------------
    # Status lifecycle methods
    # -------------------------------------------------------------------------

    def is_active(self) -> bool:
        """Check if tenant is active and can be accessed."""
        return self.status == TenantStatus.ACTIVE.value

    def is_suspended(self) -> bool:
        """Check if tenant is suspended."""
        return self.status == TenantStatus.SUSPENDED.value

    def is_deleted(self) -> bool:
        """Check if tenant is soft-deleted."""
        return self.status == TenantStatus.DELETED.value

    def is_pending(self) -> bool:
        """Check if tenant is pending provisioning."""
        return self.status == TenantStatus.PENDING.value

    def can_transition_to(self, new_status: str) -> bool:
        """Check if transition to new_status is valid."""
        return validate_status_transition(self.status, new_status)

    def transition_status(self, new_status: str) -> bool:
        """Attempt to transition to new status.

        Args:
            new_status: Target status

        Returns:
            True if transition was successful, False if invalid
        """
        if not self.can_transition_to(new_status):
            return False
        self.status = new_status
        self.updated_at = datetime.now(UTC)
        return True

    def activate(self) -> bool:
        """Activate tenant (pending -> active or suspended -> active)."""
        return self.transition_status(TenantStatus.ACTIVE.value)

    def suspend(self) -> bool:
        """Suspend tenant (active -> suspended)."""
        return self.transition_status(TenantStatus.SUSPENDED.value)

    def mark_deleted(self) -> bool:
        """Soft-delete tenant."""
        return self.transition_status(TenantStatus.DELETED.value)
