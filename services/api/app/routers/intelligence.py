from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.core.tenant_context import tenant_required
from app.core.database import db
from app.models.schemas import Signal, Stakeholder

router = APIRouter(prefix="/accounts/{account_id}", tags=["Intelligence"])


@router.get("/signals", response_model=List[Signal])
async def list_signals(account_id: str, tenant_id: str = Depends(tenant_required)):
    return db.signals.list(tenant_id=tenant_id, filter_fn=lambda s: s.account_id == account_id)


@router.post("/signals/extract", response_model=Signal)
async def extract_signal(account_id: str, signal: Signal, tenant_id: str = Depends(tenant_required)):
    signal.account_id = account_id
    signal.tenant_id = tenant_id
    db.signals.insert(signal.id, signal)
    return signal


@router.get("/stakeholders", response_model=List[Stakeholder])
async def list_stakeholders(account_id: str, tenant_id: str = Depends(tenant_required)):
    return db.stakeholders.list(tenant_id=tenant_id, filter_fn=lambda s: s.account_id == account_id)


@router.get("/ontology-match")
async def get_ontology_match(account_id: str, tenant_id: str = Depends(tenant_required)):
    acc = db.accounts.get(account_id, tenant_id=tenant_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    pack = db.value_packs.get(acc.value_pack_id) if acc.value_pack_id else None
    return {
        "account_id": account_id,
        "matched_pack": pack,
        "confidence": 0.85 if pack else 0.0,
        "gaps": [] if pack else ["No value pack assigned"],
    }


@router.get("/enrichment")
async def get_enrichment(account_id: str, tenant_id: str = Depends(tenant_required)):
    acc = db.accounts.get(account_id, tenant_id=tenant_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "account_id": account_id,
        "firmographics": {
            "revenue": acc.annual_revenue,
            "employees": acc.employee_count,
            "industry": acc.industry,
            "website": acc.website,
        },
        "tech_stack": ["Salesforce", "HubSpot", "Slack"],
        "public_sources": ["LinkedIn", "Crunchbase"],
    }
