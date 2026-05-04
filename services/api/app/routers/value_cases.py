from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.tenant_context import tenant_required
from app.models.schemas import BusinessCase

router = APIRouter(prefix="/accounts/{account_id}", tags=["Value Case"])


@router.get("/value-case", response_model=BusinessCase)
async def get_value_case(account_id: str, tenant_id: str = Depends(tenant_required)):
    cases = db.business_cases.list(
        tenant_id=tenant_id, filter_fn=lambda c: c.account_id == account_id
    )
    if not cases:
        raise HTTPException(status_code=404, detail="No value case found for account")
    return cases[0]


@router.post("/value-case/generate", response_model=BusinessCase, status_code=201)
async def generate_value_case(
    account_id: str, case: BusinessCase, tenant_id: str = Depends(tenant_required)
):
    case.account_id = account_id
    case.tenant_id = tenant_id
    db.business_cases.insert(case.id, case)
    return case


@router.patch("/value-cases/{value_case_id}", response_model=BusinessCase)
async def update_value_case(
    value_case_id: str,
    fields: dict[str, Any],
    tenant_id: str = Depends(tenant_required),
):
    bc = db.business_cases.update(value_case_id, tenant_id=tenant_id, **fields)
    if not bc:
        raise HTTPException(status_code=404, detail="Value case not found")
    return bc
