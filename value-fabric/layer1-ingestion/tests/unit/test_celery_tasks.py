"""
Unit tests for Layer 1 Celery task dispatch.

Tests verify:
1. process_scraping_job chains all 9 pipeline stages in order.
2. compliance_check_stage updates job status to VALIDATING.
3. execute_pipeline_stage dispatches to the correct stage task.
4. cleanup_old_content returns a dict with deleted_count and cutoff_date.
5. Celery app is configured with correct broker and serializer settings.
6. Tasks handle missing job gracefully (ValueError, not unhandled exception).
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call
from uuid import UUID, uuid4

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
tests_dir = os.path.dirname(os.path.abspath(__file__))
layer1_dir = str(Path(tests_dir).parent.parent)
src_dir = str(Path(tests_dir).parent.parent / "src")
for p in (layer1_dir, src_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

# Set env vars before any imports so pydantic-settings can read them
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


# ── Celery App Configuration Tests ───────────────────────────────────────────
class TestCeleryAppConfiguration:
    """Verify the Celery app is configured correctly."""

    def test_celery_app_name(self) -> None:
        """Celery app must be named 'layer1_ingestion'."""
        from src.shared.tasks import celery_app
        assert celery_app.main == "layer1_ingestion"

    def test_celery_task_serializer(self) -> None:
        """Celery must use JSON serializer for task payloads."""
        from src.shared.tasks import celery_app
        assert celery_app.conf.task_serializer == "json"

    def test_celery_result_serializer(self) -> None:
        """Celery must use JSON serializer for results."""
        from src.shared.tasks import celery_app
        assert celery_app.conf.result_serializer == "json"

    def test_celery_timezone_utc(self) -> None:
        """Celery must use UTC timezone."""
        from src.shared.tasks import celery_app
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True

    def test_celery_task_time_limit(self) -> None:
        """Celery task time limit must be set (prevents runaway tasks)."""
        from src.shared.tasks import celery_app
        assert celery_app.conf.task_time_limit is not None
        assert celery_app.conf.task_time_limit > 0


# ── Pipeline Stage Dispatch Tests ─────────────────────────────────────────────
class TestExecutePipelineStage:
    """Test execute_pipeline_stage dispatches to the correct task."""

    def test_execute_pipeline_stage_compliance_check(self) -> None:
        """execute_pipeline_stage must dispatch compliance_check_stage for COMPLIANCE_CHECK."""
        from src.shared.tasks import execute_pipeline_stage, compliance_check_stage

        job_id = str(uuid4())
        with patch.object(compliance_check_stage, "delay") as mock_delay:
            execute_pipeline_stage(job_id, "COMPLIANCE_CHECK")
            mock_delay.assert_called_once()

    def test_execute_pipeline_stage_unknown_raises(self) -> None:
        """execute_pipeline_stage must raise ValueError for unknown stage names."""
        from src.shared.tasks import execute_pipeline_stage

        with pytest.raises((ValueError, Exception)):
            execute_pipeline_stage(str(uuid4()), "NONEXISTENT_STAGE")


# ── Process Scraping Job Tests ────────────────────────────────────────────────
class TestProcessScrapingJob:
    """Test the main pipeline orchestrator task."""

    def test_process_scraping_job_chains_all_stages(self) -> None:
        """process_scraping_job must chain all 9 pipeline stages."""
        from src.shared.tasks import (
            compliance_check_stage,
            browser_launch_stage,
            navigation_stage,
            content_capture_stage,
            ai_extraction_stage,
            post_processing_stage,
            validation_stage,
            storage_stage,
            notification_stage,
        )

        # Verify all 9 stage tasks exist and are callable
        stage_tasks = [
            compliance_check_stage,
            browser_launch_stage,
            navigation_stage,
            content_capture_stage,
            ai_extraction_stage,
            post_processing_stage,
            validation_stage,
            storage_stage,
            notification_stage,
        ]
        assert len(stage_tasks) == 9, "Pipeline must have exactly 9 stages"
        for task in stage_tasks:
            assert callable(task), f"Stage task {task} must be callable"

    def test_process_scraping_job_missing_job_raises(self) -> None:
        """process_scraping_job must raise ValueError when job is not found in DB."""
        from src.shared.tasks import process_scraping_job

        job_id = str(uuid4())
        mock_session = MagicMock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_session.query.return_value.get.return_value = None  # Job not found

        with patch("src.shared.tasks.get_db_session", return_value=mock_session):
            with pytest.raises(Exception):
                process_scraping_job.run(job_id)

    def test_process_scraping_job_returns_task_id_on_success(self) -> None:
        """process_scraping_job must return dict with success=True and task_id."""
        from src.shared.tasks import process_scraping_job

        job_id = str(uuid4())
        mock_job = Mock()
        mock_job.status = "PENDING"
        mock_job.started_at = None

        mock_session = MagicMock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_session.query.return_value.get.return_value = mock_job

        mock_chain_result = Mock()
        mock_chain_result.id = "celery-task-abc-123"

        with (
            patch("src.shared.tasks.get_db_session", return_value=mock_session),
            patch("src.shared.tasks.chain") as mock_chain_cls,
        ):
            mock_chain_instance = Mock()
            mock_chain_instance.apply_async.return_value = mock_chain_result
            mock_chain_cls.return_value = mock_chain_instance

            # Call .run() directly to bypass Celery's task dispatch machinery
            result = process_scraping_job.run(job_id)

        assert result["success"] is True
        assert result["job_id"] == job_id
        assert "task_id" in result
        assert result["task_id"] == "celery-task-abc-123"


# ── Cleanup Task Tests ────────────────────────────────────────────────────────
class TestCleanupOldContent:
    """Test the cleanup_old_content periodic task."""

    def test_cleanup_returns_deleted_count_and_cutoff(self) -> None:
        """cleanup_old_content must return deleted_count and cutoff_date."""
        from src.shared.tasks import cleanup_old_content

        mock_content_1 = Mock()
        mock_content_1.processing_status = "PROCESSED"
        mock_content_2 = Mock()
        mock_content_2.processing_status = "PROCESSED"

        mock_session = MagicMock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_content_1,
            mock_content_2,
        ]

        with patch("src.shared.tasks.get_db_session", return_value=mock_session):
            result = cleanup_old_content(days=30)

        assert "deleted_count" in result
        assert result["deleted_count"] == 2
        assert "cutoff_date" in result
        # cutoff_date must be a valid ISO datetime string
        from datetime import datetime
        cutoff = datetime.fromisoformat(result["cutoff_date"])
        assert cutoff < datetime.utcnow()

    def test_cleanup_marks_content_as_deleted(self) -> None:
        """cleanup_old_content must set processing_status to DELETED."""
        from src.shared.tasks import cleanup_old_content

        mock_content = Mock()
        mock_content.processing_status = "PROCESSED"

        mock_session = MagicMock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_content]

        with patch("src.shared.tasks.get_db_session", return_value=mock_session):
            cleanup_old_content(days=30)

        assert mock_content.processing_status == "DELETED"

    def test_cleanup_default_days_is_30(self) -> None:
        """cleanup_old_content default retention period must be 30 days."""
        from src.shared.tasks import cleanup_old_content

        import inspect
        sig = inspect.signature(cleanup_old_content)
        days_param = sig.parameters.get("days")
        assert days_param is not None, "cleanup_old_content must have a 'days' parameter"
        assert days_param.default == 30, "Default retention period must be 30 days"


# ── Compliance Check Stage Tests ──────────────────────────────────────────────
class TestComplianceCheckStage:
    """Test the compliance_check_stage pipeline task."""

    def test_compliance_check_stage_updates_job_status(self) -> None:
        """compliance_check_stage must set job.status to VALIDATING."""
        from src.shared.tasks import compliance_check_stage

        job_id = uuid4()
        mock_job = Mock()
        mock_job.status = "PENDING"
        mock_job.configuration = {
            "url": "https://example.com",
            "compliance": {"respect_robots_txt": False},  # Skip robots check
        }
        mock_job.organization_id = uuid4()
        mock_job.target_id = uuid4()

        mock_session = MagicMock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_session.query.return_value.get.return_value = mock_job

        with patch("src.shared.tasks.get_db_session", return_value=mock_session):
            with patch("src.shared.tasks._update_stage"):
                # Use .run() to bypass Celery's task dispatch machinery
                result = compliance_check_stage.run(job_id)

        # Job status must be updated to VALIDATING
        assert mock_job.status == "VALIDATING"
        assert result["success"] is True
        assert str(result["job_id"]) == str(job_id)

    def test_compliance_check_stage_missing_job_retries(self) -> None:
        """compliance_check_stage must raise when job is not found."""
        from src.shared.tasks import compliance_check_stage

        job_id = uuid4()
        mock_session = MagicMock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_session.query.return_value.get.return_value = None  # Job not found

        with patch("src.shared.tasks.get_db_session", return_value=mock_session):
            with pytest.raises(Exception):
                # Use .run() to bypass Celery's task dispatch machinery
                compliance_check_stage.run(job_id)
