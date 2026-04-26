"""
Competitive Intelligence API routes — Data Intelligence Layer Phase 2, Task 2.2.

Provides REST endpoints for managing competitors, battlecards, win/loss records,
and competitive landscape analysis.

Endpoints:
  POST   /api/v1/competitive/competitors              — Add a competitor
  GET    /api/v1/competitive/competitors               — List competitors
  GET    /api/v1/competitive/competitors/{id}          — Get competitor detail
  PUT    /api/v1/competitive/competitors/{id}          — Update a competitor
  DELETE /api/v1/competitive/competitors/{id}          — Delete a competitor
  POST   /api/v1/competitive/competitors/{id}/battlecards — Add a battlecard
  GET    /api/v1/competitive/competitors/{id}/battlecards — Get battlecards
  POST   /api/v1/competitive/win-loss                  — Record a win/loss
  GET    /api/v1/competitive/landscape                 — Competitive landscape analysis
  GET    /api/v1/competitive/win-loss/summary          — Win/loss summary
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/competitive", tags=["Competitive Intelligence"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class CompetitorCreateRequest(BaseModel):
    """Request to create a competitor."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    domain: str | None = Field(None, max_length=200)
    founded_year: int | None = Field(None, ge=1900, le=2030)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    market_position: str = Field("challenger")
    pricing_tier: str = Field("mid")
    target_segments: list[str] = Field(default_factory=list)


class CompetitorUpdateRequest(BaseModel):
    """Request to update a competitor."""
    name: str | None = None
    description: str | None = None
    domain: str | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    market_position: str | None = None
    pricing_tier: str | None = None
    target_segments: list[str] | None = None


class BattlecardCreateRequest(BaseModel):
    """Request to create a battlecard."""
    product_id: str = Field(...)
    positioning: str = Field(..., min_length=1, max_length=5000)
    differentiators: list[str] = Field(default_factory=list)
    objection_handlers: list[dict[str, str]] = Field(default_factory=list)
    talk_tracks: list[str] = Field(default_factory=list)
    win_themes: list[str] = Field(default_factory=list)
    trap_questions: list[str] = Field(default_factory=list)


class WinLossRequest(BaseModel):
    """Request to record a win or loss."""
    competitor_id: str = Field(...)
    product_id: str = Field(...)
    outcome: str = Field(..., description="'won' or 'lost'")
    deal_size_usd: float = Field(0.0, ge=0)
    reason: str = Field("", max_length=2000)
    industry: str = Field("", max_length=200)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _extract_tenant_id(request: Request) -> str:
    """Extract tenant_id from request state or headers."""
    if hasattr(request.state, "tenant_id"):
        return request.state.tenant_id
    tenant = request.headers.get("X-Tenant-ID", "")
    if not tenant:
        raise HTTPException(status_code=400, detail="Missing tenant context")
    return tenant


def _get_neo4j_driver(request: Request):
    """Get Neo4j driver from app state."""
    return request.app.state.neo4j_driver


# ---------------------------------------------------------------------------
# Competitor Endpoints
# ---------------------------------------------------------------------------


@router.post("/competitors")
async def add_competitor(body: CompetitorCreateRequest, request: Request):
    """Add a new competitor to the knowledge graph."""
    from ...services.competitive_intel_service import CompetitorCreate, CompetitiveIntelService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    competitor = CompetitorCreate(
        name=body.name,
        description=body.description,
        domain=body.domain,
        founded_year=body.founded_year,
        strengths=body.strengths,
        weaknesses=body.weaknesses,
        market_position=body.market_position,
        pricing_tier=body.pricing_tier,
        target_segments=body.target_segments,
    )
    result = await svc.add_competitor(tenant_id, competitor)
    return {"status": "created", **result}


@router.get("/competitors")
async def list_competitors(
    request: Request,
    market_position: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List competitors with optional filtering."""
    from ...services.competitive_intel_service import CompetitiveIntelService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    return await svc.list_competitors(
        tenant_id,
        market_position=market_position,
        skip=skip,
        limit=limit,
    )


@router.get("/competitors/{competitor_id}")
async def get_competitor(competitor_id: str, request: Request):
    """Get a competitor with related products and battlecards."""
    from ...services.competitive_intel_service import CompetitiveIntelService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    result = await svc.get_competitor(tenant_id, competitor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return result


@router.put("/competitors/{competitor_id}")
async def update_competitor(
    competitor_id: str,
    body: CompetitorUpdateRequest,
    request: Request,
):
    """Update a competitor's properties."""
    from ...services.competitive_intel_service import CompetitiveIntelService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    result = await svc.update_competitor(tenant_id, competitor_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"status": "updated", **result}


@router.delete("/competitors/{competitor_id}")
async def delete_competitor(competitor_id: str, request: Request):
    """Delete a competitor and its battlecards."""
    from ...services.competitive_intel_service import CompetitiveIntelService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    deleted = await svc.delete_competitor(tenant_id, competitor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"status": "deleted", "competitor_id": competitor_id}


# ---------------------------------------------------------------------------
# Battlecard Endpoints
# ---------------------------------------------------------------------------


@router.post("/competitors/{competitor_id}/battlecards")
async def add_battlecard(
    competitor_id: str,
    body: BattlecardCreateRequest,
    request: Request,
):
    """Create a battlecard for a competitor + product pair."""
    from ...services.competitive_intel_service import BattlecardCreate, CompetitiveIntelService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    bc = BattlecardCreate(
        product_id=body.product_id,
        positioning=body.positioning,
        differentiators=body.differentiators,
        objection_handlers=body.objection_handlers,
        talk_tracks=body.talk_tracks,
        win_themes=body.win_themes,
        trap_questions=body.trap_questions,
    )
    result = await svc.add_battlecard(tenant_id, competitor_id, bc)
    return {"status": "created", **result}


@router.get("/competitors/{competitor_id}/battlecards")
async def get_battlecards(
    competitor_id: str,
    request: Request,
    product_id: str | None = Query(None),
):
    """Get battlecards for a competitor."""
    from ...services.competitive_intel_service import CompetitiveIntelService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    return await svc.get_battlecard(tenant_id, competitor_id, product_id)


# ---------------------------------------------------------------------------
# Win/Loss Endpoints
# ---------------------------------------------------------------------------


@router.post("/win-loss")
async def record_win_loss(body: WinLossRequest, request: Request):
    """Record a competitive win or loss."""
    from ...services.competitive_intel_service import CompetitiveIntelService, WinLossRecord

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    if body.outcome not in ("won", "lost"):
        raise HTTPException(status_code=400, detail="Outcome must be 'won' or 'lost'")

    wl = WinLossRecord(
        competitor_id=body.competitor_id,
        product_id=body.product_id,
        outcome=body.outcome,
        deal_size_usd=body.deal_size_usd,
        reason=body.reason,
        industry=body.industry,
    )
    result = await svc.record_win_loss(tenant_id, wl)
    return {"status": "recorded", **result}


@router.get("/win-loss/summary")
async def get_win_loss_summary(request: Request):
    """Get aggregated win/loss data across all competitors."""
    from ...services.competitive_intel_service import CompetitiveIntelService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    return await svc.get_win_loss_summary(tenant_id)


# ---------------------------------------------------------------------------
# Analysis Endpoints
# ---------------------------------------------------------------------------


@router.get("/landscape")
async def get_competitive_landscape(
    request: Request,
    product_id: str | None = Query(None),
):
    """Analyze the competitive landscape."""
    from ...services.competitive_intel_service import CompetitiveIntelService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = CompetitiveIntelService(driver)

    return await svc.analyze_competitive_landscape(tenant_id, product_id)
