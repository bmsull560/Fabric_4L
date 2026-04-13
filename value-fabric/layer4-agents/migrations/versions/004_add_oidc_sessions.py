"""Add oidc_sessions table for SSO/OIDC state management.

Revision ID: 004
Revises: 003
Create Date: 2026-04-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "oidc_sessions",
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
        sa.Column("state", sa.String(256), nullable=False, unique=True),
        sa.Column("nonce", sa.String(256), nullable=False),
        sa.Column("redirect_uri", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.create_index("ix_oidc_sessions_tenant_id", "oidc_sessions", ["tenant_id"])
    op.create_index("ix_oidc_sessions_expires_at", "oidc_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_oidc_sessions_expires_at", table_name="oidc_sessions")
    op.drop_index("ix_oidc_sessions_tenant_id", table_name="oidc_sessions")
    op.drop_table("oidc_sessions")
