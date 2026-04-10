"""Formula API routes.

Provides endpoints for formula evaluation and variable registry.
Delegates calculation logic to the ROI calculation agent.
"""

from typing import Any, Dict, List, Optional, Literal
from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator

from ..dependencies import get_roi_calculation_agent

router = APIRouter()


class FormulaInput(BaseModel):
    """Single formula input variable."""
    name: str = Field(..., description="Variable name")
    value: float = Field(..., description="Variable value")
    unit: Optional[str] = Field(None, description="Unit of measurement")


class FormulaEvaluateRequest(BaseModel):
    """Request to evaluate a formula."""
    formula_id: Optional[str] = Field(None, description="Optional formula identifier from registry")
    expression: Optional[str] = Field(None, description="Custom formula expression (if formula_id not provided)")
    inputs: List[FormulaInput] = Field(default_factory=list, description="Input variables")
    output_unit: Optional[str] = Field(None, description="Desired output unit")

    @validator('expression')
    def validate_expression_or_formula_id(cls, v, values):
        if not v and not values.get('formula_id'):
            raise ValueError('Either formula_id or expression must be provided')
        return v


class CalculationStep(BaseModel):
    """Single step in formula calculation."""
    step: int = Field(..., description="Step number")
    operation: str = Field(..., description="Operation performed")
    result: str = Field(..., description="Intermediate result")


class FormulaEvaluateResponse(BaseModel):
    """Response from formula evaluation."""
    result: float = Field(..., description="Calculated result")
    unit: str = Field(..., description="Output unit")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0, description="Confidence in result")
    calculation_steps: List[CalculationStep] = Field(default_factory=list, description="Step-by-step calculation")
    formula_used: str = Field(..., description="Formula expression used")


class VariableMetadata(BaseModel):
    """Metadata for a formula variable."""
    name: str = Field(..., description="Variable name")
    display_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Variable description")
    type: Literal["number", "currency", "percentage", "count"] = Field(..., description="Data type")
    unit: Optional[str] = Field(None, description="Default unit")
    default_value: Optional[float] = Field(None, description="Default value if not provided")
    min_value: Optional[float] = Field(None, description="Minimum allowed value")
    max_value: Optional[float] = Field(None, description="Maximum allowed value")
    required: bool = Field(default=True, description="Whether variable is required")


class FormulaMetadata(BaseModel):
    """Metadata for a registered formula."""
    id: str = Field(..., description="Formula identifier")
    name: str = Field(..., description="Formula name")
    description: str = Field(..., description="Formula description")
    category: str = Field(..., description="Formula category (e.g., ROI, Payback, NPV)")
    expression: str = Field(..., description="Formula expression template")
    variables: List[VariableMetadata] = Field(..., description="Required variables")
    output_unit: str = Field(..., description="Output unit")


class VariablesRegistryResponse(BaseModel):
    """Response containing available variables."""
    variables: List[VariableMetadata] = Field(..., description="Available variables")
    total: int = Field(..., description="Total number of variables")
    categories: List[str] = Field(default_factory=list, description="Variable categories")


class FormulasRegistryResponse(BaseModel):
    """Response containing registered formulas."""
    formulas: List[FormulaMetadata] = Field(..., description="Registered formulas")
    total: int = Field(..., description="Total number of formulas")


# ============================================================================
# Variable Registry
# ============================================================================

