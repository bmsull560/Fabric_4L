from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.core.tenant_context import tenant_required
from app.core.database import db
from app.models.schemas import ValueDriver

router = APIRouter(prefix="/accounts/{account_id}", tags=["Driver Tree"])


@router.get("/drivers", response_model=List[ValueDriver])
async def list_drivers(account_id: str, tenant_id: str = Depends(tenant_required)):
    return db.drivers.list(tenant_id=tenant_id, filter_fn=lambda d: d.account_id == account_id)


@router.get("/value-tree")
async def get_value_tree(account_id: str, tenant_id: str = Depends(tenant_required)):
    drivers = db.drivers.list(tenant_id=tenant_id, filter_fn=lambda d: d.account_id == account_id)
    return {
        "account_id": account_id,
        "categories": {
            "revenue_uplift": [d for d in drivers if d.category == "revenue_uplift"],
            "cost_savings": [d for d in drivers if d.category == "cost_savings"],
            "risk_reduction": [d for d in drivers if d.category == "risk_reduction"],
        },
    }


@router.post("/drivers/generate", response_model=ValueDriver)
async def generate_driver(account_id: str, driver: ValueDriver, tenant_id: str = Depends(tenant_required)):
    driver.account_id = account_id
    driver.tenant_id = tenant_id
    db.drivers.insert(driver.id, driver)
    return driver


@router.patch("/drivers/{driver_id}", response_model=ValueDriver)
async def update_driver(driver_id: str, fields: dict, tenant_id: str = Depends(tenant_required)):
    drv = db.drivers.update(driver_id, tenant_id=tenant_id, **fields)
    if not drv:
        raise HTTPException(status_code=404, detail="Driver not found")
    return drv
