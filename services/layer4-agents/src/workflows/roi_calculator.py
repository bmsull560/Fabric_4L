"""ROI Calculator workflow implementation.

Calculates ROI from value driver formulas using prospect data and industry
benchmarks.  Each step validates the output of the previous step so that
errors surface early rather than propagating as missing keys or division-by-
zero downstream.
"""

from __future__ import annotations

import logging
from typing import Any

from value_fabric.shared.models.typed_dict import TypedDictModel

from ..models.agent_state import ROIAgentState, ROIInputData, ROIResult, WorkflowStatus
from ..models.workflow_config import ROI_WORKFLOW_CONFIG
from ..tools.registry import ToolRegistry
from .base import BaseWorkflow
from .queries import get_benchmark_variables_query, get_value_driver_formulas_query

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_IMPLEMENTATION_COST = 250_000
DEFAULT_ANNUAL_LICENSE_COST = 50_000
DEFAULT_HOURLY_RATE = 75
DEFAULT_HOURS_SAVED_WEEKLY = 40
DEFAULT_EMPLOYEE_COUNT = 500
DEFAULT_ANNUAL_REVENUE = 10_000_000
DEFAULT_DISCOUNT_RATE = 0.10
NPV_YEARS = 3

CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60
CONFIDENCE_LOW = 0.30
CONFIDENCE_NONE = 0.0


# ---------------------------------------------------------------------------
# Internal result shapes (kept minimal – dict[str, Any] is fine for workflow
# state, but these models give us validation and docstrings).
# ---------------------------------------------------------------------------
class _ProspectDataResult(TypedDictModel):
    enriched: dict[str, Any] | None = None
    error: str = ""
    prospect_id: str | None = None
    raw_data: dict[str, Any] | None = None


class _BenchmarkResult(TypedDictModel):
    benchmarks: dict[str, Any] | None = None
    error: str = ""
    industry: str | None = None


class _VariablesResult(TypedDictModel):
    confidence: float = 0.0
    variable_count: int = 0
    variables: dict[str, Any] | None = None
    error: str = ""


class _EvaluationResult(TypedDictModel):
    calculated_count: int = 0
    error: str = ""
    results: list[dict[str, Any]] | None = None


class _AggregationResult(TypedDictModel):
    aggregated: dict[str, Any] | None = None
    detailed_results: list[dict[str, Any]] | None = None
    error: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _unwrap_tool_data(tool_result: Any) -> dict[str, Any]:
    """Extract the data payload from a ToolResult (or passthrough a dict)."""
    if hasattr(tool_result, "data"):
        return tool_result.data or {}
    if isinstance(tool_result, dict):
        return tool_result
    return {}


def _unwrap_tool_error(tool_result: Any) -> str | None:
    """Return a human-readable error message if the tool result failed."""
    if hasattr(tool_result, "is_error") and tool_result.is_error():
        error = getattr(tool_result, "error", None) or {}
        return error.get("message", "Unknown tool error") if isinstance(error, dict) else str(error)
    return None


def _tenant_id_from_state(state: ROIAgentState) -> str | None:
    """Best-effort tenant extraction from state metadata or input_data."""
    return (
        state.metadata.get("tenant_id")
        or state.input_data.get("tenant_id")
        or None
    )


