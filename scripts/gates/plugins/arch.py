"""Architecture conformance gate plugin."""

import ast
import json
import subprocess
from pathlib import Path
from typing import List, Set

from sdk.models import CheckResult, GateResult, GateSeverity
from sdk.plugin import GateContext, GatePlugin


class ArchitectureGate(GatePlugin):
    """Gate for architecture conformance validation."""
    
    @property
    def gate_id(self) -> str:
        return "arch"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.BLOCKER
    
    @property
    def expected_artifacts(self) -> list[str]:
        return [
            "arch/report.json",
            "arch/summary.md",
        ]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        """Run architecture conformance checks."""
        results = []
        
        # Check 1: Layer structure compliance
        layer_structure_ok = self._check_layer_structure(ctx.workspace_dir)
        results.append(CheckResult(
            name="layer_structure",
            result=GateResult.PASS if layer_structure_ok else GateResult.FAIL,
            value=layer_structure_ok,
            threshold=True,
            comparator="eq",
            message="Layer directory structure follows conventions",
        ))
        
        # Check 2: Import patterns (no cross-layer violations)
        import_violations = self._check_import_patterns(ctx.workspace_dir)
        results.append(CheckResult(
            name="import_patterns",
            result=GateResult.PASS if len(import_violations) == 0 else GateResult.FAIL,
            value=len(import_violations),
            threshold=0,
            comparator="eq",
            message=f"Found {len(import_violations)} import violations",
        ))
        
        # Check 3: Contract.md references in code
        contract_refs = self._check_contract_references(ctx.workspace_dir)
        results.append(CheckResult(
            name="contract_references",
            result=GateResult.PASS if contract_refs >= 10 else GateResult.FAIL,
            value=contract_refs,
            threshold=10,
            comparator="gte",
            message=f"Found {contract_refs} contract references in code",
        ))
        
        # Check 4: API route structure
        api_structure_ok = self._check_api_structure(ctx.workspace_dir)
        results.append(CheckResult(
            name="api_structure",
            result=GateResult.PASS if api_structure_ok else GateResult.FAIL,
            value=api_structure_ok,
            threshold=True,
            comparator="eq",
            message="API routes follow FastAPI conventions",
        ))
        
        # Check 5: Test directory structure
        test_structure_ok = self._check_test_structure(ctx.workspace_dir)
        results.append(CheckResult(
            name="test_structure",
            result=GateResult.PASS if test_structure_ok else GateResult.FAIL,
            value=test_structure_ok,
            threshold=True,
            comparator="eq",
            message="Test directories follow conventions",
        ))
        
        return results
    
    def _check_layer_structure(self, workspace: Path) -> bool:
        """Check that layers follow directory conventions."""
        required = [
            "value-fabric/layer1-ingestion/src",
            "value-fabric/layer2-extraction/src", 
            "value-fabric/layer3-knowledge/src",
            "value-fabric/layer4-agents/src",
            "value-fabric/layer5-ground-truth",
        ]
        
        for path in required:
            if not (workspace / path).exists():
                return False
        return True
    
    def _check_import_patterns(self, workspace: Path) -> List[str]:
        """Check for cross-layer import violations."""
        violations = []
        
        # Scan Python files for problematic imports
        for py_file in workspace.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        # Check for cross-layer imports
                        if "layer4" in str(py_file) and "layer1" in module:
                            violations.append(f"{py_file}: imports {module}")
            except SyntaxError:
                continue
        
        return violations[:20]  # Limit to first 20
    
    def _check_contract_references(self, workspace: Path) -> int:
        """Count CONTRACT.md references in code."""
        refs = 0
        contract_md = workspace / "CONTRACT.md"
        
        if not contract_md.exists():
            return 0
        
        for py_file in workspace.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "CONTRACT.md" in content or "Contract" in content:
                    refs += 1
            except:
                pass
        
        return refs
    
    def _check_api_structure(self, workspace: Path) -> bool:
        """Check API route structure."""
        # Look for FastAPI routers in expected locations
        api_paths = [
            workspace / "value-fabric/layer3-knowledge/src/api/routes",
            workspace / "value-fabric/layer4-agents/src/api/routes",
        ]
        
        found_routes = 0
        for api_path in api_paths:
            if api_path.exists():
                found_routes += len(list(api_path.glob("*.py")))
        
        return found_routes >= 3
    
    def _check_test_structure(self, workspace: Path) -> bool:
        """Check test directory structure."""
        test_paths = [
            workspace / "tests",
            workspace / "value-fabric/layer1-ingestion/tests",
            workspace / "value-fabric/layer2-extraction/tests",
            workspace / "value-fabric/layer3-knowledge/tests",
            workspace / "value-fabric/layer4-agents/tests",
        ]
        
        found_tests = sum(1 for p in test_paths if p.exists())
        return found_tests >= 3
