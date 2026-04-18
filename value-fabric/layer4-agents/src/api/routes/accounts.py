"""
Accounts API routes for CRM account management.

Phase 1: Accounts-first operational surface with embedded opportunities/contacts.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.account import CRMProvider, SyncStatus
from ...services.account_service import AccountService
from ..schemas.accounts import (
    AccountActivityResponse,
    AccountDetailSchema,
    AccountFilterOptionsResponse,
    AccountListItemSchema,
    AccountListResponse,
    AccountSearchRequest,
    ContactSchema,
    OpportunitySchema,
    SyncAccountsRequest,
    SyncAccountsResponse,
    SyncStatusListResponse,
    SyncStatusSchema,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts", tags=["Accounts"])


# ============================================================================
# Helper Functions
# ============================================================================


def format_source_attribution(account) -> str:
    """Generate human-readable source attribution string."""
    if not account.last_synced_at:
        return f"Pending sync from {account.provider}"

    time_diff = datetime.now(UTC) - account.last_synced_at
    if time_diff.days > 0:
        time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
    elif time_diff.seconds // 3600 > 0:
        hours = time_diff.seconds // 3600
        time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif time_diff.seconds // 60 > 0:
        minutes = time_diff.seconds // 60
        time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        time_str = "just now"

    return f"Synced from {account.provider.capitalize()} {time_str}"


def to_list_item_schema(account) -> AccountListItemSchema:
    """Convert Account model to list item schema."""
    return AccountListItemSchema(
        id=account.id,
        provider=CRMProvider(account.provider),
        name=account.name,
        domain=account.domain,
        industry=account.industry,
        region=account.region,
        company_size=account.company_size,
        owner_name=account.owner_name,
        stage=account.stage,
        segment=account.segment,
        sync_status=SyncStatus(account.sync_status),
        last_synced_at=account.last_synced_at,
        updated_at=account.updated_at,
        provider_badge=account.provider.capitalize(),
    )


def to_detail_schema(account) -> AccountDetailSchema:
    """Convert Account model to detail schema."""
    # Convert embedded opportunities
    opportunities = [OpportunitySchema(**opp) for opp in (account.opportunities or [])]

    # Convert embedded contacts
    contacts = [ContactSchema(**contact) for contact in (account.contacts or [])]

    return AccountDetailSchema(
        id=account.id,
        provider=CRMProvider(account.provider),
        provider_record_id=account.provider_record_id,
        name=account.name,
        domain=account.domain,
        industry=account.industry,
        region=account.region,
        company_size=account.company_size,
        annual_revenue=account.annual_revenue,
        headquarters=account.headquarters,
        website=account.website,
        owner_id=account.owner_id,
        owner_name=account.owner_name,
        owner_email=account.owner_email,
        stage=account.stage,
        segment=account.segment,
        created_at=account.created_at,
        updated_at=account.updated_at,
        last_synced_at=account.last_synced_at,
        sync_status=SyncStatus(account.sync_status),
        source_attribution=format_source_attribution(account),
        provider_badge=account.provider.capitalize(),
        opportunities=opportunities,
        contacts=contacts,
    )


# ============================================================================
# Routes
# ============================================================================


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    provider: CRMProvider | None = None,
    stage: str | None = None,
    industry: str | None = None,
    region: str | None = None,
    segment: str | None = None,
    owner_id: str | None = None,
    sync_status: SyncStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("updated_at", pattern="^(name|updated_at|company_size|last_synced_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
) -> AccountListResponse:
    """List accounts with filtering and pagination."""
    service = AccountService(db)

    accounts, total = await service.list_accounts(
        provider=provider,
        stage=stage,
        industry=industry,
        region=region,
        segment=segment,
        owner_id=owner_id,
        sync_status=sync_status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return AccountListResponse(
        items=[to_list_item_schema(acc) for acc in accounts],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("/search", response_model=AccountListResponse)
async def search_accounts(
    request: AccountSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> AccountListResponse:
    """Search accounts across name, domain, and owner."""
    service = AccountService(db)

    accounts, total = await service.search_accounts(
        query_str=request.query,
        provider=request.provider,
        stage=request.stage,
        industry=request.industry,
        region=request.region,
        segment=request.segment,
        owner_id=request.owner_id,
        sync_status=request.sync_status,
        page=request.page,
        page_size=request.page_size,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
    )

    return AccountListResponse(
        items=[to_list_item_schema(acc) for acc in accounts],
        total=total,
        page=request.page,
        page_size=request.page_size,
        has_more=(request.page * request.page_size) < total,
    )


@router.get("/filters", response_model=AccountFilterOptionsResponse)
async def get_filter_options(
    db: AsyncSession = Depends(get_db),
) -> AccountFilterOptionsResponse:
    """Get available filter options for account list."""
    service = AccountService(db)
    options = await service.get_filter_options()

    return AccountFilterOptionsResponse(
        industries=options["industries"],
        stages=options["stages"],
        regions=options["regions"],
        segments=options["segments"],
        providers=[CRMProvider(p) for p in options["providers"]],
        owners=options["owners"],
    )


@router.get("/sync-status", response_model=SyncStatusListResponse)
async def get_sync_status_all(
    db: AsyncSession = Depends(get_db),
) -> SyncStatusListResponse:
    """Get sync status for all CRM providers."""
    service = AccountService(db)

    sync_statuses = await service.get_all_sync_status()

    # Determine overall status
    any_failed = any(s.status == "failed" for s in sync_statuses)
    any_running = any(s.status == "running" for s in sync_statuses)

    if any_failed:
        overall = "degraded"
    elif any_running:
        overall = "syncing"
    else:
        overall = "healthy"

    return SyncStatusListResponse(
        providers=[
            SyncStatusSchema(
                provider=CRMProvider(s.provider),
                status=s.status,
                last_sync_at=s.last_sync_at,
                last_successful_sync_at=s.last_successful_sync_at,
                records_synced=s.records_synced,
                records_updated=s.records_updated,
                records_failed=s.records_failed,
                error_message=s.error_message,
            )
            for s in sync_statuses
        ],
        overall_status=overall,
    )


@router.post("/sync", response_model=SyncAccountsResponse)
async def sync_accounts(
    request: SyncAccountsRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncAccountsResponse:
    """Trigger manual sync for accounts."""
    service = AccountService(db)

    result = await service.trigger_sync(
        provider=request.provider,
        account_ids=request.account_ids,
        force_refresh=request.force_refresh,
    )

    return SyncAccountsResponse(**result)


@router.get("/{account_id}", response_model=AccountDetailSchema)
async def get_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AccountDetailSchema:
    """Get full account detail."""
    service = AccountService(db)

    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found: {account_id}",
        )

    return to_detail_schema(account)


@router.get("/{account_id}/activity", response_model=AccountActivityResponse)
async def get_account_activity(
    account_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    since_days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> AccountActivityResponse:
    """Get account activity timeline."""
    service = AccountService(db)

    # Verify account exists
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found: {account_id}",
        )

    activity = await service.get_account_activity(
        account_id=account_id,
        limit=limit,
        since_days=since_days,
    )

    return AccountActivityResponse(**activity)


@router.post("/{account_id}/refresh")
async def refresh_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AccountDetailSchema:
    """Refresh account data from CRM provider."""
    service = AccountService(db)

    # Verify account exists
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found: {account_id}",
        )

    # Trigger refresh
    refreshed = await service.refresh_account(account_id)
    if not refreshed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh account from CRM",
        )

    return to_detail_schema(refreshed)
