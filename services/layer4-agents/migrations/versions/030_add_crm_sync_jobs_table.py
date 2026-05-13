"""Add durable CRM sync jobs table.

Revision ID: 030
Revises: 029
Create Date: 2026-05-13
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crm_sync_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("requested_by", sa.String(length=255), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crm_sync_jobs_tenant_status", "crm_sync_jobs", ["tenant_id", "status"], unique=False)
    op.create_index("ix_crm_sync_jobs_tenant_provider", "crm_sync_jobs", ["tenant_id", "provider"], unique=False)
    op.create_index("ix_crm_sync_jobs_queued_at", "crm_sync_jobs", ["queued_at"], unique=False)

    op.execute("ALTER TABLE crm_sync_jobs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE crm_sync_jobs FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON crm_sync_jobs
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
        """
    )
    op.execute(
        """
        CREATE POLICY admin_bypass_policy ON crm_sync_jobs
            FOR ALL
            TO admin_role, system_role
            USING (current_setting('app.tenant_id', true) = '')
        """
    )


def downgrade() -> None:
    op.execute("REVOKE ALL ON crm_sync_jobs FROM admin_role, system_role")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON crm_sync_jobs")
    op.execute("DROP POLICY IF EXISTS admin_bypass_policy ON crm_sync_jobs")
    op.execute("ALTER TABLE crm_sync_jobs NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE crm_sync_jobs DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_crm_sync_jobs_queued_at", table_name="crm_sync_jobs")
    op.drop_index("ix_crm_sync_jobs_tenant_provider", table_name="crm_sync_jobs")
    op.drop_index("ix_crm_sync_jobs_tenant_status", table_name="crm_sync_jobs")
    op.drop_table("crm_sync_jobs")
