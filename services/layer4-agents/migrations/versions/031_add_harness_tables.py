"""Add harness persistence tables for governed agentic workflow execution.

Creates five tables backing the Fabric Harness in-memory stores:
  harness_runs            — HarnessRun lifecycle
  harness_human_gates     — HumanGate approval gates
  harness_checkpoints     — deterministic state snapshots
  harness_tool_contracts  — tenant-scoped tool contract registry
  harness_trace_events    — structured telemetry events

All tables carry tenant_id with strict RLS policies matching the
Layer 4 convention established in migrations 007 and 028.

Revision ID: 031
Revises: 030
Create Date: 2026-05-16
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables created by this migration — order matters for FK dependencies
_TABLES_IN_ORDER = [
    "harness_runs",
    "harness_tool_contracts",
    "harness_human_gates",
    "harness_checkpoints",
    "harness_trace_events",
]

# Tables in reverse order for downgrade
_TABLES_IN_REVERSE = list(reversed(_TABLES_IN_ORDER))


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. harness_runs — no FK dependencies
    # ------------------------------------------------------------------ #
    op.create_table(
        "harness_runs",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("account_id", sa.String(255), nullable=True),
        sa.Column("workflow_type", sa.String(64), nullable=False),
        sa.Column("initiated_by", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("current_state", sa.String(32), nullable=False),
        sa.Column("value_pack_id", sa.String(255), nullable=True),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_harness_runs_tenant_status", "harness_runs", ["tenant_id", "status"])
    op.create_index("ix_harness_runs_tenant_state", "harness_runs", ["tenant_id", "current_state"])
    op.create_index("ix_harness_runs_trace_id", "harness_runs", ["trace_id"])

    # ------------------------------------------------------------------ #
    # 2. harness_tool_contracts — no FK dependencies
    # ------------------------------------------------------------------ #
    op.create_table(
        "harness_tool_contracts",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("tool_id", sa.String(255), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("layer", sa.String(32), nullable=False),
        sa.Column("version", sa.String(32), nullable=False, server_default="v1"),
        sa.Column("input_schema_ref", sa.String(255), nullable=False),
        sa.Column("output_schema_ref", sa.String(255), nullable=False),
        sa.Column("side_effect_class", sa.String(64), nullable=False),
        sa.Column("risk_level", sa.String(32), nullable=False),
        sa.Column("requires_tenant_context", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_account_context", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("approval_policy_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "tool_id", name="uq_harness_tool_contracts_tenant_tool"),
    )
    op.create_index("ix_harness_tool_contracts_tenant_layer", "harness_tool_contracts", ["tenant_id", "layer"])
    op.create_index("ix_harness_tool_contracts_tenant_risk", "harness_tool_contracts", ["tenant_id", "risk_level"])

    # ------------------------------------------------------------------ #
    # 3. harness_human_gates — FK → harness_runs
    # ------------------------------------------------------------------ #
    op.create_table(
        "harness_human_gates",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("gate_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("decision_by", sa.String(255), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["harness_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_harness_human_gates_run_tenant", "harness_human_gates", ["run_id", "tenant_id"])
    op.create_index("ix_harness_human_gates_tenant_status", "harness_human_gates", ["tenant_id", "status"])

    # ------------------------------------------------------------------ #
    # 4. harness_checkpoints — FK → harness_runs
    # ------------------------------------------------------------------ #
    op.create_table(
        "harness_checkpoints",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("state_name", sa.String(32), nullable=False),
        sa.Column("state_payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("output_hash", sa.String(64), nullable=True),
        sa.Column("tool_calls", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["harness_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_harness_checkpoints_run_tenant", "harness_checkpoints", ["run_id", "tenant_id"])
    op.create_index("ix_harness_checkpoints_tenant_state", "harness_checkpoints", ["tenant_id", "state_name"])
    op.create_index("ix_harness_checkpoints_input_hash", "harness_checkpoints", ["input_hash"])

    # ------------------------------------------------------------------ #
    # 5. harness_trace_events — FK → harness_runs
    # ------------------------------------------------------------------ #
    op.create_table(
        "harness_trace_events",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("account_id", sa.String(255), nullable=True),
        sa.Column("workflow_type", sa.String(64), nullable=False),
        sa.Column("from_state", sa.String(32), nullable=True),
        sa.Column("to_state", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=True),
        sa.Column("value_pack_id", sa.String(255), nullable=True),
        sa.Column("validation_state", sa.String(32), nullable=True),
        sa.Column("human_gate_id", sa.String(64), nullable=True),
        sa.Column("tool_contract_id", sa.String(64), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False, server_default="transition"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["harness_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_harness_trace_events_run_tenant", "harness_trace_events", ["run_id", "tenant_id"])
    op.create_index("ix_harness_trace_events_tenant_type", "harness_trace_events", ["tenant_id", "event_type"])
    op.create_index("ix_harness_trace_events_trace_id", "harness_trace_events", ["trace_id"])

    # ------------------------------------------------------------------ #
    # RLS — strict tenant isolation matching migration 028 pattern
    # ------------------------------------------------------------------ #
    for table in _TABLES_IN_ORDER:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
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
            CREATE POLICY admin_bypass_policy ON {table}
                FOR ALL
                TO admin_role, system_role
                USING (current_setting('app.tenant_id', true) = '')
                WITH CHECK (current_setting('app.tenant_id', true) = '')
        """)


def downgrade() -> None:
    # Drop RLS policies first, then tables in reverse dependency order
    for table in _TABLES_IN_REVERSE:
        op.execute(f"DROP POLICY IF EXISTS admin_bypass_policy ON {table}")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}")

    # harness_trace_events
    op.drop_index("ix_harness_trace_events_trace_id", table_name="harness_trace_events")
    op.drop_index("ix_harness_trace_events_tenant_type", table_name="harness_trace_events")
    op.drop_index("ix_harness_trace_events_run_tenant", table_name="harness_trace_events")
    op.drop_table("harness_trace_events")

    # harness_checkpoints
    op.drop_index("ix_harness_checkpoints_input_hash", table_name="harness_checkpoints")
    op.drop_index("ix_harness_checkpoints_tenant_state", table_name="harness_checkpoints")
    op.drop_index("ix_harness_checkpoints_run_tenant", table_name="harness_checkpoints")
    op.drop_table("harness_checkpoints")

    # harness_human_gates
    op.drop_index("ix_harness_human_gates_tenant_status", table_name="harness_human_gates")
    op.drop_index("ix_harness_human_gates_run_tenant", table_name="harness_human_gates")
    op.drop_table("harness_human_gates")

    # harness_tool_contracts
    op.drop_index("ix_harness_tool_contracts_tenant_risk", table_name="harness_tool_contracts")
    op.drop_index("ix_harness_tool_contracts_tenant_layer", table_name="harness_tool_contracts")
    op.drop_table("harness_tool_contracts")

    # harness_runs (last — other tables FK into it)
    op.drop_index("ix_harness_runs_trace_id", table_name="harness_runs")
    op.drop_index("ix_harness_runs_tenant_state", table_name="harness_runs")
    op.drop_index("ix_harness_runs_tenant_status", table_name="harness_runs")
    op.drop_table("harness_runs")
