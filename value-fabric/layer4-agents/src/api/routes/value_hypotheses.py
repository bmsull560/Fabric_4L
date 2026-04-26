"""
Value Hypotheses API routes — Data Intelligence Layer Phase 2, Task 2.1.

Provides REST endpoints for generating, retrieving, ranking, and validating
value hypotheses. These endpoints orchestrate the ValueHypothesisEngine
service and expose its capabilities to the frontend and other consumers.

Endpoints:
  POST   /api/v1/hypotheses/generate          — Generate hypotheses for an account
  GET    /api/v1/hypotheses/{hypothesis_id}    — Get a single hypothesis
  GET    /api/v1/hypotheses/account/{account_id} — List hypotheses for an account
  POST   /api/v1/hypotheses/{hypothesis_id}/validate — Validate/reject a hypothesis
  DELETE /api/v1/hypotheses/{hypothesis_id}    — Delete a hypothesis
  GET    /api/v1/hypotheses/summary            — Aggregate hypothesis statistics
  POST   /api/v1/hypotheses/rank               — Re-rank a set of hypotheses
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

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
    hypothesis_ids: list[str] = Field(..., min_length=1)
    strategy: str = Field("balanced", description="Ranking strategy")


# ---------------------------------------------------------------------------
# Helper: Extract tenant ID
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
async def generate_hypotheses(
    body: GenerateHypothesesRequest,
    request: Request,
):
    """Generate value hypotheses for an account.

    Traverses the knowledge graph to find signal→capability→product paths,
    enriches with evidence, and returns ranked hypotheses.
    """
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    tenant_id = _extract_tenant_id(request)
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
):
    """Get a single value hypothesis with full detail."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    tenant_id = _extract_tenant_id(request)
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
):
    """List all hypotheses for an account with optional filtering."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    tenant_id = _extract_tenant_id(request)
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
):
    """Validate, reject, or provide feedback on a hypothesis."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    engine = ValueHypothesisEngine(driver)

    # Validate status transition
    valid_statuses = {"validated", "rejected", "converted", None}
    if body.new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses - {None}}",
        )

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
):
    """Delete a value hypothesis."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    tenant_id = _extract_tenant_id(request)
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
):
    """Get aggregate statistics about hypotheses."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    engine = ValueHypothesisEngine(driver)

    return await engine.get_hypothesis_summary(tenant_id, account_id)


@router.post("/rank")
async def rank_hypotheses(
    body: RankHypothesesRequest,
    request: Request,
):
    """Re-rank a set of hypotheses using a specified strategy."""
    from ...services.value_hypothesis_engine import ValueHypothesisEngine

    tenant_id = _extract_tenant_id(request)
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
