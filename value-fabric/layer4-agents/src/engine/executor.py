"""Orchestration Controller - Enhanced workflow execution engine.

Provides comprehensive workflow orchestration with:
- Multi-agent coordination
- Task scheduling with priorities
- Backpressure handling
- Message-based agent communication
- Failure recovery

This implements the OrchestrationController agent type from the specification.
"""

from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime
import asyncio
import logging

from ..models.agent_state import AgentState, WorkflowStatus
from ..tools.registry import ToolRegistry
from ..workflows.base import BaseWorkflow
from ..workflows import create_workflow
from ..agents.base import BaseAgent
from ..agents.taxonomy import OrchestrationController as OrchestrationAgent
from ..messaging.bus import MessageBus, InMemoryMessageBus
from ..messaging.router import MessageRouter
from ..messaging.types import MessageType, MessagePriority
from .state_manager import StateManager
from .scheduler import TaskScheduler, ScheduledTask, TaskPriority

logger = logging.getLogger(__name__)


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
        state_manager: Optional[StateManager] = None,
        message_bus: Optional[MessageBus] = None,
        max_concurrent: int = 100,
        scaling_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize orchestration controller.
        
        Args:
            tool_registry: Registry of available tools
            state_manager: State persistence manager
            message_bus: Message bus for agent communication
            max_concurrent: Maximum concurrent tasks
            scaling_config: Scaling policy configuration
        """
        self.tool_registry = tool_registry
        self.state_manager = state_manager or StateManager()
        self.message_bus = message_bus or InMemoryMessageBus()
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
        self._registered_agents: Dict[str, BaseAgent] = {}
        self._agent_pool: Dict[str, Dict[str, Any]] = {}
        
        # Workflow tracking
        self._active_workflows: Dict[str, asyncio.Task] = {}
        self._workflow_metadata: Dict[str, Dict[str, Any]] = {}
        
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
        input_data: Dict[str, Any],
        workflow_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
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
        """
        # Create workflow
        workflow = create_workflow(workflow_type, self.tool_registry)
        initial_state = workflow.create_initial_state(input_data)
        workflow_id = workflow_id or initial_state.workflow_id
        
        # Store metadata
        self._workflow_metadata[workflow_id] = {
            "workflow_type": workflow_type,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "priority": priority.value,
            "started_at": datetime.utcnow().isoformat(),
        }
        
        # Schedule workflow execution
        task = ScheduledTask(
            priority=priority.value,
            scheduled_time=datetime.utcnow(),
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
        )
        
        await self.scheduler.schedule_task(task)
        
        # Wait for completion (blocking call)
        return await self._wait_for_workflow(workflow_id)
    
    async def schedule_workflow(
        self,
        workflow_type: str,
        input_data: Dict[str, Any],
        scheduled_time: Optional[datetime] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
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
        schedule_id = f"sched-{datetime.utcnow().timestamp()}"
        
        execute_time = scheduled_time or datetime.utcnow()
        
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
        parameters: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        tenant_id: Optional[str] = None,
        timeout_seconds: int = 300,
    ) -> Optional[str]:
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
        task_id = f"task-{datetime.utcnow().timestamp()}"
        
        task = ScheduledTask(
            priority=priority.value,
            scheduled_time=datetime.utcnow(),
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
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
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
        
        return {
            "workflow_id": workflow_id,
            "workflow_type": state.workflow_type.value if hasattr(state.workflow_type, 'value') else str(state.workflow_type),
            "status": state.status.value if hasattr(state.status, 'value') else str(state.status),
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
        }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a workflow.
        
        Args:
            workflow_id: Workflow to cancel
            
        Returns:
            True if cancelled
        """
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
            state.completed_at = datetime.utcnow()
            await self.state_manager.save_state(workflow_id, state)
        
        return cancelled
    
    async def list_active_workflows(
        self,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
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
    
    def get_cluster_health(self) -> Dict[str, Any]:
        """Get orchestration cluster health.
        
        Returns:
            Health metrics
        """
        router_health = self.message_router.get_cluster_health()
        scheduler_stats = self.scheduler.get_stats()
        
        return {
            "status": router_health.get("status", "unknown"),
            "registered_agents": len(self._registered_agents),
            "active_workflows": len(self._active_workflows),
            "pending_tasks": scheduler_stats.get("pending_tasks", 0),
            "running_tasks": scheduler_stats.get("running_tasks", 0),
            "avg_load": router_health.get("avg_load", 0),
            "utilization": scheduler_stats.get("utilization", 0),
        }
    
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
    
    async def _wait_for_workflow(self, workflow_id: str) -> AgentState:
        """Wait for workflow completion.
        
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


# Backward compatibility alias
WorkflowExecutor = OrchestrationController


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""
    pass
