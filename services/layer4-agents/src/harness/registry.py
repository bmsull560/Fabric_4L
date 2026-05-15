"""
Harness Registry — coordinates runs, checkpoints, gates, and validation.

This is the top-level orchestrator that ties together all harness components.
It does not replace individual layers but governs how they interact.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from harness.checkpoints import CheckpointManager
from harness.human_gates import HumanGateManager
from harness.models import (
    ClaimValidationResult,
    GateStatus,
    GateType,
    HarnessCheckpoint,
    HarnessRun,
    HarnessRunStatus,
    HarnessState,
    HarnessTraceEvent,
    HarnessWorkflowType,
    HumanGate,
    InitiatedBy,
    ToolContract,
    ValidationState,
)
from harness.validation_hooks import ClaimValidationRequest
from harness.policies import can_publish_output, PublicationBlockedError
from harness.state_machine import StateMachine, TerminalStateError, TransitionError, ValidationRequiredError
from harness.telemetry import TelemetryEmitter
from harness.tool_contracts import ToolContractRegistry
from harness.validation_hooks import ValidationHook


class HarnessRegistryError(RuntimeError):
    """Raised when a registry operation fails."""

    pass


class HarnessRegistry:
    """
    Top-level harness orchestrator.

    Coordinates:
      - Run lifecycle
      - State transitions
      - Checkpoint management
      - Human gates
      - Tool contract enforcement
      - Validation hooks
      - Telemetry emission
    """

    def __init__(
        self,
        state_machine: Optional[StateMachine] = None,
        tool_registry: Optional[ToolContractRegistry] = None,
        gate_manager: Optional[HumanGateManager] = None,
        checkpoint_manager: Optional[CheckpointManager] = None,
        telemetry: Optional[TelemetryEmitter] = None,
        validation_hook: Optional[ValidationHook] = None,
    ) -> None:
        self._sm = state_machine or StateMachine()
        self._tools = tool_registry or ToolContractRegistry()
        self._gates = gate_manager or HumanGateManager()
        self._checkpoints = checkpoint_manager or CheckpointManager()
        self._telemetry = telemetry or TelemetryEmitter()
        self._validation = validation_hook or ValidationHook()

        # Run store
        self._runs: Dict[str, HarnessRun] = {}

    # ---- Run Lifecycle ----

    def create_run(
        self,
        tenant_id: str,
        workflow_type: HarnessWorkflowType,
        initiated_by: InitiatedBy,
        account_id: Optional[str] = None,
        value_pack_id: Optional[str] = None,
    ) -> HarnessRun:
        """Create a new harness run."""
        run = HarnessRun(
            tenant_id=tenant_id,
            account_id=account_id,
            workflow_type=workflow_type,
            initiated_by=initiated_by,
            value_pack_id=value_pack_id,
        )
        self._runs[run.id] = run

        # Emit creation event
        self._telemetry.emit_transition_event(
            run=run,
            from_state=None,  # type: ignore[arg-type]
            to_state=HarnessState.INIT,
        )

        return run

    def get_run(self, run_id: str, tenant_id: str) -> HarnessRun:
        """Get a run with tenant scoping."""
        run = self._runs.get(run_id)
        if run is None:
            raise HarnessRegistryError(f"Run '{run_id}' not found")
        if run.tenant_id != tenant_id:
            raise HarnessRegistryError(
                f"Run '{run_id}' not found for tenant '{tenant_id}'"
            )
        return run

    # ---- State Transitions ----

    def transition(
        self,
        run_id: str,
        tenant_id: str,
        to_state: HarnessState,
        validation_results: Optional[List[ClaimValidationResult]] = None,
        human_override: bool = False,
        state_payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[HarnessRun, HarnessTraceEvent]:
        """
        Execute a state transition.

        Returns:
            Tuple of (updated_run, trace_event).
        """
        run = self.get_run(run_id, tenant_id)

        # Derive validation state from results
        validation_state: Optional[ValidationState] = None
        if validation_results is not None:
            # Aggregate: if any failed, use failed; if any need review, use needs_review
            states = [vr.validation_state for vr in validation_results]
            if ValidationState.FAILED in states:
                validation_state = ValidationState.FAILED
            elif ValidationState.INSUFFICIENT_EVIDENCE in states:
                validation_state = ValidationState.INSUFFICIENT_EVIDENCE
            elif ValidationState.NEEDS_REVIEW in states:
                validation_state = ValidationState.NEEDS_REVIEW
            elif states and all(s == ValidationState.PASSED for s in states):
                validation_state = ValidationState.PASSED

        updated, event = self._sm.transition(
            run=run,
            to_state=to_state,
            validation_state=validation_state,
            human_override=human_override,
        )

        # Emit telemetry directly (avoids mutating injected StateMachine hooks)
        self._telemetry.emit_transition_event(
            run=updated,
            from_state=run.current_state,
            to_state=to_state,
        )

        # Persist updated run
        self._runs[run_id] = updated

        # Checkpoint
        if state_payload is not None:
            self._checkpoints.create_checkpoint(
                run_id=run_id,
                tenant_id=tenant_id,
                state_name=to_state,
                state_payload=state_payload,
            )

        return updated, event

    # ---- Human Gates ----

    def create_human_gate(
        self,
        run_id: str,
        tenant_id: str,
        gate_type: GateType,
    ) -> HumanGate:
        """Create a human gate for a run."""
        run = self.get_run(run_id, tenant_id)
        gate, event = self._gates.create_gate(run_id, tenant_id, gate_type)
        event = event.model_copy(
            update={
                "trace_id": run.trace_id,
                "workflow_type": run.workflow_type,
            }
        )
        self._telemetry._dispatch(event)
        return gate

    def decide_gate(
        self,
        gate_id: str,
        tenant_id: str,
        decision: GateStatus,
        decision_by: str,
        decision_reason: Optional[str] = None,
    ) -> HumanGate:
        """Make a decision on a human gate."""
        if decision == GateStatus.APPROVED:
            gate, event = self._gates.approve_gate(
                gate_id, tenant_id, decision_by, decision_reason
            )
        elif decision == GateStatus.REJECTED:
            gate, event = self._gates.reject_gate(
                gate_id, tenant_id, decision_by, decision_reason
            )
        elif decision == GateStatus.MODIFIED:
            gate, event = self._gates.modify_gate(
                gate_id, tenant_id, decision_by, decision_reason
            )
        elif decision == GateStatus.EXPIRED:
            gate, event = self._gates.expire_gate(gate_id, tenant_id)
        else:
            raise HarnessRegistryError(f"Invalid gate decision: {decision}")

        # Enrich event with run trace
        run = self._runs.get(gate.run_id)
        if run is not None:
            event = event.model_copy(
                update={
                    "trace_id": run.trace_id,
                    "workflow_type": run.workflow_type,
                }
            )
            self._telemetry._dispatch(event)

        return gate

    def get_gate(self, gate_id: str, tenant_id: str) -> HumanGate:
        """Get a gate with tenant scoping."""
        return self._gates.get_gate(gate_id, tenant_id)

    def list_gates_for_run(self, run_id: str, tenant_id: str) -> List[HumanGate]:
        """List gates for a run."""
        return self._gates.list_gates_for_run(run_id, tenant_id)

    # ---- Validation ----

    def validate_claims(
        self,
        tenant_id: str,
        requests: List[ClaimValidationRequest],
    ) -> List[ClaimValidationResult]:
        """Validate claims through the L5 hook."""
        return self._validation.validate_claims(requests)

    # ---- Checkpoints ----

    def get_checkpoints(self, run_id: str, tenant_id: str) -> List[HarnessCheckpoint]:
        """List checkpoints for a run."""
        return self._checkpoints.list_checkpoints_for_run(run_id, tenant_id)

    # ---- Tool Registry ----

    def register_tool(self, tool: ToolContract, tenant_id: str) -> ToolContract:
        """Register a tool contract."""
        return self._tools.register_tool(tool, tenant_id)

    def get_tool(self, tool_id: str, tenant_id: str) -> ToolContract:
        """Get a tool with tenant scoping."""
        return self._tools.get_tool(tool_id, tenant_id)

    # ---- Queries ----

    def list_runs(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[HarnessRunStatus] = None,
    ) -> List[HarnessRun]:
        """List runs with optional filtering."""
        runs = list(self._runs.values())
        if tenant_id is not None:
            runs = [r for r in runs if r.tenant_id == tenant_id]
        if status is not None:
            runs = [r for r in runs if r.status == status]
        return runs

    @property
    def telemetry(self) -> TelemetryEmitter:
        return self._telemetry

    @property
    def validation_available(self) -> bool:
        return self._validation.is_available
