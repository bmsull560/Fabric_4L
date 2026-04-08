"""Unit tests for shared models."""

import pytest
from datetime import datetime
from uuid import UUID

from src.shared.models import (
    CrawlJob, CrawlQueueItem, CrawledContent,
    JobStatus, JobPriority, ContentType, QueueStatus,
    create_crawl_job, create_crawl_queue_item
)


class TestCrawlJob:
    """Test cases for CrawlJob model."""
    
    def test_create_crawl_job(self):
        """Test creating a crawl job."""
        job = create_crawl_job(
            job_type='website',
            domain='example.com',
            priority=JobPriority.HIGH,
            depth=2,
            max_pages=100,
            config={'start_url': 'https://example.com'}
        )
        
        assert job.job_type == 'website'
        assert job.domain == 'example.com'
        assert job.priority == JobPriority.HIGH.value
        assert job.depth == 2
        assert job.max_pages == 100
        assert job.status == JobStatus.PENDING.value
        assert job.config['start_url'] == 'https://example.com'
        assert isinstance(job.id, UUID)
    
    def test_job_status_enum(self):
        """Test job status enumeration."""
        assert JobStatus.PENDING.value == 'pending'
        assert JobStatus.RUNNING.value == 'running'
        assert JobStatus.COMPLETED.value == 'completed'
        assert JobStatus.FAILED.value == 'failed'
    
    def test_job_priority_enum(self):
        """Test job priority enumeration."""
        assert JobPriority.LOW.value == 'low'
        assert JobPriority.MEDIUM.value == 'medium'
        assert JobPriority.HIGH.value == 'high'
        assert JobPriority.CRITICAL.value == 'critical'


class TestCrawlQueueItem:
    """Test cases for CrawlQueueItem model."""
    
    def test_create_queue_item(self):
        """Test creating a queue item."""
        job_id = UUID('12345678-1234-1234-1234-123456789abc')
        
        item = create_crawl_queue_item(
            job_id=job_id,
            url='https://example.com/page',
            domain='example.com',
            depth=1,
            priority=3,
            parent_url='https://example.com'
        )
        
        assert item.job_id == job_id
        assert item.url == 'https://example.com/page'
        assert item.domain == 'example.com'
        assert item.depth == 1
        assert item.priority == 3
        assert item.parent_url == 'https://example.com'
        assert item.status == QueueStatus.PENDING.value
        assert item.retry_count == 0
        assert item.max_retries == 3


class TestCrawledContent:
    """Test cases for CrawledContent model."""
    
    def test_content_creation(self):
        """Test creating crawled content."""
        job_id = UUID('12345678-1234-1234-1234-123456789abc')
        
        content = CrawledContent(
            job_id=job_id,
            url='https://example.com/page',
            domain='example.com',
            content_type=ContentType.PRODUCT_PAGE.value,
            title='Product Page',
            description='A product description',
            author='John Doe',
            markdown_content='# Product\n\nDescription',
            raw_html_size_bytes=1024,
            markdown_size_bytes=256,
            http_status=200,
            metadata={'og_title': 'Product Page'}
        )
        
        assert content.url == 'https://example.com/page'
        assert content.domain == 'example.com'
        assert content.content_type == 'product_page'
        assert content.title == 'Product Page'
        assert content.http_status == 200
        assert content.is_deleted == False
        assert content.robots_allowed == True


class TestContentType:
    """Test cases for ContentType enum."""
    
    def test_content_types(self):
        """Test all content types are defined."""
        assert ContentType.PRODUCT_PAGE.value == 'product_page'
        assert ContentType.PRESS_RELEASE.value == 'press_release'
        assert ContentType.FINANCIAL_FILING.value == 'financial_filing'
        assert ContentType.BLOG_POST.value == 'blog_post'
        assert ContentType.DOCUMENTATION.value == 'documentation'
        assert ContentType.NEWS_ARTICLE.value == 'news_article'
        assert ContentType.PATENT.value == 'patent'
        assert ContentType.UNKNOWN.value == 'unknown'


class TestQueueStatus:
    """Test cases for QueueStatus enum."""
    
    def test_queue_statuses(self):
        """Test all queue statuses are defined."""
        assert QueueStatus.PENDING.value == 'pending'
        assert QueueStatus.PROCESSING.value == 'processing'
        assert QueueStatus.COMPLETED.value == 'completed'
        assert QueueStatus.FAILED.value == 'failed'
        assert QueueStatus.RETRYING.value == 'retrying'
