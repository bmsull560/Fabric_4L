"""Add crawl_path to scraping_targets and create crawl_decisions table.

Revision ID: 005
Revises: 004
Create Date: 2026-04-19
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add crawl_path column and create crawl_decisions table."""
    # Create CrawlPath enum type
    crawlpath_enum = sa.Enum("fast", "browser", "fast_fallback", name="crawlpath")
    crawlpath_enum.create(op.get_bind(), checkfirst=True)

    # Add crawl_path column to scraping_targets with safe default
    op.add_column(
        "scraping_targets",
        sa.Column(
            "crawl_path",
            sa.Enum("fast", "browser", "fast_fallback", name="crawlpath"),
            nullable=False,
            server_default="browser",  # Safe default: existing targets use browser
        ),
    )

    # Create crawl_decisions table
    op.create_table(
        "crawl_decisions",
        sa.Column("decision_id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scraping_jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False, index=True),
        sa.Column("requested_path", sa.String(20), nullable=False),
        sa.Column("router_decision", sa.String(20), nullable=False),
        sa.Column("router_rule", sa.String(50), nullable=False, index=True),
        sa.Column("quality_passed", sa.Boolean(), nullable=True),
        sa.Column("quality_checks", JSONB(), nullable=True),
        sa.Column("fallback_reason", sa.String(50), nullable=True, index=True),
        sa.Column("final_path", sa.String(20), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("fast_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("browser_duration_ms", sa.Integer(), nullable=True),
        sa.Column("fetch_time_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bytes_transferred", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spa_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("text_length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_type", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Create composite indexes for common query patterns
    op.create_index(
        "idx_crawl_decisions_job_created",
        "crawl_decisions",
        ["job_id", "created_at"],
    )
    op.create_index(
        "idx_crawl_decisions_domain_created",
        "crawl_decisions",
        ["domain", "created_at"],
    )

    # Add comments for documentation
    op.execute("""
        COMMENT ON TABLE crawl_decisions IS 
        'Canonical record of crawl routing decisions for Smart Router observability';
    """)
    op.execute("""
        COMMENT ON COLUMN crawl_decisions.requested_path IS 
        'Target-level crawl mode: fast, browser, or fast_fallback';
    """)
    op.execute("""
        COMMENT ON COLUMN crawl_decisions.router_decision IS 
        'Path chosen by SmartRouter based on URL analysis';
    """)
    op.execute("""
        COMMENT ON COLUMN crawl_decisions.final_path IS 
        'Actual execution path including any fallback that occurred';
    """)

    # Enable RLS on new table (consistent with other tables)
    op.execute("ALTER TABLE crawl_decisions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE crawl_decisions FORCE ROW LEVEL SECURITY")

    # Create RLS policy for crawl_decisions
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON crawl_decisions
            FOR ALL
            TO PUBLIC
            USING (
                tenant_id IS NULL OR
                tenant_id::text = current_setting('app.tenant_id', true)
            )
            WITH CHECK (
                tenant_id IS NULL OR
                tenant_id::text = current_setting('app.tenant_id', true)
            )
    """)

    # Create admin bypass policy
    op.execute("""
        CREATE POLICY admin_bypass_policy ON crawl_decisions
            FOR ALL
            TO admin_role, system_role
            USING (current_setting('app.tenant_id', true) = '')
    """)


def downgrade() -> None:
    """Remove crawl_path column and crawl_decisions table."""
    # Drop RLS policies first
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON crawl_decisions")
    op.execute("DROP POLICY IF EXISTS admin_bypass_policy ON crawl_decisions")
    op.execute("ALTER TABLE crawl_decisions NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE crawl_decisions DISABLE ROW LEVEL SECURITY")

    # Drop indexes
    op.drop_index("idx_crawl_decisions_job_created", table_name="crawl_decisions")
    op.drop_index("idx_crawl_decisions_domain_created", table_name="crawl_decisions")

    # Drop crawl_decisions table
    op.drop_table("crawl_decisions")

    # Drop crawl_path column from scraping_targets
    op.drop_column("scraping_targets", "crawl_path")

    # Drop CrawlPath enum
    crawlpath_enum = sa.Enum("fast", "browser", "fast_fallback", name="crawlpath")
    crawlpath_enum.drop(op.get_bind(), checkfirst=True)
