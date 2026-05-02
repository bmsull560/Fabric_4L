"""Invariant evaluator for GATE framework.

Enforces per-agent runtime invariants declared in ABOM manifests:
- Tool call count limits
- Budget caps
- Human approval requirements
- Custom invariant hooks

GATE Framework §2.3 — InvariantEvaluator
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from .abom import AgentBillOfMaterials
from value_fabric.shared.models.typed_dict import TypedDictModel


class InvariantEvaluator_get_run_summaryResult(TypedDictModel):
    agent_type: Any
    budget_limit_usd: Any
    budget_used_usd: Any
    max_tool_calls: Any
    tool_calls: Any
    violations_would_occur: bool

logger = logging.getLogger(__name__)


@dataclass
class InvariantResult:
    """Result of invariant evaluation."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class InvariantEvaluator:
    """Evaluates runtime invariants from ABOM manifests.

    Tracks per-run state (tool call counts, budget usage) and
    evaluates invariant constraints before each tool invocation.

    Usage:
        evaluator = InvariantEvaluator(abom)
        result = evaluator.check_pre_invocation("crm_sync", {"amount": 1.50})
        if not result.passed:
            raise InvariantViolation(result.violations)
        evaluator.record_invocation("crm_sync", cost_usd=1.50)
    """

    def __init__(self, abom: AgentBillOfMaterials) -> None:
        self._abom = abom
        self._tool_call_count: int = 0
        self._budget_used_usd: float = 0.0
        self._tool_call_log: list[dict[str, Any]] = []

    @property
    def tool_call_count(self) -> int:
        """Current tool call count for this run."""
        return self._tool_call_count

    @property
    def budget_used_usd(self) -> float:
        """Current budget usage for this run."""
        return self._budget_used_usd

    def check_pre_invocation(
        self,
        tool_name: str,
        input_data: dict[str, Any] | None = None,
        estimated_cost_usd: float = 0.0,
    ) -> InvariantResult:
        """Evaluate invariants before a tool invocation.

        Args:
            tool_name: Name of the tool about to be invoked.
            input_data: Tool input parameters (for custom invariants).
            estimated_cost_usd: Estimated cost of this invocation.

        Returns:
            InvariantResult with pass/fail and any violations.
        """
        violations: list[str] = []
        warnings: list[str] = []
        inv = self._abom.invariants

        # Check tool call limit
        if self._tool_call_count >= inv.max_tool_calls_per_run:
            violations.append(
                f"Tool call limit exceeded: {self._tool_call_count}/{inv.max_tool_calls_per_run}"
            )

        # Check budget limit
        if inv.budget_limit_usd is not None:
            projected = self._budget_used_usd + estimated_cost_usd
            if projected > inv.budget_limit_usd:
                violations.append(
                    f"Budget limit exceeded: ${projected:.2f} > ${inv.budget_limit_usd:.2f}"
                )
            elif projected > inv.budget_limit_usd * 0.8:
                warnings.append(
                    f"Budget usage at {projected / inv.budget_limit_usd * 100:.0f}%"
                )

        # Check human approval requirement
        if tool_name in inv.require_human_approval:
            # In production, this would check an approval queue
            approval_mode = os.getenv("GATE_APPROVAL_MODE", "enforce")
            if approval_mode == "enforce":
                violations.append(
                    f"Tool '{tool_name}' requires human approval (GATE_APPROVAL_MODE=enforce)"
                )
            else:
                warnings.append(
                    f"Tool '{tool_name}' requires human approval (bypassed in {approval_mode} mode)"
                )

        return InvariantResult(
            passed=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )

    def record_invocation(
        self,
        tool_name: str,
        cost_usd: float = 0.0,
        success: bool = True,
    ) -> None:
        """Record a completed tool invocation for invariant tracking.

        Args:
            tool_name: Name of the tool that was invoked.
            cost_usd: Actual cost of the invocation.
            success: Whether the invocation succeeded.
        """
        self._tool_call_count += 1
        self._budget_used_usd += cost_usd
        self._tool_call_log.append({
            "tool_name": tool_name,
            "cost_usd": cost_usd,
            "success": success,
            "call_number": self._tool_call_count,
        })

    def reset(self) -> None:
        """Reset per-run state (for new agent runs)."""
        self._tool_call_count = 0
        self._budget_used_usd = 0.0
        self._tool_call_log.clear()

    def get_run_summary(self) -> dict[str, Any]:
        """Return summary of invariant state for this run."""
        inv = self._abom.invariants
        return InvariantEvaluator_get_run_summaryResult.model_validate({
            "agent_type": self._abom.agent_type,
            "tool_calls": self._tool_call_count,
            "max_tool_calls": inv.max_tool_calls_per_run,
            "budget_used_usd": self._budget_used_usd,
            "budget_limit_usd": inv.budget_limit_usd,
            "violations_would_occur": self._tool_call_count >= inv.max_tool_calls_per_run,
        })


