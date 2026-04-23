"""Gate daemon execution engine."""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from policy.engine import PolicyEngine
from sdk.models import GateExecution, GateProfile, GateResult, GateVerdict
from sdk.plugin import GateContext, GatePlugin


class GateDaemon:
    """Central gate execution orchestrator."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("gated.daemon")
        self._plugins: dict[str, GatePlugin] = {}
        self._executions: dict[str, GateExecution] = {}
        self._semaphore = asyncio.Semaphore(config.max_concurrent_gates)
        self._policy_engine: Optional[PolicyEngine] = None
        
        # Initialize policy engine if policy file exists
        if hasattr(config, 'policy_file') and config.policy_file:
            policy_path = Path(config.policy_file)
            if policy_path.exists():
                self._policy_engine = PolicyEngine(policy_path=str(policy_path))
                self.logger.info(f"Loaded policy from {policy_path}")
    
    def register_plugin(self, plugin: GatePlugin) -> None:
        """Register a gate plugin."""
        self._plugins[plugin.gate_id] = plugin
        self.logger.info(f"Registered gate plugin: {plugin.gate_id}")
    
    def get_plugin(self, gate_id: str) -> Optional[GatePlugin]:
        """Get a registered plugin by ID."""
        return self._plugins.get(gate_id)
    
    def list_gates(self) -> list[dict]:
        """List all registered gates."""
        return [
            {
                "gate_id": p.gate_id,
                "severity": p.severity.value,
                "artifacts": p.expected_artifacts,
            }
            for p in self._plugins.values()
        ]
    
    async def execute_gate(
        self,
        gate_id: str,
        profile: str = "pr-fast",
        trace_id: Optional[str] = None,
    ) -> GateExecution:
        """
        Execute a single gate.
        
        Args:
            gate_id: Gate identifier
            profile: Execution profile
            trace_id: Optional trace ID for observability
            
        Returns:
            Gate execution record
        """
        plugin = self.get_plugin(gate_id)
        if not plugin:
            raise ValueError(f"Unknown gate: {gate_id}")
        
        async with self._semaphore:
            if not trace_id:
                trace_id = str(uuid4())
            
            self.logger.info(f"Executing gate {gate_id} with profile {profile}")
            
            # Create context
            ctx = GateContext(
                gate_id=gate_id,
                profile=GateProfile(profile),
                workspace_dir=Path.cwd(),
                output_dir=Path(self.config.artifact_store),
                trace_id=trace_id,
            )
            
            # Run gate
            execution = await asyncio.to_thread(plugin.run, ctx)
            
            # Evaluate against policy
            if self._policy_engine:
                verdict = self._policy_engine.evaluate(execution)
                execution.verdict = verdict
            
            self._executions[str(execution.execution_id)] = execution
            
            self.logger.info(
                f"Gate {gate_id} completed: {len(execution.results)} checks, "
                f"{len(execution.artifacts)} artifacts, "
                f"verdict: {execution.verdict.result.value if execution.verdict else 'unknown'}"
            )
            
            return execution
    
    def get_execution(self, execution_id: str) -> Optional[GateExecution]:
        """Get execution by ID."""
        return self._executions.get(execution_id)
    
    def evaluate_release(
        self,
        gate_ids: Optional[list[str]] = None,
        block_on_missing: bool = True,
        stale_threshold_hours: int = 24,
        profile: str = "release-candidate",
    ) -> dict:
        """
        Evaluate all gates for release.
        
        Args:
            gate_ids: Specific gates to evaluate (default: all)
            block_on_missing: Fail if artifacts missing
            stale_threshold_hours: Max age for gate results
            profile: Release profile
            
        Returns:
            Release verdict
        """
        # Use policy engine if available for comprehensive evaluation
        if self._policy_engine:
            executions = list(self._executions.values())
            return self._policy_engine.evaluate_release(
                executions,
                profile=profile,
                stale_threshold_hours=stale_threshold_hours,
            )
        
        # Fallback to basic evaluation
        if not gate_ids:
            gate_ids = list(self._plugins.keys())
        
        results = []
        blocks_release = False
        
        for gate_id in gate_ids:
            plugin = self.get_plugin(gate_id)
            
            # Find latest execution
            latest = None
            for exec in self._executions.values():
                if exec.gate_id == gate_id:
                    if not latest or exec.started_at > latest.started_at:
                        latest = exec
            
            if not latest:
                if block_on_missing:
                    blocks_release = True
                    results.append({
                        "gate_id": gate_id,
                        "result": "missing",
                        "blocks_release": True,
                        "reason": "No execution found",
                    })
                continue
            
            # Check for errors
            errors = [r for r in latest.results if r.result == GateResult.ERROR]
            failures = [r for r in latest.results if r.result == GateResult.FAIL]
            
            gate_blocks = False
            if errors:
                gate_blocks = plugin.severity.value in ("blocker", "critical")
            elif failures:
                gate_blocks = plugin.severity.value in ("blocker", "critical")
            
            if gate_blocks:
                blocks_release = True
            
            results.append({
                "gate_id": gate_id,
                "result": latest.verdict.result.value if latest.verdict else "unknown",
                "blocks_release": gate_blocks,
                "artifacts": [str(a.path) for a in latest.artifacts],
                "checks": len(latest.results),
                "failures": len(failures),
                "errors": len(errors),
            })
        
        return {
            "result": "blocked" if blocks_release else "approved",
            "blocks_release": blocks_release,
            "profile": profile,
            "gates_evaluated": len(gate_ids),
            "gate_results": results,
        }
