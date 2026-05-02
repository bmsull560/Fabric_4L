"""Add model registry tables.

Revision ID: 005
Revises: 004
Create Date: 2026-04-13
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column(
            "stage",
            sa.String(20),
            nullable=False,
            server_default="dev",
            comment="One of: dev, staging, production, deprecated",
        ),
        sa.Column(
            "promoted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("eval_score", sa.Float, nullable=True),
        sa.Column("eval_run_id", sa.String(100), nullable=True),
        sa.Column("config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index("ix_model_versions_tenant_id", "model_versions", ["tenant_id"])
    op.create_index("ix_model_versions_stage", "model_versions", ["stage"])
    op.create_index(
        "ix_model_versions_tenant_provider_stage",
        "model_versions",
        ["tenant_id", "provider", "stage"],
    )

    op.create_table(
        "model_promotion_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "model_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("model_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_stage", sa.String(20), nullable=False),
        sa.Column("to_stage", sa.String(20), nullable=False),
        sa.Column(
            "promoted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("eval_score", sa.Float, nullable=True),
        sa.Column("eval_gate_passed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index(
        "ix_model_promotion_log_model_version_id",
        "model_promotion_log",
        ["model_version_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_model_promotion_log_model_version_id",
        table_name="model_promotion_log",
    )
    op.drop_table("model_promotion_log")

    op.drop_index("ix_model_versions_tenant_provider_stage", table_name="model_versions")
    op.drop_index("ix_model_versions_stage", table_name="model_versions")
    op.drop_index("ix_model_versions_tenant_id", table_name="model_versions")
    op.drop_table("model_versions")
