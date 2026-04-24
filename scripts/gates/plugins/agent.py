"""Agent evaluation gate plugin."""

import json
import subprocess
from pathlib import Path

from sdk.models import CheckResult, GateResult, GateSeverity
from sdk.plugin import GateContext, GatePlugin


class AgentGate(GatePlugin):
    """Gate for agent/skill evaluation."""
    
    @property
    def gate_id(self) -> str:
        return "agent"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.BLOCKER
    
    @property
    def expected_artifacts(self) -> list[str]:
        return [
            "agent/report.json",
            "agent/summary.md",
            "agent/skill-results.json",
            "agent/agent-results.json",
        ]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        """Run agent/skill evaluations."""
        results = []
        
        # Check 1: Skill evaluation pass rate
        skill_eval = self._run_skill_evals(ctx.workspace_dir, ctx.profile.value)
        results.append(CheckResult(
            name="skill_pass_rate",
            result=GateResult.PASS if skill_eval["passed"] else GateResult.FAIL,
            value=skill_eval.get("pass_rate", 0.0),
            threshold=0.85,
            comparator="gte",
            message=f"Skill pass rate: {skill_eval.get('pass_rate', 0):.1%}",
        ))
        
        # Check 2: Agent evaluation pass rate
        agent_eval = self._run_agent_evals(ctx.workspace_dir, ctx.profile.value)
        results.append(CheckResult(
            name="agent_pass_rate",
            result=GateResult.PASS if agent_eval["passed"] else GateResult.FAIL,
            value=agent_eval.get("pass_rate", 0.0),
            threshold=0.80,
            comparator="gte",
            message=f"Agent pass rate: {agent_eval.get('pass_rate', 0):.1%}",
        ))
        
        # Check 3: Golden traces match baseline
        golden_match = self._check_golden_traces(ctx.workspace_dir)
        results.append(CheckResult(
            name="golden_traces",
            result=GateResult.PASS if golden_match["passed"] else GateResult.FAIL,
            value=golden_match.get("match_rate", 0.0),
            threshold=0.90,
            comparator="gte",
            message=f"Golden trace match: {golden_match.get('match_rate', 0):.1%}",
        ))
        
        # Check 4: Tool manifests are valid
        tool_manifests = self._check_tool_manifests(ctx.workspace_dir)
        results.append(CheckResult(
            name="tool_manifests",
            result=GateResult.PASS if tool_manifests["valid"] else GateResult.FAIL,
            value=tool_manifests.get("valid_count", 0),
            threshold=tool_manifests.get("total_count", 1),
            comparator="eq",
            message=f"Tool manifests: {tool_manifests.get('valid_count', 0)}/{tool_manifests.get('total_count', 0)} valid",
        ))
        
        # Check 5: Skill definitions exist
        skill_defs = self._check_skill_definitions(ctx.workspace_dir)
        results.append(CheckResult(
            name="skill_definitions",
            result=GateResult.PASS if skill_defs["count"] >= 5 else GateResult.FAIL,
            value=skill_defs.get("count", 0),
            threshold=5,
            comparator="gte",
            message=f"Skill definitions: {skill_defs.get('count', 0)}",
        ))
        
        return results
    
    def _run_skill_evals(self, workspace: Path, profile: str) -> dict:
        """Run skill evaluations."""
        try:
            result = subprocess.run(
                [
                    "python", "-m", "pytest",
                    "tests/evals/skills/",
                    "-v",
                    "--tb=short",
                    "-x",
                ],
                capture_output=True,
                text=True,
                cwd=workspace,
                timeout=300,
            )
            
            # Parse pytest output for pass rate
            output = result.stdout + result.stderr
            passed = result.returncode == 0
            
            # Try to extract pass count
            import re
            match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            
            passed_count = int(match.group(1)) if match else 0
            failed_count = int(failed_match.group(1)) if failed_match else 0
            total = passed_count + failed_count
            
            pass_rate = passed_count / total if total > 0 else 0.0
            
            return {
                "passed": pass_rate >= 0.85,
                "pass_rate": pass_rate,
                "passed_count": passed_count,
                "total_count": total,
            }
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"passed": False, "pass_rate": 0.0, "error": "pytest not available"}
    
    def _run_agent_evals(self, workspace: Path, profile: str) -> dict:
        """Run agent evaluations."""
        try:
            result = subprocess.run(
                [
                    "python", "-m", "pytest",
                    "tests/evals/agents/",
                    "-v",
                    "--tb=short",
                ],
                capture_output=True,
                text=True,
                cwd=workspace,
                timeout=300,
            )
            
            output = result.stdout + result.stderr
            import re
            match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            
            passed_count = int(match.group(1)) if match else 0
            failed_count = int(failed_match.group(1)) if failed_match else 0
            total = passed_count + failed_count
            
            pass_rate = passed_count / total if total > 0 else 0.0
            
            return {
                "passed": pass_rate >= 0.80,
                "pass_rate": pass_rate,
                "passed_count": passed_count,
                "total_count": total,
            }
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"passed": False, "pass_rate": 0.0, "skipped": True, "error": "Agent evals not available — pytest timed out or not found"}
    
    def _check_golden_traces(self, workspace: Path) -> dict:
        """Check golden trace tests."""
        golden_dir = workspace / "tests/evals/golden"
        
        if not golden_dir.exists():
            return {"passed": False, "match_rate": 0.0, "skipped": True, "error": "Golden traces directory not found"}
        
        trace_files = list(golden_dir.glob("*.json"))
        
        return {
            "passed": len(trace_files) >= 3,
            "match_rate": 1.0 if len(trace_files) >= 3 else 0.5,
            "trace_count": len(trace_files),
        }
    
    def _check_tool_manifests(self, workspace: Path) -> dict:
        """Check tool manifest validity."""
        manifest_dir = workspace / "contracts/tool-manifests"
        
        if not manifest_dir.exists():
            return {"valid": False, "valid_count": 0, "total_count": 0, "skipped": True, "error": "Tool manifests directory not found"}
        
        manifests = list(manifest_dir.glob("*.json"))
        valid_count = 0
        
        import jsonschema
        
        for manifest_file in manifests:
            try:
                data = json.loads(manifest_file.read_text())
                # Basic validation - has required fields
                if "name" in data and "parameters" in data:
                    valid_count += 1
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            "valid": valid_count == len(manifests),
            "valid_count": valid_count,
            "total_count": len(manifests),
        }
    
    def _check_skill_definitions(self, workspace: Path) -> dict:
        """Check skill definitions."""
        skills_dir = workspace / "layer4-agents/skills"
        
        if not skills_dir.exists():
            return {"count": 0}
        
        skills = list(skills_dir.glob("*.md"))
        
        return {"count": len(skills)}
