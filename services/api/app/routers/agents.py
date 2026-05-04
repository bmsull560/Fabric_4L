from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.core.tenant_context import tenant_required
from app.core.database import db
from app.models.schemas import AgentRun
from app.services.agent_orchestrator import orchestrator

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("/runs", response_model=AgentRun)
async def create_agent_run(payload: dict, tenant_id: str = Depends(tenant_required)):
    run = orchestrator.create_run(
        tenant_id=tenant_id,
        workflow_type=payload.get("workflow_type", "unknown"),
        account_id=payload.get("account_id"),
        input_data=payload.get("input"),
    )
    return run


@router.get("/runs/{run_id}", response_model=AgentRun)
async def get_agent_run(run_id: str, tenant_id: str = Depends(tenant_required)):
    run = db.agent_runs.get(run_id, tenant_id=tenant_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@router.post("/runs/{run_id}/resume", response_model=AgentRun)
async def resume_agent_run(run_id: str, tenant_id: str = Depends(tenant_required)):
    run = db.agent_runs.get(run_id, tenant_id=tenant_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return orchestrator.resume_run(run_id)


@router.post("/runs/{run_id}/cancel", response_model=AgentRun)
async def cancel_agent_run(run_id: str, tenant_id: str = Depends(tenant_required)):
    run = db.agent_runs.get(run_id, tenant_id=tenant_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return orchestrator.cancel_run(run_id)
