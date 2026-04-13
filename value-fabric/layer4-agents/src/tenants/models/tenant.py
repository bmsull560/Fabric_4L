"""SQLAlchemy model for Tenant."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...database import Base


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

    settings: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Tenant-level configuration blob (rate limits, feature flags, etc.)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("slug", name="uix_tenant_slug"),
        Index("ix_tenants_status", "status"),
        Index("ix_tenants_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, slug={self.slug!r}, status={self.status!r})>"
