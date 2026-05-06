"""SQLAlchemy models for Layer 2 PostgreSQL persistence.

Currently includes only the pending_ingestions table for retry durability.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for Layer 2 SQLAlchemy models."""
    pass


class PendingIngestion(Base):
    """Durable pending ingestion record for Layer 2 -> Layer 3 retries.

    Stores extraction results that need to be retried due to transient failures
    in Layer 3 knowledge graph ingestion.
    """

    __tablename__ = "pending_ingestions"

    job_id: Mapped[str] = mapped_column(String(255), primary_key=True, comment="Unique job identifier")
    source_url: Mapped[str] = mapped_column(Text, nullable=False, comment="Source document URL")
    extraction_result_json: Mapped[str] = mapped_column(
        Text, nullable=False, comment="JSON serialization of extraction result"
    )
    relationships_json: Mapped[str] = mapped_column(Text, nullable=False, comment="JSON serialization of relationships")
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of retry attempts"
    )
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, comment="Maximum retry attempts allowed")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Last error message")
    next_retry_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="When to retry next"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("idx_pending_ingestions_next_retry", "next_retry_at"),
    )

    def __repr__(self) -> str:
        return f"<PendingIngestion(job_id={self.job_id}, retry_count={self.retry_count})>"
