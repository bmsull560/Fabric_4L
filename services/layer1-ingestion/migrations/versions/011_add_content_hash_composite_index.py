"""Add composite index on raw_content (tenant_id, content_hash) for deduplication queries.

Revision ID: 011
Revises: 010
Create Date: 2026-05-13

This migration adds a B-tree composite index to the raw_content table for the
tenant_id + content_hash combination, which is queried on every crawl for
duplicate detection. Without this index, the query performs a sequential scan
on the raw_content table, degrading linearly with table growth.

Related optimization: browser_crawl_stage now computes SHA256 hashes and queries
this index for deduplication on every job.
"""

from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Add composite index for deduplication queries."""
    op.create_index(
        "idx_raw_content_tenant_hash",
        "raw_content",
        ["tenant_id", "content_hash"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Remove composite index."""
    op.drop_index("idx_raw_content_tenant_hash", table_name="raw_content")
