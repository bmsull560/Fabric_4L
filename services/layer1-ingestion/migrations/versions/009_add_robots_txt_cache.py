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
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS robots_txt_cache (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            domain VARCHAR(255) NOT NULL,
            url TEXT,
            content TEXT,
            rules JSONB DEFAULT '{}'::jsonb,
            fetched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            http_status INTEGER,
            is_valid BOOLEAN DEFAULT true,
            parse_error TEXT,
            UNIQUE (tenant_id, domain)
        )
        """
    )
    op.execute("ALTER TABLE robots_txt_cache ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute("CREATE INDEX IF NOT EXISTS idx_robots_txt_cache_domain ON robots_txt_cache (domain)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_robots_txt_cache_tenant_domain ON robots_txt_cache (tenant_id, domain)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_robots_txt_cache_expires_at ON robots_txt_cache (expires_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_robots_txt_cache_is_valid ON robots_txt_cache (is_valid)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_robots_txt_cache_rules_gin ON robots_txt_cache USING GIN (rules)")


def downgrade() -> None:
    """Remove robots_txt_cache table and indexes."""
    
    op.drop_index('idx_robots_txt_cache_rules_gin', table_name='robots_txt_cache')
    op.drop_index('idx_robots_txt_cache_is_valid', table_name='robots_txt_cache')
    op.drop_index('idx_robots_txt_cache_expires_at', table_name='robots_txt_cache')
    op.drop_index('idx_robots_txt_cache_domain', table_name='robots_txt_cache')
    
    op.drop_table('robots_txt_cache')
