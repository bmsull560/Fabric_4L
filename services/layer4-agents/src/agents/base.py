"""Base agent class and state definitions.

Provides the foundation for all 9 canonical agent types in the Value Fabric
Layer 4 system.  See taxonomy.py for the full roster.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any

from value_fabric.shared.models.typed_dict import TypedDictModel

_PLATFORM_CONTRACT_PYTHON = next(
    (parent / "packages" / "platform-contract" / "src" / "python" for parent in Path(__file__).resolve().parents if (parent / "packages" / "platform-contract" / "src" / "python").exists()),
    None,
)
if _PLATFORM_CONTRACT_PYTHON and str(_PLATFORM_CONTRACT_PYTHON) not in sys.path:
    sys.path.append(str(_PLATFORM_CONTRACT_PYTHON))

try:  # pragma: no cover - contract tests configure this path explicitly
    from agent_contracts import build_agent_output_envelope, validate_agent_output
except Exception:  # pragma: no cover - runtime remains warning-only if package import fails
    build_agent_output_envelope = None  # type: ignore[assignment]
    validate_agent_output = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)
SEMANTIC_CONTRACT_VERSION = "2.0.0"


class AgentState_to_dictResult(TypedDictModel):
    agent_id: Any
    agent_type: Any
    completed_at: Any
    context: Any
    current_task: Any
    errors: Any
    metadata: Any
    started_at: Any
    status: Any

try:
    from value_fabric.shared.testability import Clock, IDGenerator, SystemClock, UUIDGenerator
except ImportError:
    # Fallback implementations when shared package unavailable
    class Clock:
        @staticmethod
        def now() -> datetime:
            return datetime.now()
    
    class SystemClock(Clock):
        pass
    
    class IDGenerator:
        @staticmethod
        def generate() -> str:
            import uuid
            return str(uuid.uuid4())
    
    class UUIDGenerator(IDGenerator):
        pass


class AgentStatus(Enum):
    """Agent execution status."""

    IDLE = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class AgentCapability:
    """Capability that an agent can perform.

    Attributes:
        name: Capability identifier
        description: Human-readable description
        input_schema: Expected input structure
        output_schema: Expected output structure
        timeout_seconds: Maximum execution time
    """

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300


@dataclass
class AgentState:
    """Current state of an agent instance.

    Attributes:
        agent_id: Unique identifier
        agent_type: Type of agent
        status: Current status
        current_task: What the agent is currently doing
        context: Execution context (tenant_id, user_id, etc.)
        started_at: When agent started
        completed_at: When agent finished
        errors: List of errors encountered
        metadata: Additional runtime data
    """

    agent_id: str
    agent_type: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary."""
        return AgentState_to_dictResult.model_validate({
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.name,
            "current_task": self.current_task,
            "context": self.context,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "errors": self.errors,
            "metadata": self.metadata,
        })


