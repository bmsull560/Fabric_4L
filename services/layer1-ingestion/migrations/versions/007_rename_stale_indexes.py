"""Rename stale organization_id indexes to tenant_id.

Revision ID: 007
Revises: 006
Create Date: 2026-04-30

Renames auto-generated indexes and constraints that still reference
organization_id/org after column rename in 006.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table_name, old_index_name, new_index_name)
INDEX_RENAMES = [
    ("compliance_logs", "ix_compliance_logs_organization_id", "ix_compliance_logs_tenant_id"),
    ("crawl_queue", "ix_crawl_queue_organization_id", "ix_crawl_queue_tenant_id"),
    ("extracted_data", "ix_extracted_data_organization_id", "ix_extracted_data_tenant_id"),
    ("job_errors", "ix_job_errors_organization_id", "ix_job_errors_tenant_id"),
    ("job_stage_details", "ix_job_stage_details_organization_id", "ix_job_stage_details_tenant_id"),
    ("proxy_pools", "ix_proxy_pools_organization_id", "ix_proxy_pools_tenant_id"),
    ("raw_content", "ix_raw_content_organization_id", "ix_raw_content_tenant_id"),
    ("scraping_jobs", "ix_scraping_jobs_organization_id", "ix_scraping_jobs_tenant_id"),
    ("scraping_targets", "ix_scraping_targets_organization_id", "ix_scraping_targets_tenant_id"),
]

# (table_name, old_constraint_name, new_constraint_name)
CONSTRAINT_RENAMES = [
    ("proxy_pools", "uq_proxy_pool_org_name", "uq_proxy_pool_tenant_name"),
]


def upgrade() -> None:
    """Rename indexes and constraints to match tenant_id naming."""
    for table_name, old_name, new_name in INDEX_RENAMES:
        op.execute(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"')

    for table_name, old_name, new_name in CONSTRAINT_RENAMES:
        op.execute(f'ALTER TABLE "{table_name}" RENAME CONSTRAINT "{old_name}" TO "{new_name}"')


def downgrade() -> None:
    """Revert names back to organization_id variants."""
    for table_name, old_name, new_name in INDEX_RENAMES:
        op.execute(f'ALTER INDEX "{new_name}" RENAME TO "{old_name}"')

    for table_name, old_name, new_name in CONSTRAINT_RENAMES:
        op.execute(f'ALTER TABLE "{table_name}" RENAME CONSTRAINT "{new_name}" TO "{old_name}"')
