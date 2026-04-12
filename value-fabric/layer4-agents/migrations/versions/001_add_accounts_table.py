"""Add accounts and account_sync_status tables.

Revision ID: 001
Revises: 
Create Date: 2026-04-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create accounts table
    op.create_table(
        'accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('provider_record_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('normalized_name', sa.String(255), nullable=True),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('company_size', sa.Integer, nullable=True),
        sa.Column('annual_revenue', sa.Float, nullable=True),
        sa.Column('headquarters', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('owner_id', sa.String(100), nullable=True),
        sa.Column('owner_name', sa.String(255), nullable=True),
        sa.Column('owner_email', sa.String(255), nullable=True),
        sa.Column('stage', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('raw_crm_data', postgresql.JSONB, nullable=True),
        sa.Column('opportunities', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('contacts', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.UniqueConstraint('provider', 'provider_record_id', name='uix_account_provider_record'),
    )
    
    # Create indexes for accounts table
    op.create_index('ix_accounts_provider', 'accounts', ['provider'])
    op.create_index('ix_accounts_sync_status', 'accounts', ['sync_status'])
    op.create_index('ix_accounts_name', 'accounts', ['name'])
    op.create_index('ix_accounts_domain', 'accounts', ['domain'])
    op.create_index('ix_accounts_owner_id', 'accounts', ['owner_id'])
    op.create_index('ix_accounts_last_synced_at', 'accounts', ['last_synced_at'])
    op.create_index('ix_accounts_provider_sync_updated', 'accounts', ['provider', 'sync_status', 'updated_at'])
    
    # Create account_sync_status table
    op.create_table(
        'account_sync_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('provider', sa.String(20), nullable=False, unique=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('records_synced', sa.Integer, nullable=False, server_default='0'),
        sa.Column('records_updated', sa.Integer, nullable=False, server_default='0'),
        sa.Column('records_failed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='idle'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create index for sync status table
    op.create_index('ix_sync_status_provider', 'account_sync_status', ['provider', 'status'])


def downgrade() -> None:
    op.drop_index('ix_sync_status_provider', table_name='account_sync_status')
    op.drop_table('account_sync_status')
    
    op.drop_index('ix_accounts_provider_sync_updated', table_name='accounts')
    op.drop_index('ix_accounts_last_synced_at', table_name='accounts')
    op.drop_index('ix_accounts_owner_id', table_name='accounts')
    op.drop_index('ix_accounts_domain', table_name='accounts')
    op.drop_index('ix_accounts_name', table_name='accounts')
    op.drop_index('ix_accounts_sync_status', table_name='accounts')
    op.drop_index('ix_accounts_provider', table_name='accounts')
    op.drop_table('accounts')
