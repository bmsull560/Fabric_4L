"""
ROI Calculator API routes — Data Intelligence Layer Phase 2, Task 2.3.

Provides REST endpoints for calculating ROI projections, managing templates,
comparing scenarios, and retrieving industry benchmarks.

Endpoints:
  POST   /api/v1/roi/calculate          — Calculate ROI from inputs
  POST   /api/v1/roi/compare            — Compare multiple scenarios
  GET    /api/v1/roi/templates           — List ROI templates
  POST   /api/v1/roi/templates           — Create an ROI template
  GET    /api/v1/roi/calculations        — List saved calculations
  GET    /api/v1/roi/calculations/{id}   — Get a saved calculation
  GET    /api/v1/roi/benchmarks/{industry} — Get industry benchmarks
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/roi", tags=["ROI Calculator"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class ROICalculateRequest(BaseModel):
    """Request to calculate ROI."""
    annual_revenue: float = Field(0.0, ge=0)
    num_employees: int = Field(0, ge=0)
    avg_salary: float = Field(75000.0, ge=0)
    current_cost_annual: float = Field(0.0, ge=0)
    implementation_cost: float = Field(0.0, ge=0)
    annual_license_cost: float = Field(0.0, ge=0)
    training_cost: float = Field(0.0, ge=0)
    productivity_gain_pct: float = Field(0.10, ge=0, le=1.0)
    error_reduction_pct: float = Field(0.20, ge=0, le=1.0)
    time_savings_hours_per_week: float = Field(5.0, ge=0)
    affected_employees_pct: float = Field(0.25, ge=0, le=1.0)
    custom_inputs: dict[str, float] = Field(default_factory=dict)
    # Calculation parameters
    time_horizon_months: int = Field(36, ge=1, le=120)
    discount_rate: float = Field(0.10, ge=0, le=1.0)
    scenario: str = Field("moderate")
    # Optional persistence
    account_id: str | None = Field(None)
    template_id: str | None = Field(None)
    save: bool = Field(False, description="Whether to persist the calculation")


class ScenarioCompareRequest(BaseModel):
    """Request to compare scenarios."""
    annual_revenue: float = Field(0.0, ge=0)
    num_employees: int = Field(0, ge=0)
    avg_salary: float = Field(75000.0, ge=0)
    current_cost_annual: float = Field(0.0, ge=0)
    implementation_cost: float = Field(0.0, ge=0)
    annual_license_cost: float = Field(0.0, ge=0)
    training_cost: float = Field(0.0, ge=0)
    productivity_gain_pct: float = Field(0.10, ge=0, le=1.0)
    error_reduction_pct: float = Field(0.20, ge=0, le=1.0)
    time_savings_hours_per_week: float = Field(5.0, ge=0)
    affected_employees_pct: float = Field(0.25, ge=0, le=1.0)
    custom_inputs: dict[str, float] = Field(default_factory=dict)
    time_horizon_months: int = Field(36, ge=1, le=120)
    discount_rate: float = Field(0.10, ge=0, le=1.0)
    scenarios: list[str] = Field(
        default=["conservative", "moderate", "aggressive"],
        description="Scenario names to compare",
    )


class TemplateCreateRequest(BaseModel):
    """Request to create an ROI template."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    category: str = Field("general", max_length=100)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    default_assumptions: dict[str, float] = Field(default_factory=dict)
    applicable_industries: list[str] = Field(default_factory=list)
    applicable_products: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helper
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
# Calculation Endpoints
# ---------------------------------------------------------------------------


