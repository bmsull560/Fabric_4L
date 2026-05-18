"""Add harness_claim_validation_results table for persisting per-claim validation outcomes.

Enables GET /harness/runs/{run_id}/validation to return stored results without
re-running validation. Linked to harness_runs via FK with CASCADE delete.

Revision ID: 034
Revises: 033
Create Date: 2026-05-18
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "034"
down_revision: Union[str, None] = "033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "harness_claim_validation_results"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("claim_id", sa.String(255), nullable=False),
        sa.Column("validation_state", sa.String(32), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("validator", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["harness_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_harness_cvr_run_tenant", _TABLE, ["run_id", "tenant_id"])
    op.create_index("ix_harness_cvr_tenant_state", _TABLE, ["tenant_id", "validation_state"])
    op.create_index("ix_harness_cvr_claim_id", _TABLE, ["claim_id"])

    # RLS — same pattern as migration 031
    op.execute(f"ALTER TABLE {_TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_TABLE} FORCE ROW LEVEL SECURITY")

    op.execute(f"""
        CREATE POLICY tenant_isolation_policy ON {_TABLE}
            FOR ALL
            TO PUBLIC
            USING (
                tenant_id::text = current_setting('app.tenant_id', true)
            )
            WITH CHECK (
                tenant_id::text = current_setting('app.tenant_id', true)
            )
    """)

    op.execute(f"""
        CREATE POLICY admin_bypass_policy ON {_TABLE}
            FOR ALL
            TO admin_role, system_role
            USING (current_setting('app.tenant_id', true) = '')
            WITH CHECK (current_setting('app.tenant_id', true) = '')
    """)


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS admin_bypass_policy ON {_TABLE}")
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {_TABLE}")
    op.drop_index("ix_harness_cvr_claim_id", table_name=_TABLE)
    op.drop_index("ix_harness_cvr_tenant_state", table_name=_TABLE)
    op.drop_index("ix_harness_cvr_run_tenant", table_name=_TABLE)
    op.drop_table(_TABLE)
