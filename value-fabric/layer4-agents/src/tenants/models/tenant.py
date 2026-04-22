"""SQLAlchemy model for Tenant."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...database import Base


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
        default="active",
        comment="Lifecycle status: active | suspended | deleted",
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
