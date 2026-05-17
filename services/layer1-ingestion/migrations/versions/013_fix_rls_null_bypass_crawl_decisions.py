"""Fix unsafe tenant_id IS NULL bypass in crawl_decisions RLS policy.

Revision ID: 013
Revises: 012
Create Date: 2026-05-17

Migration 005 created the crawl_decisions table with an RLS policy using:

    USING (tenant_id IS NULL OR tenant_id::text = current_setting(...))

The ``tenant_id IS NULL`` clause makes any row inserted without a tenant_id
visible to every tenant. Crawl decision records contain URL patterns and
routing metadata that could reveal a tenant's data sources to other tenants.

This migration replaces the policy with strict matching only:

    USING (tenant_id::text = current_setting('app.tenant_id', true))

Rows with NULL tenant_id become invisible to tenant-scoped queries and are
only accessible via the admin_bypass_policy (admin_role, system_role with
empty app.tenant_id). This matches the pattern established in Layer 4
migrations 026 and 028.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op


revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Canonical list used by the test scanner to identify RLS-covered tables.
# NOTE: Must be a literal list (not expression) so the regex-based
# test scanner can parse it.
RLS_TABLES = [
    "crawl_decisions",
]


def upgrade() -> None:
    """Replace NULL-permissive RLS policy with strict tenant matching."""
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON crawl_decisions")

    op.execute("ALTER TABLE crawl_decisions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE crawl_decisions FORCE ROW LEVEL SECURITY")

    op.execute("""
        CREATE POLICY tenant_isolation_policy ON crawl_decisions
            FOR ALL
            TO PUBLIC
            USING (
                tenant_id::text = current_setting('app.tenant_id', true)
            )
            WITH CHECK (
                tenant_id::text = current_setting('app.tenant_id', true)
            )
    """)


def downgrade() -> None:
    """Revert to NULL-permissive policy (restores the pre-fix state)."""
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON crawl_decisions")

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
