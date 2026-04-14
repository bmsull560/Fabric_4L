"""Background scheduler for periodic CRM account synchronization.

Integrates CRMSyncService with TaskScheduler for automated background syncing
of Salesforce and HubSpot accounts at configured intervals.
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from ..engine.scheduler import ScheduledTask, TaskPriority, TaskScheduler
from ..models.account import CRMProvider
from ..database import db_session
from .crm_sync_service import CRMSyncService

logger = logging.getLogger(__name__)


class CRMSyncScheduler:
    """Schedules and manages periodic CRM account synchronization.

    Uses TaskScheduler for background execution with BACKGROUND priority
    to avoid impacting user-facing workflows.

    Configuration via environment variables:
    - CRM_SYNC_INTERVAL_MINUTES: Sync interval (default: 60)
    - CRM_SYNC_BATCH_SIZE: Records per sync batch (default: 100)

    Example:
        scheduler = CRMSyncScheduler()
        await scheduler.start()  # Begins periodic sync
    """

    def __init__(self, scheduler: TaskScheduler | None = None):
        """Initialize the CRM sync scheduler.

        Args:
            scheduler: TaskScheduler instance to use. Creates new if None.
        """
        self._scheduler = scheduler or TaskScheduler(max_concurrent_tasks=10)
        self._sync_interval_minutes = int(os.getenv("CRM_SYNC_INTERVAL_MINUTES", "60"))
        self._batch_size = int(os.getenv("CRM_SYNC_BATCH_SIZE", "100"))
        self._running = False
        self._scheduled_task_ids: list[str] = []

    async def start(self) -> None:
        """Start the CRM sync scheduler.

        Schedules periodic sync tasks for Salesforce and HubSpot.
        """
        if self._running:
            logger.warning("CRMSyncScheduler already running")
            return

        await self._scheduler.start()
        self._running = True

        # Schedule initial sync tasks
        await self._schedule_provider_sync(CRMProvider.SALESFORCE)
        await self._schedule_provider_sync(CRMProvider.HUBSPOT)

        logger.info(
            f"CRM sync scheduler started: interval={self._sync_interval_minutes}min, "
            f"batch_size={self._batch_size}"
        )

    async def stop(self) -> None:
        """Stop the CRM sync scheduler.

        Cancels pending sync tasks and stops the underlying scheduler.
        """
        if not self._running:
            return

        self._running = False

        # Cancel all scheduled sync tasks
        for task_id in self._scheduled_task_ids:
            try:
                await self._scheduler.cancel_task(task_id)
            except Exception as e:
                logger.warning(f"Failed to cancel sync task {task_id}: {e}")

        self._scheduled_task_ids.clear()
        await self._scheduler.stop()

        logger.info("CRM sync scheduler stopped")

    async def _schedule_provider_sync(self, provider: CRMProvider) -> None:
        """Schedule a sync task for a specific CRM provider.

        Args:
            provider: CRM provider to sync (Salesforce or HubSpot)
        """
        if not self._running:
            return

        # Schedule at next interval
        next_run = datetime.now(UTC) + timedelta(minutes=self._sync_interval_minutes)

        task = ScheduledTask(
            priority=TaskPriority.BACKGROUND.value,
            scheduled_time=next_run,
            task_id=f"crm_sync_{provider.value}_{next_run.isoformat()}",
            workflow_instance_id="crm_background_sync",
            capability="crm_sync",
            agent_type="CRMSyncScheduler",
            context={"provider": provider.value},
            parameters={"provider": provider.value, "incremental": True},
            timeout_seconds=1800,  # 30 minute timeout for sync
        )

        task_id = await self._scheduler.schedule_task(task)
        self._scheduled_task_ids.append(task_id)

        logger.debug(f"Scheduled {provider.value} sync for {next_run.isoformat()}")

    async def _execute_sync(self, provider_str: str, incremental: bool = True) -> dict[str, Any]:
        """Execute the actual CRM sync.

        Args:
            provider_str: CRM provider name ('salesforce' or 'hubspot')
            incremental: If True, only sync recently modified records

        Returns:
            Sync statistics
        """
        try:
            provider = CRMProvider(provider_str)
        except ValueError:
            logger.error(f"Invalid CRM provider: {provider_str}")
            return {"error": f"Invalid provider: {provider_str}"}

        # Check if CRM is configured for this provider
        crm_type = os.getenv("CRM_TYPE", "").lower()
        if crm_type and crm_type != provider.value:
            logger.debug(f"Skipping {provider.value} sync - CRM_TYPE is {crm_type}")
            return {"skipped": True, "reason": "Provider not configured"}

        # Check for required credentials
        api_key = os.getenv("CRM_API_KEY")
        if not api_key:
            logger.warning(f"Skipping {provider.value} sync - no CRM_API_KEY configured")
            return {"skipped": True, "reason": "No API key configured"}

        async with db_session() as db:
            service = CRMSyncService(db, batch_size=self._batch_size)
            stats = await service.sync_provider(provider, incremental=incremental)

        return stats

    async def trigger_sync_now(
        self, provider: CRMProvider | None = None, incremental: bool = True
    ) -> dict[str, Any]:
        """Manually trigger a sync immediately.

        Args:
            provider: Specific provider to sync, or None for both
            incremental: If True, only sync recently modified records

        Returns:
            Sync statistics
        """
        if provider:
            return await self._execute_sync(provider.value, incremental)

        # Sync both providers
        results = {}
        for prov in [CRMProvider.SALESFORCE, CRMProvider.HUBSPOT]:
            results[prov.value] = await self._execute_sync(prov.value, incremental)

        return results

    def get_status(self) -> dict[str, Any]:
        """Get scheduler status and statistics.

        Returns:
            Status dict with configuration and scheduler stats
        """
        return {
            "running": self._running,
            "sync_interval_minutes": self._sync_interval_minutes,
            "batch_size": self._batch_size,
            "scheduled_tasks": len(self._scheduled_task_ids),
            "scheduler_stats": self._scheduler.get_stats(),
        }


# Global scheduler instance for singleton access
_crm_sync_scheduler: CRMSyncScheduler | None = None


async def get_crm_sync_scheduler() -> CRMSyncScheduler:
    """Get or create the global CRM sync scheduler instance.

    Returns:
        CRMSyncScheduler singleton
    """
    global _crm_sync_scheduler
    if _crm_sync_scheduler is None:
        _crm_sync_scheduler = CRMSyncScheduler()
    return _crm_sync_scheduler
