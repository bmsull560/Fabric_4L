"""Analysis API routes for quick ROI and whitespace calculations."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from shared.audit import AuditAction, AuditEmitter, emit_audit_event
from shared.identity.context import RequestContext
from shared.identity.dependencies import get_optional_context

from ...config.settings import settings
from ...database import get_db
from ...engine.executor import WorkflowExecutor
from ...models.agent_state import BusinessCaseInputData, ROIInputData, WhitespaceInputData
from ...services.account_service import AccountService
from ...services.business_case_service import BusinessCaseService
from ...services.export_provenance import build_export_provenance_manifest
from ...services.export_storage import generate_download_url, upload_bytes

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

    account_id: UUID = Field(..., description="Account UUID identifier")
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
    custom_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional custom inputs, including truth_requirements and organization_id",
    )


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
    truth_references: list[dict[str, Any]] = Field(default_factory=list)
    remediation_items: list[dict[str, Any]] = Field(default_factory=list)
    case_metadata: dict[str, Any] = Field(default_factory=dict)


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

<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
        result = await executor.execute_workflow(
            workflow_type="roi_calculator", input_data=input_data.model_dump()
=======
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
        result = await executor.run(
            workflow_type="roi_calculator",
            input_data=input_data.model_dump(),
            tenant_id=str(context.tenant_id),
            user_id=context.user_id,
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
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

<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
        result = await executor.execute_workflow(
            workflow_type="whitespace_analysis", input_data=input_data.model_dump()
=======
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
        result = await executor.run(
            workflow_type="whitespace_analysis",
            input_data=input_data.model_dump(),
            tenant_id=str(context.tenant_id),
            user_id=context.user_id,
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
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
    db: AsyncSession = Depends(get_db),
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
    context: RequestContext = Depends(require_authenticated),
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
    context: RequestContext = Depends(require_authenticated),
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
    context: RequestContext = Depends(require_authenticated),
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
    context: RequestContext = Depends(require_authenticated),
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
    context: RequestContext = Depends(require_authenticated),
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
    context: RequestContext = Depends(require_authenticated),
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
) -> BusinessCaseResponse:
    """Generate a business case document.

    Creates a comprehensive business case with ROI analysis and narrative sections.

    Example:
        POST /v1/cases
        {
            "account_id": "550e8400-e29b-41d4-a716-446655440000",
            "sections": ["executive_summary", "roi_analysis"],
            "output_format": "pdf"
        }
    """
    try:
        account_service = AccountService(db)
        account = await account_service.get_account(request.account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not found: {request.account_id}",
            )

        custom_inputs = dict(request.custom_inputs)
        custom_inputs["provider_record_id"] = account.provider_record_id

        input_data = BusinessCaseInputData(
            account_id=request.account_id,
            opportunity_id=request.opportunity_id,
            sections_requested=request.sections,
            output_format=request.output_format,
            custom_inputs=custom_inputs,
        )

<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
<<<<<<< C:/Users/BBB/Fabric_4L/value-fabric/layer4-agents/src/api/routes/analysis.py
        result = await executor.execute_workflow(
            workflow_type="business_case", input_data=input_data.model_dump()
=======
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
=======
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
        result = await executor.run(
            workflow_type="business_case",
            input_data=input_data.model_dump(),
            tenant_id=str(context.tenant_id),
            user_id=context.user_id,
        )

        workflow_id = getattr(result, "workflow_id", None) or request.custom_inputs.get("workflow_id")
        account_id = request.custom_inputs.get("account_id")
        event = emit_audit_event(
            AuditAction.BUSINESS_CASE_GENERATED,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            api_key_id=context.api_key_id,
            resource_type="BusinessCase",
            resource_id=workflow_id,
            details={
                "case_id": workflow_id,
                "workflow_id": workflow_id,
                "account_id": account_id,
            },
>>>>>>> C:/Users/BBB/.windsurf/worktrees/Fabric_4L/Fabric_4L-de8927c6/value-fabric/layer4-agents/src/api/routes/analysis.py
        )

        assemble_data = result.output_data.get("assemble_document", {})
        truth_gate = result.output_data.get("verify_truth_requirements", {})
        case_metadata = dict(assemble_data.get("case_metadata", {}))
        case_metadata["account_id"] = str(request.account_id)

        business_case_service = BusinessCaseService(db)
        await business_case_service.upsert_case_record(
            case_id=result.workflow_id,
            workflow_id=result.workflow_id,
            account_id=request.account_id,
            opportunity_id=request.opportunity_id,
            status=result.status.value,
            document_url=assemble_data.get("document_url"),
        )

        return BusinessCaseResponse(
            case_id=result.workflow_id,
            status=result.status.value,
            document_url=assemble_data.get("document_url"),
            page_count=assemble_data.get("page_count", 0),
            file_size_bytes=assemble_data.get("file_size_bytes", 0),
            truth_references=assemble_data.get("truth_references", truth_gate.get("truth_references", [])),
            remediation_items=assemble_data.get("remediation_items", truth_gate.get("remediation_items", [])),
            case_metadata=case_metadata,
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
    truth_gate = output.get("verify_truth_requirements", {})
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
        truth_references=assemble_data.get("truth_references", truth_gate.get("truth_references", [])),
        remediation_items=assemble_data.get("remediation_items", truth_gate.get("remediation_items", [])),
        case_metadata=assemble_data.get("case_metadata", {}),
    )

@router.get("/cases/{case_id}/export")
async def export_business_case(
    case_id: str,
    format: str = "pdf",
    executor: WorkflowExecutor = Depends(get_executor),
    context: RequestContext | None = Depends(get_optional_context),
) -> dict[str, Any]:
    """Export a generated business case.

    This version resolves the merge conflict by preserving both:
    1. Truth-gating / blocking behavior
    2. Provenance manifest generation, storage upload, and audit events
    """
    if not settings.export_storage_endpoint:
        raise HTTPException(status_code=503, detail="Export storage endpoint is not configured")

    result = await executor.get_result(case_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Business case {case_id} not found")

    output = result.get("output", {})
    assemble_data = output.get("assemble_document", {})
    truth_gate = output.get("verify_truth_requirements", {})

    blocked = bool(assemble_data.get("blocked")) or not truth_gate.get("passed", True)
    truth_references = assemble_data.get(
        "truth_references", truth_gate.get("truth_references", [])
    )
    remediation_items = assemble_data.get(
        "remediation_items", truth_gate.get("remediation_items", [])
    )

    document_bytes = assemble_data.get("document_bytes")
    export_id = str(uuid4())

    if blocked:
        return {
            "case_id": case_id,
            "export_id": export_id,
            "format": format,
            "document_url": assemble_data.get("document_url"),
            "download_ready": False,
            "blocked": True,
            "remediation_items": remediation_items,
            "truth_references": truth_references,
            "manifest": {
                "case_id": case_id,
                "format": format,
                "blocked": True,
                "truth_references": truth_references,
                "remediation_items": remediation_items,
                "truth_gate": {
                    "passed": truth_gate.get("passed", False),
                    "requirements": truth_gate.get("requirements", []),
                },
            },
        }

    if not document_bytes:
        raise HTTPException(status_code=409, detail="Business case document bytes unavailable")

    if not isinstance(document_bytes, bytes):
        document_bytes = bytes(document_bytes)

    workflow_id = (
        result.get("workflow_id")
        or result.get("metadata", {}).get("workflow_id")
        or case_id
    )
    filename = f"business_case_{case_id}.{format}"
    manifest_filename = f"business_case_{case_id}.provenance.json"

    manifest = build_export_provenance_manifest(
        case_id=case_id,
        workflow_result=result,
        actor_context=context,
        export_id=export_id,
    )
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")

    base_prefix = f"exports/{case_id}/{export_id}"
    object_key = f"{base_prefix}/{filename}"
    manifest_key = f"{base_prefix}/{manifest_filename}"
    metadata = {
        "case-id": case_id,
        "workflow-id": workflow_id,
        "export-id": export_id,
        "tenant-id": str(context.tenant_id) if context else "unknown",
    }

    content_type = "application/pdf" if format == "pdf" else "application/octet-stream"

    await upload_bytes(
        object_key=object_key,
        content=document_bytes,
        content_type=content_type,
        metadata=metadata,
    )
    await upload_bytes(
        object_key=manifest_key,
        content=manifest_bytes,
        content_type="application/json",
        metadata=metadata,
    )

    document_url = await generate_download_url(object_key=object_key)
    manifest_url = await generate_download_url(object_key=manifest_key)
    expires_at = datetime.fromtimestamp(
        datetime.now(UTC).timestamp() + settings.export_signed_url_ttl_seconds,
        tz=UTC,
    ).isoformat()

    request_event = emit_audit_event(
        AuditAction.EXPORT_REQUESTED,
        tenant_id=context.tenant_id if context else None,
        user_id=context.user_id if context else None,
        api_key_id=context.api_key_id if context else None,
        resource_type="BusinessCaseExport",
        resource_id=case_id,
        details={
            "case_id": case_id,
            "workflow_id": workflow_id,
            "export_id": export_id,
            "format": format,
        },
    )
    await AuditEmitter.write_to_db(request_event, get_db)

    package_event = emit_audit_event(
        AuditAction.EXPORT_PACKAGE_GENERATED,
        tenant_id=context.tenant_id if context else None,
        user_id=context.user_id if context else None,
        api_key_id=context.api_key_id if context else None,
        resource_type="BusinessCaseExport",
        resource_id=case_id,
        details={
            "case_id": case_id,
            "workflow_id": workflow_id,
            "export_id": export_id,
            "pdf_object_key": object_key,
            "manifest_object_key": manifest_key,
            "truth_object_ids": manifest.get("truth_object_ids", []),
            "source_references": manifest.get("source_references", []),
        },
    )
    await AuditEmitter.write_to_db(package_event, get_db)

    access_event = emit_audit_event(
        AuditAction.EXPORT_DOWNLOAD_ACCESSED,
        tenant_id=context.tenant_id if context else None,
        user_id=context.user_id if context else None,
        api_key_id=context.api_key_id if context else None,
        resource_type="BusinessCaseExport",
        resource_id=case_id,
        details={
            "case_id": case_id,
            "workflow_id": workflow_id,
            "export_id": export_id,
            "pdf_object_key": object_key,
        },
    )
    await AuditEmitter.write_to_db(access_event, get_db)

    return {
        "case_id": case_id,
        "export_id": export_id,
        "format": format,
        "document_url": document_url,
        "manifest_url": manifest_url,
        "download_ready": True,
        "blocked": False,
        "remediation_items": remediation_items,
        "truth_references": truth_references,
        "url_expires_at": expires_at,
    }
