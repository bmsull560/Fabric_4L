"""Thin workflow facade endpoints for durable UI value-flow navigation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from shared.identity.dependencies import require_authenticated

from ..schemas.value_flow import (
    CompletionStatusResponse,
    ConfirmationActionRequest,
    ConfirmationActionResponse,
    StepStateRequest,
    StepStateResponse,
)
from ...services.value_flow_facade import ValueFlowFacadeService

router = APIRouter(prefix="/v1/value-flow", tags=["Value Flow Facade"])


def _service(request: Request) -> ValueFlowFacadeService:
    service = getattr(request.app.state, "value_flow_facade", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Value flow facade service unavailable")
    return service


@router.post("/setup", response_model=StepStateResponse)
@router.post("/intelligence", response_model=StepStateResponse)
@router.post("/model", response_model=StepStateResponse)
@router.post("/validation", response_model=StepStateResponse)
@router.post("/completion", response_model=StepStateResponse)
async def save_step(
    payload: StepStateRequest,
    request: Request,
    _ctx=Depends(require_authenticated),
):
    service = _service(request)
    saved = await service.save_step_state(
        payload.flow_instance_id,
        payload.step,
        payload.state.data,
        payload.idempotency_key,
    )
    return StepStateResponse(
        flow_instance_id=payload.flow_instance_id,
        step=payload.step,
        saved=True,
        resumed=False,
        state={"data": saved["state"]},
        updated_at=saved["updated_at"],
    )


@router.get("/{flow_instance_id}/{step}", response_model=StepStateResponse)
async def resume_step(flow_instance_id: str, step: str, request: Request, _ctx=Depends(require_authenticated)):
    service = _service(request)
    try:
        from ..schemas.value_flow import ValueFlowStep

        step_enum = ValueFlowStep(step)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid step") from exc
    state = await service.load_step_state(flow_instance_id, step_enum)
    if state is None:
        raise HTTPException(status_code=404, detail="Step state not found")
    return StepStateResponse(
        flow_instance_id=flow_instance_id,
        step=step_enum,
        saved=True,
        resumed=True,
        state={"data": state["state"]},
        updated_at=state["updated_at"],
    )


@router.post("/confirm", response_model=ConfirmationActionResponse)
async def confirm_action(
    payload: ConfirmationActionRequest,
    request: Request,
    _ctx=Depends(require_authenticated),
):
    service = _service(request)
    result = await service.apply_confirmation(
        payload.flow_instance_id,
        payload.step,
        payload.action,
        payload.rationale,
        payload.metadata,
    )
    return ConfirmationActionResponse(
        flow_instance_id=payload.flow_instance_id,
        step=payload.step,
        action=payload.action,
        accepted=result["accepted"],
        message=result["message"],
        next_step=result["next_step"],
    )


@router.get("/{flow_instance_id}/status", response_model=CompletionStatusResponse)
async def completion_status(flow_instance_id: str, request: Request, _ctx=Depends(require_authenticated)):
    service = _service(request)
    status = await service.completion_status(flow_instance_id)
    return CompletionStatusResponse(flow_instance_id=flow_instance_id, **status)
