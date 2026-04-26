"""
Value Hypotheses API routes — Data Intelligence Layer Phase 2, Task 2.1.

Provides REST endpoints for generating, retrieving, ranking, and validating
value hypotheses. These endpoints orchestrate the ValueHypothesisEngine
service and expose its capabilities to the frontend and other consumers.

All endpoints require authentication via GovernanceMiddleware.
Tenant identity is extracted from the verified JWT/API-key context (V-001, V-002).
Hypothesis status transitions are validated against an enum (V-008).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from shared.security.dil_auth import (
    get_verified_tenant_id,
    validate_enum_value,
    VALID_HYPOTHESIS_STATUSES,
)

router = APIRouter(prefix="/hypotheses", tags=["Value Hypotheses"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class GenerateHypothesesRequest(BaseModel):
    """Request to generate value hypotheses for an account."""
    account_id: str = Field(..., description="Account ID to generate hypotheses for")
    min_confidence: float = Field(0.3, ge=0.0, le=1.0)
    max_hypotheses: int = Field(20, ge=1, le=100)
    include_evidence: bool = Field(True)


class ValidateHypothesisRequest(BaseModel):
    """Request to validate or reject a hypothesis."""
    feedback: str = Field(..., min_length=1, max_length=2000)
    new_status: str | None = Field(
        None,
        description="New status: validated, rejected, or converted",
    )
    confidence_adjustment: float = Field(
        0.0,
        ge=-1.0,
        le=1.0,
        description="Additive confidence adjustment",
    )


class RankHypothesesRequest(BaseModel):
    """Request to re-rank hypotheses."""
    hypothesis_ids: list[str] = Field(..., min_length=1, max_length=200)
    strategy: str = Field("balanced", description="Ranking strategy")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_neo4j_driver(request: Request):
    """Get Neo4j driver from app state."""
    return request.app.state.neo4j_driver


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate")
async def generate_hypotheses(
    body: GenerateHypothesesRequest,
    request: Request,
    tenant_id: str = Depends(get_verified_tenant_id),
):
    """Generate value hypotheses for an account.

    Traverses the knowledge graph to find signal->capability->product paths,
    enriches with evidence, and returns ranked hypotheses.
    """
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    driver = _get_neo4j_driver(request)
    engine = ValueHypothesisEngine(driver)

    hypotheses = await engine.generate_hypotheses(
        tenant_id,
        body.account_id,
        min_confidence=body.min_confidence,
        max_hypotheses=body.max_hypotheses,
        include_evidence=body.include_evidence,
    )

    return {
        "status": "success",
        "account_id": body.account_id,
        "count": len(hypotheses),
        "hypotheses": hypotheses,
    }


@router.get("/{hypothesis_id}")
async def get_hypothesis(
    hypothesis_id: str,
    request: Request,
    tenant_id: str = Depends(get_verified_tenant_id),
):
    """Get a single value hypothesis with full detail."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    driver = _get_neo4j_driver(request)
    engine = ValueHypothesisEngine(driver)

    result = await engine.get_hypothesis(tenant_id, hypothesis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Hypothesis not found")

    return result


@router.get("/account/{account_id}")
async def get_account_hypotheses(
    account_id: str,
    request: Request,
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tenant_id: str = Depends(get_verified_tenant_id),
):
    """List all hypotheses for an account with optional filtering."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    driver = _get_neo4j_driver(request)
    engine = ValueHypothesisEngine(driver)

    return await engine.get_account_hypotheses(
        tenant_id,
        account_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.post("/{hypothesis_id}/validate")
async def validate_hypothesis(
    hypothesis_id: str,
    body: ValidateHypothesisRequest,
    request: Request,
    tenant_id: str = Depends(get_verified_tenant_id),
):
    """Validate, reject, or provide feedback on a hypothesis."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    driver = _get_neo4j_driver(request)
    engine = ValueHypothesisEngine(driver)

    # V-008: Validate status transition against enum
    if body.new_status is not None:
        validate_enum_value(body.new_status, VALID_HYPOTHESIS_STATUSES, "new_status")

    result = await engine.validate_hypothesis(
        tenant_id,
        hypothesis_id,
        feedback=body.feedback,
        new_status=body.new_status,
        confidence_adjustment=body.confidence_adjustment,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Hypothesis not found")

    return {"status": "updated", "hypothesis": result}


@router.delete("/{hypothesis_id}")
async def delete_hypothesis(
    hypothesis_id: str,
    request: Request,
    tenant_id: str = Depends(get_verified_tenant_id),
):
    """Delete a value hypothesis."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    driver = _get_neo4j_driver(request)
    engine = ValueHypothesisEngine(driver)

    deleted = await engine.delete_hypothesis(tenant_id, hypothesis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Hypothesis not found")

    return {"status": "deleted", "hypothesis_id": hypothesis_id}


@router.get("/summary/stats")
async def get_hypothesis_summary(
    request: Request,
    account_id: str | None = Query(None),
    tenant_id: str = Depends(get_verified_tenant_id),
):
    """Get aggregate statistics about hypotheses."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    driver = _get_neo4j_driver(request)
    engine = ValueHypothesisEngine(driver)

    return await engine.get_hypothesis_summary(tenant_id, account_id)


@router.post("/rank")
async def rank_hypotheses(
    body: RankHypothesesRequest,
    request: Request,
    tenant_id: str = Depends(get_verified_tenant_id),
):
    """Re-rank a set of hypotheses using a specified strategy."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    driver = _get_neo4j_driver(request)
    engine = ValueHypothesisEngine(driver)

    # Fetch each hypothesis
    hypotheses = []
    for hid in body.hypothesis_ids:
        h = await engine.get_hypothesis(tenant_id, hid)
        if h:
            hypotheses.append(h)

    if not hypotheses:
        raise HTTPException(status_code=404, detail="No valid hypotheses found")

    ranked = engine.rank_hypotheses(hypotheses, body.strategy)

    return {
        "strategy": body.strategy,
        "count": len(ranked),
        "hypotheses": ranked,
    }
