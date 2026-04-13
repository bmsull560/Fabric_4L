"""SQLAlchemy model for persistent API keys.

Persists what was previously stored only in L3's in-memory APIKeyManager,
adding tenant_id scoping, issuing user, and HMAC-SHA256 key hashing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...database import Base


class APIKey(Base):
    """A long-lived credential granting API access for a tenant.

    Key hash is stored using HMAC-SHA256 with the server secret
    (``API_KEY_HMAC_SECRET`` env var).  The raw key is shown exactly once
    at creation time and is never stored.
    """

    __tablename__ = "api_keys"

    key_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="vf_<uuid> format identifier",
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="Owning tenant",
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Issuing user (null for system/automation keys)",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable key name",
    )

    # HMAC-SHA256(API_KEY_HMAC_SECRET, raw_key) — 64-char hex
    key_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="HMAC-SHA256 digest of the raw API key",
    )

    prefix: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="First 12 chars of raw key for identification in UI",
    )

    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Canonical role from shared.identity.permissions.Role",
    )

    # Optional per-key permission overrides (stored as list of permission strings)
    permissions: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Explicit permission overrides (null → inherit from role)",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    rate_limit_per_minute: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Per-key override (null → inherit from tenant settings)",
    )

    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
    )

    __table_args__ = (
        Index("ix_api_keys_tenant_id", "tenant_id"),
        Index("ix_api_keys_key_hash", "key_hash"),
        Index("ix_api_keys_tenant_enabled", "tenant_id", "enabled"),
    )

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self) -> str:
        return f"<APIKey(key_id={self.key_id!r}, tenant={self.tenant_id}, role={self.role!r})>"
