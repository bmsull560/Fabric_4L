"""Add PKCE support to OIDC sessions (P0-10).

Revision ID: 008
Revises: 007
Create Date: 2026-04-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add code_verifier column for PKCE support."""
    op.add_column(
        "oidc_sessions",
        sa.Column("code_verifier", sa.String(256), nullable=True)
    )
    # Add use_pkce flag to track which sessions use PKCE
    op.add_column(
        "oidc_sessions",
        sa.Column("use_pkce", sa.Boolean, nullable=False, server_default="true")
    )


def downgrade() -> None:
    """Remove PKCE columns."""
    op.drop_column("oidc_sessions", "code_verifier")
    op.drop_column("oidc_sessions", "use_pkce")
