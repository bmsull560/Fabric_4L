from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.tenant_context import tenant_required
from app.models.schemas import ROICalculation, Scenario
from app.services.roi_service import calculate_roi

router = APIRouter(prefix="/accounts/{account_id}", tags=["Calculator"])


@router.get("/scenarios", response_model=list[Scenario])
async def list_scenarios(account_id: str, tenant_id: str = Depends(tenant_required)):
    return db.scenarios.list(tenant_id=tenant_id, filter_fn=lambda s: s.account_id == account_id)


@router.post("/scenarios", response_model=Scenario, status_code=201)
async def create_scenario(
    account_id: str, scenario: Scenario, tenant_id: str = Depends(tenant_required)
):
    scenario.account_id = account_id
    scenario.tenant_id = tenant_id
    db.scenarios.insert(scenario.id, scenario)
    return scenario


@router.post("/roi/calculate", response_model=ROICalculation, status_code=201)
async def run_roi_calculation(
    account_id: str, payload: dict[str, Any], tenant_id: str = Depends(tenant_required)
):
    scenario_id = payload.get("scenario_id", "custom")
    calc = calculate_roi(
        account_id=account_id,
        tenant_id=tenant_id,
        scenario_id=scenario_id,
        revenue_uplift=payload.get("revenue_uplift", 0.0),
        cost_savings=payload.get("cost_savings", 0.0),
        risk_reduction=payload.get("risk_reduction", 0.0),
        solution_cost=payload.get("solution_cost", 0.0),
    )
    return calc


@router.get("/roi-calculations/{calculation_id}", response_model=ROICalculation)
async def get_roi_calculation(calculation_id: str, tenant_id: str = Depends(tenant_required)):
    calc = db.roi_calculations.get(calculation_id, tenant_id=tenant_id)
    if not calc:
        raise HTTPException(status_code=404, detail="ROI calculation not found")
    return calc