VARIABLE_REGISTRY: List[VariableMetadata] = [
    VariableMetadata(
        name="annual_cost_savings",
        display_name="Annual Cost Savings",
        description="Estimated annual cost savings from the initiative",
        type="currency",
        unit="USD",
        required=True,
        min_value=0,
    ),
    VariableMetadata(
        name="implementation_cost",
        display_name="Implementation Cost",
        description="Total cost to implement the solution",
        type="currency",
        unit="USD",
        required=True,
        min_value=0,
    ),
    VariableMetadata(
        name="annual_revenue_increase",
        display_name="Annual Revenue Increase",
        description="Estimated annual revenue increase",
        type="currency",
        unit="USD",
        default_value=0,
        min_value=0,
    ),
    VariableMetadata(
        name="time_period_years",
        display_name="Time Period",
        description="Analysis time period in years",
        type="count",
        unit="years",
        default_value=3,
        min_value=1,
        max_value=10,
    ),
    VariableMetadata(
        name="discount_rate",
        display_name="Discount Rate",
        description="Annual discount rate for NPV calculations",
        type="percentage",
        unit="percent",
        default_value=0.10,
        min_value=0,
        max_value=1,
    ),
    VariableMetadata(
        name="current_manual_hours",
        display_name="Current Manual Hours",
        description="Hours spent on manual process per month",
        type="count",
        unit="hours",
        required=True,
        min_value=0,
    ),
    VariableMetadata(
        name="hourly_rate",
        display_name="Hourly Rate",
        description="Fully loaded hourly cost",
        type="currency",
        unit="USD",
        default_value=75.0,
        min_value=0,
    ),
    VariableMetadata(
        name="automation_efficiency",
        display_name="Automation Efficiency",
        description="Percentage of time saved through automation",
        type="percentage",
        unit="percent",
        default_value=0.70,
        min_value=0,
        max_value=1,
    ),
    VariableMetadata(
        name="monthly_transaction_volume",
        display_name="Monthly Transaction Volume",
        description="Number of transactions processed per month",
        type="count",
        unit="transactions",
        required=True,
        min_value=0,
    ),
    VariableMetadata(
        name="error_rate_before",
        display_name="Error Rate Before",
        description="Error rate in current process (0-1)",
        type="percentage",
        unit="percent",
        default_value=0.05,
        min_value=0,
        max_value=1,
    ),
    VariableMetadata(
        name="error_rate_after",
        display_name="Error Rate After",
        description="Error rate after automation (0-1)",
        type="percentage",
        unit="percent",
        default_value=0.01,
        min_value=0,
        max_value=1,
    ),
    VariableMetadata(
        name="cost_per_error",
        display_name="Cost Per Error",
        description="Average cost to fix an error",
        type="currency",
        unit="USD",
        default_value=500.0,
        min_value=0,
    ),
]

# ============================================================================
# Formula Registry
# ============================================================================

