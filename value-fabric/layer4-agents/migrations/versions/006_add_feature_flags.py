"""Add feature_flags table.

Revision ID: 006
Revises: 005
Create Date: 2026-04-13
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_flags",
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
            nullable=True,
            comment="Owning tenant (NULL for platform-wide flags)",
        ),
        sa.Column("flag_key", sa.String(255), nullable=False, comment="Feature flag identifier"),
        sa.Column("enabled", sa.Boolean, nullable=False, default=False, server_default="false"),
        sa.Column(
            "rollout_percentage",
            sa.Integer,
            nullable=False,
            default=0,
            server_default="0",
            comment="Percentage of users that should see the feature (0-100)",
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
            comment="Arbitrary key-value metadata for the flag",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("tenant_id", "flag_key", name="uix_feature_flag_tenant_key"),
    )
    op.create_index("ix_feature_flags_tenant_id", "feature_flags", ["tenant_id"])
    op.create_index("ix_feature_flags_flag_key", "feature_flags", ["flag_key"])


def downgrade() -> None:
    op.drop_index("ix_feature_flags_flag_key", table_name="feature_flags")
    op.drop_index("ix_feature_flags_tenant_id", table_name="feature_flags")
    op.drop_table("feature_flags")
