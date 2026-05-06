"""Extraction job routes for Layer 2 API."""

import logging
import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request, HTTPException
from pydantic import BaseModel, Field
from value_fabric.shared.identity import require_authenticated

from .. import main as handlers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["extraction"], dependencies=[Depends(require_authenticated)])


# ============================================================================
# Extraction Entities Models
# =============================================================================


class EntitySourceSpan(BaseModel):
    """Source span information for an extracted entity."""
    document_id: str = Field(..., description="Document identifier")
    start: int = Field(..., description="Start position in document")
    end: int = Field(..., description="End position in document")


class EntityProvenance(BaseModel):
    """Provenance information for an extracted entity."""
    extraction_job_id: str = Field(..., description="Extraction job identifier")
    source_url: str | None = Field(None, description="Source URL if applicable")
    trace_id: str | None = Field(None, description="Trace identifier for observability")


class ExtractedEntity(BaseModel):
    """Single extracted entity from an extraction job."""
    entity_id: str = Field(..., description="Entity identifier")
    type: str = Field(..., description="Entity type (e.g., Capability, UseCase, Persona)")
    name: str = Field(..., description="Entity name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    source_span: EntitySourceSpan | None = Field(None, description="Source span in document")
    provenance: EntityProvenance | None = Field(None, description="Provenance information")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Additional entity attributes")


class ExtractionEntitiesResponse(BaseModel):
    """Response for extraction entities endpoint."""
    job_id: str = Field(..., description="Extraction job identifier")
    entities: list[ExtractedEntity] = Field(..., description="List of extracted entities")
    total: int = Field(..., description="Total number of entities")


# ============================================================================
# Operational Signal Extraction Models
# =============================================================================


class ProspectDataInput(BaseModel):
    """Prospect data for signal extraction."""

    account_id: str = Field(..., description="Account identifier")
    company_name: str = Field(..., description="Company name")
    industry: str | None = Field(default=None, description="Industry vertical")
    business_pains: list[str] = Field(default_factory=list, description="Business pains")
    friction_points: list[str] = Field(default_factory=list, description="Friction points")
    desired_outcomes: list[str] = Field(default_factory=list, description="Desired outcomes")
    prompt_text: str = Field(..., description="Freeform prompt text")
    prompt_id: str | None = Field(default=None, description="Prompt identifier")
    attachments: list[dict[str, Any]] = Field(default_factory=list, description="Attachments")


class SignalExtractionRequest(BaseModel):
    """Request for operational signal extraction."""

    prospect_data: ProspectDataInput = Field(..., description="Prospect information")
    extraction_type: str = Field(default="operational_signals", description="Extraction type")
    category: str = Field(default="Operational", description="Signal category")


class SignalExtractionResult(BaseModel):
    """Single extracted signal result."""

    name: str = Field(..., description="Signal name")
    category: str = Field(default="Operational", description="Signal category")
    description: str = Field(..., description="Signal description")
    confidence_score: float = Field(..., description="Confidence 0.0-1.0")
    confidence_explanation: str = Field(default="", description="Why this confidence")
    impact_indicators: list[str] = Field(default_factory=list, description="Impact clues")
    trend_direction: str = Field(default="new", description="increasing|decreasing|stable|new")
    trend_explanation: str = Field(default="", description="Why this trend")
    stakeholder_quotes: list[str] = Field(default_factory=list, description="Evidence quotes")
    likely_value_drivers: list[str] = Field(default_factory=list, description="Mapped value drivers")


class SignalExtractionResponse(BaseModel):
    """Response from signal extraction."""

    signals: list[SignalExtractionResult] = Field(default_factory=list, description="Extracted signals")
    duration_ms: int = Field(default=0, description="Processing duration")
    model_version: str = Field(default="gpt-4o-2024-08-06", description="LLM model used")
    prompt_version: str = Field(default="1.0.0", description="Prompt version")


@router.post("/extract/signals", response_model=SignalExtractionResponse)
async def extract_signals(
    request: SignalExtractionRequest,
    http_request: Request,
    x_tenant_id: str = Header(..., description="Tenant ID for scoping"),
    x_trace_id: str | None = Header(None, description="Trace ID for observability"),
):
    """Extract operational pain signals from prospect setup data.

    Uses LLM-based structured extraction to identify operational signals
    (equipment downtime, changeover inefficiency, quality defects, etc.)
    from prospect-provided business context.

    Args:
        request: Signal extraction request with prospect data
        http_request: HTTP request object
        x_tenant_id: Tenant ID from header
        x_trace_id: Optional trace ID from header

    Returns:
        SignalExtractionResponse with extracted signals
    """

    from layer2_extraction.extraction.prompts import load_prompt
    from layer2_extraction.models.operational_signal_extraction import (
        OperationalSignalExtractionResponse,
    )
    from layer2_extraction.shared.llm_client import LLMClient

    start_time = time.time()

    # Load the operational signal extraction prompt
    prompt_text = load_prompt("operational_signal_extraction.txt")

    # Prepare input for LLM
    # P1-12 FIX: Wrap all user-controlled content in delimiters to prevent prompt injection
    prospect = request.prospect_data
    user_content = f"""
Company: <<<USER_INPUT>>>{prospect.company_name}<<</USER_INPUT>>>
Industry: <<<USER_INPUT>>>{prospect.industry or "Unknown"}<<</USER_INPUT>>>

Business Pains:
<<<USER_INPUT>>>
{chr(10).join(f"- {pain}" for pain in prospect.business_pains)}
<<</USER_INPUT>>>

Friction Points:
<<<USER_INPUT>>>
{chr(10).join(f"- {point}" for point in prospect.friction_points)}
<<</USER_INPUT>>>

Desired Outcomes:
<<<USER_INPUT>>>
{chr(10).join(f"- {outcome}" for outcome in prospect.desired_outcomes)}
<<</USER_INPUT>>>

Freeform Context:
<<<USER_INPUT>>>{prospect.prompt_text}<<</USER_INPUT>>>
"""

    # Call LLM for structured extraction using existing LLMClient

    llm_client = LLMClient()
    messages = [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": user_content},
    ]

    extraction_result, _ = await llm_client.chat_completion_structured(
        messages=messages,
        extraction_job_id=x_trace_id or f"signal_{x_tenant_id}_{int(time.time())}",
        endpoint="operational_signal_extraction",
        response_format=OperationalSignalExtractionResponse,
        temperature=0.1,
    )

    duration_ms = int((time.time() - start_time) * 1000)

    # Transform to API response format
    signals = []
    for signal in extraction_result.signals:
        signals.append(
            SignalExtractionResult(
                name=signal.name,
                category=signal.category.value if hasattr(signal.category, "value") else str(signal.category),
                description=signal.description,
                confidence_score=signal.confidence_score,
                confidence_explanation=signal.confidence_explanation,
                impact_indicators=signal.impact_indicators,
                trend_direction=signal.trend_direction.value if hasattr(signal.trend_direction, "value") else str(signal.trend_direction),
                trend_explanation=signal.trend_explanation or "",
                stakeholder_quotes=signal.stakeholder_quotes,
                likely_value_drivers=signal.likely_value_drivers,
            )
        )

    return SignalExtractionResponse(
        signals=signals,
        duration_ms=duration_ms,
        model_version=extraction_result.extraction_metadata.model_version,
        prompt_version=extraction_result.extraction_metadata.prompt_version,
    )


@router.post("/extract", response_model=handlers.ExtractResponse)
async def extract(request: handlers.ExtractRequest, background_tasks: BackgroundTasks):
    return await handlers.extract(request, background_tasks)


@router.post("/extract-and-ingest", response_model=handlers.ExtractAndIngestResponse)
async def extract_and_ingest(request: handlers.ExtractRequest, background_tasks: BackgroundTasks):
    return await handlers.extract_and_ingest(request, background_tasks)


@router.get("/extract/status/{job_id}", response_model=handlers.ExtractionStatusResponse)
async def get_extraction_status(job_id: str):
    return await handlers.get_extraction_status(job_id)


@router.post("/extract/batch")
async def extract_batch(requests: list[handlers.ExtractRequest], background_tasks: BackgroundTasks):
    return await handlers.extract_batch(requests, background_tasks)


@router.get("/extract/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    return await handlers.stream_job_events(job_id)


@router.get("/extract/{job_id}/entities", response_model=ExtractionEntitiesResponse)
async def get_extraction_entities(job_id: str, request: Request):
    """Get extracted entities for a specific extraction job.
    
    Args:
        job_id: Extraction job identifier
        request: HTTP request for tenant context
        
    Returns:
        ExtractionEntitiesResponse with extracted entities
        
    Raises:
        HTTPException 404: Job not found for tenant
        HTTPException 409: Extraction not complete
    """
    from layer2_extraction.integration.job_store import build_job_store
    
    # Get tenant context from governance middleware
    ctx = getattr(request.state, "governance_context", None)
    if not ctx:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    tenant_id = ctx.tenant_id
    
    # Get job store
    job_store = build_job_store()
    
    # Retrieve job
    try:
        job = await job_store.get_job(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Verify tenant access (if job has tenant_id attribute)
    if hasattr(job, 'tenant_id') and job.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Check if extraction is complete
    if job.extraction_status not in ("completed", "partial_success"):
        raise HTTPException(
            status_code=409,
            detail=f"Extraction not complete (status: {job.extraction_status})"
        )
    
    # Retrieve extraction artifacts
    artifacts = await job_store.get_artifacts(job_id)
    if not artifacts or not artifacts.result:
        raise HTTPException(status_code=404, detail=f"No extraction artifacts found for job {job_id}")
    
    # Extract entities from result
    result = artifacts.result
    entities = []
    
    # Convert to response format
    if hasattr(result, 'get_all_entities'):
        for entity in result.get_all_entities():
            entities.append(ExtractedEntity(
                entity_id=entity.id,
                type=entity.type,
                name=entity.name,
                confidence=entity.confidence if hasattr(entity, 'confidence') else 0.0,
                source_span=EntitySourceSpan(
                    document_id=getattr(entity, 'document_id', ''),
                    start=getattr(entity, 'start', 0),
                    end=getattr(entity, 'end', 0)
                ) if hasattr(entity, 'document_id') else None,
                provenance=EntityProvenance(
                    extraction_job_id=job_id,
                    source_url=getattr(job, 'source_url', None),
                    trace_id=getattr(job, 'trace_id', None)
                ),
                attributes=getattr(entity, 'attributes', {})
            ))
    
    return ExtractionEntitiesResponse(
        job_id=job_id,
        entities=entities,
        total=len(entities)
    )

