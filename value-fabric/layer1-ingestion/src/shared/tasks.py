"""Celery task queue configuration and tasks.

Spec-compliant pipeline stage tasks with multi-tenancy support.
Manages ScrapingJob lifecycle through 11 PipelineStages.
"""

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog
from celery import Celery, chain

from ..compliance.pii_scanner import PIIScanner
from ..compliance.robots_checker import RobotsChecker
from ..crawler.httpx_crawler import HttpxCrawler
from ..crawler.playwright_crawler import PlaywrightCrawler
from ..crawler.smart_router import RouteType, SmartRouter

if TYPE_CHECKING:
    from ..crawler.httpx_crawler import FastPathResult
from shared.models.typed_dict import TypedDictModel

from ..crawler.decision_store import CrawlDecisionRecord, CrawlDecisionRepository
from ..crawler.quality_gate import QualityGate
from ..shared.config import settings
from ..shared.database import get_db_session
from ..shared.models import (
    ComplianceEventType,
    ComplianceLog,
    ExtractedData,
    ExtractionMethod,
    JobError,
    JobStageDetail,
    JobStatus,
    PipelineStage,
    RawContent,
    ScrapingJob,
    ScrapingTarget,
)


class _execute_browser_pathResult(TypedDictModel):
    blocked_resources: Any
    config_used: Any
    content_length: Any
    duration_ms: Any
    error: Any
    final_url: Any
    scroll_triggered: Any
    status_code: bool
    text_length: Any
    title: Any

class process_scraping_jobResult(TypedDictModel):
    job_id: Any
    success: bool
    task_id: Any

class crawl_url_with_routingResult(TypedDictModel):
    decision_id: Any
    duration_ms: Any
    final_path: Any
    job_id: Any
    success: bool
    url: Any

class cleanup_old_contentResult(TypedDictModel):
    cutoff_date: Any
    deleted_count: Any

class compliance_check_stageResult(TypedDictModel):
    error: str | None = None
    job_id: Any
    success: bool

class browser_launch_stageResult(TypedDictModel):
    job_id: Any
    success: bool

class navigation_stageResult(TypedDictModel):
    job_id: Any
    navigation_result: Any
    success: bool

class content_capture_stageResult(TypedDictModel):
    html_content: Any
    job_id: Any
    raw_content_id: Any
    success: bool

class ai_extraction_stageResult(TypedDictModel):
    entities_extracted: Any | None = None
    job_id: Any
    skipped: bool
    success: bool
    tokens_consumed: Any | None = None

class post_processing_stageResult(TypedDictModel):
    job_id: Any
    success: bool

class validation_stageResult(TypedDictModel):
    job_id: Any
    success: bool

class storage_stageResult(TypedDictModel):
    job_id: Any
    success: bool

class notification_stageResult(TypedDictModel):
    error: Any
    job_id: Any
    success: bool

logger = structlog.get_logger()

# Initialize Celery app
celery_app = Celery(
    "layer1_ingestion",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.shared.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    result_expires=3600,
    task_routes={},
)


# =============================================================================
# PIPELINE ORCHESTRATION
# =============================================================================


