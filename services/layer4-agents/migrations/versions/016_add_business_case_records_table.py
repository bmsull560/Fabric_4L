"""Add durable business_case_records table for account-case linkage.

Revision ID: 016
Revises: 015
Create Date: 2026-04-23
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create business_case_records table."""
    op.create_table(
        "business_case_records",
        sa.Column("case_id", sa.String(length=100), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", sa.String(length=100), nullable=False),
        sa.Column("opportunity_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("document_url", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("case_id"),
    )
    op.create_index(
        "ix_business_case_records_account_id",
        "business_case_records",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_business_case_records_workflow_id",
        "business_case_records",
        ["workflow_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop business_case_records table."""
    op.drop_index("ix_business_case_records_workflow_id", table_name="business_case_records")
    op.drop_index("ix_business_case_records_account_id", table_name="business_case_records")
    op.drop_table("business_case_records")

