"""Analysis API routes for quick ROI and whitespace calculations."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from value_fabric.shared.audit import AuditAction, emit_audit_event
from value_fabric.shared.identity.context import RequestContext
from value_fabric.shared.identity.dependencies import require_authenticated
from value_fabric.shared.models.typed_dict import TypedDictModel

from ...config.settings import settings
from ..common.audit import emit_and_persist_audit
from ..common.db import get_route_db
from ..common.errors import normalize_exception
from ...engine.executor import WorkflowExecutor
from ...models.agent_state import BusinessCaseInputData, ROIInputData, WhitespaceInputData
from ...models.business_case_record import BusinessCaseRecord
from ...models.saved_scenario import SavedBusinessCaseScenario
from ...models.workspace_tab_data import WorkspaceTabData
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

class generate_workspace_intelligenceResult(TypedDictModel):
    account_id: Any
    case_id: Any
    generated: bool
    stats: dict[str, Any]

router = APIRouter()


def _get_neo4j_driver(request: Request) -> Any:
    """Return the app-scoped Neo4j driver for routes that read graph context."""
    return request.app.state.neo4j_driver


# ROI Analysis Models
class ROIAnalysisRequest(BaseModel):
    """Quick ROI analysis request."""

    prospect_id: str | None = Field(None, description="Prospect identifier")
    value_driver_ids: list[str] = Field(default_factory=list, description="Value drivers to calculate")
    prospect_data: dict[str, float] = Field(
        default_factory=dict, description="Prospect-specific variables"
    )
    industry_vertical: str | None = None
    company_size: str | None = None

    # Legacy/release-smoke compatibility fields. Canonical clients should continue
    # to send prospect_id, value_driver_ids, and prospect_data.
    account_id: str | None = None
    variables: dict[str, float] = Field(default_factory=dict)
    formula_id: str | None = None


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
    from ..main import workflow_executor

    if workflow_executor is None:
        raise HTTPException(status_code=503, detail="Workflow executor not initialized")
    return workflow_executor


def _is_smoke_mode(http_request: Request, *, body_mode: str | None = None) -> bool:
    """Return true only for explicit validation smoke-mode requests."""
    validation_mode = http_request.headers.get("X-Validation-Mode", "").strip().lower()
    smoke_header = http_request.headers.get("X-Fabric-Smoke-Test", "").strip().lower()
    body_mode_normalized = (body_mode or "").strip().lower()
    return validation_mode == "smoke" or smoke_header in {"1", "true", "yes"} or body_mode_normalized == "smoke"


def _validation_trace_id(http_request: Request) -> str:
    """Return a stable request trace identifier for validation responses."""
    return http_request.headers.get("X-Validation-Run-ID") or http_request.headers.get("X-Request-ID") or str(uuid4())


async def _smoke_roi_response(
    http_request: Request,
    prospect_id: str,
    account: Any,
    context: RequestContext,
) -> ROIAnalysisResponse:
    """Build deterministic smoke-mode ROI response without invoking the workflow executor."""
    trace_id = _validation_trace_id(http_request)
    emit_audit_event(
        AuditAction.ROI_CALCULATED,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        api_key_id=context.api_key_id,
        resource_type="ROIAnalysis",
        resource_id=str(account.id),
        request_id=trace_id,
        details={
            "mode": "smoke",
            "status": "draft",
            "account_id": str(account.id),
            "requires_full_analysis": True,
        },
    )
    return ROIAnalysisResponse(
        prospect_id=prospect_id,
        aggregated_roi={
            "status": "draft",
            "mode": "smoke",
            "calculation": "roi",
            "result": {
                "total_value": 0,
                "roi": None,
                "payback_months": None,
            },
            "requires_full_analysis": True,
            "trace_id": trace_id,
            "tenant_id": str(context.tenant_id),
            "account_id": str(account.id),
        },
        detailed_results=[],
        benchmark_comparison={"mode": "smoke", "status": "not_evaluated"},
    )


async def _smoke_business_case_response(
    http_request: Request,
    request: BusinessCaseRequest,
    account: Any,
    db: AsyncSession,
    context: RequestContext,
) -> BusinessCaseResponse:
    """Build deterministic smoke-mode business case response without invoking the workflow executor."""
    trace_id = _validation_trace_id(http_request)
    case_id = f"smoke-case-{uuid4()}"
    business_case_service = BusinessCaseService(db)
    await business_case_service.upsert_case_record(
        case_id=case_id,
        workflow_id=case_id,
        account_id=request.account_id,
        opportunity_id=request.opportunity_id,
        status="draft",
        document_url=None,
    )
    emit_audit_event(
        AuditAction.BUSINESS_CASE_GENERATED,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        api_key_id=context.api_key_id,
        resource_type="BusinessCase",
        resource_id=case_id,
        request_id=trace_id,
        details={
            "mode": "smoke",
            "status": "draft",
            "account_id": str(account.id),
            "approval_required": True,
            "export_allowed": False,
            "requires_full_generation": True,
        },
    )
    return BusinessCaseResponse(
        case_id=case_id,
        title="Business Case Draft",
        summary="Draft smoke-mode business case; full generation is still required.",
        status="draft",
        created_at=datetime.now(UTC).isoformat(),
        remediation_items=[
            {
                "code": "FULL_GENERATION_REQUIRED",
                "message": "Run full business-case generation before approval or export.",
            }
        ],
        case_metadata={
            "mode": "smoke",
            "trace_id": trace_id,
            "tenant_id": str(context.tenant_id),
            "account_id": str(account.id),
            "approval_required": True,
            "export_allowed": False,
            "requires_full_generation": True,
        },
    )


async def _require_tenant_account(db: AsyncSession, account_id: UUID, context: RequestContext) -> Any:
    """Load an account through the authenticated tenant boundary or fail closed."""
    account = await AccountService(db).get_account(account_id, tenant_id=str(context.tenant_id))
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found: {account_id}",
        )
    return account


@router.post("/analysis/roi", response_model=ROIAnalysisResponse)
async def quick_roi_analysis(
    http_request: Request,
    request: ROIAnalysisRequest = Body(...),
    executor: WorkflowExecutor = Depends(get_executor),
    db: AsyncSession = Depends(get_route_db),
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
        prospect_id = request.prospect_id or request.account_id
        if not prospect_id:
            raise HTTPException(status_code=422, detail="prospect_id or account_id is required")
        value_driver_ids = request.value_driver_ids or ([request.formula_id] if request.formula_id else list(request.variables.keys()))
        if not value_driver_ids:
            value_driver_ids = ["roi"]
        prospect_data = request.prospect_data or request.variables

        if _is_smoke_mode(http_request):
            if not request.account_id:
                raise HTTPException(status_code=422, detail="account_id is required for smoke-mode ROI validation")
            try:
                account_uuid = UUID(request.account_id)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail="account_id must be a UUID for smoke-mode ROI validation") from exc
            account = await _require_tenant_account(db, account_uuid, context)
            return await _smoke_roi_response(http_request, prospect_id, account, context)

        input_data = ROIInputData(
            prospect_id=prospect_id,
            value_driver_ids=value_driver_ids,
            prospect_data=prospect_data,
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
            prospect_id=prospect_id,
            aggregated_roi=aggregate.get("aggregated", {}) or {"calculation": "roi", "result": aggregate},
            detailed_results=aggregate.get("detailed_results", []),
            benchmark_comparison=result.output_data.get("fetch_benchmarks", {}).get("benchmarks"),
        )

    except Exception as e:
        raise normalize_exception(e, status_code=500, detail=f"ROI analysis failed: {str(e)}")


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
        raise normalize_exception(e, status_code=500, detail=f"Whitespace analysis failed: {str(e)}")


@router.post("/cases", response_model=BusinessCaseResponse)
async def generate_business_case(
    request: BusinessCaseRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    executor: WorkflowExecutor = Depends(get_executor),
    db: AsyncSession = Depends(get_route_db),
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
        account = await account_service.get_account(request.account_id, tenant_id=str(context.tenant_id))
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not found: {request.account_id}",
            )

        custom_inputs = dict(request.custom_inputs)
        custom_inputs["provider_record_id"] = account.provider_record_id

        if _is_smoke_mode(http_request, body_mode=str(custom_inputs.get("mode", ""))):
            return await _smoke_business_case_response(http_request, request, account, db, context)

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
        raise normalize_exception(e, status_code=500, detail=f"Business case generation failed: {str(e)}")


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
    db: AsyncSession = Depends(get_route_db),
    context: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    """Export a generated business case.

    This version resolves the merge conflict by preserving both:
    1. Truth-gating / blocking behavior
    2. Provenance manifest generation, storage upload, and audit events
    """
    result = await executor.get_result(case_id)
    if not result:
        record = await db.get(BusinessCaseRecord, case_id)
        if record:
            await _require_tenant_account(db, record.account_id, context)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Business case draft is not approved or document bytes unavailable",
            )
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

    if not settings.export_storage_endpoint:
        raise HTTPException(status_code=503, detail="Export storage endpoint is not configured")

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

    await emit_and_persist_audit(
        action=AuditAction.EXPORT_REQUESTED,
        context=context,
        resource_type="BusinessCaseExport",
        resource_id=case_id,
        details={
            "case_id": case_id,
            "workflow_id": workflow_id,
            "export_id": export_id,
            "format": format,
        },
    )

    await emit_and_persist_audit(
        action=AuditAction.EXPORT_PACKAGE_GENERATED,
        context=context,
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

    await emit_and_persist_audit(
        action=AuditAction.EXPORT_DOWNLOAD_ACCESSED,
        context=context,
        resource_type="BusinessCaseExport",
        resource_id=case_id,
        details={
            "case_id": case_id,
            "workflow_id": workflow_id,
            "export_id": export_id,
            "pdf_object_key": object_key,
        },
    )

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


class SaveScenarioRequest(BaseModel):
    """Persist a business-case what-if scenario."""

    name: str = Field(..., min_length=1, max_length=120)
    adjustments: list[dict[str, Any]] = Field(default_factory=list, max_length=100)


class SavedScenarioSummary(BaseModel):
    """Safe scenario metadata returned to the frontend."""

    id: str
    name: str
    created_at: str


class SavedScenarioDetail(SavedScenarioSummary):
    """Full server-side scenario payload."""

    adjustments: list[dict[str, Any]]


class WorkspaceTabData(BaseModel):
    """Generic workspace tab data container."""
    signals: list[dict[str, Any]] = Field(default_factory=list)
    drivers: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    stakeholders: list[dict[str, Any]] = Field(default_factory=list)


class WorkspaceEvidenceItem(BaseModel):
    id: str
    title: str
    type: str = "evidence"
    source: str = "Unknown"
    matchScore: int = 0
    verification: str = "unverified"
    linkedSignals: list[str] = Field(default_factory=list)
    excerpt: str = ""
    decision_status: str | None = None
    attached_driver_id: str | None = None
    provenance_id: str | None = None
    confidence: float | None = None
    decision_note: str | None = None


class WorkspaceEvidenceResponse(BaseModel):
    evidence: list[WorkspaceEvidenceItem] = Field(default_factory=list)


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    account_id: str,
    db: AsyncSession = Depends(get_route_db),
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
    db: AsyncSession = Depends(get_route_db),
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
        tenant_id=str(context.tenant_id) if context.tenant_id else "default",
    )
    db.add(record)

    return CreateCaseResponse(
        case_id=case_id,
        account_id=request.account_id,
        title=request.title,
        status="created",
        created_at=now,
    )


@router.get("/cases/{case_id}/scenarios", response_model=list[SavedScenarioSummary])
async def list_saved_scenarios(
    case_id: str,
    db: AsyncSession = Depends(get_route_db),
    context: RequestContext = Depends(require_authenticated),
) -> list[SavedScenarioSummary]:
    """List saved scenario metadata for a business case."""
    tenant_id = str(context.tenant_id)
    result = await db.execute(
        select(SavedBusinessCaseScenario)
        .where(
            SavedBusinessCaseScenario.case_id == case_id,
            SavedBusinessCaseScenario.tenant_id == tenant_id,
        )
        .order_by(SavedBusinessCaseScenario.created_at.desc())
    )
    records = result.scalars().all()
    return [
        SavedScenarioSummary(
            id=record.scenario_id,
            name=record.name,
            created_at=record.created_at.isoformat(),
        )
        for record in records
    ]


@router.post(
    "/cases/{case_id}/scenarios",
    response_model=SavedScenarioDetail,
    status_code=status.HTTP_201_CREATED,
)
async def save_scenario(
    case_id: str,
    request: SaveScenarioRequest,
    db: AsyncSession = Depends(get_route_db),
    context: RequestContext = Depends(require_authenticated),
) -> SavedScenarioDetail:
    """Persist a business-case what-if scenario server-side."""
    now = datetime.now(UTC)
    record = SavedBusinessCaseScenario(
        scenario_id=f"scenario_{uuid4().hex}",
        case_id=case_id,
        tenant_id=str(context.tenant_id),
        name=request.name,
        adjustments=request.adjustments,
        created_at=now,
    )
    db.add(record)
    return SavedScenarioDetail(
        id=record.scenario_id,
        name=record.name,
        adjustments=record.adjustments,
        created_at=now.isoformat(),
    )


@router.get("/cases/{case_id}/scenarios/{scenario_id}", response_model=SavedScenarioDetail)
async def get_saved_scenario(
    case_id: str,
    scenario_id: str,
    db: AsyncSession = Depends(get_route_db),
    context: RequestContext = Depends(require_authenticated),
) -> SavedScenarioDetail:
    """Fetch a saved scenario with sensitive adjustments from server storage."""
    result = await db.execute(
        select(SavedBusinessCaseScenario).where(
            SavedBusinessCaseScenario.case_id == case_id,
            SavedBusinessCaseScenario.scenario_id == scenario_id,
            SavedBusinessCaseScenario.tenant_id == str(context.tenant_id),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Saved scenario not found")
    return SavedScenarioDetail(
        id=record.scenario_id,
        name=record.name,
        adjustments=record.adjustments,
        created_at=record.created_at.isoformat(),
    )


@router.delete("/cases/{case_id}/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_scenario(
    case_id: str,
    scenario_id: str,
    db: AsyncSession = Depends(get_route_db),
    context: RequestContext = Depends(require_authenticated),
) -> None:
    """Delete a saved scenario only within the authenticated tenant scope."""
    result = await db.execute(
        delete(SavedBusinessCaseScenario).where(
            SavedBusinessCaseScenario.case_id == case_id,
            SavedBusinessCaseScenario.scenario_id == scenario_id,
            SavedBusinessCaseScenario.tenant_id == str(context.tenant_id),
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Saved scenario not found")


@router.get("/cases/{case_id}/workspace/evidence", response_model=WorkspaceEvidenceResponse)
async def get_workspace_evidence(
    case_id: str,
    db: AsyncSession = Depends(get_route_db),
    context: RequestContext = Depends(require_authenticated),
) -> WorkspaceEvidenceResponse:
    from sqlalchemy import select
    from ...models.workspace_tab_data import WorkspaceTabData

    tenant_id = str(context.tenant_id)
    result = await db.execute(
        select(WorkspaceTabData).where(
            WorkspaceTabData.case_id == case_id,
            WorkspaceTabData.tab_key == "evidence",
            WorkspaceTabData.tenant_id == tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        return WorkspaceEvidenceResponse(evidence=[])
    payload = record.data if isinstance(record.data, dict) else {}
    evidence_items = payload.get("evidence", [])
    if not isinstance(evidence_items, list):
        raise HTTPException(status_code=500, detail="Invalid persisted evidence payload shape")
    return WorkspaceEvidenceResponse(evidence=[WorkspaceEvidenceItem.model_validate(item) for item in evidence_items])



@router.get("/cases/{case_id}/workspace/{tab_key}")
async def get_workspace_tab(
    case_id: str,
    tab_key: str,
    db: AsyncSession = Depends(get_route_db),
    context: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    """Get persisted workspace tab data."""
    valid_tabs = {"signals", "drivers", "evidence", "stakeholders", "action-plan", "value-model", "narrative", "intake", "evidence-links"}
    if tab_key not in valid_tabs:
        raise HTTPException(status_code=400, detail=f"Invalid tab_key. Must be one of: {valid_tabs}")

    from sqlalchemy import select
    from ...models.workspace_tab_data import WorkspaceTabData

    tenant_id = str(context.tenant_id)
    result = await db.execute(
        select(WorkspaceTabData).where(
            WorkspaceTabData.case_id == case_id,
            WorkspaceTabData.tab_key == tab_key,
            WorkspaceTabData.tenant_id == tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        return {tab_key: []}
    data = record.data if isinstance(record.data, dict) else {"data": record.data}
    return data or {tab_key: []}


@router.put("/cases/{case_id}/workspace/{tab_key}")
async def update_workspace_tab(
    case_id: str,
    tab_key: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_route_db),
    context: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    """Update persisted workspace tab data."""
    valid_tabs = {"signals", "drivers", "evidence", "stakeholders", "action-plan", "value-model", "narrative", "intake", "evidence-links"}
    if tab_key not in valid_tabs:
        raise HTTPException(status_code=400, detail=f"Invalid tab_key. Must be one of: {valid_tabs}")

    from sqlalchemy import select
    from ...models.workspace_tab_data import WorkspaceTabData

    tenant_id = str(context.tenant_id)
    result = await db.execute(
        select(WorkspaceTabData).where(
            WorkspaceTabData.case_id == case_id,
            WorkspaceTabData.tab_key == tab_key,
            WorkspaceTabData.tenant_id == tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        record = WorkspaceTabData(case_id=case_id, tab_key=tab_key, tenant_id=tenant_id, data=payload)
        db.add(record)
    else:
        record.data = payload

    await db.commit()
    return {"case_id": case_id, "tab": tab_key, "updated": True, "data": payload}


@router.post("/cases/{case_id}/workspace/generate")
async def generate_workspace_intelligence(
    case_id: str,
    request: Request,
    executor: WorkflowExecutor = Depends(get_executor),
    db: AsyncSession = Depends(get_route_db),
    context: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    """Generate workspace intelligence data for a case.

    Lightweight generation that surfaces existing Neo4j data (signals,
    hypotheses) for the account. No LLM call — just exposes graph data
    the frontend currently can't see.
    """
    from ...models.business_case_record import BusinessCaseRecord
    from ...models.workspace_tab_data import WorkspaceTabData as WorkspaceTabDataModel

    record = await db.get(BusinessCaseRecord, case_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    tenant_id = str(context.tenant_id) if context.tenant_id else "default"
    account_id = str(record.account_id)

    driver = _get_neo4j_driver(request)

    # Query existing signals for the account
    signal_query = """
    MATCH (ps:PainSignal {account_id: $account_id, tenant_id: $tenant_id})
    RETURN ps {.id, .name, .category, .confidence_score, .impact_value, .trend} AS signal
    LIMIT 50
    """
    signals = []
    async with driver.session() as session:
        result = await session.run(signal_query, {"account_id": account_id, "tenant_id": tenant_id})
        async for record_row in result:
            s = record_row["signal"]
            if s:
                signals.append({
                    "id": s.get("id", ""),
                    "name": s.get("name", ""),
                    "category": s.get("category", "Unknown"),
                    "confidence": int((s.get("confidence_score") or 0.5) * 100),
                    "impact": s.get("impact_value", "medium"),
                    "trend": s.get("trend", "stable"),
                })

    # Query existing hypotheses for the account
    hypothesis_query = """
    MATCH (vh:ValueHypothesis {account_id: $account_id, tenant_id: $tenant_id})
    RETURN vh {.id, .hypothesis_text, .confidence_score, .value_path_category, .status, .capability_name} AS hypothesis
    LIMIT 50
    """
    hypotheses = []
    async with driver.session() as session:
        result = await session.run(hypothesis_query, {"account_id": account_id, "tenant_id": tenant_id})
        async for record_row in result:
            h = record_row["hypothesis"]
            if h:
                hypotheses.append({
                    "id": h.get("id", ""),
                    "hypothesis_text": h.get("hypothesis_text", ""),
                    "confidence": h.get("confidence_score", 0.5),
                    "value_path_category": h.get("value_path_category"),
                    "status": h.get("status", "draft"),
                    "capability_name": h.get("capability_name", ""),
                })

    # Store in workspace tab persistence
    tab_data = {
        "signals": {"signals": signals},
        "drivers": {"drivers": hypotheses},
        "evidence": {"evidence": []},
        "stakeholders": {"stakeholders": []},
        "action-plan": {"recommendations": []},
        "value-model": {"value_models": []},
        "narrative": {"narratives": []},
    }

    for tab_key, data in tab_data.items():
        result = await db.execute(
            select(WorkspaceTabDataModel).where(
                WorkspaceTabDataModel.case_id == case_id,
                WorkspaceTabDataModel.tab_key == tab_key,
                WorkspaceTabDataModel.tenant_id == tenant_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.data = data
        else:
            db.add(WorkspaceTabDataModel(
                case_id=case_id,
                tab_key=tab_key,
                tenant_id=tenant_id,
                data=data,
            ))

    await db.commit()

    return {
        "case_id": case_id,
        "account_id": account_id,
        "generated": True,
        "stats": {
            "signals": len(signals),
            "drivers": len(hypotheses),
            "evidence": 0,
            "stakeholders": 0,
        },
    }
