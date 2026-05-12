"""Add company knowledge onboarding tables.

Revision ID: 029
Revises: 028
Create Date: 2026-05-07

Adds CompanyKnowledgeProfile, KnowledgeSource, ValueExtractionRecord,
and ICPProfile tables with tenant-scoped RLS policies.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that need RLS policies
RLS_TABLES = [
    "company_knowledge_profiles",
    "knowledge_sources",
    "value_extraction_records",
    "icp_profiles",
]


def upgrade() -> None:
    """Create company knowledge tables and enable RLS."""

    # ------------------------------------------------------------------
    # CompanyKnowledgeProfile
    # ------------------------------------------------------------------
    op.create_table(
        "company_knowledge_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("identity", sa.JSON(), nullable=True),
        sa.Column("product_catalog", sa.JSON(), nullable=True),
        sa.Column("target_customer", sa.JSON(), nullable=True),
        sa.Column("personas", sa.JSON(), nullable=True),
        sa.Column("use_cases", sa.JSON(), nullable=True),
        sa.Column("value_drivers", sa.JSON(), nullable=True),
        sa.Column("proof_points", sa.JSON(), nullable=True),
        sa.Column("trust_commercial", sa.JSON(), nullable=True),
        sa.Column("active_source_ids", sa.JSON(), nullable=False),
        sa.Column("review_status", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "company_name", "version",
            name="uix_ckp_tenant_name_version",
        ),
    )
    op.create_index(
        "ix_ckp_tenant_status", "company_knowledge_profiles",
        ["tenant_id", "status"], unique=False,
    )
    op.create_index(
        "ix_ckp_tenant_updated", "company_knowledge_profiles",
        ["tenant_id", "updated_at"], unique=False,
    )
    op.create_index(
        "ix_ckp_website", "company_knowledge_profiles",
        ["website"], unique=False,
    )

    # ------------------------------------------------------------------
    # KnowledgeSource
    # ------------------------------------------------------------------
    op.create_table(
        "knowledge_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column(
            "profile_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("document_name", sa.String(length=255), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("raw_storage_path", sa.Text(), nullable=True),
        sa.Column("crawl_status", sa.String(length=50), nullable=False),
        sa.Column("authority_weight", sa.String(length=20), nullable=False),
        sa.Column("page_type", sa.String(length=50), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["company_knowledge_profiles.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ks_tenant_profile", "knowledge_sources",
        ["tenant_id", "profile_id"], unique=False,
    )
    op.create_index(
        "ix_ks_tenant_type", "knowledge_sources",
        ["tenant_id", "source_type"], unique=False,
    )
    op.create_index(
        "ix_ks_crawl_status", "knowledge_sources",
        ["crawl_status"], unique=False,
    )
    op.create_index(
        "ix_ks_content_hash", "knowledge_sources",
        ["content_hash"], unique=False,
    )

    # ------------------------------------------------------------------
    # ValueExtractionRecord
    # ------------------------------------------------------------------
    op.create_table(
        "value_extraction_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column(
            "profile_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column("page_type", sa.String(length=50), nullable=True),
        sa.Column("extracted", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("review_status", sa.String(length=50), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extraction_version", sa.String(length=50), nullable=True),
        sa.Column("llm_model", sa.String(length=100), nullable=True),
        sa.Column("trace_span_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"], ["knowledge_sources.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["company_knowledge_profiles.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ver_tenant_profile", "value_extraction_records",
        ["tenant_id", "profile_id"], unique=False,
    )
    op.create_index(
        "ix_ver_tenant_review", "value_extraction_records",
        ["tenant_id", "review_status"], unique=False,
    )
    op.create_index(
        "ix_ver_confidence", "value_extraction_records",
        ["confidence"], unique=False,
    )
    op.create_index(
        "ix_ver_requires_review", "value_extraction_records",
        ["requires_review"], unique=False,
    )
    op.create_index(
        "ix_ver_source_id", "value_extraction_records",
        ["source_id"], unique=False,
    )

    # ------------------------------------------------------------------
    # ICPProfile
    # ------------------------------------------------------------------
    op.create_table(
        "icp_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column(
            "profile_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column("industries", sa.JSON(), nullable=False),
        sa.Column("company_size", sa.JSON(), nullable=False),
        sa.Column("buyer_personas", sa.JSON(), nullable=False),
        sa.Column("user_personas", sa.JSON(), nullable=False),
        sa.Column("pain_points", sa.JSON(), nullable=False),
        sa.Column("trigger_events", sa.JSON(), nullable=False),
        sa.Column("qualification_criteria", sa.JSON(), nullable=False),
        sa.Column("disqualification_criteria", sa.JSON(), nullable=False),
        sa.Column("competitive_context", sa.JSON(), nullable=True),
        sa.Column("buying_committee_structure", sa.JSON(), nullable=True),
        sa.Column("typical_sales_motion", sa.String(length=50), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["company_knowledge_profiles.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_icp_tenant_profile", "icp_profiles",
        ["tenant_id", "profile_id"], unique=False,
    )
    op.create_index(
        "ix_icp_tenant_source", "icp_profiles",
        ["tenant_id", "source_type"], unique=False,
    )

    # ------------------------------------------------------------------
    # RLS policies
    # ------------------------------------------------------------------
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    for table in RLS_TABLES:
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

    for table in RLS_TABLES:
        op.execute(f"""
            CREATE POLICY admin_bypass_policy ON {table}
                FOR ALL
                TO admin_role, system_role
                USING (current_setting('app.tenant_id', true) = '')
        """)


def downgrade() -> None:
    """Drop company knowledge tables and RLS policies."""

    # Drop RLS policies
    for table in RLS_TABLES:
        op.execute(f"REVOKE ALL ON {table} FROM admin_role, system_role")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}")
        op.execute(f"DROP POLICY IF EXISTS admin_bypass_policy ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # Drop tables (order matters because of FKs)
    op.drop_index("ix_icp_tenant_source", table_name="icp_profiles")
    op.drop_index("ix_icp_tenant_profile", table_name="icp_profiles")
    op.drop_table("icp_profiles")

    op.drop_index("ix_ver_source_id", table_name="value_extraction_records")
    op.drop_index("ix_ver_requires_review", table_name="value_extraction_records")
    op.drop_index("ix_ver_confidence", table_name="value_extraction_records")
    op.drop_index("ix_ver_tenant_review", table_name="value_extraction_records")
    op.drop_index("ix_ver_tenant_profile", table_name="value_extraction_records")
    op.drop_table("value_extraction_records")

    op.drop_index("ix_ks_content_hash", table_name="knowledge_sources")
    op.drop_index("ix_ks_crawl_status", table_name="knowledge_sources")
    op.drop_index("ix_ks_tenant_type", table_name="knowledge_sources")
    op.drop_index("ix_ks_tenant_profile", table_name="knowledge_sources")
    op.drop_table("knowledge_sources")

    op.drop_index("ix_ckp_website", table_name="company_knowledge_profiles")
    op.drop_index("ix_ckp_tenant_updated", table_name="company_knowledge_profiles")
    op.drop_index("ix_ckp_tenant_status", table_name="company_knowledge_profiles")
    op.drop_table("company_knowledge_profiles")
