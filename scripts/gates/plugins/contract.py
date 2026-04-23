"""Contract compliance gate plugin."""

import json
import subprocess
from pathlib import Path

from sdk.models import CheckResult, GateResult, GateSeverity
from sdk.plugin import GateContext, GatePlugin


class ContractGate(GatePlugin):
    """Gate for contract compliance validation."""
    
    @property
    def gate_id(self) -> str:
        return "contract"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.WARNING  # Contract drift is advisory
    
    @property
    def expected_artifacts(self) -> list[str]:
        return [
            "contract/report.json",
            "contract/report.md",
        ]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        """Run contract compliance checks."""
        results = []
        
        # Run the existing contract compliance script
        try:
            # First, run contract gate script
            result = subprocess.run(
                ["python", "scripts/gates/run_contract.py", "--profile", ctx.profile.value],
                capture_output=True,
                text=True,
                cwd=ctx.workspace_dir,
                timeout=300,
            )
            
            # Parse results from artifacts
            report_path = ctx.workspace_dir / "artifacts/contract/contract-gate-report.json"
            if report_path.exists():
                with open(report_path) as f:
                    data = json.load(f)
                
                violations = data.get("violations", [])
                
                results.append(CheckResult(
                    name="contract_violations",
                    result=GateResult.PASS if len(violations) == 0 else GateResult.FAIL,
                    value=len(violations),
                    threshold=0,
                    comparator="eq",
                    message=f"Found {len(violations)} contract violations",
                ))
                
                results.append(CheckResult(
                    name="contract_doc_exists",
                    result=GateResult.PASS if data.get("contract_doc_exists") else GateResult.FAIL,
                    value=data.get("contract_doc_exists", False),
                    threshold=True,
                    comparator="eq",
                ))
                
                results.append(CheckResult(
                    name="eslint_plugin_tests",
                    result=GateResult.PASS if data.get("eslint_plugin_tests_passed") else GateResult.FAIL,
                    value=data.get("eslint_plugin_tests_passed", False),
                    threshold=True,
                    comparator="eq",
                ))
            else:
                # Fallback: check for CONTRACT.md
                contract_md = ctx.workspace_dir / "CONTRACT.md"
                if contract_md.exists():
                    results.append(CheckResult(
                        name="contract_doc_exists",
                        result=GateResult.PASS,
                        value=True,
                        threshold=True,
                        comparator="eq",
                    ))
                else:
                    results.append(CheckResult(
                        name="contract_doc_exists",
                        result=GateResult.FAIL,
                        value=False,
                        threshold=True,
                        comparator="eq",
                        message="CONTRACT.md not found",
                    ))
        
        except subprocess.TimeoutExpired:
            results.append(CheckResult(
                name="contract_check",
                result=GateResult.ERROR,
                message="Contract check timed out after 300s",
            ))
        except Exception as e:
            results.append(CheckResult(
                name="contract_check",
                result=GateResult.ERROR,
                message=f"Contract check failed: {e}",
            ))
        
        return results
