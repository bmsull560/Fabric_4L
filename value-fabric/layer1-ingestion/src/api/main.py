"""FastAPI application for Layer 1: Intelligent Data Ingestion Service.

Spec-compliant REST API with multi-tenancy support.
Base URL: /api/v1/ingestion

Provides endpoints for:
- ScrapingTarget CRUD (/targets)
- ScrapingJob management (/jobs)
- Content retrieval (/content)
- Compliance auditing (/compliance)
"""

import os
import json
import hashlib
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, HttpUrl, validator
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from ..metrics import initialize_metrics, MetricsMiddleware, get_metrics

from ..shared.config import settings
from ..shared.database import get_db, engine
from ..shared.models import (
    Base, ScrapingTarget, ScrapingJob, RawContent, ExtractedData,
    ComplianceLog, ProxyPool, JobStageDetail, JobError, CrawlQueueItem,
    JobStatus, PipelineStage, ExtractionMethod, TargetType, TargetStatus,
    ComplianceEventType, ProxyRotationStrategy, TriggeredBy, RetryBackoff,
    AuthenticationType, BrowserEngine, LLMProvider, PIIStatus,
    create_scraping_target, create_scraping_job, create_proxy_pool
)
from ..shared.tasks import process_scraping_job, cleanup_old_content, execute_pipeline_stage

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# =============================================================================
# FASTAPI APP INITIALIZATION
# =============================================================================

# Initialize Prometheus metrics
metrics = initialize_metrics()

