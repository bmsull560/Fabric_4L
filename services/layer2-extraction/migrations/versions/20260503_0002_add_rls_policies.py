"""Add Row-Level Security (RLS) policies for tenant isolation.

Revision ID: 20260503_0002
Revises: 20250418_0001
Create Date: 2026-05-03

Enables RLS on all Layer 2 tables that carry tenant_id and adds
policies enforcing current_setting('app.tenant_id') isolation.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260503_0002"
down_revision: Union[str, None] = "20250418_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables that carry tenant_id directly
_TENANT_TABLES = [
    "ontology_types",
    "ontology_relationships",
    "ontology_schema_versions",
]


def upgrade() -> None:
    for table in _TENANT_TABLES:
        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

        # Tenant isolation policy — rows visible only when tenant_id matches session var
        op.execute(
            f"CREATE POLICY {table}_tenant_isolation ON {table} "
            f"USING (tenant_id = current_setting('app.tenant_id', true))"
        )

    # ontology_properties inherits isolation through its FK to ontology_types,
    # but we add RLS for defence-in-depth via a join check.
    op.execute("ALTER TABLE ontology_properties ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE ontology_properties FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY ontology_properties_tenant_isolation "
        "ON ontology_properties "
        "USING (EXISTS ("
        "  SELECT 1 FROM ontology_types "
        "  WHERE ontology_types.id = ontology_properties.type_id "
        "  AND ontology_types.tenant_id = current_setting('app.tenant_id', true)"
        "))"
    )


def downgrade() -> None:
    # Drop policies and disable RLS in reverse order
    op.execute(
        "DROP POLICY IF EXISTS ontology_properties_tenant_isolation "
        "ON ontology_properties"
    )
    op.execute("ALTER TABLE ontology_properties DISABLE ROW LEVEL SECURITY")

    for table in reversed(_TENANT_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