@router.post("/calculate")
async def calculate_roi(body: ROICalculateRequest, request: Request):
    """Calculate ROI from inputs.

    Optionally saves the calculation to the knowledge graph if save=True.
    """
    from ...services.roi_calculator_service import ROICalculatorService, ROIInputs

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = ROICalculatorService(driver)

    inputs = ROIInputs(
        annual_revenue=body.annual_revenue,
        num_employees=body.num_employees,
        avg_salary=body.avg_salary,
        current_cost_annual=body.current_cost_annual,
        implementation_cost=body.implementation_cost,
        annual_license_cost=body.annual_license_cost,
        training_cost=body.training_cost,
        productivity_gain_pct=body.productivity_gain_pct,
        error_reduction_pct=body.error_reduction_pct,
        time_savings_hours_per_week=body.time_savings_hours_per_week,
        affected_employees_pct=body.affected_employees_pct,
        custom_inputs=body.custom_inputs,
    )

    result = svc.calculate_roi(
        inputs,
        time_horizon_months=body.time_horizon_months,
        discount_rate=body.discount_rate,
        scenario=body.scenario,
    )

    response = {
        "status": "calculated",
        "scenario": body.scenario,
        "time_horizon_months": body.time_horizon_months,
        "discount_rate": body.discount_rate,
        "results": {
            "total_benefit_year1": result.total_benefit_year1,
            "total_benefit_3year": result.total_benefit_3year,
            "total_cost_year1": result.total_cost_year1,
            "total_cost_3year": result.total_cost_3year,
            "net_benefit_year1": result.net_benefit_year1,
            "net_benefit_3year": result.net_benefit_3year,
            "roi_pct_year1": result.roi_pct_year1,
            "roi_pct_3year": result.roi_pct_3year,
            "payback_months": result.payback_months,
            "npv": result.npv,
            "irr": result.irr,
            "benefit_breakdown": result.benefit_breakdown,
            "cost_breakdown": result.cost_breakdown,
        },
    }

    # Optionally persist
    if body.save:
        saved = await svc.save_calculation(
            tenant_id,
            account_id=body.account_id,
            template_id=body.template_id,
            inputs=body.model_dump(exclude={"save", "scenario", "time_horizon_months", "discount_rate"}),
            outputs=response["results"],
            scenario_name=body.scenario,
            time_horizon_months=body.time_horizon_months,
            discount_rate=body.discount_rate,
        )
        response["calculation_id"] = saved.get("id")

    return response


@router.post("/compare")
async def compare_scenarios(body: ScenarioCompareRequest, request: Request):
    """Compare ROI across multiple scenarios."""
    from ...services.roi_calculator_service import ROICalculatorService, ROIInputs

    _extract_tenant_id(request)  # Validate tenant
    driver = _get_neo4j_driver(request)
    svc = ROICalculatorService(driver)

    inputs = ROIInputs(
        annual_revenue=body.annual_revenue,
        num_employees=body.num_employees,
        avg_salary=body.avg_salary,
        current_cost_annual=body.current_cost_annual,
        implementation_cost=body.implementation_cost,
        annual_license_cost=body.annual_license_cost,
        training_cost=body.training_cost,
        productivity_gain_pct=body.productivity_gain_pct,
        error_reduction_pct=body.error_reduction_pct,
        time_savings_hours_per_week=body.time_savings_hours_per_week,
        affected_employees_pct=body.affected_employees_pct,
        custom_inputs=body.custom_inputs,
    )

    return svc.compare_scenarios(
        inputs,
        scenarios=body.scenarios,
        time_horizon_months=body.time_horizon_months,
        discount_rate=body.discount_rate,
    )


# ---------------------------------------------------------------------------
# Template Endpoints
# ---------------------------------------------------------------------------


@router.get("/templates")
async def list_templates(
    request: Request,
    category: str | None = Query(None),
    industry: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List available ROI templates."""
    from ...services.roi_calculator_service import ROICalculatorService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = ROICalculatorService(driver)

    return await svc.get_templates(
        tenant_id, category=category, industry=industry, skip=skip, limit=limit
    )


@router.post("/templates")
async def create_template(body: TemplateCreateRequest, request: Request):
    """Create a new ROI calculation template."""
    from ...services.roi_calculator_service import ROICalculatorService, ROITemplateCreate

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = ROICalculatorService(driver)

    template = ROITemplateCreate(
        name=body.name,
        description=body.description,
        category=body.category,
        input_schema=body.input_schema,
        default_assumptions=body.default_assumptions,
        applicable_industries=body.applicable_industries,
        applicable_products=body.applicable_products,
    )
    return await svc.create_template(tenant_id, template)


# ---------------------------------------------------------------------------
# Calculation History
# ---------------------------------------------------------------------------


@router.get("/calculations")
async def list_calculations(
    request: Request,
    account_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List saved ROI calculations."""
    from ...services.roi_calculator_service import ROICalculatorService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = ROICalculatorService(driver)

    return await svc.list_calculations(
        tenant_id, account_id=account_id, skip=skip, limit=limit
    )


@router.get("/calculations/{calc_id}")
async def get_calculation(calc_id: str, request: Request):
    """Get a saved ROI calculation."""
    from ...services.roi_calculator_service import ROICalculatorService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = ROICalculatorService(driver)

    result = await svc.get_calculation(tenant_id, calc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return result


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------


@router.get("/benchmarks/{industry}")
async def get_industry_benchmarks(industry: str, request: Request):
    """Get industry-specific benchmarks for ROI assumptions."""
    from ...services.roi_calculator_service import ROICalculatorService

    tenant_id = _extract_tenant_id(request)
    driver = _get_neo4j_driver(request)
    svc = ROICalculatorService(driver)

    return await svc.get_industry_benchmarks(tenant_id, industry)
