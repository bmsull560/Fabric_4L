"""Add integrations table for CRM provider configurations.

Revision ID: 010
Revises: 009
Create Date: 2026-04-16

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create integrations table for CRM configurations
    op.create_table(
        'integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),  # 'salesforce', 'hubspot'
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        
        # Encrypted credentials
        sa.Column('credentials_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('encryption_key_id', sa.String(255), nullable=False),
        
        # Configuration
        sa.Column('instance_url', sa.String(500), nullable=True),
        sa.Column('sync_interval_minutes', sa.Integer(), nullable=False, server_default=sa.text('60')),
        sa.Column('sync_batch_size', sa.Integer(), nullable=False, server_default=sa.text('100')),
        
        # Sync status (denormalized for quick reads)
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('records_synced', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('records_updated', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('records_failed', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('sync_status', sa.String(50), nullable=False, server_default='idle'),
        sa.Column('last_error_message', sa.String(1000), nullable=True),
        
        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        
        # Indexes
        sa.Index('ix_integrations_tenant_provider', 'tenant_id', 'provider', unique=True),
        sa.Index('ix_integrations_tenant', 'tenant_id'),
        sa.Index('ix_integrations_provider', 'provider'),
        sa.Index('ix_integrations_status', 'sync_status'),
    )


def downgrade() -> None:
    op.drop_table('integrations')