FORMULA_REGISTRY: List[FormulaMetadata] = [
    FormulaMetadata(
        id="roi_basic",
        name="Basic ROI",
        description="Simple Return on Investment calculation",
        category="ROI",
        expression="(annual_benefit - annual_cost) / implementation_cost * 100",
        variables=[
            VariableMetadata(
                name="annual_benefit",
                display_name="Annual Benefit",
                description="Annual benefit value",
                type="currency",
                unit="USD",
                required=True,
            ),
            VariableMetadata(
                name="annual_cost",
                display_name="Annual Cost",
                description="Annual cost value",
                type="currency",
                unit="USD",
                default_value=0,
            ),
            VariableMetadata(
                name="implementation_cost",
                display_name="Implementation Cost",
                type="currency",
                unit="USD",
                required=True,
            ),
        ],
        output_unit="percent",
    ),
    FormulaMetadata(
        id="payback_period",
        name="Payback Period",
        description="Time to recover initial investment",
        category="Payback",
        expression="implementation_cost / (annual_savings / 12)",
        variables=[
            VariableMetadata(
                name="implementation_cost",
                display_name="Implementation Cost",
                description="Total cost to implement the solution",
                type="currency",
                unit="USD",
                required=True,
            ),
            VariableMetadata(
                name="annual_savings",
                display_name="Annual Savings",
                description="Annual cost savings from the initiative",
                type="currency",
                unit="USD",
                required=True,
            ),
        ],
        output_unit="months",
    ),
    FormulaMetadata(
        id="automation_savings",
        name="Labor Cost Savings",
        description="Cost savings from process automation",
        category="Cost Reduction",
        expression="current_manual_hours * hourly_rate * 12 * automation_efficiency",
        variables=[
            VariableMetadata(
                name="current_manual_hours",
                display_name="Current Manual Hours",
                description="Hours spent on manual process per month",
                type="count",
                unit="hours/month",
                required=True,
            ),
            VariableMetadata(
                name="hourly_rate",
                display_name="Hourly Rate",
                description="Fully loaded hourly cost",
                type="currency",
                unit="USD",
                default_value=75.0,
            ),
            VariableMetadata(
                name="automation_efficiency",
                display_name="Automation Efficiency",
                description="Percentage of time saved through automation",
                type="percentage",
                unit="percent",
                default_value=0.70,
            ),
        ],
        output_unit="USD/year",
    ),
    FormulaMetadata(
        id="error_reduction_savings",
        name="Error Reduction Savings",
        description="Savings from reduced error rates",
        category="Cost Reduction",
        expression="monthly_transaction_volume * 12 * (error_rate_before - error_rate_after) * cost_per_error",
        variables=[
            VariableMetadata(
                name="monthly_transaction_volume",
                display_name="Monthly Transaction Volume",
                description="Number of transactions processed per month",
                type="count",
                unit="transactions",
                required=True,
            ),
            VariableMetadata(
                name="error_rate_before",
                display_name="Error Rate Before",
                description="Error rate in current process (0-1)",
                type="percentage",
                unit="percent",
                default_value=0.05,
            ),
            VariableMetadata(
                name="error_rate_after",
                display_name="Error Rate After",
                description="Error rate after automation (0-1)",
                type="percentage",
                unit="percent",
                default_value=0.01,
            ),
            VariableMetadata(
                name="cost_per_error",
                display_name="Cost Per Error",
                description="Average cost to fix an error",
                type="currency",
                unit="USD",
                default_value=500.0,
            ),
        ],
        output_unit="USD/year",
    ),
]


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/formulas/evaluate",
    response_model=FormulaEvaluateResponse,
    tags=["Formulas"],
    summary="Evaluate Formula",
    description="Execute a formula with typed inputs and return the result.",
    responses={
        200: {
            "description": "Formula evaluated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "result": 245.5,
                        "unit": "percent",
                        "confidence": 0.92,
                        "calculation_steps": [
                            {"step": 1, "operation": "annual_benefit - annual_cost", "result": "245500.0"},
                            {"step": 2, "operation": "divide by implementation_cost", "result": "245.5"},
                        ],
                        "formula_used": "(annual_benefit - annual_cost) / implementation_cost * 100"
                    }
                }
            }
        },
        400: {"description": "Invalid inputs or formula"},
        422: {"description": "Validation error"},
    }
)
async def evaluate_formula(
    request: FormulaEvaluateRequest,
) -> FormulaEvaluateResponse:
    """Evaluate a formula with the provided inputs.

    Either `formula_id` (to use a registered formula) or `expression`
    (for custom formulas) must be provided.
    """
    try:
        # Get formula and variables
        if request.formula_id:
            formula = next((f for f in FORMULA_REGISTRY if f.id == request.formula_id), None)
            if not formula:
                raise HTTPException(status_code=404, detail=f"Formula {request.formula_id} not found")
            expression = formula.expression
            output_unit = request.output_unit or formula.output_unit
        else:
            expression = request.expression or ""
            output_unit = request.output_unit or "value"

        # Build variable lookup
        inputs_dict = {inp.name: inp.value for inp in request.inputs}

        # Calculate result using safe evaluation
        try:
            result = evaluate_expression(expression, inputs_dict)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Formula evaluation error: {str(e)}")

        # Generate calculation steps for transparency
        steps = generate_calculation_steps(expression, inputs_dict, result)

        return FormulaEvaluateResponse(
            result=result,
            unit=output_unit,
            confidence=0.92,  # Default confidence
            calculation_steps=steps,
            formula_used=expression,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate formula: {str(e)}")


@router.get(
    "/formulas/variables",
    response_model=VariablesRegistryResponse,
    tags=["Formulas"],
    summary="Get Variables Registry",
    description="Returns metadata for all available formula variables.",
)
async def get_variables_registry(
    category: Optional[str] = None,
) -> VariablesRegistryResponse:
    """Get the registry of available variables for formula building."""
    variables = VARIABLE_REGISTRY

    if category:
        # Filter by implied category from name patterns
        pass  # All variables returned for now

    categories = list(set([
        "Financial", "Operational", "Efficiency", "Quality"
    ]))

    return VariablesRegistryResponse(
        variables=variables,
        total=len(variables),
        categories=categories,
    )


@router.get(
    "/formulas",
    response_model=FormulasRegistryResponse,
    tags=["Formulas"],
    summary="List Registered Formulas",
    description="Returns all registered formulas with their metadata.",
)
async def list_formulas(
    category: Optional[str] = None,
) -> FormulasRegistryResponse:
    """List all registered formulas."""
    formulas = FORMULA_REGISTRY

    if category:
        formulas = [f for f in formulas if f.category.lower() == category.lower()]

    return FormulasRegistryResponse(
        formulas=formulas,
        total=len(formulas),
    )


@router.get(
    "/formulas/{formula_id}",
    response_model=FormulaMetadata,
    tags=["Formulas"],
    summary="Get Formula Details",
    description="Returns details for a specific registered formula.",
)
async def get_formula(formula_id: str) -> FormulaMetadata:
    """Get details for a specific formula."""
    formula = next((f for f in FORMULA_REGISTRY if f.id == formula_id), None)
    if not formula:
        raise HTTPException(status_code=404, detail=f"Formula {formula_id} not found")
    return formula


# ============================================================================
# Helper Functions
# ============================================================================

def evaluate_expression(expression: str, variables: Dict[str, float]) -> float:
    """Safely evaluate a mathematical expression with variables."""
    # Simple expression evaluation with basic operators
    # In production, use a proper math parser like numexpr or asteval

    import re
    import operator

    # Supported operators
    ops = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '**': operator.pow,
    }

    # Replace variable names with values
    expr = expression
    for var_name, var_value in sorted(variables.items(), key=lambda x: -len(x[0])):
        expr = expr.replace(var_name, str(var_value))

    # Tokenize and evaluate
    # This is a simplified evaluator - production should use a proper parser
    try:
        # Handle parentheses with recursive evaluation
        while '(' in expr:
            # Find innermost parentheses
            match = re.search(r'\(([^()]+)\)', expr)
            if not match:
                break
            inner = match.group(1)
            inner_result = evaluate_simple(inner)
            expr = expr[:match.start()] + str(inner_result) + expr[match.end():]

        result = evaluate_simple(expr)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")