def _build_roi_result(
    vd: dict[str, Any],
    eval_result: dict[str, Any] | None,
    variables: dict[str, Any],
    confidence: float,
    missing_variables: list[str],
) -> ROIResult:
    """Construct an ROIResult from a value driver and optional evaluation output."""
    formula = vd.get("formula") or ""
    return ROIResult(
        value_driver_id=vd["id"],
        value_driver_name=vd["name"],
        formula=formula,
        substituted_formula=(eval_result or {}).get("substituted_formula", formula),
        result=(eval_result or {}).get("result", 0),
        unit=vd.get("unit", "USD"),
        confidence=confidence,
        variables_used=variables,
        missing_variables=missing_variables,
    )


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------
class ROICalculatorWorkflow(BaseWorkflow):
    """Workflow for calculating ROI from value driver formulas.

    Pipeline:
    1. Load prospect data from CRM
    2. Fetch industry benchmarks
    3. Substitute variables in formulas
    4. Evaluate formulas
    5. Validate and aggregate results

    Example:
        workflow = ROICalculatorWorkflow(tool_registry)
        initial_state = workflow.create_initial_state({
            "prospect_id": "prospect-001",
            "value_driver_ids": ["vd-001", "vd-002"],
            "industry_vertical": "manufacturing"
        })
        result = await workflow.run(initial_state)
    """

    def __init__(self, tool_registry: ToolRegistry, checkpoint_saver=None):
        """Initialize ROI Calculator workflow."""
        super().__init__(
            config=ROI_WORKFLOW_CONFIG,
            tool_registry=tool_registry,
            checkpoint_saver=checkpoint_saver,
        )

    def _get_state_type(self):
        """Return ROI-specific state type."""
        return ROIAgentState

    def create_initial_state(self, input_data: dict[str, Any]) -> ROIAgentState:
        """Create initial state from input data."""
        roi_input = ROIInputData(**input_data)

        return ROIAgentState(
            workflow_type=self.config.workflow_type,
            status=WorkflowStatus.PENDING,
            roi_input=roi_input,
            input_data=input_data,
            output_data={},
            errors=[],
            metadata={"workflow_name": self.name, "tenant_id": input_data.get("tenant_id")},
        )

    async def _execute_tool(
        self, tool_name: str, state: ROIAgentState, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool with ROI-specific input building."""

        if tool_name == "get_prospect_data":
            return await self._execute_get_prospect_data(state)

        if tool_name == "fetch_benchmarks":
            return await self._execute_fetch_benchmarks(state)

        if tool_name == "substitute_variables":
            return await self._execute_substitute_variables(state)

        if tool_name == "evaluate_formula":
            return await self._execute_evaluate_formula(state)

        if tool_name == "aggregate_roi":
            return await self._execute_aggregate_roi(state)

        return await super()._execute_tool(tool_name, state, config)

    # -----------------------------------------------------------------------
    # Step 1 – Prospect data
    # -----------------------------------------------------------------------
    async def _execute_get_prospect_data(self, state: ROIAgentState) -> dict[str, Any]:
        """Load and enrich prospect data."""
        if not state.roi_input:
            return _ProspectDataResult(
                error="No ROI input configured"
            ).model_dump()

        tool_input = {
            "prospect_id": state.roi_input.prospect_id,
            "data_types": ["profile", "interactions", "opportunities"],
        }
        tenant_id = _tenant_id_from_state(state)
        if tenant_id:
            tool_input["tenant_id"] = tenant_id

        raw = await self.tool_registry.execute("get_prospect_data", tool_input)

        error = _unwrap_tool_error(raw)
        if error:
            logger.warning("get_prospect_data failed: %s", error)
            return _ProspectDataResult(
                error=error,
                prospect_id=state.roi_input.prospect_id,
            ).model_dump()

        data = _unwrap_tool_data(raw)
        profile = data.get("profile") or {}
        custom_fields = data.get("custom_fields") or {}

        enriched = {
            "company_size": profile.get("employees", 0),
            "industry": profile.get("industry", state.roi_input.industry_vertical or ""),
            "annual_revenue": profile.get("annual_revenue", 0),
            "pain_points": custom_fields.get("pain_points", []),
        }

        return _ProspectDataResult(
            raw_data=data,
            enriched=enriched,
            prospect_id=state.roi_input.prospect_id,
        ).model_dump()

    # -----------------------------------------------------------------------
    # Step 2 – Benchmarks
    # -----------------------------------------------------------------------
    async def _execute_fetch_benchmarks(self, state: ROIAgentState) -> dict[str, Any]:
        """Fetch industry benchmarks for comparison."""
        if not state.roi_input:
            return _BenchmarkResult(error="No ROI input configured").model_dump()

        industry = state.roi_input.industry_vertical or "technology"
        company_size = state.roi_input.company_size or "medium"
        tenant_id = _tenant_id_from_state(state)

        benchmarks: dict[str, Any] = {}
        errors: list[str] = []

        for metric in ("roi_percent", "cost_reduction", "time_to_value_months"):
            try:
                tool_input = {
                    "metric_name": metric,
                    "value": 0,
                    "industry": industry,
                    "company_size": company_size,
                }
                if tenant_id:
                    tool_input["tenant_id"] = tenant_id

                raw = await self.tool_registry.execute("compare_benchmarks", tool_input)

                err = _unwrap_tool_error(raw)
                if err:
                    logger.warning("compare_benchmarks(%s) failed: %s", metric, err)
                    errors.append(f"{metric}: {err}")
                    benchmarks[metric] = None
                else:
                    benchmarks[metric] = _unwrap_tool_data(raw)
            except Exception as exc:
                logger.exception("Unexpected error fetching benchmark %s", metric)
                errors.append(f"{metric}: {exc}")
                benchmarks[metric] = None

        if errors:
            logger.info("Benchmark fetch completed with %d errors", len(errors))

        return _BenchmarkResult(
            benchmarks=benchmarks,
            industry=industry,
            error="; ".join(errors) if errors else "",
        ).model_dump()

    # -----------------------------------------------------------------------
    # Step 3 – Variable substitution
    # -----------------------------------------------------------------------
    async def _execute_substitute_variables(self, state: ROIAgentState) -> dict[str, Any]:
        """Substitute variables in value driver formulas from Neo4j."""
        prior = state.output_data.get("load_prospect", {})
        if prior.get("error"):
            return _VariablesResult(
                error=f"Cannot substitute variables: prior step failed – {prior['error']}"
            ).model_dump()

        prospect_data = prior.get("enriched") or {}
        industry = prospect_data.get("industry", "technology")
        tenant_id = _tenant_id_from_state(state)

        query = get_benchmark_variables_query(industry, tenant_id=tenant_id)

        raw = await self.tool_registry.execute("query_graph", query)

        err = _unwrap_tool_error(raw)
        if err:
            logger.warning("query_graph(benchmark_variables) failed: %s", err)

        data = _unwrap_tool_data(raw)
        defaults = (
            data.get("results", [{}])[0].get("defaults", {})
            if data.get("results")
            else {}
        )

        variables: dict[str, Any] = {
            "annual_revenue": prospect_data.get(
                "annual_revenue", defaults.get("annual_revenue", DEFAULT_ANNUAL_REVENUE)
            ),
            "employee_count": prospect_data.get(
                "company_size", defaults.get("employee_count", DEFAULT_EMPLOYEE_COUNT)
            ),
            "hours_saved_weekly": defaults.get("hours_saved_weekly", DEFAULT_HOURS_SAVED_WEEKLY),
            "hourly_rate": defaults.get("hourly_rate", DEFAULT_HOURLY_RATE),
            "implementation_cost": defaults.get("implementation_cost", DEFAULT_IMPLEMENTATION_COST),
            "annual_license_cost": defaults.get("annual_license_cost", DEFAULT_ANNUAL_LICENSE_COST),
        }

        custom = prospect_data.get("custom_variables")
        if isinstance(custom, dict):
            variables.update(custom)

        confidence = CONFIDENCE_HIGH if prospect_data else CONFIDENCE_MEDIUM

        return _VariablesResult(
            variables=variables,
            variable_count=len(variables),
            confidence=confidence,
        ).model_dump()

    # -----------------------------------------------------------------------
    # Step 4 – Formula evaluation
    # -----------------------------------------------------------------------
    async def _execute_evaluate_formula(self, state: ROIAgentState) -> dict[str, Any]:
        """Evaluate formulas for each value driver from Neo4j."""
        if not state.roi_input:
            return _EvaluationResult(error="No ROI input configured").model_dump()

        vars_prior = state.output_data.get("substitute_vars", {})
        if vars_prior.get("error"):
            return _EvaluationResult(
                error=f"Cannot evaluate: variable substitution failed – {vars_prior['error']}"
            ).model_dump()

        variables = vars_prior.get("variables") or {}
        tenant_id = _tenant_id_from_state(state)

        query = get_value_driver_formulas_query(
            state.roi_input.value_driver_ids, tenant_id=tenant_id
        )

        raw = await self.tool_registry.execute("query_graph", query)

        err = _unwrap_tool_error(raw)
        if err:
            logger.error("query_graph(value_drivers) failed: %s", err)
            return _EvaluationResult(error=f"Failed to load value drivers: {err}").model_dump()

        data = _unwrap_tool_data(raw)
        value_drivers = []
        for record in data.get("results", []):
            value_drivers.append(
                {
                    "id": record.get("id"),
                    "name": record.get("name"),
                    "category": record.get("category"),
                    "formula": record.get("formula"),
                    "unit": record.get("unit", "USD"),
                }
            )

        results: list[ROIResult] = []

        for vd in value_drivers:
            if not vd.get("formula"):
                results.append(
                    _build_roi_result(
                        vd,
                        None,
                        variables,
                        CONFIDENCE_NONE,
                        ["Value driver has no formula"],
                    )
                )
                continue

            try:
                tool_input = {
                    "formula": vd["formula"],
                    "variables": variables,
                    "unit": vd["unit"],
                }
                if tenant_id:
                    tool_input["tenant_id"] = tenant_id

                raw_eval = await self.tool_registry.execute("evaluate_formula", tool_input)

                eval_err = _unwrap_tool_error(raw_eval)
                if eval_err:
                    results.append(
                        _build_roi_result(
                            vd,
                            None,
                            {},
                            CONFIDENCE_LOW,
                            [eval_err],
                        )
                    )
                    continue

                eval_data = _unwrap_tool_data(raw_eval)
                if eval_data.get("success"):
                    results.append(
                        _build_roi_result(
                            vd,
                            eval_data,
                            variables,
                            CONFIDENCE_HIGH,
                            [],
                        )
                    )
                else:
                    results.append(
                        _build_roi_result(
                            vd,
                            eval_data,
                            {},
                            CONFIDENCE_LOW,
                            [eval_data.get("error", "Unknown evaluation error")],
                        )
                    )

            except Exception as exc:
                logger.exception("Formula evaluation failed for %s", vd.get("id"))
                results.append(
                    _build_roi_result(
                        vd,
                        None,
                        {},
                        CONFIDENCE_NONE,
                        [str(exc)],
                    )
                )

        return _EvaluationResult(
            calculated_count=len(results),
            results=[r.model_dump() for r in results],
        ).model_dump()

    # -----------------------------------------------------------------------
    # Step 5 – Aggregation
    # -----------------------------------------------------------------------
    async def _execute_aggregate_roi(self, state: ROIAgentState) -> dict[str, Any]:
        """Aggregate individual ROI calculations."""
        eval_prior = state.output_data.get("evaluate", {})
        if eval_prior.get("error"):
            return _AggregationResult(
                error=f"Cannot aggregate: evaluation failed – {eval_prior['error']}"
            ).model_dump()

        calc_results = eval_prior.get("results") or []
        if not calc_results:
            return _AggregationResult(error="No calculation results to aggregate").model_dump()

        benchmark_prior = state.output_data.get("fetch_benchmarks", {})
        benchmarks = benchmark_prior.get("benchmarks") or {}

        total_annual_value = sum(r.get("result", 0) for r in calc_results)

        vars_prior = state.output_data.get("substitute_vars", {})
        variables = vars_prior.get("variables") or {}
        investment = variables.get("implementation_cost", DEFAULT_IMPLEMENTATION_COST)

        # Guard against invalid investment
        if not isinstance(investment, (int, float)) or investment <= 0:
            investment = DEFAULT_IMPLEMENTATION_COST

        simple_roi = (
            ((total_annual_value - investment) / investment * 100)
            if investment > 0
            else 0.0
        )

        payback_months = None
        if total_annual_value > 0:
            payback_months = investment / (total_annual_value / 12)

        npv = -investment
        for year in range(1, NPV_YEARS + 1):
            npv += total_annual_value / ((1 + DEFAULT_DISCOUNT_RATE) ** year)

        avg_confidence = (
            sum(r.get("confidence", 0) for r in calc_results) / len(calc_results)
            if calc_results
            else 0.0
        )

        aggregated = {
            "total_annual_value": round(total_annual_value, 2),
            "investment_required": investment,
            "simple_roi_percent": round(simple_roi, 2),
            "three_year_npv": round(npv, 2),
            "payback_period_months": round(payback_months, 1) if payback_months else None,
            "value_driver_count": len(calc_results),
            "average_confidence": round(avg_confidence, 2),
            "benchmarks_available": bool(benchmarks),
            "benchmarks": benchmarks,
        }

        return _AggregationResult(
            aggregated=aggregated,
            detailed_results=calc_results,
        ).model_dump()
