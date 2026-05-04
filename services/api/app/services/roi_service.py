from typing import Any

from app.core.database import db
from app.models.schemas import ROICalculation


def calculate_roi(
    account_id: str,
    tenant_id: str,
    scenario_id: str,
    revenue_uplift: float,
    cost_savings: float,
    risk_reduction: float,
    solution_cost: float,
) -> ROICalculation:
    total_benefit = revenue_uplift + cost_savings + risk_reduction
    net_benefit = total_benefit - solution_cost
    roi_percent = (net_benefit / solution_cost) * 100 if solution_cost > 0 else 0.0
    payback_months = solution_cost / (total_benefit / 12) if total_benefit > 0 else float("inf")

    trace: list[dict[str, Any]] = [
        {"step": "revenue_uplift", "value": revenue_uplift},
        {"step": "cost_savings", "value": cost_savings},
        {"step": "risk_reduction", "value": risk_reduction},
        {
            "step": "total_benefit",
            "value": total_benefit,
            "note": "revenue_uplift + cost_savings + risk_reduction",
        },
        {"step": "net_benefit", "value": net_benefit, "note": "total_benefit - solution_cost"},
        {
            "step": "roi_percent",
            "value": round(roi_percent, 2),
            "note": "(net_benefit / solution_cost) * 100",
        },
        {
            "step": "payback_months",
            "value": round(payback_months, 2),
            "note": "solution_cost / (total_benefit / 12)",
        },
    ]

    calc_id = f"roi-{account_id}-{scenario_id}"
    calc = ROICalculation(
        id=calc_id,
        account_id=account_id,
        tenant_id=tenant_id,
        scenario_id=scenario_id,
        revenue_uplift=revenue_uplift,
        cost_savings=cost_savings,
        risk_reduction=risk_reduction,
        total_benefit=total_benefit,
        solution_cost=solution_cost,
        net_benefit=net_benefit,
        roi_percent=round(roi_percent, 2),
        payback_months=round(payback_months, 2) if payback_months != float("inf") else 0.0,
        calculation_trace=trace,
    )
    db.roi_calculations.insert(calc_id, calc)
    return calc
