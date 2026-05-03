"""SQLAlchemy models for Layer 1 Ingestion Service.

Spec-compliant database schema with multi-tenancy support.
Defines: ScrapingTarget, ScrapingJob, RawContent, ExtractedData,
ComplianceLog, ProxyPool, JobStageDetail, JobError entities.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# =============================================================================
# ENUMS
# =============================================================================


class JobStatus(str, PyEnum):
    """Job lifecycle states - 11 states as per spec."""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    BROWSER_ACQUIRING = "BROWSER_ACQUIRING"
    NAVIGATING = "NAVIGATING"
    EXTRACTING = "EXTRACTING"
    TRANSFORMING = "TRANSFORMING"
    STORING = "STORING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"


class PipelineStage(str, PyEnum):
    """Pipeline execution stages - 11 stages as per spec."""

    INIT = "INIT"
    COMPLIANCE_CHECK = "COMPLIANCE_CHECK"
    BROWSER_LAUNCH = "BROWSER_LAUNCH"
    NAVIGATION = "NAVIGATION"
    CONTENT_CAPTURE = "CONTENT_CAPTURE"
    AI_EXTRACTION = "AI_EXTRACTION"
    POST_PROCESSING = "POST_PROCESSING"
    VALIDATION = "VALIDATION"
    STORAGE = "STORAGE"
    NOTIFICATION = "NOTIFICATION"


class ExtractionMethod(str, PyEnum):
    """Content extraction methods."""

    AI_LLM = "AI_LLM"
    DETERMINISTIC = "DETERMINISTIC"
    HYBRID = "HYBRID"


class TargetType(str, PyEnum):
    """Scraping target types."""

    SINGLE_PAGE = "SINGLE_PAGE"
    PAGINATED = "PAGINATED"
    SPIDER = "SPIDER"
    API_ENDPOINT = "API_ENDPOINT"


class TargetStatus(str, PyEnum):
    """Scraping target lifecycle status."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"
    ERROR = "ERROR"


class ComplianceEventType(str, PyEnum):
    """Compliance event types."""

    ROBOTS_TXT_CHECK = "ROBOTS_TXT_CHECK"
    RATE_LIMIT_APPLIED = "RATE_LIMIT_APPLIED"
    PII_DETECTED = "PII_DETECTED"
    PII_REDACTED = "PII_REDACTED"
    DOMAIN_BLOCKED = "DOMAIN_BLOCKED"
    DOMAIN_ALLOWED = "DOMAIN_ALLOWED"
    CAPTCHA_ENCOUNTERED = "CAPTCHA_ENCOUNTERED"
    BLOCKED_BY_TARGET = "BLOCKED_BY_TARGET"
    TERMS_VIOLATION = "TERMS_VIOLATION"
    DATA_RETENTION_DELETION = "DATA_RETENTION_DELETION"


class ProxyRotationStrategy(str, PyEnum):
    """Proxy rotation strategies."""

    ROUND_ROBIN = "ROUND_ROBIN"
    RANDOM = "RANDOM"
    GEO_BASED = "GEO_BASED"
    SESSION_BASED = "SESSION_BASED"
    LEAST_USED = "LEAST_USED"


class ProxyType(str, PyEnum):
    """Proxy types."""

    RESIDENTIAL = "RESIDENTIAL"
    DATACENTER = "DATACENTER"
    MOBILE = "MOBILE"


class ProxyStatus(str, PyEnum):
    """Proxy health status."""

    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class TriggeredBy(str, PyEnum):
    """Job trigger sources."""

    SCHEDULE = "SCHEDULE"
    MANUAL = "MANUAL"
    API = "API"
    WEBHOOK = "WEBHOOK"
    WORKFLOW = "WORKFLOW"


class RetryBackoff(str, PyEnum):
    """Retry backoff strategies."""

    FIXED = "fixed"
    EXPONENTIAL = "exponential"