class BaseAgent(ABC):
    """Base class for all Value Fabric agents.

    All agents must inherit from this class and implement:
    - execute(): The main agent execution logic
    - get_capabilities(): Return list of supported capabilities

    Example:
        class MyAgent(BaseAgent):
            agent_type = "MY_AGENT"

            def get_capabilities(self) -> List[AgentCapability]:
                return [AgentCapability(name="do_something", ...)]

            async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
                # Implementation here
                return dict(result="success")
    """

    agent_type: str = "BASE"
    capabilities: list[AgentCapability] = []

    def __init__(
        self,
        agent_id: str | None = None,
        config: dict[str, Any] | None = None,
        message_bus: Any | None = None,
        clock: Clock | None = None,
        id_generator: IDGenerator | None = None,
    ):
        """Initialize agent.

        Args:
            agent_id: Unique identifier (generated if not provided)
            config: Agent-specific configuration
            message_bus: Message bus for inter-agent communication
            clock: Injectable clock for time operations.  Defaults to
                ``SystemClock``.
            id_generator: Injectable ID generator.  Defaults to ``UUIDGenerator``.
        """
        self._clock: Clock = clock or SystemClock()
        self._id_gen: IDGenerator = id_generator or UUIDGenerator()
        self.agent_id = agent_id or f"{self.agent_type.lower()}-{self._id_gen.generate()[:8]}"
        self.config = config or {}
        self.message_bus = message_bus
        self.state = AgentState(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            context={"config": self.config},
        )
        self._initialized = False
        self._execution_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize agent resources."""
        if self._initialized:
            return

        self.state.status = AgentStatus.INITIALIZING
        await self._initialize_resources()
        self._initialized = True
        self.state.status = AgentStatus.IDLE

    async def _initialize_resources(self) -> None:
        """Override to initialize agent-specific resources."""
        pass

    @abstractmethod
    def get_capabilities(self) -> list[AgentCapability]:
        """Return list of capabilities this agent supports."""
        pass

    @abstractmethod
    async def execute(
        self,
        task: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a task.

        Args:
            task: Task specification with 'capability' and 'parameters'
            context: Execution context (tenant_id, user_id, workflow_id, etc.)

        Returns:
            Task execution result
        """
        pass

    def _semantic_contract_mode(self) -> str:
        """Resolve Phase 2 semantic-contract enforcement mode."""

        mode = os.getenv("AGENT_SEMANTIC_CONTRACT_MODE", "warn").strip().lower()
        return "strict" if mode == "strict" else "warn"

    def _validate_agent_output_contract(
        self,
        result: dict[str, Any],
        task: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate an agent result against the shared semantic output envelope."""

        mode = self._semantic_contract_mode()
        if build_agent_output_envelope is None or validate_agent_output is None:
            validation_metadata = {
                "version": SEMANTIC_CONTRACT_VERSION,
                "mode": mode,
                "valid": False,
                "violations": [
                    {
                        "code": "semantic_contract_validator_unavailable",
                        "message": "agent_contracts package is unavailable in this runtime",
                        "severity": "warning",
                        "path": "$",
                    }
                ],
            }
            self.state.metadata["semantic_contract"] = validation_metadata
            return validation_metadata

        tenant_id = str(context.get("tenant_id") or context.get("tenantId") or "unknown")
        trace_id = str(context.get("trace_id") or context.get("traceId") or self.agent_id)
        workflow_id = context.get("workflow_id") or context.get("workflowId")
        audit_event_id = context.get("audit_event_id") or context.get("auditEventId")
        capability = str(task.get("capability", "unknown"))

        envelope = build_agent_output_envelope(
            agent_type=self.agent_type,
            output=result,
            tenant_id=tenant_id,
            trace_id=trace_id,
            workflow_id=str(workflow_id) if workflow_id else None,
            audit_event_id=str(audit_event_id) if audit_event_id else None,
            source_node=f"{self.agent_type}.{capability}",
            confidence=result.get("confidence") if isinstance(result.get("confidence"), (int, float)) else None,
            explainability={"capability": capability},
            contract_versions={
                "semantic_contract": SEMANTIC_CONTRACT_VERSION,
                "agent_registry": "1.0.0",
            },
        )
        validation = validate_agent_output(envelope, mode=mode)
        violations = [
            violation.model_dump() if hasattr(violation, "model_dump") else violation
            for violation in validation.violations
        ]
        validation_metadata = {
            "version": SEMANTIC_CONTRACT_VERSION,
            "mode": validation.mode.value if hasattr(validation.mode, "value") else str(validation.mode),
            "valid": validation.valid,
            "violations": violations,
        }
        self.state.metadata["semantic_contract"] = validation_metadata
        if validation.blocking:
            raise AgentExecutionError(
                f"Agent {self.agent_id} produced output that violates semantic contract: {violations}"
            )
        if violations:
            logger.warning(
                "Agent %s semantic-contract warnings: %s",
                self.agent_id,
                violations,
            )
        return validation_metadata

    async def run(
        self,
        task: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the agent with a task (handles lifecycle).

        GATE integration: If a ``tool_registry`` and ``abom`` are present in
        context, a ``ToolGateway`` is created and injected into ``ctx`` so that
        ``execute()`` implementations can call ``ctx['tool_gateway'].execute()``
        instead of using the registry directly.  A ``ReplayRecorder`` is also
        attached when available.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Execution result
        """
        await self.initialize()

        ctx = context or {}
        self.state.context.update(ctx)
        self.state.started_at = self._clock.now()
        self.state.status = AgentStatus.RUNNING
        self.state.current_task = task.get("capability", "unknown")

        # ── GATE Phase 2: ToolGateway injection ──
        tool_gateway = None
        if "tool_registry" in ctx and "abom" in ctx:
            try:
                from value_fabric.shared.governance.tool_gateway import ToolGateway

                tool_gateway = ToolGateway(
                    registry=ctx["tool_registry"],
                    abom=ctx["abom"],
                    tenant_id=ctx.get("tenant_id"),
                    trace_id=ctx.get("trace_id"),
                )
                ctx["tool_gateway"] = tool_gateway
            except ImportError:
                pass  # GATE not installed — graceful degradation

        # ── GATE Phase 3: ReplayRecorder injection ──
        replay_recorder = None
        if tool_gateway is not None:
            try:
                from value_fabric.shared.governance.replay import ReplayRecorder

                replay_recorder = ReplayRecorder(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    abom=ctx.get("abom"),
                    tenant_id=ctx.get("tenant_id"),
                    trace_id=ctx.get("trace_id"),
                )
                ctx["replay_recorder"] = replay_recorder
            except ImportError:
                pass  # Replay not installed — graceful degradation

        try:
            # Send status update via message bus if available
            if self.message_bus:
                await self.message_bus.publish(
                    agent_id=self.agent_id,
                    event_type="AGENT_STARTED",
                    payload={"task": task, "context": ctx},
                )

            # Execute the task
            async with self._execution_lock:
                result = await self.execute(task, ctx)

            semantic_contract = self._validate_agent_output_contract(result, task, ctx)

            # Mark completion
            self.state.status = AgentStatus.COMPLETED
            self.state.completed_at = self._clock.now()

            # ── GATE Phase 3: Commit replay snapshot ──
            if replay_recorder is not None and tool_gateway is not None:
                replay_recorder.record_tool_invocations(tool_gateway.invocation_log)
                await replay_recorder.commit()

            # Send completion event
            if self.message_bus:
                await self.message_bus.publish(
                    agent_id=self.agent_id,
                    event_type="AGENT_COMPLETED",
                    payload={"result": result, "semantic_contract": semantic_contract},
                )

            return result

        except Exception as e:
            self.state.status = AgentStatus.FAILED
            self.state.errors.append(str(e))
            self.state.completed_at = self._clock.now()

            # Send failure event
            if self.message_bus:
                await self.message_bus.publish(
                    agent_id=self.agent_id,
                    event_type="AGENT_FAILED",
                    payload={"error": str(e)},
                )

            raise AgentExecutionError(f"Agent {self.agent_id} failed: {e}") from e

    async def pause(self) -> None:
        """Pause agent execution (if supported)."""
        if self.state.status == AgentStatus.RUNNING:
            self.state.status = AgentStatus.PAUSED

    async def resume(self) -> None:
        """Resume paused execution."""
        if self.state.status == AgentStatus.PAUSED:
            self.state.status = AgentStatus.RUNNING

    async def cancel(self) -> None:
        """Cancel current execution."""
        self.state.status = AgentStatus.CANCELLED
        self.state.completed_at = self._clock.now()

    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state

    def has_capability(self, capability_name: str) -> bool:
        """Check if agent supports a capability."""
        return any(c.name == capability_name for c in self.get_capabilities())


class AgentExecutionError(Exception):
    """Raised when agent execution fails."""

    pass


class AgentNotFoundError(Exception):
    """Raised when requested agent type is not found."""

    pass