app = FastAPI(
    title="Value Fabric - Layer 1: Intelligent Data Ingestion",
    description="Production-grade web data ingestion service with spec-compliant API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add metrics middleware if available
if metrics:
    metrics_middleware = MetricsMiddleware(metrics)
    app.middleware("http")(metrics_middleware)

# GovernanceMiddleware — verifies JWTs and resolves tenant/user context.
# api_key_resolver is None here (L1 uses JWT auth primarily); pass a resolver
# callable to support X-API-Key if the shared key store is accessible.
try:
    from shared.identity.middleware import GovernanceMiddleware
    app.add_middleware(GovernanceMiddleware, api_key_resolver=None)
except ImportError:
    import logging as _log
    _log.getLogger(__name__).warning(
        "shared.identity not importable — GovernanceMiddleware skipped in L1. "
        "Ensure the shared package is installed."
    )

# CORS middleware
# Note: allow_origins=["*"] cannot be used with allow_credentials=True per browser security spec
# In production, specify exact origins or use environment variable
import os as _os
allow_origins = _os.getenv("CORS_ORIGINS", "").split(",") if _os.getenv("CORS_ORIGINS") else ["*"]
allow_credentials = False  # Must be False when using wildcard origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create router for spec-compliant endpoints
router = APIRouter(prefix="/api/v1/ingestion")


# =============================================================================
# DEPENDENCY: ORGANIZATION ID (Multi-tenancy)
# =============================================================================

def get_organization_id(request: Request) -> UUID:
    """Extract organization (tenant) ID from the GovernanceMiddleware context.

    Falls back to the X-Organization-ID header for backward compatibility
    with existing integration tests.
    """
    ctx = getattr(request.state, "governance_context", None)
    if ctx is not None:
        return ctx.tenant_id

    # Legacy header fallback (integration tests / dev only)
    header_value = request.headers.get("X-Organization-ID")
    if header_value:
        try:
            return UUID(header_value)
        except ValueError:
            pass

    # Default for local dev without auth
    return UUID("00000000-0000-0000-0000-000000000001")


def get_current_user_id(request: Request) -> UUID:
    """Extract user ID from the GovernanceMiddleware context."""
    ctx = getattr(request.state, "governance_context", None)
    if ctx is not None and ctx.user_id:
        try:
            return UUID(ctx.user_id)
        except ValueError:
            pass
    return UUID("00000000-0000-0000-0000-000000000001")


# =============================================================================
# PYDANTIC SCHEMAS - ScrapingTarget
# =============================================================================

class ExtractionConfigInput(BaseModel):
    """Extraction configuration for a target."""
    method: ExtractionMethod = ExtractionMethod.DETERMINISTIC
    llm_provider: Optional[LLMProvider] = None
    extraction_schema: Optional[Dict[str, Any]] = None
    visual_hints: bool = False
    max_depth: Optional[int] = Field(None, ge=0, le=10)
    follow_links: bool = True
    link_selectors: Optional[List[str]] = None


class BrowserConfigInput(BaseModel):
    """Browser configuration for a target."""
    engine: BrowserEngine = BrowserEngine.CHROMIUM
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    javascript_enabled: bool = True
    wait_for_selector: Optional[str] = None
    wait_timeout: int = 30000
    stealth_mode: bool = True


class ScheduleInput(BaseModel):
    """Schedule configuration for a target."""
    enabled: bool = False
    cron_expression: Optional[str] = None
    timezone: str = "UTC"
    max_concurrent_jobs: int = 1
    
    @validator('cron_expression')
    def validate_cron(cls, v):
        if v:
            # Basic cron validation - TODO: use cron-validator library
            parts = v.split()
            if len(parts) != 5:
                raise ValueError("Invalid cron expression - must have 5 fields")
        return v


class RateLimitInput(BaseModel):
    """Rate limiting configuration."""
    requests_per_second: float = 1.0
    requests_per_minute: int = 30
    requests_per_hour: int = 500
    burst_limit: int = 5
    retry_attempts: int = 3
    retry_backoff: RetryBackoff = RetryBackoff.EXPONENTIAL
    retry_delay_ms: int = 1000


class ComplianceInput(BaseModel):
    """Compliance settings."""
    respect_robots_txt: bool = True
    user_agent_string: Optional[str] = None
    crawl_delay_seconds: float = 1.0
    domain_allowlist: List[str] = []
    domain_blocklist: List[str] = []
    pii_redaction_enabled: bool = True
    sensitive_field_patterns: List[str] = []


class ProxyConfigInput(BaseModel):
    """Proxy configuration."""
    enabled: bool = False
    rotation_strategy: ProxyRotationStrategy = ProxyRotationStrategy.ROUND_ROBIN
    proxy_pool_id: Optional[UUID] = None
    sticky_sessions: bool = False
    session_duration_minutes: Optional[int] = None


class AuthenticationInput(BaseModel):
    """Authentication configuration."""
    type: AuthenticationType = AuthenticationType.NONE
    credentials_ref: Optional[str] = None


class CreateTargetRequest(BaseModel):
    """Request to create a scraping target."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    url: str = Field(..., description="Target URL")
    target_type: TargetType = TargetType.SINGLE_PAGE
    extraction_config: ExtractionConfigInput = Field(default_factory=ExtractionConfigInput)
    browser_config: BrowserConfigInput = Field(default_factory=BrowserConfigInput)
    schedule: Optional[ScheduleInput] = None
    rate_limit: RateLimitInput = Field(default_factory=RateLimitInput)
    compliance: ComplianceInput = Field(default_factory=ComplianceInput)
    proxy_config: ProxyConfigInput = Field(default_factory=ProxyConfigInput)
    authentication: Optional[AuthenticationInput] = None
    tags: List[str] = []


class UpdateTargetRequest(BaseModel):
    """Request to update a scraping target."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: Optional[TargetType] = None
    extraction_config: Optional[ExtractionConfigInput] = None
    browser_config: Optional[BrowserConfigInput] = None
    schedule: Optional[ScheduleInput] = None
    rate_limit: Optional[RateLimitInput] = None
    compliance: Optional[ComplianceInput] = None
    proxy_config: Optional[ProxyConfigInput] = None
    authentication: Optional[AuthenticationInput] = None
    tags: Optional[List[str]] = None
    status: Optional[TargetStatus] = None


class ScrapingTargetSummary(BaseModel):
    """Summary of a scraping target."""
    id: UUID
    name: str
    url: str
    target_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_success_at: Optional[datetime] = None
    success_count: int
    error_count: int
    average_execution_time_ms: int
    tags: List[str]


class ScrapingTargetDetail(ScrapingTargetSummary):
    """Detailed scraping target response."""
    organization_id: UUID
    description: Optional[str]
    url_pattern: Optional[str]
    extraction_config: Dict[str, Any]
    browser_config: Dict[str, Any]
    schedule: Optional[Dict[str, Any]]
    rate_limit: Dict[str, Any]
    compliance: Dict[str, Any]
    proxy_config: Dict[str, Any]
    authentication: Optional[Dict[str, Any]]
    created_by: UUID
    last_error_at: Optional[datetime]


class TargetListResponse(BaseModel):
    """List of scraping targets."""
    data: List[ScrapingTargetSummary]
    pagination: Dict[str, Any]


class ValidateTargetRequest(BaseModel):
    """Request to validate a target configuration."""
    test_url: Optional[str] = None
    validate_robots_txt: bool = True
    validate_schema: bool = True
    test_browser_connection: bool = False


class ValidationError(BaseModel):
    """Validation error detail."""
    field: str
    message: str
    severity: str = "error"


class ValidationWarning(BaseModel):
    """Validation warning detail."""
    field: str
    message: str


class ValidateTargetResponse(BaseModel):
    """Response from target validation."""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    robots_txt_check: Optional[Dict[str, Any]] = None
    schema_validation: Optional[Dict[str, Any]] = None
    browser_test: Optional[Dict[str, Any]] = None


class ExecuteTargetRequest(BaseModel):
    """Request to execute a target."""
    priority: int = Field(default=5, ge=1, le=10)
    override_config: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None
    webhook_events: Optional[List[str]] = None


class ExecuteTargetResponse(BaseModel):
    """Response from target execution."""
    job_id: UUID
    status: str
    estimated_start_time: Optional[datetime] = None
    queue_position: int


# =============================================================================
# PYDANTIC SCHEMAS - ScrapingJob
# =============================================================================

class JobSummary(BaseModel):
    """Summary of a scraping job."""
    id: UUID
    target_id: UUID
    status: str
    priority: int
    progress_percent_complete: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobStageDetailResponse(BaseModel):
    """Pipeline stage detail."""
    stage: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None


class JobErrorResponse(BaseModel):
    """Job error detail."""
    id: UUID
    stage: str
    error_code: str
    error_message: str
    url: Optional[str] = None
    retryable: bool
    retry_count: int
    occurred_at: datetime
    resolved_at: Optional[datetime] = None


class ResourceUsageDetail(BaseModel):
    """Resource usage metrics."""
    browser_sessions_used: int
    proxy_requests_made: int
    llm_tokens_consumed: int
    compute_time_ms: int


class JobResultsDetail(BaseModel):
    """Job results summary."""
    raw_content_count: int
    extracted_record_count: int
    storage_bytes_used: int
    output_location: Optional[str] = None


class JobProgressDetail(BaseModel):
    """Job progress information."""
    total_pages: Optional[int] = None
    processed_pages: int
    failed_pages: int
    current_url: Optional[str] = None
    current_stage: str
    percent_complete: int


class ScrapingJobDetail(BaseModel):
    """Detailed job response."""
    id: UUID
    organization_id: UUID
    target_id: UUID
    configuration: Dict[str, Any]
    status: str
    priority: int
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_ms: Optional[int] = None
    progress: JobProgressDetail
    results: JobResultsDetail
    resources: ResourceUsageDetail
    triggered_by: str
    correlation_id: Optional[str] = None
    created_at: datetime
    created_by: UUID
    stages: List[JobStageDetailResponse]
    errors: List[JobErrorResponse]


class JobListResponse(BaseModel):
    """List of jobs response."""
    data: List[JobSummary]
    aggregation: Dict[str, Any]
    pagination: Dict[str, Any]


class RetryJobRequest(BaseModel):
    """Request to retry a job."""
    retry_strategy: str = "FULL"  # FULL, FAILED_ONLY, FROM_STAGE
    from_stage: Optional[str] = None
    max_retries: int = 3


class JobProgressResponse(BaseModel):
    """Real-time job progress."""
    job_id: UUID
    status: str
    progress: JobProgressDetail
    last_update: datetime


# =============================================================================
# PYDANTIC SCHEMAS - Content
# =============================================================================

class RawContentResponse(BaseModel):
    """Raw content response."""
    id: UUID
    job_id: UUID
    source_url: str
    source_final_url: Optional[str]
    source_domain: str
    source_http_status: Optional[int]
    storage: Dict[str, Optional[str]]
    metadata: Dict[str, Any]
    capture: Dict[str, Any]
    content_hash: Optional[str]
    is_duplicate: bool
    processing_status: str
    created_at: datetime


class ExtractedDataResponse(BaseModel):
    """Extracted data response."""
    id: UUID
    job_id: UUID
    raw_content_id: UUID
    extraction_method: str
    extraction_confidence_score: float
    data: Dict[str, Any]
    validation: Dict[str, Any]
    post_processing: Dict[str, Any]
    created_at: datetime


class ContentListResponse(BaseModel):
    """List of raw content items."""
    items: List[RawContentResponse]
    total: int
    page: int
    per_page: int


# =============================================================================
# PYDANTIC SCHEMAS - Compliance
# =============================================================================

class ComplianceLogResponse(BaseModel):
    """Compliance log entry."""
    id: UUID
    event_type: str
    severity: str
    request_url: str
    request_timestamp: datetime
    response_action_taken: Optional[str]
    response_reason: Optional[str]
    created_at: datetime


class ComplianceSummaryResponse(BaseModel):
    """Compliance summary statistics."""
    period: Dict[str, datetime]
    robots_txt_compliance: Dict[str, int]
    rate_limiting: Dict[str, Any]
    pii_detection: Dict[str, int]
    domain_policies: Dict[str, int]


# =============================================================================
# PYDANTIC SCHEMAS - Health & Admin
# =============================================================================

class ComponentHealth(BaseModel):
    """Component health status."""
    status: str  # healthy, degraded, unhealthy
    latency_ms: Optional[int] = None
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str  # healthy, degraded, unhealthy
    version: str
    timestamp: datetime
    components: Dict[str, ComponentHealth]
    metrics: Dict[str, Any]


class CreateProxyPoolRequest(BaseModel):
    """Request to create a proxy pool."""
    name: str
    proxies: List[Dict[str, Any]]
    rotation_strategy: ProxyRotationStrategy = ProxyRotationStrategy.ROUND_ROBIN


class ProxyPoolResponse(BaseModel):
    """Proxy pool response."""
    id: UUID
    name: str
    proxy_count: int
    rotation_strategy: str
    created_at: datetime


# =============================================================================
# API ENDPOINTS - ScrapingTarget
# =============================================================================

@router.get("/targets", response_model=TargetListResponse)
async def list_targets(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[TargetStatus] = Query(None),
    search: Optional[str] = Query(None, description="Search in name, description, url"),
    tags: Optional[List[str]] = Query(None),
    sort_by: str = Query(default="created_at", regex="^(created_at|updated_at|last_success_at|name)$"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """List all scraping targets for the organization."""
    query = db.query(ScrapingTarget).filter(ScrapingTarget.organization_id == org_id)
    
    if status:
        query = query.filter(ScrapingTarget.status == status.value)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (ScrapingTarget.name.ilike(search_filter)) |
            (ScrapingTarget.description.ilike(search_filter)) |
            (ScrapingTarget.url.ilike(search_filter))
        )
    
    if tags:
        # JSONB containment check
        for tag in tags:
            query = query.filter(ScrapingTarget.tags.contains([tag]))
    
    total = query.count()
    total_pages = (total + limit - 1) // limit
    
    # Apply sorting
    sort_column = getattr(ScrapingTarget, sort_by)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)
    
    offset = (page - 1) * limit
    targets = query.offset(offset).limit(limit).all()
    
    return TargetListResponse(
        data=[
            ScrapingTargetSummary(
                id=t.id,
                name=t.name,
                url=t.url,
                target_type=t.target_type,
                status=t.status,
                created_at=t.created_at,
                updated_at=t.updated_at,
                last_success_at=t.last_success_at,
                success_count=t.success_count,
                error_count=t.error_count,
                average_execution_time_ms=t.average_execution_time_ms,
                tags=t.tags or []
            )
            for t in targets
        ],
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    )


@router.post("/targets", response_model=ScrapingTargetDetail, status_code=201)
async def create_target(
    request: CreateTargetRequest,
    org_id: UUID = Depends(get_organization_id),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new scraping target."""
    # Validate URL
    parsed = urlparse(request.url)
    if not parsed.scheme in ('http', 'https') or not parsed.netloc:
        raise HTTPException(status_code=400, detail="URL must use http/https protocol")
    
    # Validate extraction schema if method requires LLM
    if request.extraction_config.method == ExtractionMethod.AI_LLM and not request.extraction_config.llm_provider:
        raise HTTPException(status_code=400, detail="llm_provider is required when method is AI_LLM")
    
    # Build config objects
    extraction_config = {
        "method": request.extraction_config.method.value,
        "llm_provider": request.extraction_config.llm_provider.value if request.extraction_config.llm_provider else None,
        "extraction_schema": request.extraction_config.extraction_schema,
        "visual_hints": request.extraction_config.visual_hints,
        "max_depth": request.extraction_config.max_depth,
        "follow_links": request.extraction_config.follow_links,
        "link_selectors": request.extraction_config.link_selectors
    }
    
    browser_config = {
        "engine": request.browser_config.engine.value,
        "headless": request.browser_config.headless,
        "viewport": {"width": request.browser_config.viewport_width, "height": request.browser_config.viewport_height},
        "user_agent": request.browser_config.user_agent,
        "javascript_enabled": request.browser_config.javascript_enabled,
        "wait_for_selector": request.browser_config.wait_for_selector,
        "wait_timeout": request.browser_config.wait_timeout,
        "stealth_mode": request.browser_config.stealth_mode
    }
    
    schedule = None
    if request.schedule:
        schedule = {
            "enabled": request.schedule.enabled,
            "cron_expression": request.schedule.cron_expression,
            "timezone": request.schedule.timezone,
            "max_concurrent_jobs": request.schedule.max_concurrent_jobs
        }
    
    rate_limit = {
        "requests_per_second": request.rate_limit.requests_per_second,
        "requests_per_minute": request.rate_limit.requests_per_minute,
        "requests_per_hour": request.rate_limit.requests_per_hour,
        "burst_limit": request.rate_limit.burst_limit,
        "retry_attempts": request.rate_limit.retry_attempts,
        "retry_backoff": request.rate_limit.retry_backoff.value,
        "retry_delay_ms": request.rate_limit.retry_delay_ms
    }
    
    compliance = {
        "respect_robots_txt": request.compliance.respect_robots_txt,
        "user_agent_string": request.compliance.user_agent_string,
        "crawl_delay_seconds": request.compliance.crawl_delay_seconds,
        "domain_allowlist": request.compliance.domain_allowlist,
        "domain_blocklist": request.compliance.domain_blocklist,
        "pii_redaction_enabled": request.compliance.pii_redaction_enabled,
        "sensitive_field_patterns": request.compliance.sensitive_field_patterns
    }
    
    proxy_config = {
        "enabled": request.proxy_config.enabled,
        "rotation_strategy": request.proxy_config.rotation_strategy.value,
        "proxy_pool_id": str(request.proxy_config.proxy_pool_id) if request.proxy_config.proxy_pool_id else None,
        "sticky_sessions": request.proxy_config.sticky_sessions,
        "session_duration_minutes": request.proxy_config.session_duration_minutes
    }
    
    authentication = None
    if request.authentication:
        authentication = {
            "type": request.authentication.type.value,
            "credentials_ref": request.authentication.credentials_ref
        }
    
    target = create_scraping_target(
        organization_id=org_id,
        name=request.name,
        url=request.url,
        target_type=request.target_type,
        created_by=user_id,
        description=request.description,
        extraction_config=extraction_config,
        browser_config=browser_config,
        schedule=schedule,
        rate_limit=rate_limit,
        compliance=compliance,
        proxy_config=proxy_config,
        tags=request.tags
    )
    
    if authentication:
        target.authentication = authentication
    
    db.add(target)
    db.commit()
    db.refresh(target)
    
    logger.info("Created scraping target", target_id=str(target.id), name=target.name)
    
    return _target_to_detail(target)


@router.get("/targets/{target_id}", response_model=ScrapingTargetDetail)
async def get_target(
    target_id: UUID,
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific target."""
    target = db.query(ScrapingTarget).filter(
        ScrapingTarget.id == target_id,
        ScrapingTarget.organization_id == org_id
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    return _target_to_detail(target)


@router.put("/targets/{target_id}", response_model=ScrapingTargetDetail)
async def update_target(
    target_id: UUID,
    request: UpdateTargetRequest,
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Update a scraping target."""
    target = db.query(ScrapingTarget).filter(
        ScrapingTarget.id == target_id,
        ScrapingTarget.organization_id == org_id
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    # Check if jobs are in progress
    active_jobs = db.query(ScrapingJob).filter(
        ScrapingJob.target_id == target_id,
        ScrapingJob.status.in_([
            JobStatus.PENDING.value, JobStatus.QUEUED.value,
            JobStatus.VALIDATING.value, JobStatus.BROWSER_ACQUIRING.value,
            JobStatus.NAVIGATING.value, JobStatus.EXTRACTING.value,
            JobStatus.TRANSFORMING.value, JobStatus.STORING.value
        ])
    ).count()
    
    if active_jobs > 0:
        raise HTTPException(status_code=409, detail=f"Cannot modify target with {active_jobs} active jobs")
    
    # Update fields
    if request.name is not None:
        target.name = request.name
    if request.description is not None:
        target.description = request.description
    if request.target_type is not None:
        target.target_type = request.target_type.value
    if request.status is not None:
        target.status = request.status.value
    if request.tags is not None:
        target.tags = request.tags
    
    # Update nested configs
    if request.extraction_config:
        target.extraction_config = {
            "method": request.extraction_config.method.value,
            "llm_provider": request.extraction_config.llm_provider.value if request.extraction_config.llm_provider else None,
            "extraction_schema": request.extraction_config.extraction_schema,
            "visual_hints": request.extraction_config.visual_hints,
            "max_depth": request.extraction_config.max_depth,
            "follow_links": request.extraction_config.follow_links,
            "link_selectors": request.extraction_config.link_selectors
        }
    
    if request.browser_config:
        target.browser_config = {
            "engine": request.browser_config.engine.value,
            "headless": request.browser_config.headless,
            "viewport": {"width": request.browser_config.viewport_width, "height": request.browser_config.viewport_height},
            "user_agent": request.browser_config.user_agent,
            "javascript_enabled": request.browser_config.javascript_enabled,
            "wait_for_selector": request.browser_config.wait_for_selector,
            "wait_timeout": request.browser_config.wait_timeout,
            "stealth_mode": request.browser_config.stealth_mode
        }
    
    if request.rate_limit:
        target.rate_limit = {
            "requests_per_second": request.rate_limit.requests_per_second,
            "requests_per_minute": request.rate_limit.requests_per_minute,
            "requests_per_hour": request.rate_limit.requests_per_hour,
            "burst_limit": request.rate_limit.burst_limit,
            "retry_attempts": request.rate_limit.retry_attempts,
            "retry_backoff": request.rate_limit.retry_backoff.value,
            "retry_delay_ms": request.rate_limit.retry_delay_ms
        }
    
    if request.compliance:
        target.compliance = {
            "respect_robots_txt": request.compliance.respect_robots_txt,
            "user_agent_string": request.compliance.user_agent_string,
            "crawl_delay_seconds": request.compliance.crawl_delay_seconds,
            "domain_allowlist": request.compliance.domain_allowlist,
            "domain_blocklist": request.compliance.domain_blocklist,
            "pii_redaction_enabled": request.compliance.pii_redaction_enabled,
            "sensitive_field_patterns": request.compliance.sensitive_field_patterns
        }
    
    if request.proxy_config:
        target.proxy_config = {
            "enabled": request.proxy_config.enabled,
            "rotation_strategy": request.proxy_config.rotation_strategy.value,
            "proxy_pool_id": str(request.proxy_config.proxy_pool_id) if request.proxy_config.proxy_pool_id else None,
            "sticky_sessions": request.proxy_config.sticky_sessions,
            "session_duration_minutes": request.proxy_config.session_duration_minutes
        }
    
    if request.schedule is not None:
        if request.schedule:
            target.schedule = {
                "enabled": request.schedule.enabled,
                "cron_expression": request.schedule.cron_expression,
                "timezone": request.schedule.timezone,
                "max_concurrent_jobs": request.schedule.max_concurrent_jobs
            }
        else:
            target.schedule = None
    
    if request.authentication is not None:
        if request.authentication:
            target.authentication = {
                "type": request.authentication.type.value,
                "credentials_ref": request.authentication.credentials_ref
            }
        else:
            target.authentication = None
    
    target.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(target)
    
    logger.info("Updated scraping target", target_id=str(target.id))
    
    return _target_to_detail(target)


@router.delete("/targets/{target_id}", status_code=204)
async def delete_target(
    target_id: UUID,
    force: bool = Query(default=False, description="Hard delete if no jobs exist"),
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Archive a scraping target (soft delete)."""
    target = db.query(ScrapingTarget).filter(
        ScrapingTarget.id == target_id,
        ScrapingTarget.organization_id == org_id
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    job_count = db.query(ScrapingJob).filter(ScrapingJob.target_id == target_id).count()
    
    if force and job_count == 0:
        # Hard delete
        db.delete(target)
        db.commit()
        logger.info("Hard deleted scraping target", target_id=str(target_id))
    else:
        # Soft delete (archive)
        if job_count > 0:
            target.status = TargetStatus.ARCHIVED.value
        else:
            db.delete(target)
        db.commit()
        logger.info("Archived scraping target", target_id=str(target_id))
    
    return None


@router.post("/targets/{target_id}/validate", response_model=ValidateTargetResponse)
async def validate_target(
    target_id: UUID,
    request: ValidateTargetRequest,
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Validate target configuration without executing."""
    target = db.query(ScrapingTarget).filter(
        ScrapingTarget.id == target_id,
        ScrapingTarget.organization_id == org_id
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    errors = []
    warnings = []
    robots_check = None
    
    # Validate URL
    test_url = request.test_url or target.url
    parsed = urlparse(test_url)
    if not parsed.scheme in ('http', 'https'):
        errors.append(ValidationError(field="url", message="URL must use http/https protocol"))
    
    # Validate extraction schema
    if request.validate_schema and target.extraction_config.get("extraction_schema"):
        schema = target.extraction_config.get("extraction_schema")
        if not isinstance(schema, dict):
            errors.append(ValidationError(field="extraction_schema", message="Extraction schema must be a valid JSON object"))
    
    # Check robots.txt
    if request.validate_robots_txt:
        from ..compliance.robots_checker import RobotsChecker
        checker = RobotsChecker(db)
        domain = parsed.netloc
        robots_result = await checker.check_url(domain, test_url)
        robots_check = {
            "allowed": robots_result.allowed,
            "crawl_delay": robots_result.crawl_delay
        }
        if not robots_result.allowed:
            warnings.append(ValidationWarning(field="robots_txt", message="URL is disallowed by robots.txt"))
    
    valid = len(errors) == 0
    
    return ValidateTargetResponse(
        valid=valid,
        errors=errors,
        warnings=warnings,
        robots_txt_check=robots_check
    )


@router.post("/targets/{target_id}/execute", response_model=ExecuteTargetResponse, status_code=202)
async def execute_target(
    target_id: UUID,
    request: ExecuteTargetRequest,
    background_tasks: BackgroundTasks,
    org_id: UUID = Depends(get_organization_id),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Trigger immediate execution of a target."""
    target = db.query(ScrapingTarget).filter(
        ScrapingTarget.id == target_id,
        ScrapingTarget.organization_id == org_id
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    if target.status != TargetStatus.ACTIVE.value:
        raise HTTPException(status_code=409, detail=f"Target is not active (status: {target.status})")
    
    # Create configuration snapshot
    configuration = {
        "target_id": str(target.id),
        "target_name": target.name,
        "url": target.url,
        "target_type": target.target_type,
        "extraction_config": target.extraction_config,
        "browser_config": target.browser_config,
        "rate_limit": target.rate_limit,
        "compliance": target.compliance,
        "proxy_config": target.proxy_config,
        "authentication": target.authentication,
        "override_config": request.override_config
    }
    
    # Create job
    correlation_id = str(uuid4())
    job = create_scraping_job(
        organization_id=org_id,
        target_id=target_id,
        created_by=user_id,
        configuration=configuration,
        priority=request.priority,
        triggered_by=TriggeredBy.API,
        correlation_id=correlation_id
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Initialize pipeline stages
    for stage in PipelineStage:
        stage_detail = JobStageDetail(
            job_id=job.id,
            organization_id=org_id,
            stage=stage.value,
            status="PENDING"
        )
        db.add(stage_detail)
    
    db.commit()
    
    # Queue job
    job.status = JobStatus.QUEUED.value
    db.commit()
    
    # Start background processing
    process_scraping_job.delay(str(job.id))
    
    logger.info("Queued scraping job", job_id=str(job.id), target_id=str(target_id))
    
    return ExecuteTargetResponse(
        job_id=job.id,
        status=JobStatus.QUEUED.value,
        queue_position=1,  # TODO: Calculate actual position
        estimated_start_time=None
    )


# =============================================================================
# API ENDPOINTS - ScrapingJob
# =============================================================================

@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    target_id: Optional[UUID] = Query(None),
    status: Optional[List[JobStatus]] = Query(None),
    triggered_by: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    priority_min: Optional[int] = Query(None, ge=1, le=10),
    priority_max: Optional[int] = Query(None, ge=1, le=10),
    has_errors: Optional[bool] = Query(None),
    sort_by: str = Query(default="created_at", regex="^(created_at|started_at|completed_at|priority)$"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """List all scraping jobs with filtering and pagination."""
    query = db.query(ScrapingJob).filter(ScrapingJob.organization_id == org_id)
    
    if target_id:
        query = query.filter(ScrapingJob.target_id == target_id)
    
    if status:
        status_values = [s.value for s in status]
        query = query.filter(ScrapingJob.status.in_(status_values))
    
    if triggered_by:
        query = query.filter(ScrapingJob.triggered_by == triggered_by)
    
    if date_from:
        query = query.filter(ScrapingJob.created_at >= date_from)
    
    if date_to:
        query = query.filter(ScrapingJob.created_at <= date_to)
    
    if priority_min is not None:
        query = query.filter(ScrapingJob.priority >= priority_min)
    
    if priority_max is not None:
        query = query.filter(ScrapingJob.priority <= priority_max)
    
    if has_errors is not None:
        if has_errors:
            query = query.filter(ScrapingJob.errors.any())
        # TODO: Add else case to filter jobs without errors
    
    # Aggregation
    total = query.count()
    total_pages = (total + limit - 1) // limit
    
    status_counts = db.query(
        ScrapingJob.status,
        func.count(ScrapingJob.id)
    ).filter(
        ScrapingJob.organization_id == org_id
    ).group_by(ScrapingJob.status).all()
    
    by_status = {status: count for status, count in status_counts}
    
    # Apply sorting
    sort_column = getattr(ScrapingJob, sort_by)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)
    
    offset = (page - 1) * limit
    jobs = query.offset(offset).limit(limit).all()
    
    return JobListResponse(
        data=[
            JobSummary(
                id=j.id,
                target_id=j.target_id,
                status=j.status,
                priority=j.priority,
                progress_percent_complete=j.progress_percent_complete,
                created_at=j.created_at,
                started_at=j.started_at,
                completed_at=j.completed_at
            )
            for j in jobs
        ],
        aggregation={
            "by_status": by_status,
            "total_execution_time_ms": sum(j.resources_compute_time_ms for j in jobs),
            "total_records_extracted": sum(j.results_extracted_record_count for j in jobs)
        },
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    )


@router.get("/jobs/{job_id}", response_model=ScrapingJobDetail)
async def get_job(
    job_id: UUID,
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Get detailed job information including execution stages."""
    job = db.query(ScrapingJob).filter(
        ScrapingJob.id == job_id,
        ScrapingJob.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    stages = db.query(JobStageDetail).filter(
        JobStageDetail.job_id == job_id
    ).order_by(JobStageDetail.created_at).all()
    
    errors = db.query(JobError).filter(
        JobError.job_id == job_id
    ).order_by(JobError.occurred_at.desc()).all()
    
    return ScrapingJobDetail(
        id=job.id,
        organization_id=job.organization_id,
        target_id=job.target_id,
        configuration=job.configuration,
        status=job.status,
        priority=job.priority,
        scheduled_at=job.scheduled_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        estimated_duration_ms=job.estimated_duration_ms,
        progress=JobProgressDetail(
            total_pages=job.progress_total_pages,
            processed_pages=job.progress_processed_pages,
            failed_pages=job.progress_failed_pages,
            current_url=job.progress_current_url,
            current_stage=job.progress_stage,
            percent_complete=job.progress_percent_complete
        ),
        results=JobResultsDetail(
            raw_content_count=job.results_raw_content_count,
            extracted_record_count=job.results_extracted_record_count,
            storage_bytes_used=job.results_storage_bytes_used,
            output_location=job.results_output_location
        ),
        resources=ResourceUsageDetail(
            browser_sessions_used=job.resources_browser_sessions_used,
            proxy_requests_made=job.resources_proxy_requests_made,
            llm_tokens_consumed=job.resources_llm_tokens_consumed,
            compute_time_ms=job.resources_compute_time_ms
        ),
        triggered_by=job.triggered_by,
        correlation_id=job.correlation_id,
        created_at=job.created_at,
        created_by=job.created_by,
        stages=[
            JobStageDetailResponse(
                stage=s.stage,
                status=s.status,
                started_at=s.started_at,
                completed_at=s.completed_at,
                duration_ms=s.duration_ms,
                error_message=s.error_message
            )
            for s in stages
        ],
        errors=[
            JobErrorResponse(
                id=e.id,
                stage=e.stage,
                error_code=e.error_code,
                error_message=e.error_message,
                url=e.url,
                retryable=e.retryable,
                retry_count=e.retry_count,
                occurred_at=e.occurred_at,
                resolved_at=e.resolved_at
            )
            for e in errors
        ]
    )


@router.delete("/jobs/{job_id}", status_code=202)
async def cancel_job(
    job_id: UUID,
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Cancel a running or queued job."""
    job = db.query(ScrapingJob).filter(
        ScrapingJob.id == job_id,
        ScrapingJob.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Can only cancel jobs that haven't completed
    terminal_states = [
        JobStatus.COMPLETED.value, JobStatus.FAILED.value,
        JobStatus.CANCELLED.value, JobStatus.PARTIAL_SUCCESS.value
    ]
    
    if job.status in terminal_states:
        raise HTTPException(status_code=409, detail=f"Job already in terminal state: {job.status}")
    
    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.utcnow()
    db.commit()
    
    logger.info("Cancelled scraping job", job_id=str(job_id))
    
    return {"status": "CANCELLED", "job_id": str(job_id)}


@router.get("/jobs/{job_id}/progress", response_model=JobProgressResponse)
async def get_job_progress(
    job_id: UUID,
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Get real-time job progress."""
    job = db.query(ScrapingJob).filter(
        ScrapingJob.id == job_id,
        ScrapingJob.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobProgressResponse(
        job_id=job.id,
        status=job.status,
        progress=JobProgressDetail(
            total_pages=job.progress_total_pages,
            processed_pages=job.progress_processed_pages,
            failed_pages=job.progress_failed_pages,
            current_url=job.progress_current_url,
            current_stage=job.progress_stage,
            percent_complete=job.progress_percent_complete
        ),
        last_update=datetime.utcnow()
    )


@router.get("/jobs/{job_id}/results")
async def get_job_results(
    job_id: UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    format: str = Query(default="json", regex="^(json|csv|ndjson)$"),
    include_raw: bool = Query(default=False),
    fields: Optional[List[str]] = Query(None),
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Get extracted data results for a job."""
    job = db.query(ScrapingJob).filter(
        ScrapingJob.id == job_id,
        ScrapingJob.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    query = db.query(ExtractedData).filter(
        ExtractedData.job_id == job_id,
        ExtractedData.organization_id == org_id
    )
    
    total = query.count()
    offset = (page - 1) * limit
    data = query.offset(offset).limit(limit).all()
    
    return {
        "job_id": str(job_id),
        "format": format,
        "total_records": total,
        "data": [
            {
                "id": str(d.id),
                "raw_content_id": str(d.raw_content_id),
                "extraction_method": d.extraction_method,
                "confidence": float(d.extraction_confidence_score) if d.extraction_confidence_score else None,
                "data": d.data,
                "created_at": d.created_at.isoformat()
            }
            for d in data
        ],
        "page": page,
        "limit": limit
    }


@router.post("/jobs/{job_id}/retry", status_code=202)
async def retry_job(
    job_id: UUID,
    request: RetryJobRequest,
    background_tasks: BackgroundTasks,
    org_id: UUID = Depends(get_organization_id),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Retry a failed or partially successful job."""
    original_job = db.query(ScrapingJob).filter(
        ScrapingJob.id == job_id,
        ScrapingJob.organization_id == org_id
    ).first()
    
    if not original_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if original_job.status not in [JobStatus.FAILED.value, JobStatus.PARTIAL_SUCCESS.value]:
        raise HTTPException(status_code=409, detail="Only failed or partially successful jobs can be retried")
    
    # Create new job with same configuration
    correlation_id = f"retry:{job_id}:{uuid4()}"
    new_job = create_scraping_job(
        organization_id=org_id,
        target_id=original_job.target_id,
        created_by=user_id,
        configuration=original_job.configuration,
        priority=original_job.priority,
        triggered_by=TriggeredBy.MANUAL,
        correlation_id=correlation_id
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # Initialize stages
    for stage in PipelineStage:
        stage_detail = JobStageDetail(
            job_id=new_job.id,
            organization_id=org_id,
            stage=stage.value,
            status="PENDING"
        )
        db.add(stage_detail)
    
    db.commit()
    
    # Queue new job
    new_job.status = JobStatus.QUEUED.value
    db.commit()
    
    process_scraping_job.delay(str(new_job.id))
    
    logger.info("Created retry job", original_job_id=str(job_id), new_job_id=str(new_job.id))
    
    return {
        "original_job_id": str(job_id),
        "new_job_id": str(new_job.id),
        "status": JobStatus.QUEUED.value
    }


# =============================================================================
# API ENDPOINTS - Content
# =============================================================================

@router.get("/content/raw/{content_id}", response_model=RawContentResponse)
async def get_raw_content(
    content_id: UUID,
    include_html: bool = Query(default=True),
    include_screenshot: bool = Query(default=False),
    include_har: bool = Query(default=False),
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Retrieve raw content by ID."""
    content = db.query(RawContent).filter(
        RawContent.id == content_id,
        RawContent.organization_id == org_id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    storage = {}
    if include_html:
        storage["html"] = content.storage_html_path
    if include_screenshot:
        storage["screenshot"] = content.storage_screenshot_path
    if include_har:
        storage["har"] = content.storage_har_path
    
    return RawContentResponse(
        id=content.id,
        job_id=content.job_id,
        source_url=content.source_url,
        source_final_url=content.source_final_url,
        source_domain=content.source_domain,
        source_http_status=content.source_http_status,
        storage=storage,
        metadata={
            "title": content.meta_title,
            "description": content.meta_description,
            "language": content.meta_language,
            "og_tags": content.meta_og_tags,
            "structured_data": content.meta_structured_data
        },
        capture={
            "method": content.capture_method,
            "browser_version": content.capture_browser_version,
            "javascript_executed": content.capture_javascript_executed,
            "wait_time_ms": content.capture_wait_time_ms
        },
        content_hash=content.content_hash,
        is_duplicate=content.is_duplicate,
        processing_status=content.processing_status,
        created_at=content.created_at
    )


@router.get("/content/extracted/{extracted_data_id}", response_model=ExtractedDataResponse)
async def get_extracted_data(
    extracted_data_id: UUID,
    format: str = Query(default="json", regex="^(json|markdown|flattened)$"),
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Retrieve extracted data by ID."""
    data = db.query(ExtractedData).filter(
        ExtractedData.id == extracted_data_id,
        ExtractedData.organization_id == org_id
    ).first()
    
    if not data:
        raise HTTPException(status_code=404, detail="Extracted data not found")
    
    return ExtractedDataResponse(
        id=data.id,
        job_id=data.job_id,
        raw_content_id=data.raw_content_id,
        extraction_method=data.extraction_method,
        extraction_confidence_score=float(data.extraction_confidence_score) if data.extraction_confidence_score else 0.0,
        data=data.data,
        validation={
            "schema_valid": data.validation_schema_valid,
            "errors": data.validation_errors,
            "data_quality_score": float(data.validation_data_quality_score) if data.validation_data_quality_score else 0.0
        },
        post_processing={
            "pii_redaction_applied": data.post_pii_redaction_applied,
            "redacted_fields": data.post_redacted_fields,
            "normalized_fields": data.post_normalized_fields,
            "enriched_fields": data.post_enriched_fields
        },
        created_at=data.created_at
    )


@router.get("/content")
async def list_content(
    job_id: Optional[UUID] = Query(None),
    domain: Optional[str] = Query(None),
    processing_status: Optional[str] = Query(None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """List raw content with filtering."""
    query = db.query(RawContent).filter(RawContent.organization_id == org_id)
    
    if job_id:
        query = query.filter(RawContent.job_id == job_id)
    
    if domain:
        query = query.filter(RawContent.source_domain == domain)
    
    if processing_status:
        query = query.filter(RawContent.processing_status == processing_status)
    
    total = query.count()
    offset = (page - 1) * limit
    items = query.order_by(RawContent.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "items": [
            {
                "id": str(item.id),
                "job_id": str(item.job_id),
                "source_url": item.source_url,
                "source_domain": item.source_domain,
                "processing_status": item.processing_status,
                "created_at": item.created_at.isoformat()
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


# =============================================================================
# API ENDPOINTS - Compliance
# =============================================================================

@router.get("/compliance/logs")
async def list_compliance_logs(
    event_type: Optional[List[ComplianceEventType]] = Query(None),
    severity: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    job_id: Optional[UUID] = Query(None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Query compliance logs."""
    query = db.query(ComplianceLog).filter(ComplianceLog.organization_id == org_id)
    
    if event_type:
        types = [t.value for t in event_type]
        query = query.filter(ComplianceLog.event_type.in_(types))
    
    if severity:
        query = query.filter(ComplianceLog.severity == severity)
    
    if domain:
        query = query.filter(ComplianceLog.request_url.contains(domain))
    
    if date_from:
        query = query.filter(ComplianceLog.created_at >= date_from)
    
    if date_to:
        query = query.filter(ComplianceLog.created_at <= date_to)
    
    if job_id:
        query = query.filter(ComplianceLog.job_id == job_id)
    
    total = query.count()
    offset = (page - 1) * limit
    logs = query.order_by(ComplianceLog.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "items": [
            {
                "id": str(log.id),
                "event_type": log.event_type,
                "severity": log.severity,
                "request_url": log.request_url,
                "request_timestamp": log.request_timestamp.isoformat(),
                "response_action_taken": log.response_action_taken,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/compliance/summary", response_model=ComplianceSummaryResponse)
async def get_compliance_summary(
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Get compliance summary for organization."""
    query = db.query(ComplianceLog).filter(
        ComplianceLog.organization_id == org_id,
        ComplianceLog.created_at >= period_start,
        ComplianceLog.created_at <= period_end
    )
    
    total_logs = query.count()
    
    robots_checks = query.filter(ComplianceLog.event_type == ComplianceEventType.ROBOTS_TXT_CHECK.value).count()
    allowed = query.filter(
        ComplianceLog.event_type == ComplianceEventType.ROBOTS_TXT_CHECK.value,
        ComplianceLog.robots_txt_check.isnot(None)
    ).count()  # Simplified
    
    rate_limits = query.filter(ComplianceLog.event_type == ComplianceEventType.RATE_LIMIT_APPLIED.value).count()
    pii_detections = query.filter(ComplianceLog.event_type == ComplianceEventType.PII_DETECTED.value).count()
    domain_blocks = query.filter(ComplianceLog.event_type == ComplianceEventType.DOMAIN_BLOCKED.value).count()
    
    return ComplianceSummaryResponse(
        period={"start": period_start, "end": period_end},
        robots_txt_compliance={
            "total_checks": robots_checks,
            "allowed": allowed,
            "blocked": robots_checks - allowed,
            "crawl_delays_respected": 0  # TODO: Calculate from data
        },
        rate_limiting={
            "total_requests": total_logs,
            "throttled_requests": rate_limits,
            "average_delay_ms": 0  # TODO: Calculate
        },
        pii_detection={
            "scans_performed": total_logs,
            "detections": pii_detections,
            "redactions_applied": query.filter(ComplianceLog.event_type == ComplianceEventType.PII_REDACTED.value).count()
        },
        domain_policies={
            "allowlisted": 0,  # TODO: Implement
            "blocklisted": domain_blocks,
            "blocked_requests": domain_blocks
        }
    )


# =============================================================================
# API ENDPOINTS - Health & Admin
# =============================================================================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    db: Session = Depends(get_db)
):
    """Enhanced health check endpoint."""
    components = {}
    metrics = {}
    
    # Database check
    try:
        db.execute("SELECT 1")
        components["database"] = ComponentHealth(status="healthy", latency_ms=0)
    except Exception as e:
        components["database"] = ComponentHealth(status="unhealthy", message=str(e))
    
    # Queue check (Redis)
    try:
        from ..shared.database import redis_client
        redis_client.ping()
        components["queue"] = ComponentHealth(status="healthy", latency_ms=0)
    except:
        components["queue"] = ComponentHealth(status="degraded", message="Redis not available")
    
    # Active jobs metrics
    active_jobs = db.query(ScrapingJob).filter(
        ScrapingJob.status.in_([
            JobStatus.QUEUED.value, JobStatus.VALIDATING.value,
            JobStatus.BROWSER_ACQUIRING.value, JobStatus.NAVIGATING.value,
            JobStatus.EXTRACTING.value, JobStatus.TRANSFORMING.value,
            JobStatus.STORING.value
        ])
    ).count()
    
    queued_jobs = db.query(ScrapingJob).filter(
        ScrapingJob.status == JobStatus.QUEUED.value
    ).count()
    
    metrics = {
        "active_jobs": active_jobs,
        "queued_jobs": queued_jobs,
        "available_browsers": 5,  # TODO: Get from pool
        "average_wait_time_ms": 0  # TODO: Calculate
    }
    
    # Determine overall status
    if any(c.status == "unhealthy" for c in components.values()):
        overall_status = "unhealthy"
    elif any(c.status == "degraded" for c in components.values()):
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return HealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        components={k: v.dict() for k, v in components.items()},
        metrics=metrics
    )


@router.get("/metrics")
async def metrics_endpoint(request: Request):
    """Prometheus-compatible metrics endpoint."""
    metrics = get_metrics()

    if not metrics:
        return Response(
            content="Metrics collection is disabled",
            status_code=503,
            media_type="text/plain"
        )

    try:
        metrics_data = metrics.get_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        return Response(
            content=f"Error generating metrics: {e}",
            status_code=500,
            media_type="text/plain"
        )


@router.post("/admin/cleanup")
async def trigger_cleanup(
    days: int = Query(default=30, ge=1, le=365),
    background_tasks: BackgroundTasks = None
):
    """Trigger content cleanup for old data."""
    cleanup_old_content.delay(days)
    return {"message": f"Cleanup initiated for content older than {days} days", "status": "processing"}


# =============================================================================
# API ENDPOINTS - Proxy Pools
# =============================================================================

@router.post("/proxy-pools", response_model=ProxyPoolResponse)
async def create_proxy_pool_endpoint(
    request: CreateProxyPoolRequest,
    org_id: UUID = Depends(get_organization_id),
    db: Session = Depends(get_db)
):
    """Create a proxy pool."""
    pool = create_proxy_pool(
        organization_id=org_id,
        name=request.name,
        proxies=request.proxies,
        rotation_strategy=request.rotation_strategy
    )
    
    db.add(pool)
    db.commit()
    db.refresh(pool)
    
    return ProxyPoolResponse(
        id=pool.id,
        name=pool.name,
        proxy_count=len(pool.proxies) if pool.proxies else 0,
        rotation_strategy=pool.rotation_strategy,
        created_at=pool.created_at
    )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _target_to_detail(target: ScrapingTarget) -> ScrapingTargetDetail:
    """Convert ScrapingTarget to ScrapingTargetDetail response."""
    return ScrapingTargetDetail(
        id=target.id,
        organization_id=target.organization_id,
        name=target.name,
        url=target.url,
        target_type=target.target_type,
        status=target.status,
        created_at=target.created_at,
        updated_at=target.updated_at,
        last_success_at=target.last_success_at,
        success_count=target.success_count,
        error_count=target.error_count,
        average_execution_time_ms=target.average_execution_time_ms,
        tags=target.tags or [],
        description=target.description,
        url_pattern=target.url_pattern,
        extraction_config=target.extraction_config or {},
        browser_config=target.browser_config or {},
        schedule=target.schedule,
        rate_limit=target.rate_limit or {},
        compliance=target.compliance or {},
        proxy_config=target.proxy_config or {},
        authentication=target.authentication,
        created_by=target.created_by,
        last_error_at=target.last_error_at
    )


# Include the router in the main app
app.include_router(router)

# Legacy compatibility routes (redirect to new endpoints)
@app.get("/health")
async def legacy_health_check():
    """Legacy health check - redirects to new endpoint."""
    return {"status": "healthy", "note": "Use /api/v1/ingestion/health for spec-compliant endpoint"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
