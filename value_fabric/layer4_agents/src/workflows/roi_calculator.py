"""ROI Calculator workflow implementation."""

from typing import Any

from ..models.agent_state import ROIAgentState, ROIInputData, ROIResult, WorkflowStatus
from ..models.workflow_config import ROI_WORKFLOW_CONFIG
from ..tools.registry import ToolRegistry
from .base import BaseWorkflow
from shared.models.typed_dict import TypedDictModel


class ROICalculatorWorkflow__execute_get_prospect_dataResult(TypedDictModel):
    enriched: Any | None = None
    error: str
    prospect_id: Any | None = None
    raw_data: Any | None = None

class ROICalculatorWorkflow__execute_fetch_benchmarksResult(TypedDictModel):
    benchmarks: Any | None = None
    error: str
    industry: Any | None = None

class ROICalculatorWorkflow__execute_substitute_variablesResult(TypedDictModel):
    confidence: float
    variable_count: Any
    variables: Any

class ROICalculatorWorkflow__execute_evaluate_formulaResult(TypedDictModel):
    calculated_count: Any | None = None
    error: str
    results: Any | None = None

class ROICalculatorWorkflow__execute_aggregate_roiResult(TypedDictModel):
    aggregated: Any | None = None
    detailed_results: Any | None = None
    error: str


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
            metadata={"workflow_name": self.name},
        )

    async def _execute_tool(
        self, tool_name: str, state: ROIAgentState, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool with ROI-specific input building."""

        if tool_name == "get_prospect_data":
            return await self._execute_get_prospect_data(state)

        elif tool_name == "fetch_benchmarks":
            return await self._execute_fetch_benchmarks(state)

        elif tool_name == "substitute_variables":
            return await self._execute_substitute_variables(state)

        elif tool_name == "evaluate_formula":
            return await self._execute_evaluate_formula(state)

        elif tool_name == "aggregate_roi":
            return await self._execute_aggregate_roi(state)

        return await super()._execute_tool(tool_name, state, config)

    async def _execute_get_prospect_data(self, state: ROIAgentState) -> dict[str, Any]:
        """Load and enrich prospect data."""
        if not state.roi_input:
            return ROICalculatorWorkflow__execute_get_prospect_dataResult.model_validate({"error": "No ROI input configured"})

        # Get prospect data from CRM
        result = await self.tool_registry.execute(
            "get_prospect_data",
            {
                "prospect_id": state.roi_input.prospect_id,
                "data_types": ["profile", "interactions", "opportunities"],
            },
        )

        # Extract relevant fields for ROI calculation
        profile = result.get("profile", {})
        custom_fields = result.get("custom_fields", {})

        enriched_data = {
            "company_size": profile.get("employees", 0),
            "industry": profile.get("industry", state.roi_input.industry_vertical or ""),
            "annual_revenue": profile.get("annual_revenue", 0),
            "pain_points": custom_fields.get("pain_points", []),
        }

        return ROICalculatorWorkflow__execute_get_prospect_dataResult.model_validate({
            "raw_data": result,
            "enriched": enriched_data,
            "prospect_id": state.roi_input.prospect_id,
        })


    async def _execute_fetch_benchmarks(self, state: ROIAgentState) -> dict[str, Any]:
        """Fetch industry benchmarks for comparison."""
        if not state.roi_input:
            return ROICalculatorWorkflow__execute_fetch_benchmarksResult.model_validate({"error": "No ROI input configured"})

        industry = state.roi_input.industry_vertical
        company_size = state.roi_input.company_size

        # Query benchmarks for relevant metrics
        benchmarks = {}

        for metric in ["roi_percent", "cost_reduction", "time_to_value_months"]:
            try:
                result = await self.tool_registry.execute(
                    "compare_benchmarks",
                    {
                        "metric_name": metric,
                        "value": 0,  # Will be updated after calculation
                        "industry": industry or "technology",
                        "company_size": company_size or "medium",
                    },
                )
                benchmarks[metric] = result
            except Exception:
                benchmarks[metric] = None

        return ROICalculatorWorkflow__execute_fetch_benchmarksResult.model_validate({"benchmarks": benchmarks, "industry": industry})

    async def _execute_substitute_variables(self, state: ROIAgentState) -> dict[str, Any]:
        """Substitute variables in value driver formulas from Neo4j."""
        # Fetch value drivers from knowledge graph
        prospect_data = state.prospect_data_enriched.get("enriched", {})

        # Query for industry benchmark variables from graph
        query_result = await self.tool_registry.execute(
            "query_graph",
            {
                "cypher_query": """
                    MATCH (v:ValueDriver)-[:HAS_BENCHMARK]->(b:Benchmark)
                    WHERE b.industry = $industry
                    RETURN b.variables as variables, b.defaults as defaults
                    LIMIT 1
                """,
                "parameters": {"industry": prospect_data.get("industry", "technology")},
            },
        )

        # Build variable mapping from prospect data and benchmarks
        defaults = (
            query_result.get("results", [{}])[0].get("defaults", {})
            if query_result.get("results")
            else {}
        )

        variables = {
            "annual_revenue": prospect_data.get(
                "annual_revenue", defaults.get("annual_revenue", 10000000)
            ),
            "employee_count": prospect_data.get(
                "company_size", defaults.get("employee_count", 500)
            ),
            "hours_saved_weekly": defaults.get("hours_saved_weekly", 40),
            "hourly_rate": defaults.get("hourly_rate", 75),
            "implementation_cost": defaults.get("implementation_cost", 250000),
            "annual_license_cost": defaults.get("annual_license_cost", 50000),
        }

        # Add custom variables from prospect data
        custom = prospect_data.get("custom_variables", {})
        variables.update(custom)

        return ROICalculatorWorkflow__execute_substitute_variablesResult.model_validate({
            "variables": variables,
            "variable_count": len(variables),
            "confidence": 0.85 if prospect_data else 0.6,
        })


    async def _execute_evaluate_formula(self, state: ROIAgentState) -> dict[str, Any]:
        """Evaluate formulas for each value driver from Neo4j."""
        if not state.roi_input:
            return ROICalculatorWorkflow__execute_evaluate_formulaResult.model_validate({"error": "No ROI input configured"})

        variables = state.output_data.get("substitute_vars", {}).get("variables", {})

        # Query value driver formulas from knowledge graph
        query_result = await self.tool_registry.execute(
            "query_graph",
            {
                "cypher_query": """
                    MATCH (v:ValueDriver)
                    WHERE v.id IN $driver_ids
                    RETURN v.id as id, v.name as name, v.category as category,
                           v.formula as formula, v.unit as unit
                """,
                "parameters": {"driver_ids": state.roi_input.value_driver_ids},
            },
        )

        # Transform query results
        value_drivers = []
        for record in query_result.get("results", []):
            value_drivers.append(
                {
                    "id": record.get("v.id"),
                    "name": record.get("v.name"),
                    "category": record.get("v.category"),
                    "formula": record.get("v.formula"),
                    "unit": record.get("v.unit", "USD"),
                }
            )

        results = []

        for vd in value_drivers:
            try:
                # Evaluate formula
                eval_result = await self.tool_registry.execute(
                    "evaluate_formula",
                    {"formula": vd["formula"], "variables": variables, "unit": vd["unit"]},
                )

                if eval_result.get("success"):
                    roi_result = ROIResult(
                        value_driver_id=vd["id"],
                        value_driver_name=vd["name"],
                        formula=vd["formula"],
                        substituted_formula=eval_result.get("substituted_formula", ""),
                        result=eval_result.get("result", 0),
                        unit=vd["unit"],
                        confidence=0.85,
                        variables_used=variables,
                        missing_variables=[],
                    )
                    results.append(roi_result)
                else:
                    # Handle evaluation error
                    results.append(
                        ROIResult(
                            value_driver_id=vd["id"],
                            value_driver_name=vd["name"],
                            formula=vd["formula"],
                            substituted_formula=vd["formula"],
                            result=0,
                            unit=vd["unit"],
                            confidence=0.3,
                            variables_used={},
                            missing_variables=[eval_result.get("error", "Unknown error")],
                        )
                    )

            except Exception as e:
                results.append(
                    ROIResult(
                        value_driver_id=vd["id"],
                        value_driver_name=vd["name"],
                        formula=vd["formula"],
                        substituted_formula=vd["formula"],
                        result=0,
                        unit=vd["unit"],
                        confidence=0.0,
                        variables_used={},
                        missing_variables=[str(e)],
                    )
                )

        return ROICalculatorWorkflow__execute_evaluate_formulaResult.model_validate({"calculated_count": len(results), "results": [r.model_dump() for r in results]})

    async def _execute_aggregate_roi(self, state: ROIAgentState) -> dict[str, Any]:
        """Aggregate individual ROI calculations."""
        calc_results = state.output_data.get("evaluate", {}).get("results", [])

        if not calc_results:
            return ROICalculatorWorkflow__execute_aggregate_roiResult.model_validate({"error": "No calculation results to aggregate"})

        # Sum up all value drivers
        total_annual_value = sum(r.get("result", 0) for r in calc_results)

        # Get investment cost from variables
        investment = 250000  # Default implementation cost
        variables = state.output_data.get("substitute_vars", {}).get("variables", {})
        if "implementation_cost" in variables:
            investment = variables["implementation_cost"]

        # Calculate ROI metrics
        simple_roi = ((total_annual_value - investment) / investment * 100) if investment > 0 else 0
        payback_months = (
            (investment / (total_annual_value / 12)) if total_annual_value > 0 else None
        )

        # Calculate 3-year NPV (assuming constant annual value)
        discount_rate = 0.1
        npv = -investment
        for year in range(1, 4):
            npv += total_annual_value / ((1 + discount_rate) ** year)

        aggregated = {
            "total_annual_value": round(total_annual_value, 2),
            "investment_required": investment,
            "simple_roi_percent": round(simple_roi, 2),
            "three_year_npv": round(npv, 2),
            "payback_period_months": round(payback_months, 1) if payback_months else None,
            "value_driver_count": len(calc_results),
            "average_confidence": sum(r.get("confidence", 0) for r in calc_results)
            / len(calc_results),
        }

        return ROICalculatorWorkflow__execute_aggregate_roiResult.model_validate({"aggregated": aggregated, "detailed_results": calc_results})
