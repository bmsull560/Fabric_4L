"""Initial baseline schema for Layer 4 Agents.

Revision ID: 20260101_0000
Revises:
Create Date: 2026-01-01

Creates all tables for Layer 4 operational data:
- Tenant governance (tenants, users, api_keys, isolation_tier_history)
- CRM accounts (accounts, account_sync_status)
- Billing (billing_customers, billing_subscriptions, billing_webhook_events, billing_usage_events, billing_invoices, billing_invoice_items, billing_charges)
- Integrations (integrations)

All tables include tenant_id for multi-tenant isolation via RLS.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260101_0000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all Layer 4 tables with indexes and constraints."""
    
    # -------------------------------------------------------------------------
    # Tenant Governance Tables
    # -------------------------------------------------------------------------
    
    # tenants
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False, comment="Display name (e.g. 'Acme Corp')"),
        sa.Column('slug', sa.String(63), nullable=False, unique=True, comment="URL-safe unique identifier"),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'pending'"), comment="Lifecycle status"),
        sa.Column('settings', sa.JSON(), nullable=False, server_default=sa.text("'{\"isolation_tier\": \"shared\"}'::json"), comment="Tenant configuration"),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('status_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status_reason', sa.Text(), nullable=True),
        sa.Column('status_changed_by', sa.String(255), nullable=True),
    )
    op.create_index('ix_tenants_status', 'tenants', ['status'])
    op.create_index('ix_tenants_created_at', 'tenants', ['created_at'])
    
    # users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(320), nullable=False, comment="Email address (unique per tenant)"),
        sa.Column('hashed_password', sa.String(72), nullable=True, comment="bcrypt hash"),
        sa.Column('display_name', sa.String(200), nullable=True),
        sa.Column('role', sa.String(30), nullable=False, server_default=sa.text("'analyst'")),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'invited'")),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_status', 'users', ['status'])
    op.create_index('ix_users_tenant_status', 'users', ['tenant_id', 'status'])
    op.create_unique_constraint('uix_user_tenant_email', 'users', ['tenant_id', 'email'])
    
    # api_keys
    op.create_table(
        'api_keys',
        sa.Column('key_id', sa.String(64), primary_key=True, comment="vf_<uuid> format identifier"),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(100), nullable=False, comment="Human-readable key name"),
        sa.Column('key_hash', sa.String(64), nullable=False, unique=True, comment="HMAC-SHA256 digest"),
        sa.Column('prefix', sa.String(16), nullable=False, comment="First 12 chars of raw key"),
        sa.Column('role', sa.String(30), nullable=False, comment="Canonical role"),
        sa.Column('permissions', sa.JSON(), nullable=True, comment="Permission overrides"),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
    )
    op.create_index('ix_api_keys_tenant_id', 'api_keys', ['tenant_id'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('ix_api_keys_tenant_enabled', 'api_keys', ['tenant_id', 'enabled'])
    
    # tenant_isolation_tier_history
    op.create_table(
        'tenant_isolation_tier_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_tier', sa.String(50), nullable=True),
        sa.Column('to_tier', sa.String(50), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('changed_by', sa.String(255), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
    )
    op.create_index('ix_tier_history_tenant_changed', 'tenant_isolation_tier_history', ['tenant_id', 'changed_at'])
    
    # -------------------------------------------------------------------------
    # CRM Account Tables
    # -------------------------------------------------------------------------
    
    # accounts
    op.create_table(
        'accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider', sa.String(20), nullable=False, comment="Source CRM: salesforce or hubspot"),
        sa.Column('provider_record_id', sa.String(100), nullable=False, comment="Original ID from CRM"),
        sa.Column('name', sa.String(255), nullable=False, comment="Company name as displayed"),
        sa.Column('normalized_name', sa.String(255), nullable=True, comment="Lowercase, stripped name"),
        sa.Column('domain', sa.String(255), nullable=True, comment="Primary company domain"),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('company_size', sa.Integer(), nullable=True, comment="Employee count"),
        sa.Column('annual_revenue', sa.Float(), nullable=True, comment="Annual revenue in USD"),
        sa.Column('headquarters', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('owner_id', sa.String(100), nullable=True, comment="CRM owner/user ID"),
        sa.Column('owner_name', sa.String(255), nullable=True),
        sa.Column('owner_email', sa.String(255), nullable=True),
        sa.Column('stage', sa.String(50), nullable=True),
        sa.Column('segment', sa.String(100), nullable=True),
        sa.Column('employees', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('raw_crm_data', sa.JSON(), nullable=True, comment="Full provider payload"),
        sa.Column('tenant_id', sa.String(100), nullable=False, server_default=sa.text("'default'"), comment="Tenant identifier for RLS"),
        sa.Column('opportunities', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json"), comment="Embedded opportunities"),
        sa.Column('contacts', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json"), comment="Embedded contacts"),
        sa.Column('enrichment_status', sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('enriched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('enrichment_sources', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column('tech_stack', sa.JSON(), nullable=True),
        sa.Column('executives', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column('financials', sa.JSON(), nullable=True),
        sa.Column('competitive_landscape', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column('pain_signals', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.create_index('ix_accounts_provider', 'accounts', ['provider'])
    op.create_index('ix_accounts_sync_status', 'accounts', ['sync_status'])
    op.create_index('ix_accounts_name', 'accounts', ['name'])
    op.create_index('ix_accounts_domain', 'accounts', ['domain'])
    op.create_index('ix_accounts_owner_id', 'accounts', ['owner_id'])
    op.create_index('ix_accounts_last_synced_at', 'accounts', ['last_synced_at'])
    op.create_index('ix_accounts_region', 'accounts', ['region'])
    op.create_index('ix_accounts_segment', 'accounts', ['segment'])
    op.create_index('ix_accounts_provider_sync_updated', 'accounts', ['provider', 'sync_status', 'updated_at'])
    op.create_index('ix_accounts_enrichment_status', 'accounts', ['enrichment_status'])
    op.create_index('ix_accounts_tenant_id', 'accounts', ['tenant_id'])
    op.create_unique_constraint('uix_account_tenant_provider_record', 'accounts', ['tenant_id', 'provider', 'provider_record_id'])
    
    # account_sync_status
    op.create_table(
        'account_sync_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(100), nullable=False, server_default=sa.text("'default'")),
        sa.Column('provider', sa.String(20), nullable=False, comment="CRM provider"),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('records_synced', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('records_updated', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('records_failed', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'idle'")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_sync_status_tenant_provider', 'account_sync_status', ['tenant_id', 'provider', 'status'])
    op.create_unique_constraint('uix_sync_status_tenant_provider', 'account_sync_status', ['tenant_id', 'provider'])
    
    # -------------------------------------------------------------------------
    # Billing Tables
    # -------------------------------------------------------------------------
    
    # billing_customers
    op.create_table(
        'billing_customers',
        sa.Column('id', sa.String(100), primary_key=True, comment="App user_id"),
        sa.Column('tenant_id', sa.String(255), nullable=True, index=True),
        sa.Column('stripe_customer_id', sa.String(100), unique=True, nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_billing_customers_stripe_id', 'billing_customers', ['stripe_customer_id'])
    op.create_index('ix_billing_customers_tenant', 'billing_customers', ['tenant_id'])
    op.create_unique_constraint('uq_billing_customers_tenant_id', 'billing_customers', ['tenant_id', 'id'])
    
    # billing_subscriptions
    op.create_table(
        'billing_subscriptions',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('tenant_id', sa.String(255), nullable=True, index=True),
        sa.Column('customer_id', sa.String(100), sa.ForeignKey('billing_customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(100), unique=True, nullable=True),
        sa.Column('plan_id', sa.String(50), nullable=False, server_default=sa.text("'free'")),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'incomplete'")),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_billing_subscriptions_customer', 'billing_subscriptions', ['customer_id'])
    op.create_index('ix_billing_subscriptions_status', 'billing_subscriptions', ['status'])
    op.create_index('ix_billing_subscriptions_plan', 'billing_subscriptions', ['plan_id'])
    op.create_index('ix_billing_subscriptions_tenant', 'billing_subscriptions', ['tenant_id'])
    
    # billing_webhook_events
    op.create_table(
        'billing_webhook_events',
        sa.Column('id', sa.String(100), primary_key=True, comment="Stripe event ID"),
        sa.Column('tenant_id', sa.String(255), nullable=True, index=True),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_billing_webhook_events_type', 'billing_webhook_events', ['type'])
    op.create_index('ix_billing_webhook_events_processed', 'billing_webhook_events', ['processed_at'])
    op.create_index('ix_billing_webhook_events_tenant', 'billing_webhook_events', ['tenant_id'])
    
    # billing_usage_events
    op.create_table(
        'billing_usage_events',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('event_name', sa.String(100), nullable=False, index=True),
        sa.Column('metric_name', sa.String(100), nullable=False, index=True),
        sa.Column('quantity', sa.Float(), nullable=False, server_default=sa.text('1.0')),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'pending'"), index=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_billing_usage_events_tenant_event', 'billing_usage_events', ['tenant_id', 'event_id'])
    op.create_index('ix_billing_usage_events_customer_timestamp', 'billing_usage_events', ['customer_id', 'timestamp'])
    op.create_index('ix_billing_usage_events_status_created', 'billing_usage_events', ['status', 'created_at'])
    
    # billing_invoices
    op.create_table(
        'billing_invoices',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('stripe_invoice_id', sa.String(100), nullable=True, index=True),
        sa.Column('subscription_id', sa.String(100), nullable=True, index=True),
        sa.Column('invoice_number', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default=sa.text("'draft'")),
        sa.Column('currency', sa.String(3), nullable=False, server_default=sa.text("'USD'")),
        sa.Column('subtotal', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('tax', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('total', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('amount_paid', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('amount_due', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('balance', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False, index=True, server_default=sa.text('NOW()')),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False, index=True, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('footer', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('hosted_invoice_url', sa.Text(), nullable=True),
        sa.Column('invoice_pdf_url', sa.Text(), nullable=True),
    )
    op.create_unique_constraint('uq_billing_invoices_tenant_number', 'billing_invoices', ['tenant_id', 'invoice_number'])
    op.create_index('ix_billing_invoices_tenant_status', 'billing_invoices', ['tenant_id', 'status'])
    op.create_index('ix_billing_invoices_tenant_period', 'billing_invoices', ['tenant_id', 'period_start', 'period_end'])
    op.create_index('ix_billing_invoices_created', 'billing_invoices', ['created_at'])
    
    # billing_invoice_items
    op.create_table(
        'billing_invoice_items',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('invoice_id', sa.String(100), sa.ForeignKey('billing_invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('stripe_invoice_item_id', sa.String(100), nullable=True, index=True),
        sa.Column('subscription_item_id', sa.String(100), nullable=True),
        sa.Column('price_id', sa.String(100), nullable=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=20, scale=8), nullable=False, server_default=sa.text('1.0')),
        sa.Column('unit_amount', sa.BigInteger(), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_quantity', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('usage_metric', sa.String(100), nullable=True),
        sa.Column('tax_amount', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('discount_amount', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_billing_invoice_items_invoice', 'billing_invoice_items', ['invoice_id', 'created_at'])
    op.create_index('ix_billing_invoice_items_type', 'billing_invoice_items', ['tenant_id', 'type'])
    
    # billing_charges
    op.create_table(
        'billing_charges',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('invoice_id', sa.String(100), sa.ForeignKey('billing_invoices.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('stripe_charge_id', sa.String(100), nullable=True, index=True),
        sa.Column('stripe_payment_intent_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default=sa.text("'pending'")),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default=sa.text("'USD'")),
        sa.Column('amount_refunded', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('payment_method_id', sa.String(100), nullable=True),
        sa.Column('payment_method_type', sa.String(50), nullable=True),
        sa.Column('payment_method_details', postgresql.JSONB(), nullable=True),
        sa.Column('failure_code', sa.String(100), nullable=True),
        sa.Column('failure_message', sa.Text(), nullable=True),
        sa.Column('decline_code', sa.String(100), nullable=True),
        sa.Column('receipt_url', sa.Text(), nullable=True),
        sa.Column('receipt_number', sa.String(100), nullable=True),
        sa.Column('disputed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('dispute_reason', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_billing_charges_tenant_status', 'billing_charges', ['tenant_id', 'status'])
    op.create_index('ix_billing_charges_tenant_created', 'billing_charges', ['tenant_id', 'created_at'])
    op.create_index('ix_billing_charges_stripe_id', 'billing_charges', ['stripe_charge_id'])
    
    # -------------------------------------------------------------------------
    # Integration Tables
    # -------------------------------------------------------------------------
    
    # integrations
    op.create_table(
        'integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('provider', sa.String(50), nullable=False, comment="CRM provider"),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('credentials_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.LargeBinary(), nullable=True),
        sa.Column('encryption_key_id', sa.String(255), nullable=False),
        sa.Column('salesforce_org_id', sa.String(50), nullable=True),
        sa.Column('instance_url', sa.String(500), nullable=True),
        sa.Column('sync_interval_minutes', sa.Integer(), nullable=False, server_default=sa.text('60')),
        sa.Column('sync_batch_size', sa.Integer(), nullable=False, server_default=sa.text('100')),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('records_synced', sa.Integer(), server_default=sa.text('0')),
        sa.Column('records_updated', sa.Integer(), server_default=sa.text('0')),
        sa.Column('records_failed', sa.Integer(), server_default=sa.text('0')),
        sa.Column('sync_status', sa.String(50), server_default=sa.text("'idle'"), nullable=False),
        sa.Column('last_error_message', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
    )
    op.create_unique_constraint('uq_integration_tenant_provider', 'integrations', ['tenant_id', 'provider'])


def downgrade() -> None:
    """Drop all Layer 4 tables in reverse order of creation."""
    
    # Integration tables
    op.drop_table('integrations')
    
    # Billing tables
    op.drop_table('billing_charges')
    op.drop_table('billing_invoice_items')
    op.drop_table('billing_invoices')
    op.drop_table('billing_usage_events')
    op.drop_table('billing_webhook_events')
    op.drop_table('billing_subscriptions')
    op.drop_table('billing_customers')
    
    # Account tables
    op.drop_table('account_sync_status')
    op.drop_table('accounts')
    
    # Tenant governance tables
    op.drop_table('tenant_isolation_tier_history')
    op.drop_table('api_keys')
    op.drop_table('users')
    op.drop_table('tenants')
