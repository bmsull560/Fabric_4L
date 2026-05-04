from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.tenant_context import tenant_required
from app.models.schemas import ValueHypothesis

router = APIRouter(prefix="/accounts/{account_id}", tags=["Hypotheses"])


@router.get("/hypotheses", response_model=list[ValueHypothesis])
async def list_hypotheses(account_id: str, tenant_id: str = Depends(tenant_required)):
    return db.hypotheses.list(tenant_id=tenant_id, filter_fn=lambda h: h.account_id == account_id)


@router.post("/hypotheses/generate", response_model=ValueHypothesis, status_code=201)
async def generate_hypothesis(
    account_id: str, hypothesis: ValueHypothesis, tenant_id: str = Depends(tenant_required)
):
    hypothesis.account_id = account_id
    hypothesis.tenant_id = tenant_id
    db.hypotheses.insert(hypothesis.id, hypothesis)
    return hypothesis


@router.patch("/hypotheses/{hypothesis_id}", response_model=ValueHypothesis)
async def update_hypothesis(
    hypothesis_id: str,
    fields: dict[str, Any],
    tenant_id: str = Depends(tenant_required),
):
    hyp = db.hypotheses.update(hypothesis_id, tenant_id=tenant_id, **fields)
    if not hyp:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hyp
