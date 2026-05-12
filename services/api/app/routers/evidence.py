from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.tenant_enforcement import enforce_authenticated_tenant
from app.core.tenant_context import tenant_required
from app.models.schemas import Evidence

router = APIRouter(prefix="/accounts/{account_id}", tags=["Evidence"])


@router.get("/evidence", response_model=list[Evidence])
async def list_evidence(account_id: str, tenant_id: str = Depends(tenant_required)):
    return db.evidence.list(tenant_id=tenant_id, filter_fn=lambda e: e.account_id == account_id)


@router.post("/evidence/match", response_model=Evidence, status_code=201)
async def match_evidence(
    account_id: str, evidence: Evidence, tenant_id: str = Depends(tenant_required)
):
    enforce_authenticated_tenant(
        body_tenant_id=evidence.tenant_id,
        authenticated_tenant_id=tenant_id,
        route="/v1/accounts/{account_id}/evidence/match",
        operation="match_evidence",
    )
    evidence.account_id = account_id
    evidence.tenant_id = tenant_id
    db.evidence.insert(evidence.id, evidence)
    return evidence


@router.get("/evidence/{evidence_id}", response_model=Evidence)
async def get_evidence(evidence_id: str, tenant_id: str = Depends(tenant_required)):
    ev = db.evidence.get(evidence_id, tenant_id=tenant_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev
