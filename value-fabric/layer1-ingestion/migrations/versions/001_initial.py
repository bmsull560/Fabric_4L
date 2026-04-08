"""Initial migration - Create core tables.

Revision ID: 001
Revises: 
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create crawl_jobs table
    op.create_table(
        'crawl_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('ticker', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=True),
        sa.Column('max_pages', sa.Integer(), nullable=True),
        sa.Column('pages_crawled', sa.Integer(), nullable=True),
        sa.Column('pages_total', sa.Integer(), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_crawl_jobs_domain', 'crawl_jobs', ['domain'])
    op.create_index('idx_crawl_jobs_status', 'crawl_jobs', ['status'])
    op.create_index('idx_crawl_jobs_ticker', 'crawl_jobs', ['ticker'])
    op.create_index('idx_crawl_jobs_status_created', 'crawl_jobs', ['status', 'created_at'])
    
    # Create crawled_content table
    op.create_table(
        'crawled_content',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('markdown_content', sa.Text(), nullable=True),
        sa.Column('raw_html_size_bytes', sa.Integer(), nullable=True),
        sa.Column('markdown_size_bytes', sa.Integer(), nullable=True),
        sa.Column('s3_path', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('robots_allowed', sa.Boolean(), nullable=True),
        sa.Column('noindex_present', sa.Boolean(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delete_reason', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    
    op.create_index('idx_crawled_content_domain', 'crawled_content', ['domain'])
    op.create_index('idx_crawled_content_job', 'crawled_content', ['job_id'])
    op.create_index('idx_crawled_content_is_deleted', 'crawled_content', ['is_deleted'])
    op.create_index('idx_crawled_content_job_type', 'crawled_content', ['job_id', 'content_type'])
    op.create_index('idx_crawled_content_domain_extracted', 'crawled_content', ['domain', 'extracted_at'])
    
    # Create crawl_queue table
    op.create_table(
        'crawl_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=True),
        sa.Column('parent_url', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', 'url', name='uq_crawl_queue_job_url')
    )
    
    op.create_index('idx_crawl_queue_domain', 'crawl_queue', ['domain'])
    op.create_index('idx_crawl_queue_job', 'crawl_queue', ['job_id'])
    op.create_index('idx_crawl_queue_status', 'crawl_queue', ['status'])
    op.create_index('idx_crawl_queue_job_status', 'crawl_queue', ['job_id', 'status'])
    op.create_index('idx_crawl_queue_next_retry', 'crawl_queue', ['status', 'next_retry_at'])
    op.create_index('idx_crawl_queue_domain_priority', 'crawl_queue', ['domain', 'priority'])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('bytes_downloaded', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['crawled_content.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['job_id'], ['crawl_jobs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_domain', 'audit_logs', ['domain'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_domain_action', 'audit_logs', ['domain', 'action'])
    
    # Create robots_txt_cache table
    op.create_table(
        'robots_txt_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('parse_error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain')
    )
    
    op.create_index('idx_robots_txt_cache_domain', 'robots_txt_cache', ['domain'])
    op.create_index('idx_robots_txt_cache_expires', 'robots_txt_cache', ['expires_at'])


def downgrade() -> None:
    op.drop_table('robots_txt_cache')
    op.drop_table('audit_logs')
    op.drop_table('crawl_queue')
    op.drop_table('crawled_content')
    op.drop_table('crawl_jobs')
