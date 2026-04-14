"""Add Row-Level Security (RLS) policies for tenant isolation (P0-07).

Revision ID: 004
Revises: 003
Create Date: 2026-04-13
"""

from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that have tenant_id and need RLS policies
RLS_TABLES = [
    "scraping_targets",
    "scraping_jobs",
    "raw_content",
    "extracted_data",
    "compliance_logs",
    "proxy_pools",
    "job_stage_details",
    "job_errors",
]


def upgrade() -> None:
    """Enable RLS and create policies for tenant isolation."""
    # Enable RLS on each table
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    # Create tenant isolation policy for each table
    # Uses current_setting('app.tenant_id') set by SET LOCAL
    for table in RLS_TABLES:
        # Tenant users can only see their own rows
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
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

    # Create bypass policy for admin/system operations
    # This allows operations when app.tenant_id is not set
    for table in RLS_TABLES:
        op.execute(f"""
            CREATE POLICY admin_bypass_policy ON {table}
                FOR ALL
                TO PUBLIC
                USING (current_setting('app.tenant_id', true) = '')
        """)


def downgrade() -> None:
    """Remove RLS policies and disable RLS."""
    # Drop policies first
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}")
        op.execute(f"DROP POLICY IF EXISTS admin_bypass_policy ON {table}")

    # Disable RLS
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
