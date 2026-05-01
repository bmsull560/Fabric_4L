"""Rename organization_id to tenant_id in Layer 1 tables.

Revision ID: 006
Revises: 005_add_crawl_path_and_decisions
Create Date: 2026-04-23

This migration normalizes column naming across the codebase, changing
`organization_id` to `tenant_id` for consistency with Layer 4 tenant model.

Affected tables:
- scraping_targets
- scraping_jobs
- job_stage_details
- job_errors
- raw_content
- extracted_data
- compliance_logs
- proxy_pools
- robots_txt_cache
- crawl_queue
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Rename organization_id columns to tenant_id."""
    tables_and_indexes = [
        # (table_name, list_of_index_names_to_drop_and_recreate)
        ("scraping_targets", [
            "idx_scraping_targets_org_status",
            "idx_scraping_targets_created",
        ]),
        ("scraping_jobs", [
            "idx_scraping_jobs_org_status",
        ]),
        ("job_stage_details", []),
        ("job_errors", [
            "idx_job_errors_job_occurred",
            "idx_job_errors_retryable",
        ]),
        ("raw_content", [
            "idx_raw_content_org_domain",
            "idx_raw_content_hash",
        ]),
        ("extracted_data", [
            "idx_extracted_data_org_quality",
        ]),
        ("compliance_logs", [
            "idx_compliance_logs_org_event",
        ]),
        ("proxy_pools", [
            "idx_proxy_pools_org",
        ]),
        ("robots_txt_cache", [
            "idx_robots_txt_cache_org",
        ]),
        ("crawl_queue", [
            "uq_crawl_queue_org_job_url",  # unique constraint — handled separately
            "idx_crawl_queue_org_job_status",
        ]),
    ]

    for table_name, index_names in tables_and_indexes:
        # Drop indexes/constraints first
        for index_name in index_names:
            if index_name == "uq_crawl_queue_org_job_url":
                op.drop_constraint(index_name, table_name=table_name, type_="unique")
            else:
                op.drop_index(index_name, table_name=table_name)

        # Rename column
        op.alter_column(
            table_name,
            "organization_id",
            new_column_name="tenant_id",
            existing_type=postgresql.UUID(as_uuid=True),
            existing_nullable=False,
        )

    # Recreate indexes with updated column names
    # scraping_targets
    op.create_index(
        "idx_scraping_targets_tenant_status",
        "scraping_targets",
        ["tenant_id", "status"],
    )
    op.create_index(
        "idx_scraping_targets_created",
        "scraping_targets",
        ["tenant_id", "created_at"],
    )

    # scraping_jobs
    op.create_index(
        "idx_scraping_jobs_tenant_status",
        "scraping_jobs",
        ["tenant_id", "status"],
    )

    # job_errors
    op.create_index(
        "idx_job_errors_job_occurred",
        "job_errors",
        ["job_id", "occurred_at"],
    )
    op.create_index(
        "idx_job_errors_retryable",
        "job_errors",
        ["retryable", "retry_count"],
    )

    # raw_content
    op.create_index(
        "idx_raw_content_tenant_domain",
        "raw_content",
        ["tenant_id", "source_domain"],
    )
    op.create_index(
        "idx_raw_content_hash",
        "raw_content",
        ["tenant_id", "content_hash"],
    )

    # extracted_data
    op.create_index(
        "idx_extracted_data_tenant_quality",
        "extracted_data",
        ["tenant_id", "validation_data_quality_score"],
    )

    # compliance_logs
    op.create_index(
        "idx_compliance_logs_tenant_event",
        "compliance_logs",
        ["tenant_id", "event_type"],
    )

    # proxy_pools
    op.create_index(
        "idx_proxy_pools_tenant",
        "proxy_pools",
        ["tenant_id", "created_at"],
    )

    # robots_txt_cache
    op.create_index(
        "idx_robots_txt_cache_tenant",
        "robots_txt_cache",
        ["tenant_id", "domain"],
    )

    # crawl_queue
    op.create_index(
        "uq_crawl_queue_tenant_job_url",
        "crawl_queue",
        ["tenant_id", "job_id", "url"],
        unique=True,
    )
    op.create_index(
        "idx_crawl_queue_tenant_job_status",
        "crawl_queue",
        ["tenant_id", "job_id", "status"],
    )


def downgrade():
    """Revert tenant_id columns back to organization_id."""
    tables_and_indexes = [
        ("scraping_targets", [
            "idx_scraping_targets_tenant_status",
            "idx_scraping_targets_created",
        ]),
        ("scraping_jobs", [
            "idx_scraping_jobs_tenant_status",
        ]),
        ("job_stage_details", []),
        ("job_errors", [
            "idx_job_errors_job_occurred",
            "idx_job_errors_retryable",
        ]),
        ("raw_content", [
            "idx_raw_content_tenant_domain",
            "idx_raw_content_hash",
        ]),
        ("extracted_data", [
            "idx_extracted_data_tenant_quality",
        ]),
        ("compliance_logs", [
            "idx_compliance_logs_tenant_event",
        ]),
        ("proxy_pools", [
            "idx_proxy_pools_tenant",
        ]),
        ("robots_txt_cache", [
            "idx_robots_txt_cache_tenant",
        ]),
        ("crawl_queue", [
            "uq_crawl_queue_tenant_job_url",  # unique constraint — handled separately
            "idx_crawl_queue_tenant_job_status",
        ]),
    ]

    for table_name, index_names in tables_and_indexes:
        # Drop indexes/constraints first
        for index_name in index_names:
            if index_name == "uq_crawl_queue_tenant_job_url":
                op.drop_constraint(index_name, table_name=table_name, type_="unique")
            else:
                op.drop_index(index_name, table_name=table_name)

        # Rename column back
        op.alter_column(
            table_name,
            "tenant_id",
            new_column_name="organization_id",
            existing_type=postgresql.UUID(as_uuid=True),
            existing_nullable=False,
        )

    # Recreate original indexes
    op.create_index(
        "idx_scraping_targets_org_status",
        "scraping_targets",
        ["organization_id", "status"],
    )
    op.create_index(
        "idx_scraping_targets_created",
        "scraping_targets",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "idx_scraping_jobs_org_status",
        "scraping_jobs",
        ["organization_id", "status"],
    )
    op.create_index(
        "idx_job_errors_job_occurred",
        "job_errors",
        ["job_id", "occurred_at"],
    )
    op.create_index(
        "idx_job_errors_retryable",
        "job_errors",
        ["retryable", "retry_count"],
    )
    op.create_index(
        "idx_raw_content_org_domain",
        "raw_content",
        ["organization_id", "source_domain"],
    )
    op.create_index(
        "idx_raw_content_hash",
        "raw_content",
        ["organization_id", "content_hash"],
    )
    op.create_index(
        "idx_extracted_data_org_quality",
        "extracted_data",
        ["organization_id", "validation_data_quality_score"],
    )
    op.create_index(
        "idx_compliance_logs_org_event",
        "compliance_logs",
        ["organization_id", "event_type"],
    )
    op.create_index(
        "idx_proxy_pools_org",
        "proxy_pools",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "idx_robots_txt_cache_org",
        "robots_txt_cache",
        ["organization_id", "domain"],
    )
    op.create_index(
        "uq_crawl_queue_org_job_url",
        "crawl_queue",
        ["organization_id", "job_id", "url"],
        unique=True,
    )
    op.create_index(
        "idx_crawl_queue_org_job_status",
        "crawl_queue",
        ["organization_id", "job_id", "status"],
    )
