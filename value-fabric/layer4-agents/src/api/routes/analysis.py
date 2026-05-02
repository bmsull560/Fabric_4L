"""Analysis API routes for quick ROI and whitespace calculations."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from shared.audit import AuditAction, AuditEmitter, emit_audit_event
from shared.identity.context import RequestContext
from shared.identity.dependencies import require_authenticated
from shared.models.typed_dict import TypedDictModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.settings import settings
from ...database import get_db_from_context
from ...engine.executor import WorkflowExecutor
from ...models.agent_state import BusinessCaseInputData, ROIInputData, WhitespaceInputData
from ...services.account_service import AccountService
from ...services.business_case_service import BusinessCaseService
from ...services.export_provenance import build_export_provenance_manifest
from ...services.export_storage import generate_download_url, upload_bytes


class export_business_caseResult(TypedDictModel):
    blocked: bool
    case_id: Any
    document_url: Any
    download_ready: bool
    export_id: Any
    format: Any
    manifest: dict[str, Any]
    manifest_url: Any | None = None
    remediation_items: Any
    truth_references: Any
    url_expires_at: Any | None = None

class get_workspace_tabResult(TypedDictModel):
    """Workspace tab data result - allows any fields for dynamic tab data."""
    model_config = ConfigDict(extra="allow")

class update_workspace_tabResult(TypedDictModel):
    case_id: Any
    tab: Any
    updated: bool

class generate_workspace_intelligenceResult(TypedDictModel):
    account_id: Any
    case_id: Any
    generated: bool
    stats: dict[str, Any]

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
    sdes: dict[str, Any] = Field(default_factory=dict)
    case_metadata: dict[str, Any] = Field(default_factory=dict)


def get_executor() -> WorkflowExecutor:
    """Get workflow executor instance."""
    from .main import workflow_executor

    if workflow_executor is None:
        raise HTTPException(status_code=503, detail="Workflow executor not initialized")
    return workflow_executor


@router.post("/analysis/roi", response_model=ROIAnalysisResponse)
async def quick_roi_analysis(
    request: ROIAnalysisRequest,
    executor: WorkflowExecutor = Depends(get_executor),
    context: RequestContext = Depends(require_authenticated),
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
            workflow_type="roi_calculator",
            input_data=input_data.model_dump(),
            tenant_id=str(context.tenant_id),
            user_id=context.user_id,
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
    request: WhitespaceAnalysisRequest,
    executor: WorkflowExecutor = Depends(get_executor),
    context: RequestContext = Depends(require_authenticated),
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
            workflow_type="whitespace_analysis",
            input_data=input_data.model_dump(),
            tenant_id=str(context.tenant_id),
            user_id=context.user_id,
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
    db: AsyncSession = Depends(get_db_from_context),
    context: RequestContext = Depends(require_authenticated),
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

        result = await executor.run(
            workflow_type="business_case",
            input_data=input_data.model_dump(),
            tenant_id=str(context.tenant_id),
            user_id=context.user_id,
        )

        assemble_data = result.output_data.get("assemble_document", {})
        truth_gate = result.output_data.get("verify_truth_requirements", {})
        sdes_bundle = result.output_data.get("generate_sdes", {})

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
            sdes=sdes_bundle,
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
    sdes_bundle = output.get("generate_sdes", {})
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
        sdes=sdes_bundle,
        case_metadata=assemble_data.get("case_metadata", {}),
    )

@router.get("/cases/{case_id}/export")
async def export_business_case(
    case_id: str,
    format: str = "pdf",
    executor: WorkflowExecutor = Depends(get_executor),
    context: RequestContext = Depends(require_authenticated),
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
        return export_business_caseResult.model_validate({
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
        })


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

    base_prefix = f"exports/{context.tenant_id}/{case_id}/{export_id}"
    object_key = f"{base_prefix}/{filename}"
    manifest_key = f"{base_prefix}/{manifest_filename}"
    metadata = {
        "case-id": case_id,
        "workflow-id": workflow_id,
        "export-id": export_id,
        "tenant-id": str(context.tenant_id),
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
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        api_key_id=context.api_key_id,
        resource_type="BusinessCaseExport",
        resource_id=case_id,
        details={
            "case_id": case_id,
            "workflow_id": workflow_id,
            "export_id": export_id,
            "format": format,
        },
    )
    await AuditEmitter.write_to_db(request_event, get_db_from_context)

    package_event = emit_audit_event(
        AuditAction.EXPORT_PACKAGE_GENERATED,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        api_key_id=context.api_key_id,
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
    await AuditEmitter.write_to_db(package_event, get_db_from_context)

    access_event = emit_audit_event(
        AuditAction.EXPORT_DOWNLOAD_ACCESSED,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        api_key_id=context.api_key_id,
        resource_type="BusinessCaseExport",
        resource_id=case_id,
        details={
            "case_id": case_id,
            "workflow_id": workflow_id,
            "export_id": export_id,
            "pdf_object_key": object_key,
        },
    )
    await AuditEmitter.write_to_db(access_event, get_db_from_context)

    return export_business_caseResult.model_validate({
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
    })


# ═══════════════════════════════════════════════════════════════════════════════
# WORKSPACE ENDPOINTS — Intelligence tab data for account cases
# ═══════════════════════════════════════════════════════════════════════════════

class CaseListItem(BaseModel):
    """Case list response item."""
    case_id: str
    account_id: str | None = None
    title: str | None = None
    status: str = "unknown"
    created_at: str | None = None
    updated_at: str | None = None


class CaseListResponse(BaseModel):
    """List of cases for an account."""
    items: list[CaseListItem]
    total: int


class CreateCaseRequest(BaseModel):
    """Create a new case for an account."""
    account_id: str = Field(..., description="Account identifier")
    title: str | None = Field(None, description="Case title")


class CreateCaseResponse(BaseModel):
    """Created case response."""
    case_id: str
    account_id: str
    title: str | None = None
    status: str = "created"
    created_at: str


class WorkspaceTabData(BaseModel):
    """Generic workspace tab data container."""
    signals: list[dict[str, Any]] = Field(default_factory=list)
    drivers: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    stakeholders: list[dict[str, Any]] = Field(default_factory=list)


# In-memory workspace data store (replace with Redis/DB for production)
_workspace_data: dict[str, dict[str, Any]] = {}


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    account_id: str,
    db: AsyncSession = Depends(get_db_from_context),
    context: RequestContext = Depends(require_authenticated),
) -> CaseListResponse:
    """List cases for an account.

    Returns all cases associated with the specified account.
    """
    from sqlalchemy import select

    from ...models.business_case_record import BusinessCaseRecord

    result = await db.execute(
        select(BusinessCaseRecord).where(BusinessCaseRecord.account_id == account_id)
    )
    records = result.scalars().all()

    items = [
        CaseListItem(
            case_id=str(r.case_id),
            account_id=str(r.account_id) if r.account_id else None,
            title=getattr(r, 'title', None),
            status=r.status,
            created_at=getattr(r, 'created_at', None),
            updated_at=getattr(r, 'updated_at', None),
        )
        for r in records
    ]

    return CaseListResponse(items=items, total=len(items))


@router.post("/cases", response_model=CreateCaseResponse)
async def create_case(
    request: CreateCaseRequest,
    db: AsyncSession = Depends(get_db_from_context),
    context: RequestContext = Depends(require_authenticated),
) -> CreateCaseResponse:
    """Create a new case for an account.

    Creates a case workspace for the specified account.
    """
    from ...models.business_case_record import BusinessCaseRecord

    case_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    record = BusinessCaseRecord(
        case_id=case_id,
        account_id=UUID(request.account_id) if request.account_id else None,
        workflow_id=case_id,
        status="created",
    )
    db.add(record)

    # Initialize empty workspace data
    _workspace_data[case_id] = {
        "signals": [],
        "drivers": [],
        "evidence": [],
        "stakeholders": [],
    }

    return CreateCaseResponse(
        case_id=case_id,
        account_id=request.account_id,
        title=request.title,
        status="created",
        created_at=now,
    )


@router.get("/cases/{case_id}/workspace/{tab_key}")
async def get_workspace_tab(
    case_id: str,
    tab_key: str,
    context: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    """Get workspace tab data.

    Returns data for a specific workspace tab:
    - Intelligence: signals, drivers, evidence, stakeholders
    - Value Studio: action-plan, value-model, narrative
    """
    valid_tabs = {"signals", "drivers", "evidence", "stakeholders", "action-plan", "value-model", "narrative"}
    if tab_key not in valid_tabs:
        raise HTTPException(status_code=400, detail=f"Invalid tab_key. Must be one of: {valid_tabs}")

    # Get workspace data or return empty
    workspace = _workspace_data.get(case_id, {})
    data = workspace.get(tab_key, [])

    return get_workspace_tabResult.model_validate({tab_key: data})


@router.put("/cases/{case_id}/workspace/{tab_key}")
async def update_workspace_tab(
    case_id: str,
    tab_key: str,
    payload: dict[str, Any],
    context: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    """Update workspace tab data.

    Updates data for a specific workspace tab.
    """
    valid_tabs = {"signals", "drivers", "evidence", "stakeholders", "action-plan", "value-model", "narrative"}
    if tab_key not in valid_tabs:
        raise HTTPException(status_code=400, detail=f"Invalid tab_key. Must be one of: {valid_tabs}")

    # Initialize workspace if needed
    if case_id not in _workspace_data:
        _workspace_data[case_id] = {
            "signals": [],
            "drivers": [],
            "evidence": [],
            "stakeholders": [],
        }

    # Update the specific tab data
    _workspace_data[case_id][tab_key] = payload.get(tab_key, payload)

    return update_workspace_tabResult.model_validate({"case_id": case_id, "tab": tab_key, "updated": True})


@router.post("/cases/{case_id}/workspace/generate")
async def generate_workspace_intelligence(
    case_id: str,
    executor: WorkflowExecutor = Depends(get_executor),
    db: AsyncSession = Depends(get_db_from_context),
    context: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    """Generate workspace intelligence data for a case.

    Triggers AI workflows to populate signals, drivers, evidence, and stakeholders
    based on account enrichment data.
    """
    from ...models.business_case_record import BusinessCaseRecord

    # Get case and account info
    record = await db.get(BusinessCaseRecord, case_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Get account details
    from ...services.account_service import AccountService
    account_service = AccountService(db)
    account = await account_service.get_account(record.account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account for case {case_id} not found")

    # Generate sample intelligence data based on account info
    # TODO: Replace with real AI workflow integration
    industry = account.industry or "Technology"
    name = account.name or "Company"

    signals = [
        {"id": "sig_1", "name": f"{name} - Operational inefficiency in {industry}", "category": "Operational", "confidence": 85, "impact": "High", "trend": "Increasing"},
        {"id": "sig_2", "name": f"Rising costs in {industry} sector", "category": "Cost", "confidence": 78, "impact": "Medium", "trend": "Stable"},
        {"id": "sig_3", "name": "Workforce productivity gaps", "category": "Workforce", "confidence": 72, "impact": "High", "trend": "Decreasing"},
    ]

    drivers = [
        {"id": "drv_1", "name": "Manual process overhead", "contribution": 35, "parentSignal": "Operational inefficiency", "subDrivers": ["Data entry", "Approval delays"]},
        {"id": "drv_2", "name": "Legacy system constraints", "contribution": 28, "parentSignal": "Operational inefficiency", "subDrivers": ["Integration gaps", "Maintenance cost"]},
        {"id": "drv_3", "name": "Lack of real-time visibility", "contribution": 22, "parentSignal": "Rising costs", "subDrivers": ["Delayed decisions", "Missed opportunities"]},
    ]

    evidence = [
        {"id": "ev_1", "source": "Industry Report 2024", "claim": f"{industry} sector averages 23% efficiency gap", "confidence": 88, "type": "benchmark"},
        {"id": "ev_2", "source": "Internal Analysis", "claim": "Current process takes 3x industry average", "confidence": 75, "type": "internal"},
    ]

    stakeholders = [
        {"id": "st_1", "name": "CFO", "role": "Economic Buyer", "priority": "High", "engagement": "Active"},
        {"id": "st_2", "name": "VP Operations", "role": "Technical Champion", "priority": "High", "engagement": "Engaged"},
        {"id": "st_3", "name": "IT Director", "role": "Influencer", "priority": "Medium", "engagement": "Monitoring"},
    ]

    # Generate Value Studio data
    action_plan = [
        {"id": "rec_1", "title": "Automate manual approval workflows", "priority": "critical", "projectedValue": "$2.4M annually", "confidence": "high", "horizon": "Q2-Q3", "prospectPain": "Manual routing causes 3-day delays", "rootDriver": "Manual process overhead", "ourCapability": "Workflow automation platform"},
        {"id": "rec_2", "title": "Integrate legacy systems via API", "priority": "high", "projectedValue": "$1.8M annually", "confidence": "medium", "horizon": "Q3-Q4", "prospectPain": "Data silos require duplicate entry", "rootDriver": "Legacy system constraints", "ourCapability": "Enterprise integration suite"},
        {"id": "rec_3", "title": "Deploy real-time analytics dashboard", "priority": "high", "projectedValue": "$980K annually", "confidence": "high", "horizon": "Q2", "prospectPain": "Delayed visibility into operations", "rootDriver": "Lack of real-time visibility", "ourCapability": "Analytics platform"},
    ]

    value_model = [
        {"id": "vl_1", "driver": "Labor cost reduction", "category": "hard", "conservative": 800000, "expected": 1200000, "optimistic": 1600000, "source": "Process automation"},
        {"id": "vl_2", "driver": "Error reduction", "category": "hard", "conservative": 200000, "expected": 400000, "optimistic": 600000, "source": "Data validation"},
        {"id": "vl_3", "driver": "Time-to-market improvement", "category": "strategic", "conservative": 500000, "expected": 1000000, "optimistic": 2000000, "source": "Faster iteration"},
        {"id": "vl_4", "driver": "Employee satisfaction", "category": "strategic", "conservative": 150000, "expected": 300000, "optimistic": 500000, "source": "Reduced toil"},
    ]

    narratives = [
        {"id": "nar_1", "stakeholder": "CFO", "role": "Economic Buyer", "status": "ready", "headline": "$5.2M projected ROI over 3 years with 18-month payback", "summary": "Our financial analysis shows a compelling return on investment driven primarily by labor cost reduction and error elimination. Conservative estimates place 3-year NPV at $4.1M with sensitivity analysis supporting go-forward recommendation.", "keyMetrics": [{"label": "3-Year NPV", "value": "$4.1M"}, {"label": "Payback", "value": "18 months"}, {"label": "IRR", "value": "142%"}], "lastUpdated": "2024-01-15T10:30:00Z"},
        {"id": "nar_2", "stakeholder": "VP Operations", "role": "Technical Champion", "status": "ready", "headline": "Eliminate 85% of manual touchpoints within 90 days", "summary": "The implementation roadmap addresses your critical pain points through phased rollout. Week 1-2: Discovery and mapping. Week 3-6: Pilot with one workflow. Week 7-12: Scale to full production with 24/7 support.", "keyMetrics": [{"label": "Manual touchpoints eliminated", "value": "85%"}, {"label": "Implementation time", "value": "90 days"}, {"label": "Uptime SLA", "value": "99.9%"}], "lastUpdated": "2024-01-14T16:45:00Z"},
        {"id": "nar_3", "stakeholder": "IT Director", "role": "Influencer", "status": "draft", "headline": "Secure, SOC-2 compliant integration with existing stack", "summary": "Technical architecture review complete. Solution integrates with your existing identity provider and requires no infrastructure changes. Security assessment passed with no critical findings.", "keyMetrics": [{"label": "Security score", "value": "A+"}, {"label": "Integration points", "value": "12 APIs"}, {"label": "Audit findings", "value": "0 critical"}], "lastUpdated": "2024-01-13T09:20:00Z"},
    ]

    # Store the generated data
    _workspace_data[case_id] = {
        "signals": signals,
        "drivers": drivers,
        "evidence": evidence,
        "stakeholders": stakeholders,
        "action-plan": action_plan,
        "value-model": value_model,
        "narrative": narratives,
    }

    return generate_workspace_intelligenceResult.model_validate({
        "case_id": case_id,
        "account_id": str(record.account_id),
        "generated": True,
        "stats": {
            "signals": len(signals),
            "drivers": len(drivers),
            "evidence": len(evidence),
            "stakeholders": len(stakeholders),
            "action_plan": len(action_plan),
            "value_model": len(value_model),
            "narratives": len(narratives),
        },
    })


