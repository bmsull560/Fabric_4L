"""Fix NULL-permissive RLS policies introduced after migration 026.

Revision ID: 033
Revises: 032
Create Date: 2026-05-17

SECURITY FIX: Three migration groups created tables with the unsafe pattern:

    USING (tenant_id IS NULL OR tenant_id::text = current_setting(...))

This allows any row inserted without a tenant_id to be visible to ALL tenants.
Migration 026 fixed the original 007/013 tables; migration 028 fixed the 027
batch. This migration closes the remaining gaps:

  - Billing tables (025): billing_charges, billing_customers,
    billing_invoice_items, billing_invoices, billing_subscriptions,
    billing_usage_events, billing_webhook_events
  - Company knowledge tables (029): company_knowledge_profiles, icp_profiles,
    knowledge_sources, value_extraction_records
  - CRM sync jobs (030): crm_sync_jobs

The fix replaces the USING clause with strict matching only:

    USING (tenant_id::text = current_setting('app.tenant_id', true))

Rows with NULL tenant_id become invisible to tenant-scoped queries and are
only accessible via the existing admin_bypass_policy (admin_role, system_role
with empty app.tenant_id setting).
"""

from collections.abc import Sequence
from typing import Union

from alembic import op


revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Billing tables from migration 025 — NULL-leaky policy never superseded.
BILLING_TABLES = [
    "billing_charges",
    "billing_customers",
    "billing_invoice_items",
    "billing_invoices",
    "billing_subscriptions",
    "billing_usage_events",
    "billing_webhook_events",
]

# Company knowledge tables from migration 029 — created after 028 ran.
COMPANY_KNOWLEDGE_TABLES = [
    "company_knowledge_profiles",
    "icp_profiles",
    "knowledge_sources",
    "value_extraction_records",
]

# CRM sync jobs from migration 030.
CRM_TABLES = [
    "crm_sync_jobs",
]

# Canonical list used by the RLS enforcement test scanner.
# Must be a literal list (not an expression) so the regex-based scanner in
# tests/security/test_rls_enforcement.py can parse it.
RLS_TABLES = [
    "billing_charges",
    "billing_customers",
    "billing_invoice_items",
    "billing_invoices",
    "billing_subscriptions",
    "billing_usage_events",
    "billing_webhook_events",
    "company_knowledge_profiles",
    "icp_profiles",
    "knowledge_sources",
    "value_extraction_records",
    "crm_sync_jobs",
]

ALL_TABLES = BILLING_TABLES + COMPANY_KNOWLEDGE_TABLES + CRM_TABLES


def upgrade() -> None:
    """Replace NULL-permissive tenant_isolation_policy with strict matching."""
    for table in ALL_TABLES:
        op.execute(
            f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}"
        )
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


def downgrade() -> None:
    """Revert to NULL-permissive policies for tables owned exclusively by 033.

    Tables already fixed by migration 032 (billing_customers,
    billing_subscriptions, billing_webhook_events, crm_sync_jobs) are
    intentionally excluded: reverting them here would leave the database at
    revision 032 with pre-032 leaky RLS on those tables.
    """
    # Only the tables that 033 exclusively introduced — not the 4 tables
    # that 032 already fixed and whose downgrade is 032's responsibility.
    _033_ONLY_TABLES = [
        t for t in ALL_TABLES
        if t not in {
            "billing_customers",
            "billing_subscriptions",
            "billing_webhook_events",
            "crm_sync_jobs",
        }
    ]
    for table in _033_ONLY_TABLES:
        op.execute(
            f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}"
        )
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
