"""
Fabric_4L Harness — Governed Execution Spine for Agentic Value Workflows.

The harness coordinates:
  - HarnessRun lifecycle
  - Deterministic workflow state transitions
  - Checkpoints
  - Tool contracts
  - Approval policies
  - Human gates
  - L5 claim validation hooks
  - Tenant/account/value-pack context
  - Structured trace emission
  - Customer-facing output controls
  - Auditability and replayability

Invariants:
  - Every HarnessRun has tenant_id and trace_id.
  - Every state transition is validated.
  - Terminal runs cannot continue.
  - Every checkpoint is tied to run_id and tenant_id with deterministic hashing.
  - Every high-risk tool action requires an approval policy.
  - Every customer-facing output requires L5 validation or explicit human override.
  - Unavailable L5 validation routes to needs_review — never silently approves.
"""

from harness.models import (
    HarnessRun,
    HarnessCheckpoint,
    ToolContract,
    HumanGate,
    ClaimValidationResult,
    HarnessTraceEvent,
    HarnessWorkflowType,
    HarnessRunStatus,
    HarnessState,
    ToolLayer,
    ToolSideEffectClass,
    ToolRiskLevel,
    GateType,
    GateStatus,
    ValidationState,
    InitiatedBy,
)
from harness.state_machine import StateMachine, TransitionError, TerminalStateError, ValidationRequiredError
from harness.policies import (
    requires_approval,
    can_publish_output,
    evaluate_transition_policy,
    evaluate_tool_invocation_policy,
    ApprovalRequiredError,
    PublicationBlockedError,
)
from harness.tool_contracts import (
    ToolContractRegistry,
    ToolRegistrationError,
    ToolNotFoundError,
)
from harness.human_gates import (
    HumanGateManager,
    GateDecisionError,
    GateExpiredError,
    GateNotFoundError,
)
from harness.checkpoints import CheckpointManager, CheckpointError
from harness.telemetry import TelemetryEmitter
from harness.validation_hooks import (
    ClaimValidationRequest,
    ClaimValidator,
    MockValidator,
    UnavailableValidator,
    ValidationHook,
    ValidationUnavailableError,
)
from harness.registry import HarnessRegistry, HarnessRegistryError

__all__ = [
    # Models
    "HarnessRun",
    "HarnessCheckpoint",
    "ToolContract",
    "HumanGate",
    "ClaimValidationResult",
    "HarnessTraceEvent",
    "HarnessWorkflowType",
    "HarnessRunStatus",
    "HarnessState",
    "ToolLayer",
    "ToolSideEffectClass",
    "ToolRiskLevel",
    "GateType",
    "GateStatus",
    "ValidationState",
    "InitiatedBy",
    # State machine
    "StateMachine",
    "TransitionError",
    "TerminalStateError",
    "ValidationRequiredError",
    # Policies
    "requires_approval",
    "can_publish_output",
    "evaluate_transition_policy",
    "evaluate_tool_invocation_policy",
    "ApprovalRequiredError",
    "PublicationBlockedError",
    # Tool contracts
    "ToolContractRegistry",
    "ToolRegistrationError",
    "ToolNotFoundError",
    # Human gates
    "HumanGateManager",
    "GateDecisionError",
    "GateExpiredError",
    "GateNotFoundError",
    # Checkpoints
    "CheckpointManager",
    "CheckpointError",
    # Telemetry
    "TelemetryEmitter",
    # Validation hooks
    "ClaimValidationRequest",
    "ClaimValidator",
    "MockValidator",
    "UnavailableValidator",
    "ValidationHook",
    "ValidationUnavailableError",
    # Registry
    "HarnessRegistry",
    "HarnessRegistryError",
]
