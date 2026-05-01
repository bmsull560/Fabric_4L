"""Orchestration Controller - Enhanced workflow execution engine.

Provides comprehensive workflow orchestration with:
- Multi-agent coordination
- Task scheduling with priorities
- Backpressure handling
- Message-based agent communication
- Failure recovery

This implements the OrchestrationController agent type from the specification.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from langgraph.checkpoint.base import BaseCheckpointSaver

from ..models.agent_state import AgentState, WorkflowStatus


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""

    pass


from ..agents.base import BaseAgent
from ..messaging.bus import InMemoryMessageBus, MessageBus
from ..messaging.router import MessageRouter
from ..messaging.types import MessageType
from ..registry.service import resolve_llm_model
from ..tools.registry import ToolRegistry
from ..workflows import create_workflow
from .scheduler import ScheduledTask, TaskPriority, TaskScheduler
from .state_manager import StateManager
from shared.models.typed_dict import TypedDictModel


class OrchestrationController_get_resultResult(TypedDictModel):
    completed_at: Any
    created_at: Any
    metadata: Any
    output: dict[str, Any]
    started_at: Any
    status: Any
    workflow_id: Any

class OrchestrationController_get_workflow_statusResult(TypedDictModel):
    completed_at: Any
    current_node: Any
    error_count: Any
    estimated_duration_seconds: Any
    has_output: Any
    priority: Any
    progress_percentage: Any
    scheduler_status: Any
    started_at: Any
    status: Any
    tenant_id: Any
    user_id: Any
    workflow_id: Any
    workflow_type: Any

class OrchestrationController_get_cluster_healthResult(TypedDictModel):
    active_workflows: Any
    avg_load: Any
    pending_tasks: Any
    registered_agents: Any
    running_tasks: Any
    status: Any
    utilization: Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM Cost Metrics Integration Snippet
# ---------------------------------------------------------------------------
# When making LLM calls in tools (e.g., generation_tools.py), record cost
# and token usage via the Prometheus metrics helper:
#
#     from ..metrics import get_metrics
#     from ..metrics.llm_cost_calculator import LLMCostCalculator
#
#     calculator = LLMCostCalculator()
#     cost = calculator.calculate_cost(
#         provider="openai",
#         model="gpt-4o",
#         prompt_tokens=response.usage.prompt_tokens,
#         completion_tokens=response.usage.completion_tokens,
#     )
#     metrics = get_metrics()
#     if metrics:
#         metrics.record_llm_cost(
#             provider="openai",
#             model="gpt-4o",
#             tenant_id=str(tenant_id),
#             cost=cost,
#             prompt_tokens=response.usage.prompt_tokens,
#             completion_tokens=response.usage.completion_tokens,
#             status="success",
#         )
# ---------------------------------------------------------------------------


class OrchestrationController:
    """Enhanced workflow executor with multi-agent orchestration.

    Implements the OrchestrationController from the specification:
    - workflow_scheduling: Schedule workflows with priority
    - task_distribution: Distribute tasks to agents
    - failure_recovery: Handle failures with retry
    - resource_management: Manage agent pool scaling

    Scaling Policy: min_instances=2, max_instances=50

    Example:
        controller = OrchestrationController(
            tool_registry=tool_registry,
            message_bus=message_bus,
        )
        await controller.start()

        # Execute workflow
        result = await controller.execute_workflow(
            workflow_type="roi_calculator",
            input_data={"prospect_id": "123", ...},
            priority=TaskPriority.HIGH,
        )
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        state_manager: StateManager | None = None,
        message_bus: MessageBus | None = None,
        max_concurrent: int = 100,
        scaling_config: dict[str, Any] | None = None,
        checkpoint_saver: BaseCheckpointSaver | None = None,
    ):
        """Initialize orchestration controller.

        Args:
            tool_registry: Registry of available tools
            state_manager: State persistence manager
            message_bus: Message bus for agent communication
            max_concurrent: Maximum concurrent tasks
            scaling_config: Scaling policy configuration
            checkpoint_saver: LangGraph checkpoint saver for workflow persistence
        """
        self.tool_registry = tool_registry
        self.state_manager = state_manager or StateManager()
        self.message_bus = message_bus or InMemoryMessageBus()
        self.checkpoint_saver = checkpoint_saver
        self.max_concurrent = max_concurrent

        # Scaling configuration per spec
        self.scaling_config = scaling_config or {
            "min_instances": 2,
            "max_instances": 50,
            "scale_trigger": "queue_depth > 100",
        }

        # Task scheduling
        self.scheduler = TaskScheduler(max_concurrent_tasks=max_concurrent)
        self.scheduler.set_callbacks(
            on_complete=self._on_task_complete,
            on_fail=self._on_task_fail,
        )

        # Message routing
        self.message_router = MessageRouter(self.message_bus)

        # Agent management
        self._registered_agents: dict[str, BaseAgent] = {}
        self._agent_pool: dict[str, dict[str, Any]] = {}

        # Workflow tracking
        self._active_workflows: dict[str, asyncio.Task] = {}
        self._workflow_metadata: dict[str, dict[str, Any]] = {}

        # Lifecycle
        self._started = False
        self._shutdown = False

    async def start(self) -> None:
        """Start the orchestration controller."""
        if self._started:
            return

        await self.scheduler.start()
        self._started = True
        logger.info("OrchestrationController started")

    async def stop(self) -> None:
        """Stop the orchestration controller."""
        if not self._started:
            return

        self._shutdown = True

        # Cancel active workflows
        for workflow_id, task in list(self._active_workflows.items()):
            task.cancel()

        # Stop scheduler
        await self.scheduler.stop()

        # Close message bus
        await self.message_bus.close()

        self._started = False
        logger.info("OrchestrationController stopped")

    async def resolve_model(self, tenant_id: UUID, provider: str = "openai") -> str:
        """Resolve the active production LLM model for a tenant.

        Falls back to ``os.getenv('LLM_MODEL', 'gpt-4o')`` if no production
        model is registered or the lookup fails.
        """
        import os

        try:
            from ..database import db_session_for_context
            from shared.identity.context import RequestContext

            context = RequestContext(tenant_id=tenant_id)
            async with db_session_for_context(context) as db:
                return await resolve_llm_model(db, tenant_id, provider)
        except Exception:
            return os.getenv("LLM_MODEL", "gpt-4o")

    async def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the controller.

        Args:
            agent: Agent instance to register
        """
        await agent.initialize()

        self._registered_agents[agent.agent_id] = agent

        # Register with message router
        capabilities = agent.get_capabilities()
        capability_names = [c.name for c in capabilities]

        self.message_router.register_agent(
            agent_id=agent.agent_id,
            capabilities=capability_names,
            metadata={"agent_type": agent.agent_type},
        )

        # Subscribe to task assignments
        await self.message_bus.subscribe(
            subscriber_id=agent.agent_id,
            message_type=MessageType.TASK_ASSIGNMENT,
            handler=self._create_agent_handler(agent),
        )

        logger.info(f"Registered agent {agent.agent_id} ({agent.agent_type})")

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent.

        Args:
            agent_id: Agent to unregister
        """
        if agent_id in self._registered_agents:
            del self._registered_agents[agent_id]
            self.message_router.unregister_agent(agent_id)
            logger.info(f"Unregistered agent {agent_id}")

    async def execute_workflow(
        self,
        workflow_type: str,
        input_data: dict[str, Any],
        workflow_id: str | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        tenant_id: str | None = None,
        user_id: str | None = None,
        checkpoint_interval: int = 5,
    ) -> AgentState:
        """Execute a workflow with orchestration.

        Args:
            workflow_type: Type of workflow to run
            input_data: Workflow input parameters
            workflow_id: Optional workflow ID
            priority: Execution priority
            tenant_id: Tenant context
            user_id: User context
            checkpoint_interval: Save state every N nodes

        Returns:
            Final workflow state

        Raises:
            ConcurrencyLimitExceeded: If max concurrent workflows reached (P1-42)
            WorkflowTimeoutError: If workflow exceeds global timeout (P1-25)
        """
        # P1-42: Check concurrent workflow limit
        active_count = len(self._active_workflows)
        if active_count >= self.max_concurrent:
            from ..exceptions import ConcurrencyLimitExceeded
            raise ConcurrencyLimitExceeded(
                f"Maximum concurrent workflows ({self.max_concurrent}) exceeded. "
                f"Current active: {active_count}. Retry after existing workflows complete."
            )

        # Create workflow with checkpointing if available
        workflow = create_workflow(workflow_type, self.tool_registry, self.checkpoint_saver)
        initial_state = workflow.create_initial_state(input_data)
        workflow_id = workflow_id or initial_state.workflow_id

        # Store metadata with timeout tracking
        from ..config.settings import settings
        self._workflow_metadata[workflow_id] = {
            "workflow_type": workflow_type,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "priority": priority.value,
            "started_at": datetime.now(UTC).isoformat(),
            "timeout_seconds": settings.workflow_timeout_seconds,  # P1-25
        }

        # Schedule workflow execution (Task 2.1: Capture tenant context)
        task = ScheduledTask(
            priority=priority.value,
            scheduled_time=datetime.now(UTC),
            task_id=f"wf-{workflow_id}",
            workflow_instance_id=workflow_id,
            capability="workflow_execution",
            agent_type="OrchestrationController",
            context={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "workflow_type": workflow_type,
            },
            parameters={
                "workflow": workflow,
                "initial_state": initial_state,
                "workflow_id": workflow_id,
                "checkpoint_interval": checkpoint_interval,
            },
            tenant_id=tenant_id,
            tenant_context={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "workflow_type": workflow_type,
                "auth_source": "workflow_execution",
            },
        )

        await self.scheduler.schedule_task(task)

        # P1-25: Wait for completion with global timeout
        return await self._wait_for_workflow_with_timeout(
            workflow_id, timeout_seconds=settings.workflow_timeout_seconds
        )

    async def run(
        self,
        workflow_type: str,
        input_data: dict[str, Any],
        workflow_id: str | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        tenant_id: str | None = None,
        user_id: str | None = None,
        checkpoint_interval: int = 5,
    ) -> AgentState:
        """Backward-compatible workflow entrypoint.

        Routes and older callers historically used ``run(...)``. This method
        delegates to ``execute_workflow(...)`` so all call sites share the
        same durable orchestration path.
        """
        return await self.execute_workflow(
            workflow_type=workflow_type,
            input_data=input_data,
            workflow_id=workflow_id,
            priority=priority,
            tenant_id=tenant_id,
            user_id=user_id,
            checkpoint_interval=checkpoint_interval,
        )

    async def get_result(self, workflow_id: str) -> dict[str, Any] | None:
        """Get a durable workflow result by workflow ID.

        Reads persisted workflow state via ``StateManager`` and returns a
        route-friendly shape used by analysis/tools endpoints.
        """
        state = await self.state_manager.load_state(workflow_id)
        if not state:
            return None

        persisted_metadata = dict(state.metadata or {})
        if "workflow_id" not in persisted_metadata:
            persisted_metadata["workflow_id"] = state.workflow_id
        if "workflow_type" not in persisted_metadata:
            persisted_metadata["workflow_type"] = (
                state.workflow_type.value
                if hasattr(state.workflow_type, "value")
                else str(state.workflow_type)
            )

        return OrchestrationController_get_resultResult.model_validate({
            "workflow_id": state.workflow_id,
            "output": dict(state.output_data or {}),
            "metadata": persisted_metadata,
            "status": state.status.value if hasattr(state.status, "value") else str(state.status),
            "created_at": state.started_at.isoformat() if state.started_at else None,
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
        })


    async def schedule_workflow(
        self,
        workflow_type: str,
        input_data: dict[str, Any],
        scheduled_time: datetime | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """Schedule workflow for future execution.

        Args:
            workflow_type: Type of workflow
            input_data: Input parameters
            scheduled_time: When to execute (default: now)
            priority: Execution priority
            tenant_id: Tenant context
            user_id: User context

        Returns:
            schedule_id: ID for tracking
        """
        schedule_id = f"sched-{datetime.now(UTC).timestamp()}"

        execute_time = scheduled_time or datetime.now(UTC)

        # Create scheduled task
        task = ScheduledTask(
            priority=priority.value,
            scheduled_time=execute_time,
            task_id=schedule_id,
            workflow_instance_id=schedule_id,
            capability="workflow_execution",
            agent_type="OrchestrationController",
            context={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "workflow_type": workflow_type,
            },
            parameters={
                "workflow_type": workflow_type,
                "input_data": input_data,
                "tenant_id": tenant_id,
                "user_id": user_id,
            },
        )

        await self.scheduler.schedule_task(task)

        logger.info(f"Scheduled workflow {schedule_id} for {execute_time}")
        return schedule_id

    async def distribute_task(
        self,
        capability: str,
        parameters: dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        tenant_id: str | None = None,
        timeout_seconds: int = 300,
    ) -> str | None:
        """Distribute task to appropriate agent.

        Args:
            capability: Required capability
            parameters: Task parameters
            priority: Task priority
            tenant_id: Tenant context
            timeout_seconds: Task timeout

        Returns:
            task_id: ID of scheduled task, or None if no agent available
        """
        # Route to agent
        agent_id = self.message_router.route_task(capability)

        if not agent_id:
            logger.warning(f"No agent available for capability: {capability}")
            return None

        # Create and schedule task
        task_id = f"task-{datetime.now(UTC).timestamp()}"

        task = ScheduledTask(
            priority=priority.value,
            scheduled_time=datetime.now(UTC),
            task_id=task_id,
            workflow_instance_id=task_id,
            capability=capability,
            agent_type=self._registered_agents.get(agent_id, {}).get("agent_type", "Unknown"),
            context={"tenant_id": tenant_id},
            parameters=parameters,
            timeout_seconds=timeout_seconds,
        )

        await self.scheduler.schedule_task(task)

        # Send task assignment via message bus
        await self.message_bus.publish(
            agent_id="orchestrator",
            event_type=MessageType.TASK_ASSIGNMENT,
            payload={
                "task_id": task_id,
                "capability": capability,
                "parameters": parameters,
            },
            recipient_id=agent_id,
        )

        return task_id

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get workflow status with orchestration context.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Status dict with progress information
        """
        # Get base state
        state = await self.state_manager.load_state(workflow_id)
        if not state:
            return None

        # Get scheduler status
        scheduler_status = await self.scheduler.get_task_status(f"wf-{workflow_id}")

        # Get metadata
        metadata = self._workflow_metadata.get(workflow_id, {})

        return OrchestrationController_get_workflow_statusResult.model_validate({
            "workflow_id": workflow_id,
            "workflow_type": state.workflow_type.value
            if hasattr(state.workflow_type, "value")
            else str(state.workflow_type),
            "status": state.status.value if hasattr(state.status, "value") else str(state.status),
            "current_node": state.current_node,
            "progress_percentage": self._calculate_progress(state),
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "estimated_duration_seconds": metadata.get("estimated_duration"),
            "error_count": len(state.errors),
            "has_output": bool(state.output_data),
            "tenant_id": metadata.get("tenant_id"),
            "user_id": metadata.get("user_id"),
            "priority": metadata.get("priority"),
            "scheduler_status": scheduler_status.get("status") if scheduler_status else None,
        })


    async def cancel_workflow(self, workflow_id: str, reason: str | None = None) -> bool:
        """Cancel a workflow.

        Args:
            workflow_id: Workflow to cancel
            reason: Optional reason for cancellation (logged for audit)

        Returns:
            True if cancelled
        """
        # Log cancellation reason for audit trail
        if reason:
            logger.info(f"Cancelling workflow {workflow_id}: {reason}")

        # Cancel in scheduler
        cancelled = await self.scheduler.cancel_task(f"wf-{workflow_id}")

        # Cancel active task
        if workflow_id in self._active_workflows:
            task = self._active_workflows[workflow_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Update state
        state = await self.state_manager.load_state(workflow_id)
        if state:
            state.status = WorkflowStatus.CANCELLED
            state.completed_at = datetime.now(UTC)
            await self.state_manager.save_state(workflow_id, state)

        return cancelled

    async def archive_workflow(self, workflow_id: str) -> bool:
        """Archive a workflow.

        Args:
            workflow_id: Workflow to archive

        Returns:
            True if archived
        """
        logger.info(f"Archiving workflow {workflow_id}")

        # Update state metadata
        state = await self.state_manager.load_state(workflow_id)
        if state:
            state.metadata["archived"] = True
            state.metadata["archived_at"] = datetime.now(UTC).isoformat()
            await self.state_manager.save_state(workflow_id, state)
            return True

        return False

    async def resume_workflow(
        self,
        workflow_id: str,
        user_id: str,
        resume_data: dict[str, Any] | None = None,
    ) -> AgentState:
        """Resume a workflow from its last checkpoint.

        Reloads workflow state from checkpoint storage and continues execution
        from the last completed node. Supports human-in-the-loop workflows where
        execution pauses for user input/decisions.

        Args:
            workflow_id: Workflow to resume
            user_id: User initiating resume
            resume_data: Optional user input/decision data to merge into state

        Returns:
            Final or updated workflow state

        Raises:
            WorkflowExecutionError: If workflow not found, completed, or resume fails
        """
        # Load existing state
        state = await self.state_manager.load_state(workflow_id)
        if not state:
            raise WorkflowExecutionError(f"No state found for workflow {workflow_id}")

        # Check if workflow is in a resumable state
        # PAUSED, RUNNING, PENDING, and INTERRUPTED workflows can be resumed
        if state.status not in [
            WorkflowStatus.PAUSED,
            WorkflowStatus.RUNNING,
            WorkflowStatus.PENDING,
            WorkflowStatus.INTERRUPTED,
        ]:
            raise WorkflowExecutionError(
                f"Workflow {workflow_id} is {state.status.value} and cannot be resumed. "
                f"Only PAUSED, RUNNING, PENDING, or INTERRUPTED workflows can be resumed."
            )

        # Validate workflow_id matches state
        if state.workflow_id != workflow_id:
            raise WorkflowExecutionError(
                f"Workflow ID mismatch: requested {workflow_id} but state has {state.workflow_id}"
            )

        # Merge resume data into state if provided
        # Store in output_data to avoid mutating original input_data
        if resume_data:
            if state.output_data is None:
                state.output_data = {}
            state.output_data["resume_decision"] = resume_data
            state.output_data["resumed_by"] = user_id
            state.output_data["resumed_at"] = datetime.now(UTC).isoformat()

        # Get workflow type from metadata
        metadata = self._workflow_metadata.get(workflow_id, {})
        workflow_type = metadata.get("workflow_type")

        if not workflow_type:
            raise WorkflowExecutionError(f"No workflow type found for {workflow_id}")

        # Re-create workflow with checkpoint saver
        workflow = create_workflow(workflow_type, self.tool_registry, self.checkpoint_saver)

        # Update metadata
        metadata["resumed_at"] = datetime.now(UTC).isoformat()
        metadata["resumed_by"] = user_id

        # Resume execution - LangGraph will load from checkpoint via thread_id
        # The workflow continues from where it left off
        try:
            result = await workflow.run(state, thread_id=workflow_id)
        except WorkflowExecutionError:
            raise
        except Exception as e:
            raise WorkflowExecutionError(
                f"Failed to resume workflow {workflow_id}: {e}"
            ) from e

        return result

    async def list_active_workflows(
        self,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List active workflows.

        Args:
            tenant_id: Filter by tenant

        Returns:
            List of workflow status dicts
        """
        active = []

        for workflow_id, metadata in self._workflow_metadata.items():
            if tenant_id and metadata.get("tenant_id") != tenant_id:
                continue

            status = await self.get_workflow_status(workflow_id)
            if status and status.get("status") in ["pending", "running", "retrying"]:
                active.append(status)

        return active

    def get_cluster_health(self) -> dict[str, Any]:
        """Get orchestration cluster health.

        Returns:
            Health metrics
        """
        router_health = self.message_router.get_cluster_health()
        scheduler_stats = self.scheduler.get_stats()

        return OrchestrationController_get_cluster_healthResult.model_validate({
            "status": router_health.get("status", "unknown"),
            "registered_agents": len(self._registered_agents),
            "active_workflows": len(self._active_workflows),
            "pending_tasks": scheduler_stats.get("pending_tasks", 0),
            "running_tasks": scheduler_stats.get("running_tasks", 0),
            "avg_load": router_health.get("avg_load", 0),
            "utilization": scheduler_stats.get("utilization", 0),
        })


    async def recover_workflows(self) -> list[dict[str, Any]]:
        """On startup, identify and handle orphaned workflows from previous pod.
        
        Called during application startup to find workflows that were RUNNING/PENDING
        in Redis but not in this pod's memory. Marks them as INTERRUPTED for
        manual review or auto-resume.
        
        Returns:
            List of recovered workflow IDs with status
        """
        logger.info("Scanning for orphaned workflows to recover...")
        
        # Get active workflows from Redis that aren't in our memory
        orphaned_ids = await self.state_manager.list_active_workflows()
        recovered = []
        
        for workflow_id in orphaned_ids:
            # Skip if this workflow is already in our active workflows
            if workflow_id in self._active_workflows:
                continue
            
            try:
                state = await self.state_manager.load_state(workflow_id)
                if not state:
                    continue
                
                # Mark as INTERRUPTED with recovery information
                state.status = WorkflowStatus.INTERRUPTED
                state.errors.append(
                    f"Workflow interrupted by pod restart at {datetime.now(UTC).isoformat()}. "
                    "Resume manually or via API."
                )
                await self.state_manager.save_state(workflow_id, state)
                
                recovered.append({
                    "workflow_id": workflow_id,
                    "workflow_type": state.workflow_type.value if hasattr(state.workflow_type, "value") else str(state.workflow_type),
                    "status": state.status.value,
                    "previous_status": "RUNNING",
                    "current_node": state.current_node,
                    "recovery_available": True,
                })
                
                logger.warning(
                    f"Marked orphaned workflow {workflow_id} as INTERRUPTED "
                    f"(was at node: {state.current_node})"
                )
                
            except Exception as e:
                logger.error(f"Failed to recover workflow {workflow_id}: {e}")
                recovered.append({
                    "workflow_id": workflow_id,
                    "status": "ERROR",
                    "error": str(e),
                })
        
        if recovered:
            logger.info(f"Recovery complete: {len(recovered)} workflows marked as INTERRUPTED")
        else:
            logger.info("No orphaned workflows found")
        
        return recovered

    def _create_agent_handler(
        self,
        agent: BaseAgent,
    ) -> Callable:
        """Create message handler for an agent.

        Args:
            agent: Agent to handle messages

        Returns:
            Handler function
        """

        async def handler(message):
            if message.message_type == MessageType.TASK_ASSIGNMENT:
                payload = message.payload
                task = {
                    "capability": payload.get("capability"),
                    "parameters": payload.get("parameters"),
                }
                context = {
                    "tenant_id": payload.get("tenant_id"),
                    "correlation_id": message.correlation_id,
                }

                try:
                    result = await agent.run(task, context)

                    # Send result back
                    await self.message_bus.publish(
                        agent_id=agent.agent_id,
                        event_type=MessageType.TASK_RESULT,
                        payload={
                            "task_id": payload.get("task_id"),
                            "success": True,
                            "result": result,
                        },
                        recipient_id=message.sender_id,
                        correlation_id=message.correlation_id,
                    )
                except Exception as e:
                    # Send error
                    await self.message_bus.publish(
                        agent_id=agent.agent_id,
                        event_type=MessageType.ERROR_NOTIFICATION,
                        payload={
                            "task_id": payload.get("task_id"),
                            "success": False,
                            "error": str(e),
                        },
                        recipient_id=message.sender_id,
                        correlation_id=message.correlation_id,
                    )

        return handler

    async def _wait_for_workflow_with_timeout(
        self, workflow_id: str, timeout_seconds: int
    ) -> AgentState:
        """Wait for workflow completion with global timeout (P1-25).

        Args:
            workflow_id: Workflow to wait for
            timeout_seconds: Maximum time to wait before failing

        Returns:
            Final workflow state

        Raises:
            WorkflowTimeoutError: If workflow exceeds timeout
        """
        from ..exceptions import WorkflowTimeoutError

        start_time = datetime.now(UTC)

        while True:
            # Check for timeout
            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            if elapsed > timeout_seconds:
                # Cancel the workflow
                await self.cancel_workflow(workflow_id, reason=f"Global timeout exceeded ({timeout_seconds}s)")
                raise WorkflowTimeoutError(
                    f"Workflow {workflow_id} timed out after {timeout_seconds} seconds"
                )

            state = await self.state_manager.load_state(workflow_id)

            if state and state.status in [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.CANCELLED,
            ]:
                return state

            await asyncio.sleep(0.5)

    async def _wait_for_workflow(self, workflow_id: str) -> AgentState:
        """Wait for workflow completion (legacy, no timeout).

        Args:
            workflow_id: Workflow to wait for

        Returns:
            Final workflow state
        """
        # Poll until complete
        while True:
            state = await self.state_manager.load_state(workflow_id)

            if state and state.status in [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.CANCELLED,
            ]:
                return state

            await asyncio.sleep(0.5)

    def _calculate_progress(self, state: AgentState) -> int:
        """Calculate workflow progress percentage.

        Args:
            state: Current workflow state

        Returns:
            Progress percentage (0-100)
        """
        # Simple heuristic based on status
        status_progress = {
            WorkflowStatus.PENDING: 0,
            WorkflowStatus.RUNNING: 50,
            WorkflowStatus.COMPLETED: 100,
            WorkflowStatus.FAILED: 100,
            WorkflowStatus.CANCELLED: 100,
        }

        return status_progress.get(state.status, 0)

    async def _on_task_complete(self, task: ScheduledTask) -> None:
        """Callback for task completion.

        Args:
            task: Completed task
        """
        logger.info(f"Task {task.task_id} completed")

    async def _on_task_fail(self, task: ScheduledTask, exception: Exception) -> None:
        """Callback for task failure.

        Args:
            task: Failed task
            exception: Exception that caused failure
        """
        logger.error(f"Task {task.task_id} failed: {exception}")


# Backward compatibility alias for route dependency typing.
WorkflowExecutor = OrchestrationController