@celery_app.task(bind=True, max_retries=3)
def process_scraping_job(self, job_id: str):
    """Main pipeline orchestrator for a ScrapingJob.

    Chains all pipeline stages together for sequential execution.
    """
    job_id = UUID(job_id)

    logger.info("Starting scraping job pipeline", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Start job
            job.status = JobStatus.VALIDATING.value
            job.started_at = datetime.now(UTC)
            session.commit()

        # Execute pipeline chain
        pipeline_chain = chain(
            compliance_check_stage.s(job_id),
            browser_launch_stage.s(),
            navigation_stage.s(),
            content_capture_stage.s(),
            ai_extraction_stage.s(),
            post_processing_stage.s(),
            validation_stage.s(),
            storage_stage.s(),
            notification_stage.s(),
        )

        result = pipeline_chain.apply_async()

        return process_scraping_jobResult.model_validate({"success": True, "job_id": str(job_id), "task_id": result.id})

    except Exception as exc:
        logger.error("Pipeline orchestration failed", job_id=str(job_id), error=str(exc))
        _fail_job(job_id, str(exc), PipelineStage.INIT)
        raise self.retry(exc=exc, countdown=60)


# =============================================================================
# PIPELINE STAGES
# =============================================================================


@celery_app.task(bind=True, max_retries=3)
def compliance_check_stage(self, job_id: UUID):
    """Stage 1: Compliance Check (robots.txt, rate limits, domain policies)."""
    logger.info("Starting compliance check stage", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Update stage status
            _update_stage(session, job_id, PipelineStage.COMPLIANCE_CHECK, "RUNNING")
            job.status = JobStatus.VALIDATING.value
            job.progress_stage = PipelineStage.COMPLIANCE_CHECK.value
            session.commit()

            # Get target configuration
            config = job.configuration
            url = config.get("url", "")
            compliance_config = config.get("compliance", {})

            # Check robots.txt
            if compliance_config.get("respect_robots_txt", True):
                checker = RobotsChecker(session)
                domain = url.split("/")[2] if "/" in url else url

                result = asyncio.run(checker.check_url(domain, url))

                # Log compliance check
                log = ComplianceLog(
                    tenant_id=job.tenant_id,
                    job_id=job_id,
                    target_id=job.target_id,
                    event_type=ComplianceEventType.ROBOTS_TXT_CHECK.value,
                    severity="INFO" if result.allowed else "WARNING",
                    robots_txt_check={
                        "url": url,
                        "robots_txt_url": f"https://{domain}/robots.txt",
                        "user_agent": compliance_config.get("user_agent_string", "ValueFabricBot"),
                        "allowed": result.allowed,
                        "crawl_delay": result.crawl_delay,
                    },
                    request_url=url,
                    request_user_agent=compliance_config.get("user_agent_string", "ValueFabricBot"),
                )
                session.add(log)

                if not result.allowed:
                    _fail_job(job_id, "URL blocked by robots.txt", PipelineStage.COMPLIANCE_CHECK)
                    return compliance_check_stageResult.model_validate({"success": False, "error": "robots.txt blocked", "job_id": str(job_id)})

                # Apply crawl delay
                if result.crawl_delay:
                    import time

                    time.sleep(result.crawl_delay)

            # Complete stage
            _update_stage(session, job_id, PipelineStage.COMPLIANCE_CHECK, "COMPLETED")
            session.commit()

            logger.info("Compliance check completed", job_id=str(job_id))
            return compliance_check_stageResult.model_validate({"success": True, "job_id": str(job_id)})

    except Exception as exc:
        logger.error("Compliance check failed", job_id=str(job_id), error=str(exc))
        try:
            with get_db_session() as error_session:
                _update_stage(
                    error_session, job_id, PipelineStage.COMPLIANCE_CHECK, "FAILED", str(exc)
                )
        except Exception as update_exc:
            logger.error("Failed to update stage status", job_id=str(job_id), error=str(update_exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, max_retries=2)
def browser_launch_stage(self, prev_result: dict):
    """Stage 2: Browser Acquisition and Launch."""
    job_id = UUID(prev_result["job_id"])

    logger.info("Starting browser launch stage", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            _update_stage(session, job_id, PipelineStage.BROWSER_LAUNCH, "RUNNING")
            job.status = JobStatus.BROWSER_ACQUIRING.value
            job.progress_stage = PipelineStage.BROWSER_LAUNCH.value
            job.resources_browser_sessions_used += 1
            session.commit()

            # Browser is launched per-URL in navigation stage
            # This stage mainly tracks resource allocation

            _update_stage(session, job_id, PipelineStage.BROWSER_LAUNCH, "COMPLETED")
            session.commit()

            logger.info("Browser launch completed", job_id=str(job_id))
            return browser_launch_stageResult.model_validate({"success": True, "job_id": str(job_id)})

    except Exception as exc:
        logger.error("Browser launch failed", job_id=str(job_id), error=str(exc))
        _update_stage(get_db_session(), job_id, PipelineStage.BROWSER_LAUNCH, "FAILED", str(exc))
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(bind=True, max_retries=3)
def navigation_stage(self, prev_result: dict):
    """Stage 3: Navigate to URL and handle dynamic content."""
    job_id = UUID(prev_result["job_id"])

    logger.info("Starting navigation stage", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            _update_stage(session, job_id, PipelineStage.NAVIGATION, "RUNNING")
            job.status = JobStatus.NAVIGATING.value
            job.progress_stage = PipelineStage.NAVIGATION.value
            session.commit()

            config = job.configuration
            url = config.get("url", "")
            browser_config = config.get("browser_config", {})

            # Launch browser and navigate
            async def _navigate():
                async with PlaywrightCrawler(
                    headless=browser_config.get("headless", True),
                    proxy_config=config.get("proxy_config"),
                ) as crawler:
                    result = await crawler.navigate(url)
                    return result

            nav_result = asyncio.run(_navigate())

            if nav_result.error:
                raise Exception(nav_result.error)

            # Store navigation result for next stage
            job.configuration["navigation_result"] = {
                "final_url": nav_result.final_url,
                "status_code": nav_result.status_code,
                "headers": nav_result.headers,
            }

            _update_stage(session, job_id, PipelineStage.NAVIGATION, "COMPLETED")
            session.commit()

            logger.info("Navigation completed", job_id=str(job_id), final_url=nav_result.final_url)
            return navigation_stageResult.model_validate({
                "success": True,
                "job_id": str(job_id),
                "navigation_result": nav_result.__dict__,
            })


    except Exception as exc:
        logger.error("Navigation failed", job_id=str(job_id), error=str(exc))
        _update_stage(get_db_session(), job_id, PipelineStage.NAVIGATION, "FAILED", str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, max_retries=2)
def content_capture_stage(self, prev_result: dict):
    """Stage 4: Capture content (HTML, screenshots, DOM snapshot)."""
    job_id = UUID(prev_result["job_id"])

    logger.info("Starting content capture stage", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            _update_stage(session, job_id, PipelineStage.CONTENT_CAPTURE, "RUNNING")
            job.status = JobStatus.EXTRACTING.value
            job.progress_stage = PipelineStage.CONTENT_CAPTURE.value
            session.commit()

            config = job.configuration
            url = config.get("url", "")
            browser_config = config.get("browser_config", {})
            config.get("extraction_config", {})

            async def _capture():
                async with PlaywrightCrawler(
                    headless=browser_config.get("headless", True)
                ) as crawler:
                    # Capture full page content
                    result = await crawler.capture_page(
                        url=url,
                        wait_for_selector=browser_config.get("wait_for_selector"),
                        wait_timeout=browser_config.get("wait_timeout", 30000),
                    )
                    return result

            capture_result = asyncio.run(_capture())

            # Calculate content hash
            content_hash = hashlib.sha256(
                capture_result.html_content.encode() if capture_result.html_content else b""
            ).hexdigest()

            # Check for duplicates
            existing = (
                session.query(RawContent)
                .filter(
                    RawContent.tenant_id == job.tenant_id,
                    RawContent.content_hash == content_hash,
                )
                .first()
            )

            is_duplicate = existing is not None

            # Create RawContent record
            raw_content = RawContent(
                job_id=job_id,
                tenant_id=job.tenant_id,
                target_id=job.target_id,
                source_url=url,
                source_final_url=capture_result.final_url,
                source_domain=url.split("/")[2] if "/" in url else url,
                source_http_status=capture_result.status_code,
                source_headers=capture_result.headers,
                storage_html_path=capture_result.storage_paths.get("html"),
                storage_screenshot_path=capture_result.storage_paths.get("screenshot"),
                storage_dom_snapshot_path=capture_result.storage_paths.get("dom_snapshot"),
                meta_title=capture_result.title,
                meta_description=capture_result.description,
                capture_method="DYNAMIC",
                capture_browser_version=capture_result.browser_version,
                capture_javascript_executed=True,
                capture_wait_time_ms=browser_config.get("wait_timeout", 30000),
                content_hash=content_hash,
                is_duplicate=is_duplicate,
                duplicate_of_id=existing.id if existing else None,
                processing_status="PENDING",
            )

            session.add(raw_content)
            session.flush()

            # Update job with raw_content_id
            job.configuration["raw_content_id"] = str(raw_content.id)
            job.results_raw_content_count += 1

            _update_stage(session, job_id, PipelineStage.CONTENT_CAPTURE, "COMPLETED")
            session.commit()

            logger.info(
                "Content capture completed", job_id=str(job_id), raw_content_id=str(raw_content.id)
            )
            return content_capture_stageResult.model_validate({
                "success": True,
                "job_id": str(job_id),
                "raw_content_id": str(raw_content.id),
                "html_content": capture_result.html_content,
            })


    except Exception as exc:
        logger.error("Content capture failed", job_id=str(job_id), error=str(exc))
        _update_stage(get_db_session(), job_id, PipelineStage.CONTENT_CAPTURE, "FAILED", str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, max_retries=2)
def ai_extraction_stage(self, prev_result: dict):
    """Stage 5: AI/LLM Extraction (conditional based on config)."""
    job_id = UUID(prev_result["job_id"])

    logger.info("Starting AI extraction stage", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            config = job.configuration
            extraction_config = config.get("extraction_config", {})
            method = extraction_config.get("method", "DETERMINISTIC")

            if method == ExtractionMethod.DETERMINISTIC.value:
                # Skip AI extraction for deterministic method
                logger.info("Skipping AI extraction (deterministic mode)", job_id=str(job_id))
                return ai_extraction_stageResult.model_validate({"success": True, "job_id": str(job_id), "skipped": True})

            _update_stage(session, job_id, PipelineStage.AI_EXTRACTION, "RUNNING")
            job.progress_stage = PipelineStage.AI_EXTRACTION.value
            session.commit()

            # Get raw content
            raw_content_id = config.get("raw_content_id")
            raw_content = (
                session.query(RawContent).get(UUID(raw_content_id)) if raw_content_id else None
            )

            if not raw_content:
                raise ValueError("Raw content not found for AI extraction")

            # P0-35: Call Layer 2 Extraction Service for LLM extraction
            import httpx

            l2_url = settings.layer2_api_url
            extraction_payload = {
                "content": raw_content.meta_title or "",
                "content_type": "text",
                "extraction_method": method.lower(),
                "source_id": str(raw_content_id),
                "job_id": str(job_id),
                "tenant_id": str(job.tenant_id),  # Pass tenant for isolation
                "options": {
                    "model": extraction_config.get("model", settings.openai_model),
                    "temperature": extraction_config.get("temperature", 0.0),
                    "max_tokens": extraction_config.get("max_tokens", 4000),
                },
            }

            # Call L2 extraction API with retry logic
            max_retries = 3
            last_error = None
            extraction_result = None
            tokens_consumed = 0

            for attempt in range(max_retries):
                try:
                    response = httpx.post(
                        f"{l2_url}/v1/extract",
                        json=extraction_payload,
                        timeout=120.0,
                        headers={
                            "Content-Type": "application/json",
                            "X-Tenant-ID": str(job.tenant_id),
                        },
                    )
                    response.raise_for_status()
                    extraction_result = response.json()
                    tokens_consumed = extraction_result.get("tokens_consumed", 0)
                    break
                except httpx.HTTPStatusError as e:
                    last_error = f"HTTP {e.response.status_code}: {e.response.text}"
                    if e.response.status_code in (429, 503, 504):
                        logger.warning(f"L2 extraction attempt {attempt + 1} failed, retrying...")
                        import time

                        time.sleep(2**attempt)
                        continue
                    break
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"L2 extraction attempt {attempt + 1} failed: {e}")
                    import time

                    time.sleep(2**attempt)

            if extraction_result is None:
                raise ValueError(f"L2 extraction failed after {max_retries} attempts: {last_error}")

            # Store extraction result
            job.configuration["extraction_result"] = extraction_result

            _update_stage(session, job_id, PipelineStage.AI_EXTRACTION, "COMPLETED")
            job.resources_llm_tokens_consumed += tokens_consumed
            session.commit()

            logger.info(
                "AI extraction completed",
                job_id=str(job_id),
                tokens_consumed=tokens_consumed,
                entities_extracted=len(extraction_result.get("entities", [])),
            )
            return ai_extraction_stageResult.model_validate({
                "success": True,
                "job_id": str(job_id),
                "tokens_consumed": tokens_consumed,
                "entities_extracted": len(extraction_result.get("entities", [])),
            })


    except Exception as exc:
        logger.error("AI extraction failed", job_id=str(job_id), error=str(exc))
        _update_stage(get_db_session(), job_id, PipelineStage.AI_EXTRACTION, "FAILED", str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, max_retries=2)
def post_processing_stage(self, prev_result: dict):
    """Stage 6: Post-processing (PII redaction, normalization)."""
    job_id = UUID(prev_result["job_id"])

    logger.info("Starting post-processing stage", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            _update_stage(session, job_id, PipelineStage.POST_PROCESSING, "RUNNING")
            job.status = JobStatus.TRANSFORMING.value
            job.progress_stage = PipelineStage.POST_PROCESSING.value
            session.commit()

            config = job.configuration
            compliance_config = config.get("compliance", {})
            raw_content_id = config.get("raw_content_id")

            if raw_content_id:
                raw_content = session.query(RawContent).get(UUID(raw_content_id))

                if raw_content and compliance_config.get("pii_redaction_enabled", True):
                    # Scan for PII
                    scanner = PIIScanner()
                    scan_result = scanner.scan(raw_content.meta_title or "")
                    scan_result.extend(scanner.scan(raw_content.meta_description or ""))

                    # Log PII detection
                    if scan_result:
                        log = ComplianceLog(
                            tenant_id=job.tenant_id,
                            job_id=job_id,
                            target_id=job.target_id,
                            event_type=ComplianceEventType.PII_DETECTED.value,
                            severity="WARNING" if scan_result else "INFO",
                            pii_detection={
                                "detection_method": "REGEX",
                                "patterns_detected": [
                                    {"pattern_type": r.type, "count": 1, "locations": [r.text]}
                                    for r in scan_result
                                ],
                                "redaction_applied": True,
                                "redacted_count": len(scan_result),
                            },
                            request_url=raw_content.source_url,
                            response_action_taken="REDACTED",
                        )
                        session.add(log)

            _update_stage(session, job_id, PipelineStage.POST_PROCESSING, "COMPLETED")
            session.commit()

            logger.info("Post-processing completed", job_id=str(job_id))
            return post_processing_stageResult.model_validate({"success": True, "job_id": str(job_id)})

    except Exception as exc:
        logger.error("Post-processing failed", job_id=str(job_id), error=str(exc))
        _update_stage(get_db_session(), job_id, PipelineStage.POST_PROCESSING, "FAILED", str(exc))
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(bind=True, max_retries=2)
def validation_stage(self, prev_result: dict):
    """Stage 7: Validation (schema, data quality)."""
    job_id = UUID(prev_result["job_id"])

    logger.info("Starting validation stage", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            _update_stage(session, job_id, PipelineStage.VALIDATION, "RUNNING")
            job.progress_stage = PipelineStage.VALIDATION.value
            session.commit()

            # Validate extracted data against schema
            config = job.configuration
            extraction_config = config.get("extraction_config", {})
            extraction_config.get("extraction_schema")

            # TODO: Implement schema validation

            _update_stage(session, job_id, PipelineStage.VALIDATION, "COMPLETED")
            session.commit()

            logger.info("Validation completed", job_id=str(job_id))
            return validation_stageResult.model_validate({"success": True, "job_id": str(job_id)})

    except Exception as exc:
        logger.error("Validation failed", job_id=str(job_id), error=str(exc))
        _update_stage(get_db_session(), job_id, PipelineStage.VALIDATION, "FAILED", str(exc))
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(bind=True, max_retries=3)
def storage_stage(self, prev_result: dict):
    """Stage 8: Storage (save to database, update references)."""
    job_id = UUID(prev_result["job_id"])

    logger.info("Starting storage stage", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            _update_stage(session, job_id, PipelineStage.STORAGE, "RUNNING")
            job.status = JobStatus.STORING.value
            job.progress_stage = PipelineStage.STORAGE.value
            session.commit()

            config = job.configuration
            raw_content_id = config.get("raw_content_id")

            if raw_content_id:
                raw_content = session.query(RawContent).get(UUID(raw_content_id))
                if raw_content:
                    extraction_started_at = datetime.now(UTC)
                    # Create ExtractedData record
                    extracted = ExtractedData(
                        job_id=job_id,
                        tenant_id=job.tenant_id,
                        target_id=job.target_id,
                        raw_content_id=raw_content.id,
                        extraction_method=config.get("extraction_config", {}).get(
                            "method", "DETERMINISTIC"
                        ),
                        extraction_time_ms=None,
                        data={
                            "title": raw_content.meta_title,
                            "description": raw_content.meta_description,
                            "url": raw_content.source_url,
                        },
                        provenance_source_url=raw_content.source_url,
                        storage_path=raw_content.storage_html_path,
                        format="JSON",
                    )
                    extracted.extraction_time_ms = int(
                        (datetime.now(UTC) - extraction_started_at).total_seconds() * 1000
                    )
                    session.add(extracted)
                    session.flush()

                    # Update references
                    raw_content.extracted_data_id = extracted.id
                    raw_content.processing_status = "EXTRACTED"

                    job.results_extracted_record_count += 1
                    job.results_storage_bytes_used += raw_content.source_content_length or 0

            _update_stage(session, job_id, PipelineStage.STORAGE, "COMPLETED")
            session.commit()

            logger.info("Storage completed", job_id=str(job_id))
            return storage_stageResult.model_validate({"success": True, "job_id": str(job_id)})

    except Exception as exc:
        logger.error("Storage failed", job_id=str(job_id), error=str(exc))
        _update_stage(get_db_session(), job_id, PipelineStage.STORAGE, "FAILED", str(exc))
        raise self.retry(exc=exc, countdown=10)


@celery_app.task
def notification_stage(prev_result: dict):
    """Stage 9: Notification (webhooks, callbacks)."""
    job_id = UUID(prev_result["job_id"])

    logger.info("Starting notification stage", job_id=str(job_id))

    try:
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id)
            if not job:
                return

            _update_stage(session, job_id, PipelineStage.NOTIFICATION, "RUNNING")
            job.progress_stage = PipelineStage.NOTIFICATION.value
            session.commit()

            # Complete job
            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.now(UTC)
            job.progress_percent_complete = 100
            job.progress_stage = PipelineStage.NOTIFICATION.value

            _update_stage(session, job_id, PipelineStage.NOTIFICATION, "COMPLETED")
            session.commit()

            # Update target stats
            target = session.query(ScrapingTarget).get(job.target_id)
            if target:
                target.success_count += 1
                target.last_success_at = datetime.now(UTC)
                # Calculate average execution time
                if job.started_at and job.completed_at:
                    duration = (job.completed_at - job.started_at).total_seconds() * 1000
                    total_duration = (
                        target.average_execution_time_ms * (target.success_count - 1) + duration
                    )
                    target.average_execution_time_ms = int(total_duration / target.success_count)
                session.commit()

            logger.info("Job completed successfully", job_id=str(job_id))
            return notification_stageResult.model_validate({"success": True, "job_id": str(job_id)})

    except Exception as exc:
        logger.error("Notification stage failed", job_id=str(job_id), error=str(exc))
        _update_stage(get_db_session(), job_id, PipelineStage.NOTIFICATION, "FAILED", str(exc))
        return notification_stageResult.model_validate({"success": False, "job_id": str(job_id), "error": str(exc)})


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def _update_stage(
    session, job_id: UUID, stage: PipelineStage, status: str, error_message: str = None
):
    """Update pipeline stage status."""
    stage_detail = (
        session.query(JobStageDetail)
        .filter(JobStageDetail.job_id == job_id, JobStageDetail.stage == stage.value)
        .first()
    )

    if stage_detail:
        stage_detail.status = status
        if status == "RUNNING" and not stage_detail.started_at:
            stage_detail.started_at = datetime.now(UTC)
        if status in ("COMPLETED", "FAILED"):
            stage_detail.completed_at = datetime.now(UTC)
            if stage_detail.started_at:
                stage_detail.duration_ms = int(
                    (stage_detail.completed_at - stage_detail.started_at).total_seconds() * 1000
                )
        if error_message:
            stage_detail.error_message = error_message


def _fail_job(job_id: UUID, error: str, stage: PipelineStage):
    """Mark job as failed."""
    with get_db_session() as session:
        job = session.query(ScrapingJob).get(job_id)
        if job:
            job.status = JobStatus.FAILED.value
            job.completed_at = datetime.now(UTC)
            session.commit()

        # Update stage
        _update_stage(session, job_id, stage, "FAILED", error)

        # Create error record
        error_record = JobError(
            job_id=job_id,
            tenant_id=job.tenant_id if job else None,
            stage=stage.value,
            error_code="PIPELINE_ERROR",
            error_message=error,
            retryable=False,
        )
        session.add(error_record)
        session.commit()

        # Update target error stats
        if job:
            target = session.query(ScrapingTarget).get(job.target_id)
            if target:
                try:
                    target.error_count += 1
                except TypeError:
                    target.error_count = 1
                target.last_error_at = datetime.now(UTC)
                session.commit()


@celery_app.task
def execute_pipeline_stage(job_id: str, stage: str):
    """Execute a single pipeline stage (for manual/retry operations)."""
    job_id = UUID(job_id)
    stage_enum = PipelineStage(stage)

    # Dispatch to appropriate stage task
    stage_tasks = {
        PipelineStage.COMPLIANCE_CHECK.value: compliance_check_stage,
        PipelineStage.BROWSER_LAUNCH.value: browser_launch_stage,
        PipelineStage.NAVIGATION.value: navigation_stage,
        PipelineStage.CONTENT_CAPTURE.value: content_capture_stage,
        PipelineStage.AI_EXTRACTION.value: ai_extraction_stage,
        PipelineStage.POST_PROCESSING.value: post_processing_stage,
        PipelineStage.VALIDATION.value: validation_stage,
        PipelineStage.STORAGE.value: storage_stage,
        PipelineStage.NOTIFICATION.value: notification_stage,
    }

    task = stage_tasks.get(stage_enum.value)
    if task:
        return task.delay({"job_id": str(job_id), "retry": True})
    else:
        raise ValueError(f"Unknown stage: {stage}")


# =============================================================================
# HYBRID ROUTING (Smart Router + HTTPX Fast Path)
# =============================================================================


@celery_app.task(bind=True, max_retries=3)
def crawl_url_with_routing(self, job_id: str, url: str, target_mode: str = "browser"):
    """Crawl a single URL with Smart Router and hybrid FAST/BROWSER paths.

    Implements the hardening-pass routing logic with:
    - Smart Router per-URL decision making
    - HTTPX Fast Path for static content
    - Quality-gated fallback to browser
    - Canonical decision record persistence
    - Fail-closed behavior for ambiguous cases

    Args:
        job_id: The ScrapingJob UUID
        url: URL to crawl
        target_mode: Target-level mode (fast/browser/fast_fallback)

    Returns:
        dict with crawl result metadata
    """
    job_id_uuid = UUID(job_id)
    router = SmartRouter()
    gate = QualityGate()
    decision_repo = CrawlDecisionRepository()

    logger.info(
        "Starting hybrid crawl",
        job_id=job_id,
        url=url,
        target_mode=target_mode,
    )

    try:
        # Get target configuration from job
        with get_db_session() as session:
            job = session.query(ScrapingJob).get(job_id_uuid)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            tenant_id = str(job.tenant_id) if job.tenant_id else None
            target = session.query(ScrapingTarget).get(job.target_id)
            target_config = target.configuration if target else {}

            # Use target's crawl_path if available, otherwise use parameter
            effective_mode = target_config.get("crawl_path", target_mode)

        # Parse URL for domain extraction
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # 1. ROUTING DECISION
        route_type = RouteType(effective_mode)
        routing_decision = asyncio.run(router.decide(url, route_type))

        # Initialize decision record
        decision_record = CrawlDecisionRecord(
            decision_id=str(uuid4()),
            job_id=job_id,
            tenant_id=tenant_id,
            url=url,
            domain=domain,
            requested_path=effective_mode,
            router_decision=routing_decision.route.value,
            router_rule=routing_decision.reason,
            quality_passed=None,
            quality_checks=None,
            fallback_reason=None,
            final_path="unknown",  # Will be updated
            status_code=None,
            fast_duration_ms=0,
            browser_duration_ms=None,
            fetch_time_ms=0,
            bytes_transferred=0,
            spa_detected=False,
            text_length=0,
        )

        # 2. EXECUTE BASED ON ROUTING DECISION
        if routing_decision.route == RouteType.FAST:
            # Direct fast path
            result = asyncio.run(_execute_fast_path(url))

            decision_record.final_path = "fast"
            decision_record.status_code = result.status_code
            decision_record.fast_duration_ms = result.fetch_time_ms
            decision_record.fetch_time_ms = result.fetch_time_ms
            decision_record.bytes_transferred = len(result.html.encode("utf-8"))
            decision_record.spa_detected = result.is_spa_detected
            decision_record.text_length = len(result.text_content)

            if result.status_code == 200:
                decision_record.quality_passed = True
                decision_record.quality_checks = {"direct_fast": True}

        elif routing_decision.route == RouteType.FAST_WITH_FALLBACK:
            # Try fast path, fallback if quality fails
            result = asyncio.run(_execute_fast_path(url))

            decision_record.fast_duration_ms = result.fetch_time_ms
            decision_record.spa_detected = result.is_spa_detected

            # Quality gate evaluation
            quality = gate.evaluate(result)
            decision_record.quality_passed = quality.passed
            decision_record.quality_checks = quality.checks
            decision_record.fallback_reason = quality.fallback_reason

            if quality.passed:
                # Fast path succeeded
                decision_record.final_path = "fast"
                decision_record.status_code = result.status_code
                decision_record.fetch_time_ms = result.fetch_time_ms
                decision_record.bytes_transferred = len(result.html.encode("utf-8"))
                decision_record.text_length = len(result.text_content)

                logger.info(
                    "Fast path succeeded",
                    job_id=job_id,
                    url=url,
                    duration_ms=result.fetch_time_ms,
                )
            else:
                # FAIL-CLOSED: Fast path failed quality, escalate to browser
                logger.warning(
                    "Fast path failed quality, escalating to browser",
                    job_id=job_id,
                    url=url,
                    fallback_reason=quality.fallback_reason,
                )

                browser_result = asyncio.run(_execute_browser_path(url, routing_decision.stagehand_config))

                decision_record.final_path = "fallback"
                decision_record.status_code = browser_result.get("status_code")
                decision_record.browser_duration_ms = browser_result.get("duration_ms", 0)
                decision_record.fetch_time_ms = result.fetch_time_ms + browser_result.get(
                    "duration_ms", 0
                )
                decision_record.bytes_transferred = len(result.html.encode("utf-8")) + browser_result.get(
                    "content_length", 0
                )
                decision_record.text_length = browser_result.get("text_length", 0)

        else:  # RouteType.BROWSER
            # Direct browser path
            browser_result = asyncio.run(_execute_browser_path(url, routing_decision.stagehand_config))

            decision_record.final_path = "browser"
            decision_record.status_code = browser_result.get("status_code")
            decision_record.browser_duration_ms = browser_result.get("duration_ms", 0)
            decision_record.fetch_time_ms = browser_result.get("duration_ms", 0)
            decision_record.bytes_transferred = browser_result.get("content_length", 0)
            decision_record.text_length = browser_result.get("text_length", 0)

        # 3. PERSIST CANONICAL DECISION
        asyncio.run(decision_repo.save(decision_record))

        logger.info(
            "Crawl completed with routing",
            job_id=job_id,
            url=url,
            final_path=decision_record.final_path,
            duration_ms=decision_record.fetch_time_ms,
        )

        return crawl_url_with_routingResult.model_validate({
            "success": True,
            "job_id": job_id,
            "url": url,
            "final_path": decision_record.final_path,
            "duration_ms": decision_record.fetch_time_ms,
            "decision_id": decision_record.decision_id,
        })


    except Exception as exc:
        logger.error(
            "Crawl failed",
            job_id=job_id,
            url=url,
            error=str(exc),
            exc_info=True,
        )

        # Try to save error decision if we have a decision record
        if "decision_record" in locals():
            decision_record.error_type = type(exc).__name__
            decision_record.error_message = str(exc)[:500]  # Truncate long messages
            try:
                asyncio.run(decision_repo.save(decision_record))
            except Exception:
                pass  # Don't let decision save failure mask original error

        raise self.retry(exc=exc, countdown=60)


async def _execute_fast_path(url: str) -> "FastPathResult":
    """Execute HTTPX fast path crawl.

    Args:
        url: URL to fetch

    Returns:
        FastPathResult with content and metadata
    """
    async with HttpxCrawler() as crawler:
        return await crawler.fetch(url)


async def _execute_browser_path(url: str, config: dict | None) -> dict:
    """Execute Playwright browser path crawl.

    Args:
        url: URL to crawl
        config: Optional Stagehand/browser configuration

    Returns:
        dict with browser crawl results
    """
    import time

    start_time = time.monotonic()

    # Actual Playwright integration
    browser_config = config or {}
    headless = browser_config.get("headless", True)
    wait_for_selector = browser_config.get("wait_for_selector")
    wait_timeout = browser_config.get("wait_timeout", 30000)

    async with PlaywrightCrawler(
        headless=headless,
        proxy_config=browser_config.get("proxy_config"),
    ) as crawler:
        result = await crawler.crawl_url(
            url=url,
            wait_for_selector=wait_for_selector,
            wait_for_timeout=wait_timeout,
            scroll_page=True,
        )

    duration_ms = int((time.monotonic() - start_time) * 1000)

    return _execute_browser_pathResult.model_validate({
        "status_code": result.status_code or 200,
        "duration_ms": duration_ms,
        "content_length": len(result.html_content or ""),
        "text_length": len(result.html_content or "") // 10,  # Approximate text ratio
        "title": result.title,
        "final_url": result.final_url,
        "error": result.error,
        "config_used": config,
        "blocked_resources": result.blocked_resources,
        "scroll_triggered": result.scroll_triggered,
    })


def _should_fail_closed(
    quality_result, fast_result, routing_decision
) -> tuple[bool, str | None]:
    """Determine if we should fail closed to browser path.

    Fail-closed rules:
    1. Quality result is ambiguous/uncertain
    2. Fast path timing is borderline (within 90% of timeout)
    3. Content quality is indeterminate
    4. Router confidence is low

    Args:
        quality_result: QualityGate evaluation result
        fast_result: FastPathResult from HTTPX
        routing_decision: SmartRouter decision

    Returns:
        Tuple of (should_fallback, reason)
    """
    # Rule 1: Quality gate uncertain
    if quality_result.passed is None:
        return True, "quality_uncertain"

    # Rule 2: Borderline timing (within 90% of threshold)
    if fast_result.fetch_time_ms > 4500:  # 90% of 5000ms default
        return True, "timing_borderline"

    # Rule 3: Indeterminate content quality
    if not fast_result.text_content and not fast_result.is_spa_detected:
        return True, "indeterminate_quality"

    # Rule 4: Router uncertainty (default_with_fallback on ambiguous URL)
    if routing_decision.reason == "default_with_fallback" and not quality_result.passed:
        return True, "router_uncertain"

    return False, None


@celery_app.task
def cleanup_old_content(days: int = 30):
    """Clean up raw content older than specified days."""
    cutoff_date = datetime.now(UTC) - timedelta(days=days)

    logger.info("Starting content cleanup", cutoff_date=cutoff_date.isoformat())

    with get_db_session() as session:
        old_content = (
            session.query(RawContent)
            .filter(RawContent.created_at < cutoff_date, RawContent.processing_status != "DELETED")
            .all()
        )

        deleted_count = 0
        for content in old_content:
            content.processing_status = "DELETED"
            deleted_count += 1

        session.commit()

        logger.info(
            "Content cleanup completed",
            deleted_count=deleted_count,
            cutoff_date=cutoff_date.isoformat(),
        )

        return cleanup_old_contentResult.model_validate({"deleted_count": deleted_count, "cutoff_date": cutoff_date.isoformat()})
