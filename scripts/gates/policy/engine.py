"""Policy evaluation engine."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sdk.models import GateExecution, GateResult, GateVerdict

from .loader import PolicyLoader
from .models import GatePolicy, PolicyConfig


class PolicyEngine:
    """Evaluates gate results against policy."""
    
    def __init__(self, policy_path: Optional[str] = None):
        self.logger = logging.getLogger("gated.policy")
        self.loader = PolicyLoader()
        self.config: Optional[PolicyConfig] = None
        
        if policy_path:
            from pathlib import Path
            self.config = self.loader.load(Path(policy_path))
    
    def evaluate(self, execution: GateExecution, policy: Optional[GatePolicy] = None) -> GateVerdict:
        """
        Evaluate gate execution against policy.
        
        Args:
            execution: Gate execution results
            policy: Gate policy (uses loaded config if not provided)
            
        Returns:
            Verdict with blocks_release decision
        """
        if not policy and self.config:
            policy = self._find_policy(execution.gate_id)
        
        if not policy:
            # No policy found - fail closed
            return GateVerdict(
                result=GateResult.ERROR,
                blocks_release=True,
                reason=f"No policy found for gate: {execution.gate_id}",
            )
        
        # Check for errors
        errors = [r for r in execution.results if r.result == GateResult.ERROR]
        if errors and policy.fail_on_error:
            return GateVerdict(
                result=GateResult.ERROR,
                blocks_release=True,
                reason=f"{len(errors)} infrastructure errors",
                failed_checks=errors,
                duration_seconds=self._calculate_duration(execution),
            )
        
        # Check for failures
        failures = [r for r in execution.results if r.result == GateResult.FAIL]
        
        # Apply max_allowed_failures threshold
        if len(failures) > policy.max_allowed_failures:
            blocks_release = policy.severity.value in ("blocker", "critical")
            
            return GateVerdict(
                result=GateResult.FAIL,
                blocks_release=blocks_release,
                reason=f"{len(failures)} checks failed (max allowed: {policy.max_allowed_failures})",
                failed_checks=failures,
                duration_seconds=self._calculate_duration(execution),
            )
        
        # Check artifacts
        expected_artifacts = set(policy.artifacts)
        actual_artifacts = {str(a.path) for a in execution.artifacts}
        missing = expected_artifacts - actual_artifacts
        
        if missing and self.config and self.config.block_on_missing_artifacts:
            blocks_release = policy.severity.value in ("blocker", "critical")
            
            return GateVerdict(
                result=GateResult.FAIL,
                blocks_release=blocks_release,
                reason=f"Missing artifacts: {', '.join(missing)}",
                duration_seconds=self._calculate_duration(execution),
            )
        
        return GateVerdict(
            result=GateResult.PASS,
            blocks_release=False,
            reason="All checks passed",
            duration_seconds=self._calculate_duration(execution),
        )
    
    def evaluate_release(
        self,
        executions: list[GateExecution],
        profile: str = "release-candidate",
        stale_threshold_hours: int = 24,
    ) -> dict:
        """
        Evaluate all gates for release.
        
        Args:
            executions: List of gate executions
            profile: Release profile
            stale_threshold_hours: Max age for gate results
            
        Returns:
            Release verdict with aggregate results
        """
        gate_results = []
        blocks_release = False
        
        for execution in executions:
            # Find policy for this gate
            policy = self._find_policy(execution.gate_id)
            
            if not policy:
                blocks_release = True
                gate_results.append({
                    "gate_id": execution.gate_id,
                    "result": "missing_policy",
                    "blocks_release": True,
                    "reason": "No policy defined",
                })
                continue
            
            # Check if enabled for this profile
            if profile not in policy.enabled_profiles:
                gate_results.append({
                    "gate_id": execution.gate_id,
                    "result": "skipped",
                    "blocks_release": False,
                    "reason": f"Not enabled for profile: {profile}",
                })
                continue
            
            # Check staleness
            if execution.finished_at:
                age = datetime.utcnow() - execution.finished_at
                if age > timedelta(hours=stale_threshold_hours):
                    blocks_release = True
                    gate_results.append({
                        "gate_id": execution.gate_id,
                        "result": "stale",
                        "blocks_release": True,
                        "reason": f"Results stale ({age.total_seconds()/3600:.1f}h > {stale_threshold_hours}h)",
                    })
                    continue
            
            # Evaluate gate
            verdict = self.evaluate(execution, policy)
            
            if verdict.blocks_release:
                blocks_release = True
            
            gate_results.append({
                "gate_id": execution.gate_id,
                "result": verdict.result.value,
                "blocks_release": verdict.blocks_release,
                "reason": verdict.reason,
                "severity": policy.severity.value,
                "checks": len(execution.results),
            })
        
        return {
            "result": "blocked" if blocks_release else "approved",
            "blocks_release": blocks_release,
            "profile": profile,
            "gates_evaluated": len(executions),
            "gate_results": gate_results,
        }
    
    def _find_policy(self, gate_id: str) -> Optional[GatePolicy]:
        """Find policy for a gate."""
        if not self.config:
            return None
        
        for gate in self.config.gates:
            if gate.gate_id == gate_id:
                return gate
        
        return None
    
    def _calculate_duration(self, execution: GateExecution) -> float:
        """Calculate execution duration."""
        if execution.finished_at and execution.started_at:
            return (execution.finished_at - execution.started_at).total_seconds()
        return 0.0
