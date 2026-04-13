"""
CRM Sync Service for background account synchronization.

Handles periodic syncing of accounts from Salesforce and HubSpot,
with rate limiting, deduplication, and error handling.
"""

import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.account import (
    Account,
    AccountSyncStatus,
    CRMProvider,
    SyncStatus,
)
from ..models.tool_schemas import GetProspectDataInput
from ..tools.crm_tools import GetProspectDataTool

logger = logging.getLogger(__name__)

# Module-level constants for configuration
DEFAULT_SYNC_BATCH_SIZE = int(os.getenv("CRM_SYNC_BATCH_SIZE", "100"))
DEFAULT_SYNC_INTERVAL_MINUTES = int(os.getenv("CRM_SYNC_INTERVAL_MINUTES", "60"))


class CRMSyncService:
    """Service for orchestrating CRM account synchronization.

    Handles:
    - Full sync: All accounts from CRM
    - Incremental sync: Recently modified accounts
    - Single account refresh: On-demand sync
    - Rate limiting and retry logic
    - Deduplication across providers
    """

    def __init__(self, db: AsyncSession, batch_size: int = DEFAULT_SYNC_BATCH_SIZE):
        self.db = db
        self.sync_batch_size = batch_size

    async def sync_provider(
        self,
        provider: CRMProvider,
        incremental: bool = True,
        account_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Sync accounts from a CRM provider.

        Args:
            provider: CRM provider (salesforce or hubspot)
            incremental: If True, only sync recently modified accounts
            account_ids: Optional list of specific account IDs to sync

        Returns:
            Sync statistics: synced, updated, failed, errors
        """
        # Update sync status to running
        await self._update_sync_status(provider, "running", None)

        stats = {
            "provider": provider.value,
            "synced": 0,
            "updated": 0,
            "failed": 0,
            "errors": [],
        }

        try:
            # Get CRM config from environment
            config = self._get_crm_config(provider)
            if not config or not config.get("api_key"):
                raise ValueError(f"CRM configuration missing for {provider.value}")

            # Initialize CRM tool
            tool = GetProspectDataTool(config=config)

            # Get list of accounts to sync
            if account_ids:
                # Sync specific accounts
                prospect_ids = account_ids
            else:
                # Fetch all accounts from CRM (would use CRM API query)
                # For now, we rely on accounts already in our DB
                prospect_ids = await self._get_accounts_to_sync(provider, incremental)

            # Sync each account
            for prospect_id in prospect_ids[: self.sync_batch_size]:
                try:
                    result = await self._sync_single_account(tool, provider, prospect_id)
                    if result:
                        stats["updated"] += 1
                    else:
                        stats["synced"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append(f"{prospect_id}: {str(e)}")
                    logger.error(f"Failed to sync account {prospect_id} from {provider.value}: {e}")

            # Update sync status to success
            await self._update_sync_status(
                provider,
                "idle",
                None,
                records_synced=stats["synced"] + stats["updated"],
                records_updated=stats["updated"],
                records_failed=stats["failed"],
            )

            logger.info(f"CRM sync completed for {provider.value}: {stats}")
            return stats

        except Exception as e:
            # Update sync status to failed
            await self._update_sync_status(provider, "failed", str(e))
            logger.error(f"CRM sync failed for {provider.value}: {e}")
            stats["errors"].append(str(e))
            return stats

    async def _execute_with_retry(
        self,
        tool: GetProspectDataTool,
        prospect_id: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        """Execute tool with exponential backoff retry logic.

        Args:
            tool: Configured GetProspectDataTool
            prospect_id: Provider's record ID
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff

        Returns:
            Tool execution result

        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await tool.execute(
                    GetProspectDataInput(
                        prospect_id=prospect_id,
                        data_types=["profile", "opportunities", "interactions"],
                    )
                )
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {prospect_id} after {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    break

        raise last_exception

    async def _sync_single_account(
        self,
        tool: GetProspectDataTool,
        provider: CRMProvider,
        prospect_id: str,
    ) -> bool:
        """Sync a single account from CRM.

        Args:
            tool: Configured GetProspectDataTool
            provider: CRM provider
            prospect_id: Provider's record ID

        Returns:
            True if account was updated (existed), False if created (new)
        """
        # Fetch data from CRM with retry logic
        result = await self._execute_with_retry(tool, prospect_id)

        if not result.profile:
            raise ValueError(f"No profile data returned for {prospect_id}")

        # Check if account exists
        existing = await self.db.execute(
            select(Account).where(
                and_(
                    Account.provider == provider.value,
                    Account.provider_record_id == prospect_id,
                )
            )
        )
        account = existing.scalar_one_or_none()

        is_update = account is not None

        if not account:
            # Create new account
            account = Account(
                provider=provider.value,
                provider_record_id=prospect_id,
            )
            self.db.add(account)

        # Update account fields
        profile = result.profile
        account.name = profile.get("name", account.name)
        account.industry = profile.get("industry", account.industry)
        account.company_size = profile.get("company_size", account.company_size)
        account.annual_revenue = profile.get("annual_revenue", account.annual_revenue)
        account.headquarters = profile.get("headquarters", account.headquarters)
        account.website = profile.get("website", account.website)
        account.domain = profile.get("domain", account.domain)
        account.employees = profile.get("employees", account.employees)

        # Update opportunities
        if result.opportunities:
            account.opportunities = [
                {
                    "provider_opportunity_id": opp.get("id", ""),
                    "name": opp.get("name", ""),
                    "stage": opp.get("stage", ""),
                    "value": opp.get("value"),
                    "probability": opp.get("probability"),
                    "close_date": opp.get("close_date"),
                    "pipeline": opp.get("pipeline"),
                    "last_synced_at": datetime.now(UTC).isoformat(),
                }
                for opp in result.opportunities
            ]

        # Update sync metadata
        account.last_synced_at = datetime.now(UTC)
        account.sync_status = SyncStatus.SYNCED.value
        account.updated_at = datetime.now(UTC)

        await self.db.commit()

        return is_update

    async def _get_accounts_to_sync(
        self,
        provider: CRMProvider,
        incremental: bool = True,
    ) -> list[str]:
        """Get list of account IDs that need syncing.

        For incremental sync, returns accounts with stale status or
        recently modified in CRM.
        """
        if incremental:
            # Get accounts that need sync (stale, failed, or pending)
            result = await self.db.execute(
                select(Account.provider_record_id)
                .where(
                    and_(
                        Account.provider == provider.value,
                        Account.sync_status.in_(
                            [
                                SyncStatus.STALE.value,
                                SyncStatus.FAILED.value,
                                SyncStatus.PENDING.value,
                            ]
                        ),
                    )
                )
                .limit(self.sync_batch_size)
            )
            stale_ids = [row[0] for row in result.all() if row[0]]

            # Also get accounts not synced in last 24 hours
            day_ago = datetime.now(UTC) - timedelta(hours=24)
            result = await self.db.execute(
                select(Account.provider_record_id)
                .where(
                    and_(
                        Account.provider == provider.value,
                        Account.sync_status == SyncStatus.SYNCED.value,
                        Account.last_synced_at < day_ago,
                    )
                )
                .limit(self.sync_batch_size - len(stale_ids))
            )
            old_ids = [row[0] for row in result.all() if row[0]]

            return stale_ids + old_ids
        else:
            # Full sync - all accounts for provider
            result = await self.db.execute(
                select(Account.provider_record_id)
                .where(Account.provider == provider.value)
                .limit(self.sync_batch_size)
            )
            return [row[0] for row in result.all() if row[0]]

    async def _update_sync_status(
        self,
        provider: CRMProvider,
        status: str,
        error_message: str | None,
        records_synced: int = 0,
        records_updated: int = 0,
        records_failed: int = 0,
    ) -> None:
        """Update the AccountSyncStatus record for a provider."""
        now = datetime.now(UTC)

        # Get or create sync status record
        result = await self.db.execute(
            select(AccountSyncStatus).where(AccountSyncStatus.provider == provider.value)
        )
        sync_status = result.scalar_one_or_none()

        if not sync_status:
            sync_status = AccountSyncStatus(
                provider=provider.value,
                status=status,
                last_sync_at=now if status == "running" else None,
                last_successful_sync_at=now if status == "idle" else None,
                records_synced=records_synced,
                records_updated=records_updated,
                records_failed=records_failed,
                error_message=error_message,
            )
            self.db.add(sync_status)
        else:
            sync_status.status = status
            if status == "running":
                sync_status.last_sync_at = now
            elif status == "idle":
                sync_status.last_successful_sync_at = now
                sync_status.records_synced = records_synced
                sync_status.records_updated = records_updated
                sync_status.records_failed = records_failed
                sync_status.error_message = None
            elif status == "failed":
                sync_status.error_message = error_message
                sync_status.records_failed = records_failed
            sync_status.updated_at = now

        await self.db.commit()

    def _get_crm_config(self, provider: CRMProvider) -> dict[str, Any] | None:
        """Get CRM configuration from environment variables."""
        crm_type = os.getenv("CRM_TYPE", "").lower()

        # Only return config if CRM type matches or is not set
        if crm_type and crm_type != provider.value:
            return None

        return {
            "crm_type": provider.value,
            "crm_api_key": os.getenv("CRM_API_KEY"),
            "crm_api_secret": os.getenv("CRM_API_SECRET"),
            "crm_instance_url": os.getenv("CRM_INSTANCE_URL"),
        }

    async def get_sync_status(self, provider: CRMProvider) -> AccountSyncStatus | None:
        """Get current sync status for a provider."""
        result = await self.db.execute(
            select(AccountSyncStatus).where(AccountSyncStatus.provider == provider.value)
        )
        return result.scalar_one_or_none()

    async def refresh_single_account(
        self,
        account_id: UUID,
    ) -> Account | None:
        """Refresh a single account from its CRM provider.

        Args:
            account_id: Internal account UUID

        Returns:
            Updated Account or None if not found
        """
        # Get account
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            return None

        # Get provider
        try:
            provider = CRMProvider(account.provider)
        except ValueError as e:
            raise ValueError(
                f"Invalid CRM provider '{account.provider}' for account {account_id}"
            ) from e

        # Get CRM config
        config = self._get_crm_config(provider)
        if not config or not config.get("api_key"):
            raise ValueError(f"CRM not configured for provider {provider.value}")

        # Sync the account
        tool = GetProspectDataTool(config=config)
        await self._sync_single_account(tool, provider, account.provider_record_id)

        # Refresh and return
        await self.db.refresh(account)
        return account


# Factory function for dependency injection
async def get_crm_sync_service(db: AsyncSession) -> CRMSyncService:
    """Factory for creating CRMSyncService with database session."""
    return CRMSyncService(db)
