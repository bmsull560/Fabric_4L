"""Chaos engineering gate plugin."""

import json
from pathlib import Path

from sdk.models import CheckResult, GateResult, GateSeverity
from sdk.plugin import GateContext, GatePlugin


class ChaosGate(GatePlugin):
    """Gate for chaos engineering validation."""
    
    @property
    def gate_id(self) -> str:
        return "chaos"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.CRITICAL
    
    @property
    def expected_artifacts(self) -> list[str]:
        return [
            "chaos/report.json",
            "chaos/summary.md",
            "chaos/experiments/*.yaml",
        ]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        """Run chaos engineering checks."""
        results = []
        
        # Check 1: Litmus experiments exist
        experiments = self._check_litmus_experiments(ctx.workspace_dir)
        results.append(CheckResult(
            name="litmus_experiments",
            result=GateResult.PASS if len(experiments) >= 4 else GateResult.FAIL,
            value=len(experiments),
            threshold=4,
            comparator="gte",
            message=f"Found {len(experiments)} chaos experiments",
        ))
        
        # Check 2: Chaos experiment coverage (all layers)
        coverage = self._check_layer_coverage(ctx.workspace_dir)
        results.append(CheckResult(
            name="layer_coverage",
            result=GateResult.PASS if coverage["covered_layers"] >= 3 else GateResult.FAIL,
            value=coverage["covered_layers"],
            threshold=3,
            comparator="gte",
            message=f"Layers with chaos coverage: {coverage['covered_layers']}",
        ))
        
        # Check 3: Experiment types
        types = self._check_experiment_types(ctx.workspace_dir)
        required_types = ["pod-delete", "network-partition", "cpu-stress", "memory-stress"]
        missing_types = [t for t in required_types if t not in types]
        
        results.append(CheckResult(
            name="experiment_types",
            result=GateResult.PASS if len(missing_types) == 0 else GateResult.FAIL,
            value=len(types),
            threshold=4,
            comparator="gte",
            message=f"Experiment types: {', '.join(types)}",
        ))
        
        # Check 4: Post-chaos validation
        validation_exists = self._check_post_chaos_validation(ctx.workspace_dir)
        results.append(CheckResult(
            name="post_chaos_validation",
            result=GateResult.PASS if validation_exists else GateResult.FAIL,
            value=validation_exists,
            threshold=True,
            comparator="eq",
            message="Post-chaos validation tests exist",
        ))
        
        # Check 5: Chaos results available (if workflow ran)
        results_available = self._check_chaos_results(ctx.workspace_dir)
        results.append(CheckResult(
            name="chaos_results",
            result=GateResult.PASS if results_available else GateResult.WARNING,
            value=results_available,
            threshold=True,
            comparator="eq",
            message="Chaos experiment results available",
        ))
        
        return results
    
    def _check_litmus_experiments(self, workspace: Path) -> list:
        """Check for Litmus chaos experiments."""
        experiment_dir = workspace / "k8s/chaos/litmus-experiments"
        
        if not experiment_dir.exists():
            return []
        
        experiments = []
        for exp_file in experiment_dir.glob("*.yaml"):
            content = exp_file.read_text()
            if "litmuschaos.io" in content or "ChaosExperiment" in content:
                experiments.append(exp_file.name)
        
        return experiments
    
    def _check_layer_coverage(self, workspace: Path) -> dict:
        """Check which layers have chaos coverage."""
        experiments = self._check_litmus_experiments(workspace)
        
        layers = set()
        for exp in experiments:
            if "l1" in exp.lower() or "layer1" in exp.lower():
                layers.add("layer1")
            if "l2" in exp.lower() or "layer2" in exp.lower():
                layers.add("layer2")
            if "l3" in exp.lower() or "layer3" in exp.lower():
                layers.add("layer3")
            if "l4" in exp.lower() or "layer4" in exp.lower():
                layers.add("layer4")
        
        return {
            "covered_layers": len(layers),
            "layers": list(layers),
        }
    
    def _check_experiment_types(self, workspace: Path) -> list:
        """Check which experiment types are defined."""
        experiments = self._check_litmus_experiments(workspace)
        
        types = []
        type_patterns = {
            "pod-delete": ["pod-delete", "pod-failure"],
            "network-partition": ["network", "partition"],
            "cpu-stress": ["cpu", "stress"],
            "memory-stress": ["memory", "mem"],
            "io-stress": ["io", "disk"],
            "pod-autoscaler": ["autoscaler", "hpa"],
        }
        
        for exp in experiments:
            exp_lower = exp.lower()
            for exp_type, patterns in type_patterns.items():
                if any(p in exp_lower for p in patterns):
                    types.append(exp_type)
                    break
        
        return list(set(types))
    
    def _check_post_chaos_validation(self, workspace: Path) -> bool:
        """Check if post-chaos validation tests exist."""
        # Look for test files that might be post-chaos tests
        test_patterns = [
            workspace / "tests/chaos",
            workspace / "tests/test_chaos",
        ]
        
        for pattern in test_patterns:
            if pattern.exists():
                return True
        
        # Check workflow for post-chaos steps
        workflow = workspace / ".github/workflows/chaos-testing.yml"
        if workflow.exists():
            content = workflow.read_text()
            if "post-chaos" in content.lower() or "validation" in content.lower():
                return True
        
        return False
    
    def _check_chaos_results(self, workspace: Path) -> bool:
        """Check if chaos results are available."""
        result_paths = [
            workspace / "artifacts/chaos/results.json",
            workspace / "artifacts/chaos/report.json",
        ]
        
        return any(p.exists() for p in result_paths)