class CrawlPath(str, PyEnum):
    """Ingestion path selection for a scraping target.

    Controls whether the crawler uses HTTPX fast path,
    Playwright browser automation, or hybrid fallback.
    """

    FAST = "fast"  # HTTPX only - fastest for static content
    BROWSER = "browser"  # Playwright only - handles dynamic content
    FAST_WITH_FALLBACK = "fast_fallback"  # HTTPX first, browser if quality fails


class AuthenticationType(str, PyEnum):
    """Authentication types for targets."""

    NONE = "NONE"
    BEARER = "BEARER"
    API_KEY = "API_KEY"
    BASIC = "BASIC"
    OAUTH2 = "OAUTH2"


class BrowserEngine(str, PyEnum):
    """Browser engines."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class LLMProvider(str, PyEnum):
    """LLM providers for AI extraction."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class PIIStatus(str, PyEnum):
    """PII detection status."""

    CLEAN = "clean"
    FLAGGED = "flagged"
    QUARANTINED = "quarantined"


# =============================================================================
# ENTITIES
# =============================================================================


class ScrapingTarget(Base):
    """Configuration entity for a scraping target.

    Defines what to scrape, how to extract it, scheduling, rate limits, etc.
    """

    __tablename__ = "scraping_targets"

    # Primary Identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Target Configuration
    url = Column(Text, nullable=False)
    url_pattern = Column(String(500), nullable=True)  # Regex for URL matching
    target_type = Column(String(50), nullable=False, default=TargetType.SINGLE_PAGE.value)

    # Extraction Configuration (JSONB for nested structure)
    extraction_config = Column(JSONB, default=dict)  # {
    # "method": "AI_LLM|DETERMINISTIC|HYBRID",
    # "llm_provider": "openai|anthropic|azure_openai",
    # "extraction_schema": {...},  # JSON Schema
    # "visual_hints": false,
    # "max_depth": 2,
    # "follow_links": true,
    # "link_selectors": [...]
    # }

    # Browser Configuration
    browser_config = Column(JSONB, default=dict)  # {
    # "engine": "chromium",
    # "headless": true,
    # "viewport": {"width": 1920, "height": 1080},
    # "user_agent": "...",
    # "javascript_enabled": true,
    # "wait_for_selector": null,
    # "wait_timeout": 30000,
    # "stealth_mode": true
    # }

    # Scheduling
    schedule = Column(JSONB, nullable=True)  # {
    # "enabled": true,
    # "cron_expression": "0 0 * * *",
    # "timezone": "UTC",
    # "max_concurrent_jobs": 1
    # }

    # Rate Limiting
    rate_limit = Column(JSONB, default=dict)  # {
    # "requests_per_second": 1,
    # "requests_per_minute": 30,
    # "requests_per_hour": 500,
    # "burst_limit": 5,
    # "retry_attempts": 3,
    # "retry_backoff": "exponential",
    # "retry_delay_ms": 1000
    # }

    # Compliance Settings
    compliance = Column(JSONB, default=dict)  # {
    # "respect_robots_txt": true,
    # "user_agent_string": "...",
    # "crawl_delay_seconds": 1,
    # "domain_allowlist": [],
    # "domain_blocklist": [],
    # "pii_redaction_enabled": true,
    # "sensitive_field_patterns": []
    # }

    # Proxy Configuration
    proxy_config = Column(JSONB, default=dict)  # {
    # "enabled": false,
    # "rotation_strategy": "ROUND_ROBIN|RANDOM|GEO_BASED|SESSION_BASED",
    # "proxy_pool_id": "uuid",
    # "sticky_sessions": false,
    # "session_duration_minutes": 30
    # }

    # Authentication
    authentication = Column(JSONB, nullable=True)  # {
    # "type": "NONE|BEARER|API_KEY|BASIC|OAUTH2",

    # Metadata
    status = Column(String(50), nullable=False, default=TargetStatus.ACTIVE.value)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )
    created_by = Column(UUID(as_uuid=True), nullable=False)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    success_count = Column(Integer, default=0)
    # ... (rest of the code remains the same)

    resources_proxy_requests_made = Column(Integer, default=0)
    resources_llm_tokens_consumed = Column(Integer, default=0)
    resources_compute_time_ms = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    triggered_by = Column(String(50), default=TriggeredBy.MANUAL.value)
    correlation_id = Column(String(100), nullable=True)  # Distributed tracing

    # Relationships
    # ... (rest of the code remains the same)

    duration_ms = Column(Integer, nullable=True)

    error_message = Column(Text, nullable=True)
    meta = Column(JSONB, default=dict)  # Stage-specific details

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    job = relationship("ScrapingJob", back_populates="stages")

    # ... (rest of the code remains the same)

    url = Column(Text, nullable=True)  # URL being processed when error occurred

    retryable = Column(Boolean, default=True)
    retry_count = Column(Integer, default=0)

    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution = Column(Text, nullable=True)

    # Relationships
    job = relationship("ScrapingJob", back_populates="errors")

    # ... (rest of the code remains the same)

    # Source Information
    source_url = Column(Text, nullable=False)
    source_final_url = Column(Text, nullable=True)  # After redirects
    source_domain = Column(String(255), nullable=False, index=True)
    source_ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    source_accessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    source_http_status = Column(Integer, nullable=True)
    source_headers = Column(JSONB, default=dict)
    source_content_type = Column(String(255), nullable=True)
    source_content_length = Column(Integer, nullable=True)

    # ... (rest of the code remains the same)

    # Retention
    retention_raw_content_expiry_days = Column(Integer, default=30)
    retention_screenshot_expiry_days = Column(Integer, default=30)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    job = relationship("ScrapingJob", back_populates="raw_contents")
    duplicate_of = relationship("RawContent", remote_side=[id])

    # ... (rest of the code remains the same)

    validation_data_quality_score = Column(Numeric(3, 2), default=0.00)

    # Provenance
    provenance_source_url = Column(Text, nullable=False)
    provenance_extracted_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    provenance_extraction_version = Column(String(50), nullable=True)

    # Post-Processing
    post_pii_redaction_applied = Column(Boolean, default=False)

    # ... (rest of the code remains the same)

    # Storage
    storage_path = Column(Text, nullable=True)
    format = Column(String(20), default="JSON")  # JSON, JSONL, PARQUET, MARKDOWN
    size_bytes = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    job = relationship("ScrapingJob", back_populates="extracted_data")
    raw_content = relationship("RawContent")

    # ... (rest of the code remains the same)

    # "reason": "..."

    # Request Details
    request_url = Column(Text, nullable=False)
    request_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    request_ip_address = Column(String(45), nullable=True)
    request_proxy_used = Column(String(500), nullable=True)
    request_user_agent = Column(String(500), nullable=True)
    request_headers = Column(JSONB, default=dict)

    # Response
    response_status_code = Column(Integer, nullable=True)
    response_action_taken = Column(String(100), nullable=True)
    response_reason = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    meta = Column(JSONB, default=dict)

    # Relationships
    job = relationship("ScrapingJob", back_populates="compliance_logs")

    # ... (rest of the code remains the same)

    rotation_strategy = Column(String(50), default=ProxyRotationStrategy.ROUND_ROBIN.value)
    rotation_max_failures_before_quarantine = Column(Integer, default=3)
    rotation_quarantine_duration_minutes = Column(Integer, default=60)
    rotation_health_check_interval_minutes = Column(Integer, default=5)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )

    # ... (rest of the code remains the same)

    content = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    rules = Column(JSONB, default=dict)

    fetched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    http_status = Column(Integer, nullable=True)

    is_valid = Column(Boolean, default=True)
    parse_error = Column(Text, nullable=True)

    # ... (rest of the code remains the same)

    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ... (rest of the code remains the same)
        Index("idx_crawl_queue_next_retry", "status", "next_retry_at"),
        Index("idx_crawl_queue_domain_priority", "domain", "priority"),
    )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_scraping_target(
    tenant_id: uuid.UUID,
    name: str,
    url: str,
    target_type: TargetType,
    created_by: uuid.UUID,
    description: str | None = None,
    extraction_config: dict | None = None,
    browser_config: dict | None = None,
    schedule: dict | None = None,
    rate_limit: dict | None = None,
    compliance: dict | None = None,
    proxy_config: dict | None = None,
    tags: list[str] | None = None,
) -> ScrapingTarget:
    """Factory function to create a new scraping target."""
    return ScrapingTarget(
        tenant_id=tenant_id,
        name=name,
        url=url,
        target_type=target_type.value,
        created_by=created_by,
        description=description,
        extraction_config=extraction_config or {},
        browser_config=browser_config or {},
        schedule=schedule,
        rate_limit=rate_limit or {},
        compliance=compliance or {},
        proxy_config=proxy_config or {},
        tags=tags or [],
    )


