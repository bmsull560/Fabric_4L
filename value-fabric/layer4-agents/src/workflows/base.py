"""Base workflow class and LangGraph integration.

Provides the foundation for all workflow implementations with checkpointing,
state management, and node execution.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph

from ..models.agent_state import AgentState, BaseAgentState, WorkflowStatus
from ..models.workflow_config import EdgeConfig, NodeConfig, NodeType, WorkflowConfig
from ..tools.registry import ToolRegistry

# Default recursion limit for LangGraph workflows
# Prevents infinite loops in malformed workflows
DEFAULT_RECURSION_LIMIT = 100

logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    """Raised when workflow execution fails."""

    pass


class NodeExecutionError(WorkflowError):
    """Raised when a node execution fails."""

    pass


class BaseWorkflow(ABC):
    """Base class for all LangGraph workflows.

    Provides common functionality for:
    - Graph construction from WorkflowConfig
    - State management and checkpointing
    - Node execution with error handling
    - Tool integration

    Example:
        class MyWorkflow(BaseWorkflow):
            def __init__(self, config: WorkflowConfig, tool_registry: ToolRegistry):
                super().__init__(config, tool_registry)

            def _build_graph(self) -> StateGraph:
                # Build and return LangGraph
                pass
    """

    def __init__(
        self,
        config: WorkflowConfig,
        tool_registry: ToolRegistry,
        checkpoint_saver: BaseCheckpointSaver | None = None,
    ):
        """Initialize workflow.

        Args:
            config: Workflow configuration
            tool_registry: Registry of available tools
            checkpoint_saver: Optional checkpoint saver for persistence
        """
        self.config = config
        self.tool_registry = tool_registry
        self.checkpoint_saver = checkpoint_saver
        self._graph: StateGraph | None = None
        self._compiled_graph = None

    @property
    def name(self) -> str:
        """Get workflow name."""
        return self.config.name

    @property
    def workflow_type(self) -> str:
        """Get workflow type identifier."""
        return self.config.workflow_type

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph from configuration.

        This base implementation constructs a basic graph from
        the WorkflowConfig. Subclasses can override for custom logic.

        Returns:
            Configured StateGraph
        """
        # Create state graph with our state type
        graph = StateGraph(self._get_state_type())

        # Add nodes
        for node_config in self.config.nodes:
            node_func = self._create_node_function(node_config)
            graph.add_node(node_config.id, node_func)

        # Add edges
        for edge_config in self.config.edges:
            if edge_config.edge_type.value == "conditional":
                # Conditional edge requires a router function
                graph.add_conditional_edges(
                    edge_config.source,
                    self._create_router(edge_config),
                    {True: edge_config.target, False: self.config.entry_point},
                )
            else:
                graph.add_edge(edge_config.source, edge_config.target)

        # Set entry point
        graph.set_entry_point(self.config.entry_point)

        return graph

    def _get_state_type(self) -> type:
        """Get the Pydantic state type for this workflow.

        Returns:
            Pydantic BaseModel class
        """
        return BaseAgentState

    def _create_node_function(self, node_config: NodeConfig) -> Callable:
        """Create a node execution function.

        Args:
            node_config: Node configuration

        Returns:
            Node function for LangGraph
        """

        async def node_function(state: AgentState) -> dict[str, Any]:
            """Execute node logic."""
            # Update state
            updates = {"current_node": node_config.id, "status": WorkflowStatus.RUNNING}

            try:
                if node_config.node_type == NodeType.TOOL and node_config.tool_name:
                    # Execute tool
                    result = await self._execute_tool(
                        node_config.tool_name, state, node_config.config
                    )
                    updates["output_data"] = {**state.output_data, node_config.id: result}

                elif node_config.node_type == NodeType.LLM:
                    # LLM node - handled by subclass or agent node
                    result = await self._execute_llm(node_config, state)
                    updates["output_data"] = {**state.output_data, node_config.id: result}

                elif node_config.node_type == NodeType.AGENT:
                    # Agent node - delegates to sub-workflow
                    result = await self._execute_agent(node_config, state)
                    updates["output_data"] = {**state.output_data, node_config.id: result}

                elif node_config.node_type == NodeType.END:
                    # End node
                    updates["status"] = WorkflowStatus.COMPLETED
                    updates["completed_at"] = self._now()

                return updates

            except Exception as e:
                # Handle error
                error_msg = f"Node {node_config.id} failed: {str(e)}"
                updates["errors"] = state.errors + [error_msg]
                updates["status"] = WorkflowStatus.FAILED

                # Check retry policy
                if self._should_retry(node_config, state):
                    # Return to same node for retry
                    return updates

                raise NodeExecutionError(error_msg)

        return node_function

    async def _execute_tool(
        self, tool_name: str, state: AgentState, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a tool from the registry.

        Args:
            tool_name: Name of tool to execute
            state: Current workflow state
            config: Tool configuration

        Returns:
            Tool execution result
        """
        # Build input from state
        tool_input = self._build_tool_input(tool_name, state, config)

        # Execute via registry
        result = await self.tool_registry.execute(tool_name, tool_input)

        return result

    def _build_tool_input(
        self, tool_name: str, state: AgentState, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Build tool input from state and config.

        Subclasses can override to customize input building.

        Args:
            tool_name: Tool being executed
            state: Current state
            config: Node config

        Returns:
            Tool input dictionary
        """
        # Default: merge input data with config
        tool_input = {**state.input_data, **config}

        # Add workflow-specific data
        if hasattr(state, "prospect_id"):
            tool_input["prospect_id"] = state.prospect_id

        return tool_input

    async def _execute_llm(self, node_config: NodeConfig, state: AgentState) -> dict[str, Any]:
        """Execute LLM node.

        Subclasses should override for LLM-specific logic.
        """
        return {"status": "llm_not_implemented"}

    async def _execute_agent(self, node_config: NodeConfig, state: AgentState) -> dict[str, Any]:
        """Execute agent node (sub-workflow).

        Subclasses should override for agent-specific logic.
        """
        return {"status": "agent_not_implemented"}

    def _create_router(self, edge_config: EdgeConfig) -> Callable:
        """Create a router function for conditional edges."""

        def router(state: AgentState) -> bool:
            """Route based on state."""
            # Simple condition evaluation - can be extended
            if edge_config.condition == "results_valid":
                return len(state.errors) == 0
            elif edge_config.condition == "retry_needed":
                return len(state.errors) > 0
            return True

        return router

    def _should_retry(self, node_config: NodeConfig, state: AgentState) -> bool:
        """Check if node should be retried."""
        max_retries = node_config.retry_policy.get("max_retries", 0)
        # Count retries by checking errors containing node name
        retry_count = sum(1 for e in state.errors if node_config.id in e)
        return retry_count < max_retries

    def _now(self):
        """Get current timestamp."""
        from datetime import datetime

        return datetime.utcnow()

    def compile(self) -> Any:
        """Compile the workflow graph.

        Returns:
            Compiled LangGraph runnable
        """
        if self._compiled_graph is None:
            if self._graph is None:
                self._graph = self._build_graph()

            compile_kwargs = {}
            if self.checkpoint_saver:
                compile_kwargs["checkpointer"] = self.checkpoint_saver

            self._compiled_graph = self._graph.compile(**compile_kwargs)

        return self._compiled_graph

    async def run(
        self,
        initial_state: AgentState,
        thread_id: str | None = None,
        recursion_limit: int | None = None,
        **kwargs,
    ) -> AgentState:
        """Execute the workflow.

        Args:
            initial_state: Starting workflow state
            thread_id: Optional thread ID for checkpointing
            recursion_limit: Maximum recursion steps (default: DEFAULT_RECURSION_LIMIT)
            **kwargs: Additional run parameters

        Returns:
            Final workflow state

        Raises:
            ValueError: If recursion_limit is not a positive integer
        """
        # Validate recursion_limit
        if recursion_limit is not None:
            if not isinstance(recursion_limit, int) or recursion_limit <= 0:
                raise ValueError(
                    f"recursion_limit must be a positive integer, got {recursion_limit}"
                )
        else:
            recursion_limit = DEFAULT_RECURSION_LIMIT

        compiled = self.compile()

        config = {"configurable": {}, "recursion_limit": recursion_limit}
        if thread_id:
            config["configurable"]["thread_id"] = thread_id

        workflow_id = getattr(initial_state, "workflow_id", "unknown")
        logger.info(
            "Starting workflow execution",
            workflow_id=workflow_id,
            workflow_type=getattr(initial_state, "workflow_type", "unknown"),
            thread_id=thread_id,
            recursion_limit=recursion_limit,
        )

        try:
            result = await compiled.ainvoke(initial_state.model_dump(), config=config, **kwargs)
            logger.info(f"Workflow execution completed: {workflow_id}")
            return self._state_from_dict(result)
        except Exception as e:
            logger.error(f"Workflow execution failed: {workflow_id}: {e}", exc_info=True)
            raise

    def _state_from_dict(self, data: dict[str, Any]) -> AgentState:
        """Convert dict result back to state object."""
        state_type = self._get_state_type()
        return state_type(**data)

    @abstractmethod
    def create_initial_state(self, input_data: dict[str, Any]) -> AgentState:
        """Create initial state from input data.

        Args:
            input_data: Workflow input parameters

        Returns:
            Initial workflow state
        """
        pass


class WorkflowBuilder:
    """Builder for constructing workflows programmatically.

    Example:
        builder = WorkflowBuilder("my_workflow", "My Workflow")
        builder.add_node(NodeConfig(id="step1", ...))
        builder.add_edge("step1", "step2")

        config = builder.build()
        workflow = BaseWorkflow(config, tool_registry)
    """

    def __init__(self, workflow_type: str, name: str, description: str = ""):
        """Initialize builder."""
        self.workflow_type = workflow_type
        self.name = name
        self.description = description
        self.nodes: list[NodeConfig] = []
        self.edges: list[EdgeConfig] = []
        self.entry_point: str | None = None
        self.global_config: dict[str, Any] = {}

    def add_node(self, node: NodeConfig) -> "WorkflowBuilder":
        """Add a node to the workflow."""
        self.nodes.append(node)
        return self

    def add_edge(self, source: str, target: str, **kwargs) -> "WorkflowBuilder":
        """Add an edge between nodes."""
        self.edges.append(EdgeConfig(source=source, target=target, **kwargs))
        return self

    def set_entry_point(self, node_id: str) -> "WorkflowBuilder":
        """Set the workflow entry point."""
        self.entry_point = node_id
        return self

    def set_global_config(self, config: dict[str, Any]) -> "WorkflowBuilder":
        """Set global workflow configuration."""
        self.global_config = config
        return self

    def build(self) -> WorkflowConfig:
        """Build the workflow configuration."""
        if not self.entry_point:
            raise WorkflowError("Entry point must be set")

        return WorkflowConfig(
            workflow_type=self.workflow_type,
            name=self.name,
            description=self.description,
            nodes=self.nodes,
            edges=self.edges,
            entry_point=self.entry_point,
            global_config=self.global_config,
        )
