"""Analysis API routes for quick ROI and whitespace calculations."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from ...engine.executor import WorkflowExecutor
from ...models.agent_state import BusinessCaseInputData, ROIInputData, WhitespaceInputData

router = APIRouter()


# ROI Analysis Models
class ROIAnalysisRequest(BaseModel):
    """Quick ROI analysis request."""

    prospect_id: str = Field(..., description="Prospect identifier")
    value_driver_ids: list[str] = Field(..., description="Value drivers to calculate")
    prospect_data: dict[str, float] = Field(
        default_factory=dict, description="Prospect-specific variables"
    )
    industry_vertical: str | None = None
    company_size: str | None = None


class ROIAnalysisResponse(BaseModel):
    """ROI analysis response."""

    prospect_id: str
    aggregated_roi: dict[str, Any]
    detailed_results: list[dict[str, Any]]
    benchmark_comparison: dict[str, Any] | None = None


# Whitespace Analysis Models
class WhitespaceAnalysisRequest(BaseModel):
    """Whitespace analysis request."""

    prospect_id: str = Field(..., description="Prospect identifier")
    prospect_needs: str = Field(..., min_length=10, description="Description of prospect needs")
    analysis_depth: str = Field(
        default="standard", description="Analysis depth (quick, standard, deep)"
    )


class WhitespaceAnalysisResponse(BaseModel):
    """Whitespace analysis response."""

    prospect_id: str
    extracted_needs: list[str]
    gap_analysis: list[dict[str, Any]]
    opportunity_score: float
    recommendations: list[str]


# Business Case Models
class BusinessCaseRequest(BaseModel):
    """Business case generation request."""

    prospect_id: str = Field(..., description="Prospect identifier")
    opportunity_id: str | None = None
    sections: list[str] = Field(
        default_factory=lambda: [
            "executive_summary",
            "roi_analysis",
            "implementation",
            "next_steps",
        ]
    )
    output_format: str = Field(default="pdf", description="Output format (pdf, docx, html)")


class BusinessCaseResponse(BaseModel):
    """Business case generation response."""

    case_id: str
    title: str = "Business Case"
    summary: str = ""
    total_value: float = 0.0
    implementation_cost: float = 0.0
    roi_ratio: float = 0.0
    payback_months: int = 0
    confidence_score: float = 0.0
    recommendations: list[str] = Field(default_factory=list)
    status: str = "unknown"
    created_at: str | None = None
    document_url: str | None = None
    page_count: int = 0
    file_size_bytes: int = 0


def get_executor() -> WorkflowExecutor:
    """Get workflow executor instance."""
    from .main import workflow_executor

    if workflow_executor is None:
        raise HTTPException(status_code=503, detail="Workflow executor not initialized")
    return workflow_executor


@router.post("/analysis/roi", response_model=ROIAnalysisResponse)
async def quick_roi_analysis(
    request: ROIAnalysisRequest, executor: WorkflowExecutor = Depends(get_executor)
) -> ROIAnalysisResponse:
    """Quick ROI analysis for a prospect.

    Calculates ROI for specified value drivers using prospect data.

    Example:
        POST /v1/analysis/roi
        {
            "prospect_id": "prospect-001",
            "value_driver_ids": ["vd-001", "vd-002"],
            "industry_vertical": "manufacturing"
        }
    """
    try:
        input_data = ROIInputData(
            prospect_id=request.prospect_id,
            value_driver_ids=request.value_driver_ids,
            prospect_data=request.prospect_data,
            industry_vertical=request.industry_vertical,
            company_size=request.company_size,
        )

        result = await executor.run(
            workflow_type="roi_calculator", input_data=input_data.model_dump()
        )

        aggregate = result.output_data.get("aggregate", {})

        return ROIAnalysisResponse(
            prospect_id=request.prospect_id,
            aggregated_roi=aggregate.get("aggregated", {}),
            detailed_results=aggregate.get("detailed_results", []),
            benchmark_comparison=result.output_data.get("fetch_benchmarks", {}).get("benchmarks"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ROI analysis failed: {str(e)}")


@router.post("/analysis/whitespace", response_model=WhitespaceAnalysisResponse)
async def quick_whitespace_analysis(
    request: WhitespaceAnalysisRequest, executor: WorkflowExecutor = Depends(get_executor)
) -> WhitespaceAnalysisResponse:
    """Quick whitespace analysis for a prospect.

    Identifies gaps between prospect needs and solution capabilities.

    Example:
        POST /v1/analysis/whitespace
        {
            "prospect_id": "prospect-001",
            "prospect_needs": "We need to automate invoice processing and get real-time visibility into cash flow"
        }
    """
    try:
        input_data = WhitespaceInputData(
            prospect_id=request.prospect_id,
            prospect_needs=request.prospect_needs,
            analysis_depth=request.analysis_depth,
        )

        result = await executor.run(
            workflow_type="whitespace_analysis", input_data=input_data.model_dump()
        )

        score_data = result.output_data.get("score_opportunity", {})

        return WhitespaceAnalysisResponse(
            prospect_id=request.prospect_id,
            extracted_needs=result.output_data.get("analyze_prospect", {}).get(
                "extracted_needs", []
            ),
            gap_analysis=result.output_data.get("identify_gaps", {}).get("gaps", []),
            opportunity_score=score_data.get("opportunity_score", 0),
            recommendations=score_data.get("recommendations", []),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whitespace analysis failed: {str(e)}")


@router.post("/cases", response_model=BusinessCaseResponse)
async def generate_business_case(
    request: BusinessCaseRequest,
    background_tasks: BackgroundTasks,
    executor: WorkflowExecutor = Depends(get_executor),
) -> BusinessCaseResponse:
    """Generate a business case document.

    Creates a comprehensive business case with ROI analysis and narrative sections.

    Example:
        POST /v1/cases
        {
            "prospect_id": "prospect-001",
            "sections": ["executive_summary", "roi_analysis"],
            "output_format": "pdf"
        }
    """
    try:
        input_data = BusinessCaseInputData(
            prospect_id=request.prospect_id,
            opportunity_id=request.opportunity_id,
            sections_requested=request.sections,
            output_format=request.output_format,
        )

        result = await executor.run(
            workflow_type="business_case", input_data=input_data.model_dump()
        )

        assemble_data = result.output_data.get("assemble_document", {})

        return BusinessCaseResponse(
            case_id=result.workflow_id,
            status=result.status.value,
            document_url=assemble_data.get("document_url"),
            page_count=assemble_data.get("page_count", 0),
            file_size_bytes=assemble_data.get("file_size_bytes", 0),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Business case generation failed: {str(e)}")


@router.get("/cases/{case_id}", response_model=BusinessCaseResponse)
async def get_business_case(
    case_id: str, executor: WorkflowExecutor = Depends(get_executor)
) -> BusinessCaseResponse:
    """Get a generated business case by ID."""
    result = await executor.get_result(case_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Business case {case_id} not found")

    output = result.get("output", {})
    assemble_data = output.get("assemble_document", {})
    narrative_data = output.get("synthesize_narrative", {})

    return BusinessCaseResponse(
        case_id=case_id,
        title=assemble_data.get("title", "Business Case"),
        summary=assemble_data.get("executive_summary", narrative_data.get("narrative", "")),
        total_value=assemble_data.get("total_estimated_value", 0.0),
        implementation_cost=assemble_data.get("implementation_cost_estimate", 0.0),
        roi_ratio=assemble_data.get("roi_ratio", 0.0),
        payback_months=assemble_data.get("payback_months", 0),
        confidence_score=assemble_data.get("confidence_score", 0.0),
        recommendations=assemble_data.get("recommendations", []),
        created_at=result.get("created_at"),
        status=result.get("status", "unknown"),
    )


@router.get("/cases/{case_id}/export")
async def export_business_case(
    case_id: str, format: str = "pdf", executor: WorkflowExecutor = Depends(get_executor)
) -> dict[str, Any]:
    """Export a generated business case."""
    result = await executor.get_result(case_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Business case {case_id} not found")

    assemble_data = result.get("output", {}).get("assemble_document", {})

    return {
        "case_id": case_id,
        "format": format,
        "document_url": assemble_data.get("document_url"),
        "download_ready": assemble_data.get("document_bytes") is not None,
    }