def create_scraping_job(
    tenant_id: uuid.UUID,
    target_id: uuid.UUID,
    created_by: uuid.UUID,
    configuration: dict,
    priority: int = 5,
    triggered_by: TriggeredBy = TriggeredBy.MANUAL,
    correlation_id: str | None = None,
) -> ScrapingJob:
    """Factory function to create a new scraping job."""
    return ScrapingJob(
        tenant_id=tenant_id,
        target_id=target_id,
        created_by=created_by,
        configuration=configuration,
        priority=priority,
        triggered_by=triggered_by.value,
        correlation_id=correlation_id,
    )


def create_proxy_pool(
    tenant_id: uuid.UUID,
    name: str,
    proxies: list[dict] | None = None,
    rotation_strategy: ProxyRotationStrategy = ProxyRotationStrategy.ROUND_ROBIN,
) -> ProxyPool:
    """Factory function to create a proxy pool."""
    return ProxyPool(
        tenant_id=tenant_id,
        name=name,
        proxies=proxies or [],
        rotation_strategy=rotation_strategy.value,
    )


# =============================================================================
# CRAWL DECISION MODEL (for Smart Router)
# =============================================================================


class CrawlDecision(Base):
    """Canonical record of crawl routing decisions.

    Stores immutable history of routing decisions, quality assessments,
    and execution outcomes for debugging, metrics, and optimization.
    """

    __tablename__ = "crawl_decisions"

    # Primary key
    decision_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=True, index=True)
    # Tenant context
    # - NULL = global/router-level decision not tied to a specific tenant
    # - UUID = tenant-scoped decision
    # RLS policy intentionally allows all tenants to read NULL-tenant rows
    # (global routing rules, Smart Router observability data)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # no FK — tenant table is in Layer 4

    # Request context
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    requested_path = Column(String(20), nullable=False)  # fast/browser/fast_fallback

    # Routing decision
    router_decision = Column(String(20), nullable=False)  # What router chose
    router_rule = Column(String(50), nullable=False, index=True)  # Which rule triggered

    # Quality evaluation
    quality_passed = Column(Boolean, nullable=True)
    quality_checks = Column(JSONB, nullable=True)  # Dict of check_name -> bool
    fallback_reason = Column(String(50), nullable=True, index=True)

    # Execution outcome
    final_path = Column(String(20), nullable=False)  # What actually executed
    status_code = Column(Integer, nullable=True)

    # Performance metrics
    fast_duration_ms = Column(Integer, nullable=False, default=0)
    browser_duration_ms = Column(Integer, nullable=True)
    fetch_time_ms = Column(Integer, nullable=False, default=0)
    bytes_transferred = Column(Integer, nullable=False, default=0)

    # Content analysis
    spa_detected = Column(Boolean, nullable=False, default=False)
    text_length = Column(Integer, nullable=False, default=0)

    # Error tracking
    error_type = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_crawl_decisions_job_created", "job_id", "created_at"),
        Index("idx_crawl_decisions_domain_created", "domain", "created_at"),
    )
