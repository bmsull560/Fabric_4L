"""Add audit_events table (append-only audit trail).

Revision ID: 003
Revises: 002
Create Date: 2026-04-13

The table is intentionally append-only:
- No UPDATE statements are ever issued by application code.
- A DB trigger (below) blocks UPDATE/DELETE at the database level.
- Rows are retained for 7 years; archival to cold storage is handled
  outside Alembic (e.g., pg_partman or a scheduled export job).
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="SET NULL"),
            nullable=True,
            comment="Owning tenant (null for platform-level events)",
        ),
        sa.Column("user_id", sa.Text, nullable=True),
        sa.Column("api_key_id", sa.Text, nullable=True),
        sa.Column(
            "action",
            sa.String(100),
            nullable=False,
            comment="AuditAction enum value",
        ),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("request_id", sa.Text, nullable=True),
        sa.Column(
            "outcome",
            sa.String(20),
            nullable=False,
            server_default="success",
        ),
        sa.Column(
            "details",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index("ix_audit_tenant_id", "audit_events", ["tenant_id"])
    op.create_index("ix_audit_action", "audit_events", ["action"])
    op.create_index("ix_audit_timestamp", "audit_events", ["timestamp"])
    op.create_index(
        "ix_audit_tenant_timestamp",
        "audit_events",
        ["tenant_id", "timestamp"],
    )

    # ── Append-only enforcement trigger ──────────────────────────────────────
    # Blocks any UPDATE or DELETE on this table at the DB level.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_events_immutable()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_events rows are immutable — UPDATE and DELETE are not permitted.';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_events_immutable
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION audit_events_immutable();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_events_immutable ON audit_events;")
    op.execute("DROP FUNCTION IF EXISTS audit_events_immutable();")

    op.drop_index("ix_audit_tenant_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_action", table_name="audit_events")
    op.drop_index("ix_audit_tenant_id", table_name="audit_events")
    op.drop_table("audit_events")
