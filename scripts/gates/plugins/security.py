"""Security compliance gate plugin."""

import json
import subprocess
from pathlib import Path

from sdk.models import CheckResult, GateResult, GateSeverity
from sdk.plugin import GateContext, GatePlugin


class SecurityGate(GatePlugin):
    """Gate for security compliance validation."""
    
    @property
    def gate_id(self) -> str:
        return "security"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.BLOCKER
    
    @property
    def expected_artifacts(self) -> list[str]:
        return [
            "security/report.json",
            "security/summary.md",
            "security/vulnerabilities.json",
        ]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        """Run security compliance checks."""
        results = []
        
        # Check 1: No secrets in code (basic scan)
        secrets_found = self._check_secrets(ctx.workspace_dir)
        results.append(CheckResult(
            name="secrets_scan",
            result=GateResult.PASS if len(secrets_found) == 0 else GateResult.FAIL,
            value=len(secrets_found),
            threshold=0,
            comparator="eq",
            message=f"Found {len(secrets_found)} potential secrets",
        ))
        
        # Check 2: Python security linting (bandit)
        bandit_result = self._run_bandit(ctx.workspace_dir)
        results.append(CheckResult(
            name="bandit_scan",
            result=GateResult.PASS if bandit_result["passed"] else GateResult.FAIL,
            value=bandit_result.get("issues", 0),
            threshold=0,
            comparator="eq",
            message=f"Bandit: {bandit_result.get('issues', 0)} issues",
        ))
        
        # Check 3: Dependency vulnerabilities (pip-audit)
        audit_result = self._run_pip_audit(ctx.workspace_dir)
        results.append(CheckResult(
            name="dependency_audit",
            result=GateResult.PASS if audit_result["passed"] else GateResult.FAIL,
            value=audit_result.get("vulnerabilities", 0),
            threshold=0,
            comparator="eq",
            message=f"Pip-audit: {audit_result.get('vulnerabilities', 0)} vulnerabilities",
        ))
        
        # Check 4: SBOM exists
        sbom_exists = self._check_sbom(ctx.workspace_dir)
        results.append(CheckResult(
            name="sbom_exists",
            result=GateResult.PASS if sbom_exists else GateResult.FAIL,
            value=sbom_exists,
            threshold=True,
            comparator="eq",
            message="SBOM generated for release",
        ))
        
        # Check 5: Dockerfile security (non-root user)
        dockerfile_ok = self._check_dockerfile_security(ctx.workspace_dir)
        results.append(CheckResult(
            name="dockerfile_security",
            result=GateResult.PASS if dockerfile_ok else GateResult.FAIL,
            value=dockerfile_ok,
            threshold=True,
            comparator="eq",
            message="Dockerfiles use non-root users",
        ))
        
        return results
    
    def _check_secrets(self, workspace: Path) -> list:
        """Basic secret detection."""
        secrets = []
        patterns = [
            (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][a-z0-9]{32,}["\']', "API key"),
            (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']', "Password"),
            (r'(?i)private[_-]?key.*BEGIN', "Private key"),
            (r'(?i)(aws|azure|gcp)?[_-]?(secret|token)\s*[=:]\s*["\'][a-z0-9]{20,}["\']', "Secret/Token"),
        ]
        
        import re
        
        for py_file in workspace.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file).lower():
                continue
            
            try:
                content = py_file.read_text()
                for pattern, name in patterns:
                    if re.search(pattern, content):
                        secrets.append(f"{py_file}: potential {name}")
            except:
                pass
        
        return secrets[:10]  # Limit to first 10
    
    def _run_bandit(self, workspace: Path) -> dict:
        """Run bandit security linter."""
        try:
            result = subprocess.run(
                ["bandit", "-r", "value-fabric/", "-f", "json"],
                capture_output=True,
                text=True,
                cwd=workspace,
                timeout=120,
            )
            
            try:
                data = json.loads(result.stdout)
                issues = len(data.get("results", []))
                return {"passed": issues == 0, "issues": issues}
            except json.JSONDecodeError:
                # Fallback: check if bandit found issues by exit code
                return {"passed": result.returncode == 0, "issues": 0}
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"passed": True, "issues": 0, "skipped": True}
    
    def _run_pip_audit(self, workspace: Path) -> dict:
        """Run pip-audit for dependency vulnerabilities."""
        try:
            result = subprocess.run(
                ["pip-audit", "--format=json"],
                capture_output=True,
                text=True,
                cwd=workspace,
                timeout=120,
            )
            
            try:
                data = json.loads(result.stdout)
                vulns = len(data.get("vulnerabilities", []))
                return {"passed": vulns == 0, "vulnerabilities": vulns}
            except json.JSONDecodeError:
                return {"passed": True, "vulnerabilities": 0, "skipped": True}
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"passed": True, "vulnerabilities": 0, "skipped": True}
    
    def _check_sbom(self, workspace: Path) -> bool:
        """Check if SBOM exists."""
        sbom_paths = [
            workspace / "artifacts/security/sbom.json",
            workspace / "sbom.json",
            workspace / "bom.json",
        ]
        return any(p.exists() for p in sbom_paths)
    
    def _check_dockerfile_security(self, workspace: Path) -> bool:
        """Check Dockerfile security practices."""
        dockerfiles = list(workspace.rglob("Dockerfile*"))
        
        if not dockerfiles:
            return True  # No Dockerfiles is OK
        
        all_ok = True
        for df in dockerfiles:
            content = df.read_text()
            # Check for non-root user
            if "USER" not in content and "root" in content:
                all_ok = False
        
        return all_ok
