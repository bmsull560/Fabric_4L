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
    op.execute(
        "ALTER TABLE scraping_targets ADD COLUMN IF NOT EXISTS source_category VARCHAR(50)"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'scraping_targets'
                  AND column_name = 'tenant_id'
            ) THEN
                EXECUTE 'CREATE INDEX IF NOT EXISTS idx_scraping_targets_tenant_source_category ON scraping_targets (tenant_id, source_category)';
            ELSE
                EXECUTE 'CREATE INDEX IF NOT EXISTS idx_scraping_targets_org_source_category ON scraping_targets (organization_id, source_category)';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Remove source_category column from scraping_targets."""
    op.drop_index("idx_scraping_targets_tenant_source_category", table_name="scraping_targets", if_exists=True)
    op.drop_index("idx_scraping_targets_org_source_category", table_name="scraping_targets", if_exists=True)
    op.drop_column("scraping_targets", "source_category")
