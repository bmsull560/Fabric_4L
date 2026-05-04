"""Add robots_txt_cache table for robots.txt compliance checking.

Revision ID: 009
Revises: 008
Create Date: 2026-05-04

This migration adds the robots_txt_cache table to cache fetched robots.txt files
and their parsed rules. This reduces redundant network requests and improves
compliance checking performance.

The table includes:
- domain: Unique key for the robots.txt (e.g., example.com)
- url: The full URL where robots.txt was fetched
- content: Raw robots.txt content
- rules: Parsed rules stored as JSONB
- fetched_at: Timestamp when the robots.txt was fetched
- expires_at: TTL for cache invalidation
- http_status: HTTP status code from fetch
- is_valid: Whether the robots.txt was successfully parsed
- parse_error: Error message if parsing failed
"""

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Create robots_txt_cache table with indexes."""
    
    op.create_table(
        'robots_txt_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('parse_error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain')
    )
    
    # Create indexes for common query patterns
    op.create_index('idx_robots_txt_cache_domain', 'robots_txt_cache', ['domain'], unique=True)
    op.create_index('idx_robots_txt_cache_expires_at', 'robots_txt_cache', ['expires_at'])
    op.create_index('idx_robots_txt_cache_is_valid', 'robots_txt_cache', ['is_valid'])
    
    # GIN index on rules JSONB for efficient rule queries
    op.execute("CREATE INDEX idx_robots_txt_cache_rules_gin ON robots_txt_cache USING GIN (rules)")


def downgrade() -> None:
    """Remove robots_txt_cache table and indexes."""
    
    op.drop_index('idx_robots_txt_cache_rules_gin', table_name='robots_txt_cache')
    op.drop_index('idx_robots_txt_cache_is_valid', table_name='robots_txt_cache')
    op.drop_index('idx_robots_txt_cache_expires_at', table_name='robots_txt_cache')
    op.drop_index('idx_robots_txt_cache_domain', table_name='robots_txt_cache')
    
    op.drop_table('robots_txt_cache')
