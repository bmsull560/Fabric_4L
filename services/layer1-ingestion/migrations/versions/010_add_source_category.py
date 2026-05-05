"""Add source_category column to scraping_targets.

Revision ID: 010
Revises: 009
Create Date: 2026-05-05

This migration adds the source_category column to the scraping_targets table
to store the semantic category of the data source (e.g., crm, database, file,
api, cloud_storage) independently from the scraping method (target_type).

This eliminates brittle frontend inference based on tags and URL patterns.
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Add source_category column to scraping_targets."""
    op.add_column(
        "scraping_targets",
        sa.Column("source_category", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "idx_scraping_targets_org_source_category",
        "scraping_targets",
        ["organization_id", "source_category"],
    )


def downgrade() -> None:
    """Remove source_category column from scraping_targets."""
    op.drop_index(
        "idx_scraping_targets_org_source_category",
        table_name="scraping_targets",
    )
    op.drop_column("scraping_targets", "source_category")
