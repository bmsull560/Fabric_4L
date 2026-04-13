"""SQLAlchemy ORM model for FeatureFlag."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class FeatureFlag(Base):
    """A tenant-scoped or platform-wide feature flag."""

    __tablename__ = "feature_flags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        comment="Owning tenant (NULL for platform-wide flags)",
    )

    flag_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Feature flag identifier",
    )

    enabled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    rollout_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Percentage of users that should see the feature (0-100)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
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

    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "flag_key", name="uix_feature_flag_tenant_key"),
        Index("ix_feature_flags_tenant_id", "tenant_id"),
        Index("ix_feature_flags_flag_key", "flag_key"),
    )

    def __repr__(self) -> str:
        return f"<FeatureFlag(id={self.id}, key={self.flag_key!r}, enabled={self.enabled})>"
