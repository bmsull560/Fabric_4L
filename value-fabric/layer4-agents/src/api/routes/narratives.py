"""
Narrative Builder API routes — Data Intelligence Layer Phase 3, Task 3.1.

Provides REST endpoints for generating, managing, and retrieving
sales narratives built from intelligence data.

Endpoints:
  POST   /api/v1/narratives/generate        — Generate a new narrative
  GET    /api/v1/narratives                  — List narratives
  GET    /api/v1/narratives/{id}             — Get a narrative
  PATCH  /api/v1/narratives/{id}/status      — Update narrative status
  DELETE /api/v1/narratives/{id}             — Delete a narrative
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/narratives", tags=["Narratives"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class NarrativeGenerateRequest(BaseModel):
    """Request to generate a narrative."""

    account_id: str = Field(..., description="Account to generate narrative for")
    title: str = Field("Account Intelligence Narrative", max_length=500)
    tone: str = Field("executive", description="Tone: executive, technical, financial, consultative")
    audience: str = Field("c_suite", description="Audience: c_suite, vp_director, technical_buyer, champion, evaluation_committee")
    include_sections: list[str] = Field(
        default=[
            "executive_summary",
            "pain_points",
            "value_hypotheses",
            "competitive_positioning",
            "roi_projection",
            "evidence",
            "next_steps",
        ],
        description="Sections to include in the narrative",
    )
    ranking_strategy: str = Field("balanced", description="Hypothesis ranking strategy")
    roi_scenario: str = Field("moderate", description="ROI scenario for projections")
    roi_time_horizon_months: int = Field(36, ge=1, le=120)
    top_n_hypotheses: int = Field(5, ge=1, le=20)
    custom_next_steps: list[str] = Field(default_factory=list)
    # Optional pre-fetched data (for orchestration layer)
    account_data: dict[str, Any] | None = Field(None, description="Pre-fetched account data")
    signals_data: list[dict[str, Any]] | None = Field(None, description="Pre-fetched signals")
    hypotheses_data: list[dict[str, Any]] | None = Field(None, description="Pre-fetched hypotheses")
    competitive_data: dict[str, Any] | None = Field(None, description="Pre-fetched competitive landscape")
    roi_data: dict[str, Any] | None = Field(None, description="Pre-fetched ROI results")
    evidence_data: list[dict[str, Any]] | None = Field(None, description="Pre-fetched evidence")


class StatusUpdateRequest(BaseModel):
    """Request to update narrative status."""

    status: str = Field(..., description="New status: draft, review, approved, delivered")


# ---------------------------------------------------------------------------
# Helpers
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
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate")
async def generate_narrative(body: NarrativeGenerateRequest, request: Request):
    """Generate a new sales narrative from intelligence data."""
    from ...services.narrative_builder_service import (
        NarrativeBuilderService,
        NarrativeRequest,
    )

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = NarrativeBuilderService(driver)

    narr_request = NarrativeRequest(
        tenant_id=tenant_id,
        account_id=body.account_id,
        title=body.title,
        tone=body.tone,
        audience=body.audience,
        include_sections=body.include_sections,
        ranking_strategy=body.ranking_strategy,
        roi_scenario=body.roi_scenario,
        roi_time_horizon_months=body.roi_time_horizon_months,
        top_n_hypotheses=body.top_n_hypotheses,
        custom_next_steps=body.custom_next_steps,
    )

    result = await svc.generate_narrative(
        narr_request,
        account_data=body.account_data,
        signals_data=body.signals_data,
        hypotheses_data=body.hypotheses_data,
        competitive_data=body.competitive_data,
        roi_data=body.roi_data,
        evidence_data=body.evidence_data,
    )

    return result


@router.get("")
async def list_narratives(
    request: Request,
    account_id: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List narratives with optional filtering."""
    from ...services.narrative_builder_service import NarrativeBuilderService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = NarrativeBuilderService(driver)

    return await svc.list_narratives(
        tenant_id, account_id=account_id, status=status, skip=skip, limit=limit
    )


@router.get("/{narrative_id}")
async def get_narrative(narrative_id: str, request: Request):
    """Get a specific narrative."""
    from ...services.narrative_builder_service import NarrativeBuilderService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = NarrativeBuilderService(driver)

    result = await svc.get_narrative(tenant_id, narrative_id)
    if not result:
        raise HTTPException(status_code=404, detail="Narrative not found")
    return result


@router.patch("/{narrative_id}/status")
async def update_narrative_status(
    narrative_id: str, body: StatusUpdateRequest, request: Request
):
    """Update narrative status."""
    from ...services.narrative_builder_service import NarrativeBuilderService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = NarrativeBuilderService(driver)

    result = await svc.update_status(tenant_id, narrative_id, body.status)
    if not result:
        raise HTTPException(status_code=404, detail="Narrative not found")
    return result


@router.delete("/{narrative_id}")
async def delete_narrative(narrative_id: str, request: Request):
    """Delete a narrative."""
    from ...services.narrative_builder_service import NarrativeBuilderService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = NarrativeBuilderService(driver)

    deleted = await svc.delete_narrative(tenant_id, narrative_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Narrative not found")
    return {"status": "deleted", "narrative_id": narrative_id}
