"""SQLAlchemy models for the Layer 1 ingestion service.

The active migration chain normalizes tenant ownership to a physical
``tenant_id`` column.  Older call sites may continue to use
``organization_id`` through SQLAlchemy synonyms while new code uses
``tenant_id`` directly.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declared_attr, declarative_base, relationship, synonym

Base = declarative_base()


def _now() -> datetime:
    return datetime.now(UTC)


class JobStatus(str, PyEnum):
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
    AI_LLM = "AI_LLM"
    DETERMINISTIC = "DETERMINISTIC"
    HYBRID = "HYBRID"


class TargetType(str, PyEnum):
    SINGLE_PAGE = "SINGLE_PAGE"
    PAGINATED = "PAGINATED"
    SPIDER = "SPIDER"
    API_ENDPOINT = "API_ENDPOINT"


class SourceCategory(str, PyEnum):
    CRM = "crm"
    DATABASE = "database"
    FILE = "file"
    API = "api"
    CLOUD_STORAGE = "cloud_storage"


class TargetStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"
    ERROR = "ERROR"


class ComplianceEventType(str, PyEnum):
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
    ROUND_ROBIN = "ROUND_ROBIN"
    RANDOM = "RANDOM"
    GEO_BASED = "GEO_BASED"
    SESSION_BASED = "SESSION_BASED"
    LEAST_USED = "LEAST_USED"


class ProxyType(str, PyEnum):
    RESIDENTIAL = "RESIDENTIAL"
    DATACENTER = "DATACENTER"
    MOBILE = "MOBILE"


class ProxyStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class TriggeredBy(str, PyEnum):
    SCHEDULE = "SCHEDULE"
    MANUAL = "MANUAL"
    API = "API"
    WEBHOOK = "WEBHOOK"
    WORKFLOW = "WORKFLOW"


class RetryBackoff(str, PyEnum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"


class CrawlPath(str, PyEnum):
    FAST = "fast"
    BROWSER = "browser"
    FAST_WITH_FALLBACK = "fast_fallback"


class AuthenticationType(str, PyEnum):
    NONE = "NONE"
    BEARER = "BEARER"
    API_KEY = "API_KEY"
    BASIC = "BASIC"
    OAUTH2 = "OAUTH2"


class BrowserEngine(str, PyEnum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class LLMProvider(str, PyEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class PIIStatus(str, PyEnum):
    CLEAN = "clean"
    FLAGGED = "flagged"
    QUARANTINED = "quarantined"


class TenantScoped:
    @declared_attr
    def tenant_id(cls):
        return Column(UUID(as_uuid=True), nullable=False, index=True)

    @declared_attr
    def organization_id(cls):
        return synonym("tenant_id")


class ScrapingTarget(TenantScoped, Base):
    __tablename__ = "scraping_targets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=False)
    url_pattern = Column(String(500), nullable=True)
    target_type = Column(String(50), nullable=False, default=TargetType.SINGLE_PAGE.value)
    source_category = Column(String(50), nullable=True)
    extraction_config = Column(JSONB, default=dict)
    browser_config = Column(JSONB, default=dict)
    schedule = Column(JSONB, nullable=True)
    rate_limit = Column(JSONB, default=dict)
    compliance = Column(JSONB, default=dict)
    proxy_config = Column(JSONB, default=dict)
    authentication = Column(JSONB, nullable=True)
    status = Column(String(50), nullable=False, default=TargetStatus.ACTIVE.value)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    average_execution_time_ms = Column(Integer, default=0)
    tags = Column(JSONB, default=list)

    jobs = relationship("ScrapingJob", back_populates="target")
    raw_contents = relationship("RawContent", back_populates="target")
    extracted_data = relationship("ExtractedData", back_populates="target")

    __table_args__ = (
        Index("idx_scraping_targets_tenant_status", "tenant_id", "status"),
        Index("idx_scraping_targets_created", "tenant_id", "created_at"),
    )


class ScrapingJob(TenantScoped, Base):
    __tablename__ = "scraping_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id = Column(UUID(as_uuid=True), ForeignKey("scraping_targets.id", ondelete="CASCADE"), nullable=False, index=True)
    configuration = Column(JSONB, default=dict)
    status = Column(String(50), nullable=False, default=JobStatus.PENDING.value, index=True)
    priority = Column(Integer, default=5)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_duration_ms = Column(Integer, nullable=True)
    progress_total_pages = Column(Integer, nullable=True)
    progress_processed_pages = Column(Integer, default=0)
    progress_failed_pages = Column(Integer, default=0)
    progress_current_url = Column(Text, nullable=True)
    progress_stage = Column(String(50), default=PipelineStage.INIT.value)
    progress_percent_complete = Column(Integer, default=0)
    results_raw_content_count = Column(Integer, default=0)
    results_extracted_record_count = Column(Integer, default=0)
    results_storage_bytes_used = Column(Integer, default=0)
    results_output_location = Column(Text, nullable=True)
    resources_browser_sessions_used = Column(Integer, default=0)
    resources_proxy_requests_made = Column(Integer, default=0)
    resources_llm_tokens_consumed = Column(Integer, default=0)
    resources_compute_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    triggered_by = Column(String(50), default=TriggeredBy.MANUAL.value)
    correlation_id = Column(String(100), nullable=True)

    target = relationship("ScrapingTarget", back_populates="jobs")
    stages = relationship("JobStageDetail", back_populates="job", cascade="all, delete-orphan")
    errors = relationship("JobError", back_populates="job", cascade="all, delete-orphan")
    raw_contents = relationship("RawContent", back_populates="job", cascade="all, delete-orphan")
    extracted_data = relationship("ExtractedData", back_populates="job", cascade="all, delete-orphan")
    compliance_logs = relationship("ComplianceLog", back_populates="job")
    queue_items = relationship("CrawlQueueItem", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_scraping_jobs_tenant_status", "tenant_id", "status"),
        Index("idx_scraping_jobs_target", "target_id", "created_at"),
        Index("idx_scraping_jobs_status_created", "status", "created_at"),
    )


class JobStageDetail(TenantScoped, Base):
    __tablename__ = "job_stage_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default=JobStatus.PENDING.value)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    meta = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    job = relationship("ScrapingJob", back_populates="stages")

    __table_args__ = (
        Index("idx_job_stage_details_job_stage", "job_id", "stage"),
    )


class JobError(TenantScoped, Base):
    __tablename__ = "job_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(50), nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    retryable = Column(Boolean, default=True)
    retry_count = Column(Integer, default=0)
    occurred_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution = Column(Text, nullable=True)

    job = relationship("ScrapingJob", back_populates="errors")

    __table_args__ = (
        Index("idx_job_errors_job_occurred", "job_id", "occurred_at"),
        Index("idx_job_errors_retryable", "retryable", "retry_count"),
    )


class RawContent(TenantScoped, Base):
    __tablename__ = "raw_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), ForeignKey("scraping_targets.id", ondelete="SET NULL"), nullable=True, index=True)
    source_url = Column(Text, nullable=False)
    source_final_url = Column(Text, nullable=True)
    source_domain = Column(String(255), nullable=False, index=True)
    source_ip_address = Column(String(45), nullable=True)
    source_accessed_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    source_http_status = Column(Integer, nullable=True)
    source_headers = Column(JSONB, default=dict)
    source_content_type = Column(String(255), nullable=True)
    source_content_length = Column(Integer, nullable=True)
    storage_html_path = Column(Text, nullable=True)
    storage_screenshot_path = Column(Text, nullable=True)
    storage_dom_snapshot_path = Column(Text, nullable=True)
    storage_har_path = Column(Text, nullable=True)
    storage_text_content_path = Column(Text, nullable=True)
    meta_title = Column(Text, nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_language = Column(String(10), nullable=True)
    meta_charset = Column(String(50), nullable=True)
    meta_viewport = Column(String(255), nullable=True)
    meta_canonical_url = Column(Text, nullable=True)
    meta_robots_meta = Column(String(255), nullable=True)
    meta_og_tags = Column(JSONB, default=dict)
    meta_structured_data = Column(JSONB, default=list)
    capture_method = Column(String(50), default="DYNAMIC")
    capture_browser_version = Column(String(100), nullable=True)
    capture_rendering_engine = Column(String(100), nullable=True)
    capture_javascript_executed = Column(Boolean, default=True)
    capture_wait_time_ms = Column(Integer, default=0)
    capture_scroll_depth = Column(Integer, nullable=True)
    capture_interactions = Column(JSONB, default=list)
    content_hash = Column(String(64), nullable=True, index=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(UUID(as_uuid=True), ForeignKey("raw_content.id", ondelete="SET NULL"), nullable=True)
    processing_status = Column(String(50), default=JobStatus.PENDING.value)
    extracted_data_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    retention_raw_content_expiry_days = Column(Integer, default=30)
    retention_screenshot_expiry_days = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    job = relationship("ScrapingJob", back_populates="raw_contents")
    target = relationship("ScrapingTarget", back_populates="raw_contents")
    duplicate_of = relationship("RawContent", remote_side=[id])

    __table_args__ = (
        Index("idx_raw_content_job_status", "job_id", "processing_status"),
        Index("idx_raw_content_tenant_domain", "tenant_id", "source_domain"),
        Index("idx_raw_content_hash", "tenant_id", "content_hash"),
    )


class ExtractedData(TenantScoped, Base):
    __tablename__ = "extracted_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_content_id = Column(UUID(as_uuid=True), ForeignKey("raw_content.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), ForeignKey("scraping_targets.id", ondelete="SET NULL"), nullable=True, index=True)
    extraction_method = Column(String(50), nullable=False, default=ExtractionMethod.DETERMINISTIC.value)
    extraction_llm_model = Column(String(100), nullable=True)
    extraction_prompt_version = Column(String(50), nullable=True)
    extraction_time_ms = Column(Integer, default=0)
    extraction_confidence_score = Column(Numeric(3, 2), default=0.00)
    extraction_schema_version = Column(String(50), nullable=True)
    data = Column(JSONB, default=dict)
    validation_schema_valid = Column(Boolean, default=True)
    validation_errors = Column(JSONB, default=list)
    validation_required_fields_present = Column(JSONB, default=list)
    validation_required_fields_missing = Column(JSONB, default=list)
    validation_data_quality_score = Column(Numeric(3, 2), default=0.00)
    provenance_source_url = Column(Text, nullable=False)
    provenance_extracted_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    provenance_extraction_version = Column(String(50), nullable=True)
    post_pii_redaction_applied = Column(Boolean, default=False)
    post_redacted_fields = Column(JSONB, default=list)
    post_normalized_fields = Column(JSONB, default=list)
    post_enriched_fields = Column(JSONB, default=list)
    ontology_concept_ids = Column(JSONB, default=list)
    ontology_relationship_ids = Column(JSONB, default=list)
    ontology_mapped_at = Column(DateTime(timezone=True), nullable=True)
    ontology_mapping_confidence = Column(Numeric(3, 2), nullable=True)
    storage_path = Column(Text, nullable=True)
    format = Column(String(20), default="JSON")
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    job = relationship("ScrapingJob", back_populates="extracted_data")
    raw_content = relationship("RawContent")
    target = relationship("ScrapingTarget", back_populates="extracted_data")

    __table_args__ = (
        Index("idx_extracted_data_job", "job_id", "created_at"),
        Index("idx_extracted_data_tenant_quality", "tenant_id", "validation_data_quality_score"),
    )


class ComplianceLog(TenantScoped, Base):
    __tablename__ = "compliance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    target_id = Column(UUID(as_uuid=True), ForeignKey("scraping_targets.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="INFO")
    robots_txt_check = Column(JSONB, nullable=True)
    rate_limit_event = Column(JSONB, nullable=True)
    pii_detection = Column(JSONB, nullable=True)
    domain_policy = Column(JSONB, nullable=True)
    request_url = Column(Text, nullable=False)
    request_timestamp = Column(DateTime(timezone=True), default=_now, nullable=False)
    request_ip_address = Column(String(45), nullable=True)
    request_proxy_used = Column(String(500), nullable=True)
    request_user_agent = Column(String(500), nullable=True)
    request_headers = Column(JSONB, default=dict)
    response_status_code = Column(Integer, nullable=True)
    response_action_taken = Column(String(100), nullable=True)
    response_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    meta = Column("metadata", JSONB, default=dict)

    job = relationship("ScrapingJob", back_populates="compliance_logs")
    target = relationship("ScrapingTarget")

    __table_args__ = (
        Index("idx_compliance_logs_tenant_event", "tenant_id", "event_type"),
        Index("idx_compliance_logs_timestamp", "created_at"),
        Index("idx_compliance_logs_job", "job_id", "created_at"),
    )


class ProxyPool(TenantScoped, Base):
    __tablename__ = "proxy_pools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    proxies = Column(JSONB, default=list)
    rotation_strategy = Column(String(50), default=ProxyRotationStrategy.ROUND_ROBIN.value)
    rotation_max_failures_before_quarantine = Column(Integer, default=3)
    rotation_quarantine_duration_minutes = Column(Integer, default=60)
    rotation_health_check_interval_minutes = Column(Integer, default=5)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("idx_proxy_pools_tenant", "tenant_id", "created_at"),
    )


class CrawlQueueItem(TenantScoped, Base):
    __tablename__ = "crawl_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    depth = Column(Integer, default=0)
    parent_url = Column(Text, nullable=True)
    priority = Column(Integer, default=5)
    status = Column(String(50), default=JobStatus.PENDING.value, index=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    job = relationship("ScrapingJob", back_populates="queue_items")

    __table_args__ = (
        Index("idx_crawl_queue_tenant_job_status", "tenant_id", "job_id", "status"),
        Index("idx_crawl_queue_next_retry", "status", "next_retry_at"),
        Index("idx_crawl_queue_domain_priority", "domain", "priority"),
    )


class RobotsTxtCache(TenantScoped, Base):
    __tablename__ = "robots_txt_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(255), nullable=False, index=True)
    url = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    rules = Column(JSONB, default=dict)
    fetched_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    http_status = Column(Integer, nullable=True)
    is_valid = Column(Boolean, default=True)
    parse_error = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_robots_txt_cache_tenant", "tenant_id", "domain"),
    )


class CrawlDecision(Base):
    __tablename__ = "crawl_decisions"

    decision_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    requested_path = Column(String(20), nullable=False)
    router_decision = Column(String(20), nullable=False)
    router_rule = Column(String(50), nullable=False, index=True)
    quality_passed = Column(Boolean, nullable=True)
    quality_checks = Column(JSONB, nullable=True)
    fallback_reason = Column(String(50), nullable=True, index=True)
    final_path = Column(String(20), nullable=False)
    status_code = Column(Integer, nullable=True)
    fast_duration_ms = Column(Integer, nullable=False, default=0)
    browser_duration_ms = Column(Integer, nullable=True)
    fetch_time_ms = Column(Integer, nullable=False, default=0)
    bytes_transferred = Column(Integer, nullable=False, default=0)
    spa_detected = Column(Boolean, nullable=False, default=False)
    text_length = Column(Integer, nullable=False, default=0)
    error_type = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_crawl_decisions_job_created", "job_id", "created_at"),
        Index("idx_crawl_decisions_domain_created", "domain", "created_at"),
    )


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
    source_category: SourceCategory | None = None,
) -> ScrapingTarget:
    return ScrapingTarget(
        tenant_id=tenant_id,
        name=name,
        url=url,
        target_type=target_type.value,
        source_category=source_category.value if source_category else None,
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
    return ProxyPool(
        tenant_id=tenant_id,
        name=name,
        proxies=proxies or [],
        rotation_strategy=rotation_strategy.value,
    )


__all__ = [
    "AuthenticationType",
    "Base",
    "BrowserEngine",
    "ComplianceEventType",
    "ComplianceLog",
    "CrawlDecision",
    "CrawlPath",
    "CrawlQueueItem",
    "ExtractedData",
    "ExtractionMethod",
    "JobError",
    "JobStageDetail",
    "JobStatus",
    "LLMProvider",
    "PIIStatus",
    "PipelineStage",
    "ProxyPool",
    "ProxyRotationStrategy",
    "ProxyStatus",
    "RawContent",
    "RetryBackoff",
    "RobotsTxtCache",
    "ScrapingJob",
    "ScrapingTarget",
    "SourceCategory",
    "TargetStatus",
    "TargetType",
    "TriggeredBy",
    "create_proxy_pool",
    "create_scraping_job",
    "create_scraping_target",
]
