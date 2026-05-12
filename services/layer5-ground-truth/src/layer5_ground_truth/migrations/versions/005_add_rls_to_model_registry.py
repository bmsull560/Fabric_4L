"""Add RLS policies to model registry tables.

Revision ID: 005
Revises: 004
Create Date: 2026-04-25

Model registry tables (model_versions, model_deployments, model_evaluations)
were added in migration 003 with tenant_id columns but without RLS policies.
This migration closes that gap (Phase 1, Task 1.6).

Note: The column rename from organization_id to tenant_id was handled in
migration 004.  The RLS policies here reference tenant_id.
"""

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

RLS_TABLES = [
    "model_versions",
    "model_deployments",
    "model_evaluations",
]


def upgrade() -> None:
    """Enable RLS and create tenant isolation policies on model registry tables."""
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

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

        op.execute(f"""
            CREATE POLICY admin_bypass_policy ON {table}
                FOR ALL
                TO admin_role, system_role
                USING (current_setting('app.tenant_id', true) = '')
        """)


def downgrade() -> None:
    """Remove RLS policies and disable RLS on model registry tables."""
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}")
        op.execute(f"DROP POLICY IF EXISTS admin_bypass_policy ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
