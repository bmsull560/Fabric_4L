"""Smoke test gate plugin."""

import json
import subprocess
from pathlib import Path

from sdk.models import CheckResult, GateResult, GateSeverity
from sdk.plugin import GateContext, GatePlugin


class SmokeGate(GatePlugin):
    """Gate for cross-layer smoke testing."""
    
    @property
    def gate_id(self) -> str:
        return "smoke"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.BLOCKER
    
    @property
    def expected_artifacts(self) -> list[str]:
        return [
            "smoke/report.json",
            "smoke/summary.md",
        ]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        """Run smoke tests."""
        results = []
        
        try:
            # Run the production smoke test script
            result = subprocess.run(
                ["python", "scripts/smoke/production_smoke.py", "--json"],
                capture_output=True,
                text=True,
                cwd=ctx.workspace_dir,
                timeout=600,
            )
            
            # Parse results
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                # Try to find report file
                report_path = ctx.workspace_dir / "artifacts/smoke/report.json"
                if report_path.exists():
                    with open(report_path) as f:
                        data = json.load(f)
                else:
                    data = {}
            
            # Extract stage results
            stages = data.get("stages", [])
            stage_results = {s.get("name", "unknown"): s.get("status", "unknown") for s in stages}
            
            # Key stages for smoke testing
            critical_stages = [
                "layer2_health",
                "layer3_health",
                "layer4_health",
                "extract_ingest_flow",
                "graph_query",
                "hybrid_search",
            ]
            
            for stage in critical_stages:
                status = stage_results.get(stage, "missing")
                passed = status == "passed"
                
                results.append(CheckResult(
                    name=f"smoke_{stage}",
                    result=GateResult.PASS if passed else GateResult.FAIL,
                    value=status,
                    threshold="passed",
                    comparator="eq",
                    message=f"Stage {stage}: {status}",
                ))
            
            # Overall pass/fail
            overall_passed = data.get("overall_passed", False)
            results.append(CheckResult(
                name="smoke_overall",
                result=GateResult.PASS if overall_passed else GateResult.FAIL,
                value=overall_passed,
                threshold=True,
                comparator="eq",
                message=f"Smoke tests: {'passed' if overall_passed else 'failed'}",
            ))
            
            # Duration
            duration = data.get("duration_seconds", 0)
            results.append(CheckResult(
                name="smoke_duration",
                result=GateResult.PASS,  # Duration is informational
                value=duration,
                threshold=300,  # 5 minutes
                comparator="lte",
                message=f"Duration: {duration:.1f}s",
            ))
        
        except subprocess.TimeoutExpired:
            results.append(CheckResult(
                name="smoke_tests",
                result=GateResult.ERROR,
                message="Smoke tests timed out after 600s",
            ))
        except Exception as e:
            results.append(CheckResult(
                name="smoke_tests",
                result=GateResult.ERROR,
                message=f"Smoke tests failed: {e}",
            ))
        
        return results
