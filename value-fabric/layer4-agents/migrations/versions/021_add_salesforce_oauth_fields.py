"""Add Salesforce OAuth fields to integrations table.

Revision ID: 021
Revises: 020_tenant_safe_crm_sync_constraints
Create Date: 2026-05-01

This migration adds fields required for Salesforce OAuth:
- refresh_token_encrypted: encrypted OAuth refresh token
- salesforce_org_id: Salesforce organization ID

It also adds a partial index for active Salesforce integrations
to speed up tenant sweep queries.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add refresh_token_encrypted for OAuth token rotation
    op.add_column(
        "integrations",
        sa.Column("refresh_token_encrypted", sa.LargeBinary(), nullable=True),
    )

    # Add salesforce_org_id for org identification and deduplication
    op.add_column(
        "integrations",
        sa.Column("salesforce_org_id", sa.String(50), nullable=True),
    )

    # Index for active Salesforce integrations (speeds up scheduler sweep)
    op.create_index(
        "ix_integrations_salesforce_active",
        "integrations",
        ["tenant_id", "provider", "enabled"],
        unique=False,
        postgresql_where=sa.text("provider = 'salesforce' AND enabled = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_integrations_salesforce_active", table_name="integrations")
    op.drop_column("integrations", "salesforce_org_id")
    op.drop_column("integrations", "refresh_token_encrypted")
