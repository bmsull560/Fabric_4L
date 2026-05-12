"""Initial Ground Truth schema — four tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

Creates:
  - truth_objects      (TruthObject — central fact record)
  - truth_sources      (TruthSource — evidence records)
  - validation_events  (ValidationEvent — immutable audit log)
  - maturity_history   (MaturityHistory — maturity ladder log)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # truth_objects
    # ------------------------------------------------------------------
    op.create_table(
        "truth_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(64), nullable=False, server_default="other"),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="extracted"),
        sa.Column("maturity_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("freshness", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_stale", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("applies_to", postgresql.JSONB(), nullable=True),
        sa.Column("dispute_reason", sa.String(64), nullable=True),
        sa.Column("dispute_notes", sa.Text(), nullable=True),
        sa.Column("disputed_by", sa.String(255), nullable=True),
        sa.Column("disputed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kg_node_id", sa.String(255), nullable=True),
        sa.Column("kg_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extraction_job_id", sa.String(255), nullable=True),
        sa.Column("extraction_model", sa.String(128), nullable=True),
        sa.Column("raw_extraction_data", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for truth_objects
    op.create_index("ix_truth_objects_org_id", "truth_objects", ["organization_id"])
    op.create_index("ix_truth_objects_status", "truth_objects", ["status"])
    op.create_index("ix_truth_objects_kg_node_id", "truth_objects", ["kg_node_id"])
    op.create_index(
        "ix_truth_objects_extraction_job_id", "truth_objects", ["extraction_job_id"]
    )
    op.create_index(
        "ix_truth_objects_org_status", "truth_objects", ["organization_id", "status"]
    )
    op.create_index(
        "ix_truth_objects_org_claim_type",
        "truth_objects",
        ["organization_id", "claim_type"],
    )
    op.create_index(
        "ix_truth_objects_org_maturity",
        "truth_objects",
        ["organization_id", "maturity_level"],
    )
    op.create_index(
        "ix_truth_objects_active", "truth_objects", ["organization_id", "deleted_at"]
    )
    op.create_index(
        "ix_truth_objects_applies_to",
        "truth_objects",
        ["applies_to"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_truth_objects_value",
        "truth_objects",
        ["value"],
        postgresql_using="gin",
    )

    # ------------------------------------------------------------------
    # truth_sources
    # ------------------------------------------------------------------
    op.create_table(
        "truth_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "truth_object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("truth_objects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False, server_default="other"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("source_title", sa.String(512), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("excerpt_location", sa.String(255), nullable=True),
        sa.Column(
            "confidence_contribution", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("source_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
    )

    op.create_index(
        "ix_truth_sources_truth_object_id", "truth_sources", ["truth_object_id"]
    )
    op.create_index("ix_truth_sources_org_id", "truth_sources", ["organization_id"])
    op.create_index("ix_truth_sources_source_id", "truth_sources", ["source_id"])
    op.create_index(
        "ix_truth_sources_org_type", "truth_sources", ["organization_id", "source_type"]
    )

    # ------------------------------------------------------------------
    # validation_events
    # ------------------------------------------------------------------
    op.create_table(
        "validation_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "truth_object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("truth_objects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("from_maturity", sa.Integer(), nullable=True),
        sa.Column("to_maturity", sa.Integer(), nullable=False),
        sa.Column("actor", sa.String(255), nullable=True),
        sa.Column("actor_type", sa.String(32), nullable=False, server_default="system"),
        sa.Column("confidence_at_transition", sa.Float(), nullable=True),
        sa.Column("source_count_at_transition", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index(
        "ix_validation_events_truth_object_id", "validation_events", ["truth_object_id"]
    )
    op.create_index(
        "ix_validation_events_org_id", "validation_events", ["organization_id"]
    )
    op.create_index(
        "ix_validation_events_created_at", "validation_events", ["created_at"]
    )
    op.create_index(
        "ix_validation_events_org_status",
        "validation_events",
        ["organization_id", "to_status"],
    )
    op.create_index("ix_validation_events_actor", "validation_events", ["actor"])

    # ------------------------------------------------------------------
    # maturity_history
    # ------------------------------------------------------------------
    op.create_table(
        "maturity_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "truth_object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("truth_objects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_level", sa.Integer(), nullable=True),
        sa.Column("to_level", sa.Integer(), nullable=False),
        sa.Column("trigger", sa.String(128), nullable=True),
        sa.Column("triggered_by", sa.String(255), nullable=True),
        sa.Column("context", postgresql.JSONB(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index(
        "ix_maturity_history_truth_object_id", "maturity_history", ["truth_object_id"]
    )
    op.create_index(
        "ix_maturity_history_org_id", "maturity_history", ["organization_id"]
    )
    op.create_index(
        "ix_maturity_history_recorded_at", "maturity_history", ["recorded_at"]
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("maturity_history")
    op.drop_table("validation_events")
    op.drop_table("truth_sources")
    op.drop_table("truth_objects")
