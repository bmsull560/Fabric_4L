"""Workflow API routes - OpenAPI spec compliant.

Implements the workflow API as specified in value_fabric_backend_logic_specifications.md:
- POST /api/v1/workflows - Submit workflow
- GET /api/v1/workflows/{instance_id} - Get status
- GET /api/v1/workflows/{instance_id}/events - Event streaming
- DELETE /api/v1/workflows/{instance_id} - Cancel workflow
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json

from ...engine.executor import OrchestrationController, WorkflowExecutionError
from ...engine.scheduler import TaskPriority
from ...models.agent_state import WorkflowStatus
from ...workflows import list_workflow_types
from ...tenant.context import get_current_tenant, TenantContext
from shared.identity.dependencies import require_authenticated
from shared.identity.context import RequestContext


router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models (OpenAPI Spec Compliant)
# ============================================================================

class WorkflowInputs(BaseModel):
    """Workflow inputs wrapper per spec."""
    prospect_id: Optional[str] = None
    prospect_company: Optional[str] = None
    use_case_ids: Optional[List[str]] = None
    prospect_metrics: Optional[Dict[str, Any]] = None
    custom_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WorkflowCreateRequest(BaseModel):
    """Request to submit a new workflow - OpenAPI spec compliant.
    
    Spec requires:
    - workflow_type: enum [whitespace_analysis, business_case_generation]
    - tenant_id: string
    - user_id: string
    - inputs: object
    """
    workflow_type: str = Field(
        ...,
        description="Type of workflow to run",
        enum=["roi_calculator", "whitespace_analysis", "business_case", "orchestrator"]
    )
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str = Field(..., description="User identifier")
    inputs: WorkflowInputs = Field(default_factory=WorkflowInputs, description="Workflow inputs")
    priority: str = Field(default="NORMAL", description="Execution priority")
    workflow_id: Optional[str] = Field(None, description="Optional workflow ID")


class WorkflowCreateResponse(BaseModel):
    """Response from workflow creation - OpenAPI spec compliant.
    
    Spec requires:
    - workflow_instance_id: string
    - status: string
    - estimated_duration_seconds: integer
    """
    workflow_instance_id: str = Field(..., alias="workflow_instance_id")
    status: str = Field(..., description="Workflow status")
    estimated_duration_seconds: int = Field(default=300, description="Estimated execution time")
    
    class Config:
        populate_by_name = True


class WorkflowStatusResponse(BaseModel):
    """Workflow status response - OpenAPI spec compliant.
    
    Spec requires:
    - workflow_instance_id: string
    - workflow_type: string
    - status: string
    - current_state: string
    - progress_percentage: number
    - started_at: datetime
    - completed_at: datetime
    - results: object
    """
    workflow_instance_id: str = Field(..., alias="workflow_instance_id")
    workflow_type: str
    status: str
    current_state: Optional[str] = Field(None, alias="current_state")
    current_node: Optional[str] = None
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, alias="progress_percentage")
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_count: int = 0
    has_output: bool = False
    results: Optional[Dict[str, Any]] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    priority: Optional[int] = None
    scheduler_status: Optional[str] = None
    
    class Config:
        populate_by_name = True


class WorkflowEvent(BaseModel):
    """Workflow event for streaming.
    
    Spec requires:
    - event_id: string
    - event_type: string
    - timestamp: datetime
    - message: string
    """
    event_id: str
    event_type: str
    timestamp: str
    message: str
    payload: Optional[Dict[str, Any]] = None


class WorkflowResumeRequest(BaseModel):
    """Request to resume a paused or interrupted workflow.
    
    Supports human-in-the-loop workflows where execution pauses
    for user input or approval, then resumes with decision data.
    """
    user_id: str = Field(..., description="User resuming the workflow")
    resume_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Optional user decision/input data"
    )
    tenant_id: Optional[str] = None


class WorkflowResumeResponse(BaseModel):
    """Response from workflow resume."""
    workflow_instance_id: str = Field(..., alias="workflow_instance_id")
    status: str = Field(..., description="resumed, completed, or failed")
    resumed_from_node: Optional[str] = Field(
        None,
        description="Node from which execution resumed"
    )
    message: str
    estimated_completion_seconds: int = Field(default=60)

    class Config:
        populate_by_name = True


class WorkflowPauseRequest(BaseModel):
    """Request to pause a running workflow."""
    user_id: str = Field(..., description="User pausing the workflow")
    reason: Optional[str] = Field(None, description="Reason for pausing")
    tenant_id: Optional[str] = None


class WorkflowPauseResponse(BaseModel):
    """Response from workflow pause."""
    workflow_instance_id: str = Field(..., alias="workflow_instance_id")
    status: str = Field(..., description="paused")
    paused_at: str = Field(..., description="ISO timestamp when paused")
    current_node: Optional[str] = Field(None, description="Current node when paused")
    message: str

    class Config:
        populate_by_name = True


def get_executor() -> OrchestrationController:
    """Get workflow executor instance."""
    from .main import workflow_executor
    if workflow_executor is None:
        raise HTTPException(status_code=503, detail="Workflow executor not initialized")
    return workflow_executor


@router.post("/workflows", response_model=WorkflowCreateResponse, status_code=201)
async def create_workflow(
    request: WorkflowCreateRequest,
    executor: OrchestrationController = Depends(get_executor)
) -> WorkflowCreateResponse:
    """Create and execute a new workflow - OpenAPI spec compliant.
    
    Example:
        POST /v1/workflows
        {
            "workflow_type": "roi_calculator",
            "tenant_id": "tenant-001",
            "user_id": "user-001",
            "inputs": {
                "prospect_id": "prospect-001",
                "use_case_ids": ["uc-001", "uc-002"]
            },
            "priority": "HIGH"
        }
    
    Returns:
        201 Created with workflow_instance_id and estimated duration
    """
    try:
        # Map priority string to enum
        priority_map = {
            "CRITICAL": TaskPriority.CRITICAL,
            "HIGH": TaskPriority.HIGH,
            "NORMAL": TaskPriority.NORMAL,
            "LOW": TaskPriority.LOW,
            "BACKGROUND": TaskPriority.BACKGROUND,
        }
        priority = priority_map.get(request.priority.upper(), TaskPriority.NORMAL)
        
        # Convert inputs to dict for execution
        input_data = request.inputs.dict(exclude_none=True) if request.inputs else {}
        
        # Execute workflow (async - returns immediately with scheduled task)
        result = await executor.execute_workflow(
            workflow_type=request.workflow_type,
            input_data=input_data,
            workflow_id=request.workflow_id,
            priority=priority,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
        )
        
        # Estimate duration based on workflow type
        estimated_duration = {
            "roi_calculator": 120,
            "whitespace_analysis": 300,
            "business_case": 400,
            "orchestrator": 180,
        }.get(request.workflow_type, 300)
        
        return WorkflowCreateResponse(
            workflow_instance_id=result.workflow_id,
            status=result.status.value if hasattr(result.status, 'value') else str(result.status),
            estimated_duration_seconds=estimated_duration,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    executor: OrchestrationController = Depends(get_executor)
) -> WorkflowStatusResponse:
    """Get status of a workflow - OpenAPI spec compliant.
    
    Returns detailed status including:
    - progress_percentage (0-100)
    - current_state
    - tenant_id, user_id
    """
    status = await executor.get_workflow_status(workflow_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return WorkflowStatusResponse(
        workflow_instance_id=status.get("workflow_id", workflow_id),
        workflow_type=status.get("workflow_type", "unknown"),
        status=status.get("status", "unknown"),
        current_state=status.get("current_node"),
        current_node=status.get("current_node"),
        progress_percentage=status.get("progress_percentage", 0.0),
        started_at=status.get("started_at"),
        completed_at=status.get("completed_at"),
        error_count=status.get("error_count", 0),
        has_output=status.get("has_output", False),
        results=status.get("output"),
        tenant_id=status.get("tenant_id"),
        user_id=status.get("user_id"),
        priority=status.get("priority"),
        scheduler_status=status.get("scheduler_status"),
    )


@router.get("/workflows/{workflow_id}/result")
async def get_workflow_result(
    workflow_id: str,
    executor: OrchestrationController = Depends(get_executor)
) -> Dict[str, Any]:
    """Get result of a completed workflow."""
    status = await executor.get_workflow_status(workflow_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    if status.get("status") not in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Workflow {workflow_id} not complete (status: {status.get('status')})"
        )
    
    return {
        "workflow_id": workflow_id,
        "status": status.get("status"),
        "output": status.get("output"),
        "errors": status.get("errors", []),
        "completed_at": status.get("completed_at"),
    }


@router.delete("/workflows/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    executor: OrchestrationController = Depends(get_executor)
) -> Dict[str, Any]:
    """Cancel a running workflow - OpenAPI spec compliant (DELETE method)."""
    cancelled = await executor.cancel_workflow(workflow_id)
    
    if not cancelled:
        raise HTTPException(status_code=400, detail=f"Workflow {workflow_id} could not be cancelled")
    
    return {"workflow_id": workflow_id, "status": "cancelled"}


@router.post("/workflows/{workflow_id}/resume", response_model=WorkflowResumeResponse)
async def resume_workflow(
    workflow_id: str,
    request: WorkflowResumeRequest,
    executor: OrchestrationController = Depends(get_executor)
) -> WorkflowResumeResponse:
    """Resume a paused or interrupted workflow from its last checkpoint.
    
    This endpoint enables human-in-the-loop workflows by allowing execution
    to pause for user input/decisions, then resume from the exact point
    where it stopped.
    
    The workflow state is loaded from Postgres checkpoint storage, and
    execution continues from the last completed node.
    
    Example:
        POST /v1/workflows/wf-123/resume
        {
            "user_id": "user-001",
            "resume_data": {"approved": true, "notes": "Proceed with ROI calc"}
        }
    
    Returns:
        200 OK - Workflow resumed and running (or completed if fast)
        404 Not Found - Workflow not found or no checkpoint exists
        400 Bad Request - Workflow not in resumable state (completed/failed/cancelled)
        503 Service Unavailable - Checkpointing not configured
    """
    # Verify checkpointing is available
    if executor.checkpoint_saver is None:
        raise HTTPException(
            status_code=503, 
            detail="Checkpointing not configured - cannot resume workflows"
        )
    
    # Check current status
    status = await executor.get_workflow_status(workflow_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    if status.get("status") in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Workflow {workflow_id} is {status.get('status')} and cannot be resumed"
        )
    
    # Resume execution
    try:
        result = await executor.resume_workflow(
            workflow_id=workflow_id,
            user_id=request.user_id,
            resume_data=request.resume_data,
        )
        
        # Determine response status based on result
        result_status = str(result.status.value if hasattr(result.status, 'value') else result.status)
        is_complete = result_status in ["completed", "failed"]
        
        return WorkflowResumeResponse(
            workflow_instance_id=workflow_id,
            status=result_status if is_complete else "resumed",
            resumed_from_node=status.get("current_node"),
            message=(
                f"Workflow {'completed' if is_complete else 'resumed'} "
                f"from node: {status.get('current_node', 'unknown')}"
            ),
            estimated_completion_seconds=0 if is_complete else 60,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkflowExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error resuming workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")


@router.post("/workflows/{workflow_id}/pause", response_model=WorkflowPauseResponse)
async def pause_workflow(
    workflow_id: str,
    request: WorkflowPauseRequest,
    executor: OrchestrationController = Depends(get_executor)
) -> WorkflowPauseResponse:
    """Pause a running workflow.

    This endpoint pauses workflow execution at the current node.
    The workflow can be resumed later using the resume endpoint.

    Example:
        POST /v1/workflows/wf-123/pause
        {
            "user_id": "user-001",
            "reason": "Human review required"
        }

    Returns:
        200 OK - Workflow paused
        404 Not Found - Workflow not found
        400 Bad Request - Workflow not in pausable state (completed/failed/cancelled)
        503 Service Unavailable - Workflow executor not available
    """
    # Check current status
    status = await executor.get_workflow_status(workflow_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    current_status = status.get("status")
    if current_status in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow {workflow_id} is {current_status} and cannot be paused"
        )

    if current_status == "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Workflow {workflow_id} is already paused"
        )

    # Pause execution
    try:
        paused = await executor.pause_workflow(
            workflow_id=workflow_id,
            user_id=request.user_id,
            reason=request.reason,
        )

        if not paused:
            raise HTTPException(status_code=500, detail="Failed to pause workflow")

        return WorkflowPauseResponse(
            workflow_instance_id=workflow_id,
            status="paused",
            paused_at=datetime.utcnow().isoformat(),
            current_node=status.get("current_node"),
            message=f"Workflow paused at node: {status.get('current_node', 'unknown')}",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error pausing workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to pause workflow: {str(e)}")


@router.get("/workflows/types")
async def list_available_workflows() -> Dict[str, Any]:
    """List available workflow types."""
    types = list_workflow_types()
    
    return {
        "workflows": [
            {
                "type": key,
                "name": info["name"],
                "description": info["description"]
            }
            for key, info in types.items()
        ]
    }


@router.get("/workflows/active")
async def list_active_workflows(
    request: Request,
    _ctx: RequestContext = Depends(require_authenticated),
    executor: OrchestrationController = Depends(get_executor)
) -> List[Dict[str, Any]]:
    """List currently active workflows for the authenticated tenant."""
    tenant = get_current_tenant()
    if not tenant or not tenant.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")
    
    active = await executor.list_active_workflows(tenant_id=tenant.tenant_id)
    return active


@router.get("/workflows/{workflow_id}/events")
async def get_workflow_events(
    workflow_id: str,
    executor: OrchestrationController = Depends(get_executor),
    _ctx: RequestContext = Depends(require_authenticated),
) -> StreamingResponse:
    """Get workflow events via Server-Sent Events (SSE).
    
    Streams real-time workflow progress events.
    
    Example:
        GET /v1/workflows/{id}/events
        
        Event: workflow_event
        data: {"event_id": "...", "event_type": "node_started", ...}
    """
    async def event_generator():
        """Generate SSE events for workflow."""
        last_status = None
        
        while True:
            # Get current status
            status = await executor.get_workflow_status(workflow_id)
            
            if not status:
                yield f"event: error\ndata: {json.dumps({'message': 'Workflow not found'})}\n\n"
                break
            
            # Send event if status changed
            if status != last_status:
                event = WorkflowEvent(
                    event_id=f"evt-{datetime.utcnow().timestamp()}",
                    event_type="status_update",
                    timestamp=datetime.utcnow().isoformat(),
                    message=f"Workflow status: {status.get('status')}",
                    payload={
                        "workflow_id": workflow_id,
                        "status": status.get("status"),
                        "progress": status.get("progress_percentage"),
                        "current_node": status.get("current_node"),
                    }
                )
                
                yield f"event: workflow_event\ndata: {json.dumps(event.dict())}\n\n"
                
                last_status = status
            
            # Check if workflow is complete
            if status.get("status") in ["completed", "failed", "cancelled"]:
                # Send completion event
                event = WorkflowEvent(
                    event_id=f"evt-{datetime.utcnow().timestamp()}",
                    event_type="workflow_complete",
                    timestamp=datetime.utcnow().isoformat(),
                    message=f"Workflow {status.get('status')}",
                    payload={"workflow_id": workflow_id, "status": status.get("status")},
                )
                yield f"event: workflow_event\ndata: {json.dumps(event.dict())}\n\n"
                break
            
            # Wait before next poll
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
