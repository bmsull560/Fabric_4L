from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.core.tenant_context import tenant_required
from app.core.database import db
from app.models.schemas import Account

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=List[Account])
async def list_accounts(tenant_id: str = Depends(tenant_required)):
    return db.accounts.list(tenant_id=tenant_id)


@router.post("", response_model=Account)
async def create_account(account: Account, tenant_id: str = Depends(tenant_required)):
    account.tenant_id = tenant_id
    db.accounts.insert(account.id, account)
    return account


@router.get("/{account_id}", response_model=Account)
async def get_account(account_id: str, tenant_id: str = Depends(tenant_required)):
    acc = db.accounts.get(account_id, tenant_id=tenant_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return acc


@router.patch("/{account_id}", response_model=Account)
async def update_account(account_id: str, fields: dict, tenant_id: str = Depends(tenant_required)):
    acc = db.accounts.update(account_id, tenant_id=tenant_id, **fields)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return acc


@router.get("/{account_id}/summary")
async def get_account_summary(account_id: str, tenant_id: str = Depends(tenant_required)):
    acc = db.accounts.get(account_id, tenant_id=tenant_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    signals = db.signals.list(tenant_id=tenant_id, filter_fn=lambda s: s.account_id == account_id)
    hypotheses = db.hypotheses.list(tenant_id=tenant_id, filter_fn=lambda h: h.account_id == account_id)
    roi_calcs = db.roi_calculations.list(tenant_id=tenant_id, filter_fn=lambda r: r.account_id == account_id)
    return {
        "account": acc,
        "signal_count": len(signals),
        "hypothesis_count": len(hypotheses),
        "roi_calculation_count": len(roi_calcs),
    }
