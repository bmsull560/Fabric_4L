"""
Account Enrichment API Routes — Data Intelligence Layer Phase 1.

Provides endpoints for triggering and monitoring account enrichment:
- POST /enrich/{account_id}   — Enrich a single account
- POST /enrich/batch          — Enrich a batch of pending accounts
- GET  /enrich/status         — Get enrichment coverage statistics
- GET  /enrich/{account_id}   — Get enrichment details for an account
"""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db_from_context
from ...models.account import Account
from ...services.enrichment_orchestrator import (
    EnrichmentOrchestrator,
    EnrichmentSource,
    EnrichmentStatus,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class EnrichAccountRequest(BaseModel):
    sources: list[str] | None = Field(
        None,
        description="Specific sources to use: sec_edgar, web_crawl, domain_lookup, news_scan",
    )
    force: bool = Field(False, description="Re-enrich even if already enriched")


class BatchEnrichRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID to enrich accounts for")
    limit: int = Field(50, ge=1, le=500, description="Max accounts to enrich")
    force: bool = Field(False, description="Re-enrich already enriched accounts")


class EnrichmentStatusResponse(BaseModel):
    total_accounts: int
    enriched: int
    pending: int
    in_progress: int
    failed: int
    stale: int
    coverage_pct: float


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/{account_id}", summary="Enrich a single account")
async def enrich_account(
    account_id: UUID,
    request: EnrichAccountRequest | None = None,
    db: AsyncSession = Depends(get_db_from_context),
) -> dict[str, Any]:
    """Trigger enrichment for a single account from multiple data sources.

    Enrichment sources include SEC EDGAR (financials), web crawl (tech stack),
    domain lookup (executives), and news scan (pain signals).
    """
    orchestrator = EnrichmentOrchestrator(db)

    try:
        # Parse source list if provided
        sources = None
        if request and request.sources:
            try:
                sources = [EnrichmentSource(s) for s in request.sources]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid source: {e}. Valid sources: {[s.value for s in EnrichmentSource]}",
                )

        force = request.force if request else False
        result = await orchestrator.enrich_account(account_id, sources=sources, force=force)

        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))

        return result
    finally:
        await orchestrator.close()


@router.post("/batch", summary="Enrich a batch of accounts")
async def enrich_batch(
    request: BatchEnrichRequest,
    db: AsyncSession = Depends(get_db_from_context),
) -> dict[str, Any]:
    """Enrich a batch of accounts with pending/stale enrichment status.

    Processes up to `limit` accounts for the specified tenant.
    """
    orchestrator = EnrichmentOrchestrator(db)

    try:
        result = await orchestrator.enrich_batch(
            tenant_id=request.tenant_id,
            limit=request.limit,
            force=request.force,
        )
        return result
    finally:
        await orchestrator.close()


@router.get("/status", summary="Get enrichment coverage statistics")
async def get_enrichment_status(
    tenant_id: str = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db_from_context),
) -> EnrichmentStatusResponse:
    """Get enrichment coverage statistics for a tenant.

    Returns counts of accounts by enrichment status and overall coverage percentage.
    """
    orchestrator = EnrichmentOrchestrator(db)

    try:
        status = await orchestrator.get_enrichment_status(tenant_id)
        return EnrichmentStatusResponse(**status)
    finally:
        await orchestrator.close()


@router.get("/{account_id}", summary="Get enrichment details for an account")
async def get_account_enrichment(
    account_id: UUID,
    db: AsyncSession = Depends(get_db_from_context),
) -> dict[str, Any]:
    """Get the current enrichment data for a specific account.

    Returns all enrichment fields: tech stack, executives, financials,
    competitive landscape, and pain signals.
    """
    account = await db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    return {
        "account_id": str(account.id),
        "name": account.name,
        "enrichment_status": account.enrichment_status,
        "enriched_at": account.enriched_at.isoformat() if account.enriched_at else None,
        "enrichment_sources": account.enrichment_sources or [],
        "tech_stack": account.tech_stack,
        "executives": account.executives or [],
        "financials": account.financials,
        "competitive_landscape": account.competitive_landscape or [],
        "pain_signals": account.pain_signals or [],
    }
