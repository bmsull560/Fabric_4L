"""SQLAlchemy ORM models for the Model Registry."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ModelVersion(Base):
    """A registered model version for a tenant."""

    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Model provider, e.g. openai, anthropic",
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Canonical model name",
    )

    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Version tag or identifier",
    )

    stage: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="dev",
        comment="One of: dev, staging, production, deprecated",
    )

    promoted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    eval_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Latest evaluation score",
    )

    eval_run_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Model-specific configuration blob",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_model_versions_tenant_id", "tenant_id"),
        Index("ix_model_versions_stage", "stage"),
        Index("ix_model_versions_tenant_provider_stage", "tenant_id", "provider", "stage"),
    )

    def __repr__(self) -> str:
        return (
            f"<ModelVersion(id={self.id}, provider={self.provider!r}, "
            f"model={self.model_name!r}, stage={self.stage!r})>"
        )


class ModelPromotionLog(Base):
    """Audit trail for model stage transitions."""

    __tablename__ = "model_promotion_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    model_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("model_versions.id", ondelete="CASCADE"),
        nullable=False,
    )

    from_stage: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    to_stage: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    promoted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    eval_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    eval_gate_passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_model_promotion_log_model_version_id", "model_version_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ModelPromotionLog(model_version_id={self.model_version_id}, "
            f"{self.from_stage!r} -> {self.to_stage!r})>"
        )
