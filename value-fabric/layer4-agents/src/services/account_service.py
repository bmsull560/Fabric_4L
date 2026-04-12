"""
Account service layer for CRM account operations.

Business logic and data access for the accounts surface.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.account import (
    Account,
    AccountSyncStatus,
    CRMProvider,
    SyncStatus,
)
from ..tools.crm_tools import (
    FetchInteractionHistoryTool,
    GetProspectDataTool,
)
from ..models.tool_schemas import (
    FetchInteractionHistoryInput,
    GetProspectDataInput,
)

logger = logging.getLogger(__name__)


class AccountService:
    """Service for account operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ========================================================================
    # List & Search
    # ========================================================================
    
    async def list_accounts(
        self,
        provider: Optional[CRMProvider] = None,
        stage: Optional[str] = None,
        industry: Optional[str] = None,
        owner_id: Optional[str] = None,
        sync_status: Optional[SyncStatus] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Account], int]:
        """List accounts with filtering and pagination.
        
        Returns:
            Tuple of (accounts list, total count)
        """
        # Build base query
        query = select(Account)
        count_query = select(func.count(Account.id))
        
        # Apply filters
        filters = []
        if provider:
            filters.append(Account.provider == provider.value)
        if stage:
            filters.append(Account.stage == stage)
        if industry:
            filters.append(Account.industry == industry)
        if owner_id:
            filters.append(Account.owner_id == owner_id)
        if sync_status:
            filters.append(Account.sync_status == sync_status.value)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Apply sorting
        sort_column = getattr(Account, sort_by, Account.updated_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute queries
        result = await self.db.execute(query)
        accounts = result.scalars().all()
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        return list(accounts), total
    
    async def search_accounts(
        self,
        query_str: Optional[str] = None,
        provider: Optional[CRMProvider] = None,
        stage: Optional[str] = None,
        industry: Optional[str] = None,
        owner_id: Optional[str] = None,
        sync_status: Optional[SyncStatus] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Account], int]:
        """Search accounts across name, domain, and owner."""
        # Build base query
        query = select(Account)
        count_query = select(func.count(Account.id))
        
        filters = []
        
        # Text search across name, domain, owner_name
        if query_str:
            search_filter = or_(
                Account.name.ilike(f"%{query_str}%"),
                Account.domain.ilike(f"%{query_str}%"),
                Account.owner_name.ilike(f"%{query_str}%"),
                Account.normalized_name.ilike(f"%{query_str.lower()}%"),
            )
            filters.append(search_filter)
        
        # Additional filters
        if provider:
            filters.append(Account.provider == provider.value)
        if stage:
            filters.append(Account.stage == stage)
        if industry:
            filters.append(Account.industry == industry)
        if owner_id:
            filters.append(Account.owner_id == owner_id)
        if sync_status:
            filters.append(Account.sync_status == sync_status.value)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Sorting
        sort_column = getattr(Account, sort_by, Account.updated_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute
        result = await self.db.execute(query)
        accounts = result.scalars().all()
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        return list(accounts), total
    
    # ========================================================================
    # Detail & Activity
    # ========================================================================
    
    async def get_account(self, account_id: UUID) -> Optional[Account]:
        """Get single account by ID."""
        result = await self.db.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()
    
    async def get_account_by_provider_id(
        self,
        provider: CRMProvider,
        provider_record_id: str,
    ) -> Optional[Account]:
        """Get account by provider-specific ID."""
        result = await self.db.execute(
            select(Account).where(
                and_(
                    Account.provider == provider.value,
                    Account.provider_record_id == provider_record_id,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_account_activity(
        self,
        account_id: UUID,
        limit: int = 50,
        since_days: int = 90,
    ) -> dict:
        """Fetch account activity via CRM tools.
        
        Uses fetch_interaction_history tool to get recent activity.
        """
        account = await self.get_account(account_id)
        if not account:
            raise ValueError(f"Account not found: {account_id}")
        
        # Calculate since date
        since_date = (datetime.utcnow() - timedelta(days=since_days)).strftime("%Y-%m-%d")
        
        try:
            # Use the fetch_interaction_history tool
            tool = FetchInteractionHistoryTool()
            result = await tool.execute(
                FetchInteractionHistoryInput(
                    prospect_id=account.provider_record_id,
                    limit=limit,
                    since_date=since_date,
                )
            )
            
            return {
                "account_id": account_id,
                "interactions": [
                    {
                        "id": i.get("id", ""),
                        "type": i.get("type", "unknown"),
                        "date": i.get("date", ""),
                        "subject": i.get("subject", ""),
                        "duration_minutes": i.get("duration_minutes"),
                        "notes": i.get("notes", ""),
                        "outcome": i.get("outcome", ""),
                    }
                    for i in result.interactions
                ],
                "total_count": result.total_count,
                "summary": result.summary,
            }
        except Exception as e:
            logger.error(f"Failed to fetch activity for account {account_id}: {e}")
            return {
                "account_id": account_id,
                "interactions": [],
                "total_count": 0,
                "summary": "Activity data unavailable",
            }
    
    # ========================================================================
    # Sync Operations
    # ========================================================================
    
    async def get_sync_status(self, provider: CRMProvider) -> Optional[AccountSyncStatus]:
        """Get sync status for a provider."""
        result = await self.db.execute(
            select(AccountSyncStatus).where(AccountSyncStatus.provider == provider.value)
        )
        return result.scalar_one_or_none()
    
    async def get_all_sync_status(self) -> List[AccountSyncStatus]:
        """Get sync status for all providers."""
        result = await self.db.execute(select(AccountSyncStatus))
        return list(result.scalars().all())
    
    async def trigger_sync(
        self,
        provider: Optional[CRMProvider] = None,
        account_ids: Optional[List[str]] = None,
        force_refresh: bool = False,
    ) -> dict:
        """Trigger manual sync for accounts.
        
        This is the entry point for sync operations. In Phase 1, this
        initiates the sync process. The actual sync implementation would
        typically be handled by a background job.
        """
        sync_id = f"sync-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        if provider:
            # Sync specific provider
            return {
                "sync_id": sync_id,
                "status": "queued",
                "provider": provider.value,
                "message": f"Sync queued for {provider.value}",
            }
        elif account_ids:
            # Sync specific accounts
            return {
                "sync_id": sync_id,
                "status": "queued",
                "provider": None,
                "message": f"Sync queued for {len(account_ids)} accounts",
            }
        else:
            # Sync all providers
            return {
                "sync_id": sync_id,
                "status": "queued",
                "provider": None,
                "message": "Sync queued for all providers",
            }
    
    async def refresh_account(self, account_id: UUID) -> Optional[Account]:
        """Refresh single account from CRM provider.
        
        Fetches latest data and updates the account record.
        """
        account = await self.get_account(account_id)
        if not account:
            return None
        
        try:
            # Use get_prospect_data tool to fetch fresh data
            tool = GetProspectDataTool()
            result = await tool.execute(
                GetProspectDataInput(
                    prospect_id=account.provider_record_id,
                    data_types=["profile", "opportunities", "interactions"],
                )
            )
            
            # Update account with fresh data
            profile = result.profile
            if profile:
                account.name = profile.get("name", account.name)
                account.industry = profile.get("industry", account.industry)
                account.company_size = profile.get("company_size", account.company_size)
                account.annual_revenue = profile.get("annual_revenue", account.annual_revenue)
                account.headquarters = profile.get("headquarters", account.headquarters)
                account.website = profile.get("website", account.website)
                account.domain = profile.get("domain", account.domain)
            
            # Update opportunities from result
            if result.opportunities:
                account.opportunities = [
                    {
                        "provider_opportunity_id": opp.get("id", ""),
                        "name": opp.get("name", ""),
                        "stage": opp.get("stage", ""),
                        "value": opp.get("value"),
                        "probability": opp.get("probability"),
                        "close_date": opp.get("close_date"),
                        "last_synced_at": datetime.utcnow().isoformat(),
                    }
                    for opp in result.opportunities
                ]
            
            # Update sync metadata
            account.last_synced_at = datetime.utcnow()
            account.sync_status = SyncStatus.SYNCED.value
            account.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(account)
            
            return account
            
        except Exception as e:
            logger.error(f"Failed to refresh account {account_id}: {e}")
            account.sync_status = SyncStatus.FAILED.value
            await self.db.commit()
            return account
    
    # ========================================================================
    # Filter Options
    # ========================================================================
    
    async def get_filter_options(self) -> dict:
        """Get available filter options for account list."""
        # Get distinct industries
        industry_result = await self.db.execute(
            select(Account.industry).where(Account.industry.isnot(None)).distinct()
        )
        industries = [row[0] for row in industry_result.all() if row[0]]
        
        # Get distinct stages
        stage_result = await self.db.execute(
            select(Account.stage).where(Account.stage.isnot(None)).distinct()
        )
        stages = [row[0] for row in stage_result.all() if row[0]]
        
        # Get owners
        owner_result = await self.db.execute(
            select(Account.owner_id, Account.owner_name)
            .where(Account.owner_id.isnot(None))
            .distinct()
        )
        owners = [
            {"id": row[0], "name": row[1] or "Unknown"}
            for row in owner_result.all()
            if row[0]
        ]
        
        return {
            "industries": industries,
            "stages": stages,
            "providers": [p.value for p in CRMProvider],
            "owners": owners,
        }


# Factory function for dependency injection
async def get_account_service(db: AsyncSession) -> AccountService:
    """Factory for creating AccountService with database session."""
    return AccountService(db)
