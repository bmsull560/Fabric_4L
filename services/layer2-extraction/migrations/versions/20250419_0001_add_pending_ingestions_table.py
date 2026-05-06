"""Add pending_ingestions table for Layer 2 -> Layer 3 retry durability.

Revision ID: 20250419_0001
Revises: 20250418_0001
Create Date: 2025-04-19

This migration creates the pending_ingestions table to store extraction
results that need to be retried due to transient failures in Layer 3
knowledge graph ingestion. This replaces the runtime table creation
in PostgresPendingIngestionStore._init_db().
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20250419_0001'
down_revision = '20250418_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create pending_ingestions table with indexes."""
    op.create_table(
        'pending_ingestions',
        sa.Column('job_id', sa.String(255), primary_key=True, comment='Unique job identifier'),
        sa.Column('source_url', sa.Text(), nullable=False, comment='Source document URL'),
        sa.Column('extraction_result_json', sa.Text(), nullable=False, comment='JSON serialization of extraction result'),
        sa.Column('relationships_json', sa.Text(), nullable=False, comment='JSON serialization of relationships'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0', comment='Number of retry attempts'),
        sa.Column('max_retries', sa.Integer(), nullable=False, comment='Maximum retry attempts allowed'),
        sa.Column('last_error', sa.Text(), nullable=True, comment='Last error message'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=False, comment='When to retry next'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    op.create_index('idx_pending_ingestions_next_retry', 'pending_ingestions', ['next_retry_at'])


def downgrade() -> None:
    """Drop pending_ingestions table."""
    op.drop_index('idx_pending_ingestions_next_retry', table_name='pending_ingestions')
    op.drop_table('pending_ingestions')