def evaluate_simple(expr: str) -> float:
    """Evaluate simple expression without parentheses."""
    import operator

    ops = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '**': operator.pow,
    }

    # Tokenize by operators (respecting operator precedence)
    tokens = []
    current = ""
    i = 0
    while i < len(expr):
        if expr[i:i+2] == '**':
            if current.strip():
                tokens.append(float(current.strip()))
                current = ""
            tokens.append('**')
            i += 2
        elif expr[i] in '+-*/':
            if current.strip():
                tokens.append(float(current.strip()))
                current = ""
            tokens.append(expr[i])
            i += 1
        else:
            current += expr[i]
            i += 1

    if current.strip():
        tokens.append(float(current.strip()))

    # Evaluate with precedence
    # First: **
    i = 0
    while i < len(tokens):
        if tokens[i] == '**':
            result = tokens[i-1] ** tokens[i+1]
            tokens = tokens[:i-1] + [result] + tokens[i+2:]
        else:
            i += 1

    # Then: *, /
    i = 0
    while i < len(tokens):
        if tokens[i] == '*':
            result = tokens[i-1] * tokens[i+1]
            tokens = tokens[:i-1] + [result] + tokens[i+2:]
        elif tokens[i] == '/':
            result = tokens[i-1] / tokens[i+1]
            tokens = tokens[:i-1] + [result] + tokens[i+2:]
        else:
            i += 1

    # Finally: +, -
    i = 0
    while i < len(tokens):
        if tokens[i] == '+':
            result = tokens[i-1] + tokens[i+1]
            tokens = tokens[:i-1] + [result] + tokens[i+2:]
        elif tokens[i] == '-':
            result = tokens[i-1] - tokens[i+1]
            tokens = tokens[:i-1] + [result] + tokens[i+2:]
        else:
            i += 1

    return tokens[0] if tokens else 0.0


def generate_calculation_steps(expression: str, variables: Dict[str, float], final_result: float) -> List[CalculationStep]:
    """Generate human-readable calculation steps."""
    steps = []

    # Show variable substitution
    substituted = expression
    for var, val in variables.items():
        substituted = substituted.replace(var, str(val))

    steps.append(CalculationStep(
        step=1,
        operation="Substitute variables",
        result=substituted,
    ))

    # Show final result
    steps.append(CalculationStep(
        step=2,
        operation="Evaluate expression",
        result=str(final_result),
    ))

    return steps
