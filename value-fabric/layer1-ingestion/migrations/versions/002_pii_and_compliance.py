"""Migration 002 - Add PII status and compliance fields.

Revision ID: 002
Revises: 001
Create Date: 2024-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add PII status to crawled_content
    op.add_column(
        'crawled_content',
        sa.Column('pii_status', sa.String(20), server_default='clean', nullable=False)
    )
    op.create_index('idx_crawled_content_pii_status', 'crawled_content', ['pii_status'])
    
    # Add PII scan results
    op.add_column(
        'crawled_content',
        sa.Column('pii_scan_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    
    # Add robots_status to crawl_queue
    op.add_column(
        'crawl_queue',
        sa.Column('robots_status', sa.String(50), nullable=True)
    )
    
    # Add unique constraint for ticker + accession_number on crawled_content for SEC filings
    # This is done via partial index on domain=sec.gov
    op.execute("""
        CREATE UNIQUE INDEX idx_crawled_content_sec_filing 
        ON crawled_content (url) 
        WHERE domain = 'sec.gov'
    """)


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_crawled_content_pii_status', table_name='crawled_content')
    op.execute("DROP INDEX IF EXISTS idx_crawled_content_sec_filing")
    
    # Remove columns
    op.drop_column('crawled_content', 'pii_status')
    op.drop_column('crawled_content', 'pii_scan_results')
    op.drop_column('crawl_queue', 'robots_status')
