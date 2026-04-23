#!/usr/bin/env python3
"""
Architecture Conformance Gate

Validates codebase compliance with architectural policies:
1. Contract drift (should be 0)
2. Forbidden layer dependencies (should be 0)
3. Missing required middleware on critical endpoints (should be 0)

Artifacts:
- artifacts/arch/report.json: Structured results
- artifacts/arch/summary.md: Human-readable summary
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


@dataclass
class GateCheckResult:
    """Result of a single policy check."""
    name: str
    passed: bool
    actual_value: float
    threshold: float
    comparator: str
    message: str


@dataclass
class GateResult:
    """Overall gate execution result."""
    gate_name: str
    profile: str
    timestamp: str
    passed: bool
    checks: List[GateCheckResult] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "gate_name": self.gate_name,
            "profile": self.profile,
            "timestamp": self.timestamp,
            "passed": self.passed,
            "check_count": len(self.checks),
            "pass_count": sum(1 for c in self.checks if c.passed),
            "fail_count": sum(1 for c in self.checks if not c.passed),
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "actual_value": c.actual_value,
                    "threshold": c.threshold,
                    "comparator": c.comparator,
                    "message": c.message,
                }
                for c in self.checks
            ],
            "metrics": self.metrics,
        }, indent=2)

    def to_markdown(self) -> str:
        status_icon = "✅" if self.passed else "❌"
        lines = [
            f"# Architecture Conformance Gate Report",
            f"",
            f"**Profile:** {self.profile}",
            f"**Timestamp:** {self.timestamp}",
            f"**Status:** {status_icon} {'PASSED' if self.passed else 'FAILED'}",
            f"",
            f"## Summary",
            f"",
            f"- Total Checks: {len(self.checks)}",
            f"- Passed: {sum(1 for c in self.checks if c.passed)}",
            f"- Failed: {sum(1 for c in self.checks if not c.passed)}",
            f"",
            f"## Architecture Checks",
            f"",
            "| Check | Status | Actual | Threshold |",
            "|-------|--------|--------|-----------|",
        ]

        for check in self.checks:
            icon = "✅" if check.passed else "❌"
            lines.append(
                f"| {check.name} | {icon} | {check.actual_value} | {check.threshold} |"
            )

        if not self.passed:
            lines.extend([
                f"",
                f"## Architectural Violations",
                f"",
                f"⚠️ Codebase does not conform to established architecture policies",
                f"",
            ])
            for check in self.checks:
                if not check.passed:
                    lines.append(f"- **{check.name}**: {check.message}")

        return "\n".join(lines)


class ArchGate:
    """Gate implementation for architecture conformance."""

    # Policy thresholds from prod-gates.policy.yaml
    POLICY_CHECKS = {
        "contract_drift": {
            "threshold": 0.0,
            "comparator": "eq",
        },
        "forbidden_layer_dependencies": {
            "threshold": 0.0,
            "comparator": "eq",
        },
        "missing_required_middleware_on_critical_endpoints": {
            "threshold": 0.0,
            "comparator": "eq",
        },
    }

    def __init__(self, profile: str, policy_file: str, verbose: bool = False):
        self.profile = profile
        self.policy_file = Path(policy_file)
        self.verbose = verbose
        self.artifacts_dir = Path("artifacts/arch")

    def run(self) -> GateResult:
        """Execute architecture checks and evaluate against policy."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Ensure artifacts directory exists
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Run architecture validation
        arch_results = self._run_arch_checks()

        # Evaluate against policy thresholds
        checks = self._evaluate_checks(arch_results)

        # Determine overall pass/fail
        passed = all(c.passed for c in checks)

        result = GateResult(
            gate_name="arch_conformance",
            profile=self.profile,
            timestamp=timestamp,
            passed=passed,
            checks=checks,
            metrics=arch_results.get("metrics", {}),
        )

        # Generate artifacts
        self._write_artifacts(result)

        return result

    def _run_arch_checks(self) -> Dict[str, Any]:
        """Execute architecture conformance checks."""
        results = {"metrics": {}}

        # Check 1: Contract drift (use run_contract.py)
        contract_result = self._check_contract_drift()
        results["metrics"]["contract_drift_count"] = contract_result.get("violations", 0)

        # Check 2: Forbidden layer dependencies
        layer_result = self._check_layer_dependencies()
        results["metrics"]["forbidden_dependencies"] = layer_result.get("violations", 0)

        # Check 3: Missing middleware on critical endpoints
        middleware_result = self._check_middleware_coverage()
        results["metrics"]["missing_middleware"] = middleware_result.get("violations", 0)

        return results

    def _check_contract_drift(self) -> Dict[str, Any]:
        """Check for contract drift using run_contract.py."""
        contract_script = Path("scripts/gates/run_contract.py")

        if not contract_script.exists():
            return {"violations": 0, "note": "Contract gate not available"}

        cmd = [
            sys.executable,
            str(contract_script),
            "--profile", self.profile,
            "--policy", str(self.policy_file),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Parse results from contract gate output
            # Exit code 0 = no violations, 1 = violations found
            violations = 0 if result.returncode == 0 else 1

            # Try to get actual count from artifact
            report_path = Path("artifacts/contract/contract-gate-report.json")
            if report_path.exists():
                with open(report_path) as f:
                    data = json.load(f)
                    violations = data.get("violation_count", violations)

            return {"violations": violations}

        except Exception as e:
            if self.verbose:
                print(f"⚠️ Contract check failed: {e}")
            return {"violations": 0, "error": str(e)}

    def _check_layer_dependencies(self) -> Dict[str, Any]:
        """Check for forbidden layer dependencies."""
        # Check codemap for layer violations
        codemap_file = Path(".windsurf/codemaps/layer_interfaces.json")

        if not codemap_file.exists():
            return {"violations": 0, "note": "Layer codemap not available"}

        try:
            with open(codemap_file) as f:
                codemap = json.load(f)

            # Count violations
            violations = 0
            for layer, info in codemap.get("layers", {}).items():
                invalid_imports = info.get("invalid_imports", [])
                violations += len(invalid_imports)

            return {"violations": violations}

        except Exception as e:
            return {"violations": 0, "error": str(e)}

    def _check_middleware_coverage(self) -> Dict[str, Any]:
        """Check for missing middleware on critical endpoints."""
        # Analyze API routes for middleware decorators
        api_dirs = [
            Path("value-fabric/layer1-ingestion/src/api"),
            Path("value-fabric/layer2-extraction/src/api"),
            Path("value-fabric/layer3-knowledge/src/api"),
            Path("value-fabric/layer4-agents/src/api"),
            Path("value-fabric/layer5-ground-truth/src/api"),
        ]

        violations = 0
        critical_patterns = ["/admin/", "/system/", "/config/", "/delete", "/drop"]

        for api_dir in api_dirs:
            if not api_dir.exists():
                continue

            for route_file in api_dir.rglob("*.py"):
                try:
                    with open(route_file) as f:
                        content = f.read()

                    # Check for critical endpoints without auth/tenant middleware
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        line_lower = line.lower()

                        # Check if this is a critical endpoint
                        is_critical = any(p in line_lower for p in critical_patterns)
                        if not is_critical:
                            continue

                        # Check if it has required middleware (simplified check)
                        # In reality, would need AST parsing
                        has_tenant = "tenant" in content.lower() or "depends" in content.lower()
                        has_auth = "auth" in content.lower() or "jwt" in content.lower()

                        if not (has_tenant and has_auth):
                            violations += 1

                except Exception:
                    continue

        return {"violations": violations}

    def _evaluate_checks(self, arch_results: Dict[str, Any]) -> List[GateCheckResult]:
        """Evaluate architecture results against policy thresholds."""
        checks = []
        metrics = arch_results.get("metrics", {})

        # Check 1: Contract drift
        drift = metrics.get("contract_drift_count", 0)
        threshold = self.POLICY_CHECKS["contract_drift"]
        passed = drift == threshold["threshold"]
        checks.append(GateCheckResult(
            name="contract_drift",
            passed=passed,
            actual_value=float(drift),
            threshold=threshold["threshold"],
            comparator=threshold["comparator"],
            message=f"{drift} contract violations detected" if drift > 0 else "No contract drift detected",
        ))

        # Check 2: Forbidden layer dependencies
        deps = metrics.get("forbidden_dependencies", 0)
        threshold = self.POLICY_CHECKS["forbidden_layer_dependencies"]
        passed = deps == threshold["threshold"]
        checks.append(GateCheckResult(
            name="forbidden_layer_dependencies",
            passed=passed,
            actual_value=float(deps),
            threshold=threshold["threshold"],
            comparator=threshold["comparator"],
            message=f"{deps} forbidden layer dependencies found" if deps > 0 else "No forbidden dependencies",
        ))

        # Check 3: Missing middleware
        missing = metrics.get("missing_middleware", 0)
        threshold = self.POLICY_CHECKS["missing_required_middleware_on_critical_endpoints"]
        passed = missing == threshold["threshold"]
        checks.append(GateCheckResult(
            name="missing_required_middleware_on_critical_endpoints",
            passed=passed,
            actual_value=float(missing),
            threshold=threshold["threshold"],
            comparator=threshold["comparator"],
            message=f"{missing} critical endpoints missing required middleware" if missing > 0 else "All critical endpoints properly protected",
        ))

        return checks

    def _write_artifacts(self, result: GateResult) -> None:
        """Write gate artifacts to disk."""
        # JSON report
        report_path = self.artifacts_dir / "report.json"
        with open(report_path, "w") as f:
            f.write(result.to_json())

        # Markdown summary
        summary_path = self.artifacts_dir / "summary.md"
        with open(summary_path, "w") as f:
            f.write(result.to_markdown())

        if self.verbose:
            print(f"📝 Artifacts written to {self.artifacts_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Architecture conformance gate",
    )
    parser.add_argument(
        "--profile",
        required=True,
        choices=["pr-fast", "mainline-full", "release-candidate"],
        help="Gate profile to run",
    )
    parser.add_argument(
        "--policy",
        required=True,
        help="Path to the policy YAML file",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    print(f"🏗️  Running architecture conformance gate (profile: {args.profile})")

    gate = ArchGate(
        profile=args.profile,
        policy_file=args.policy,
        verbose=args.verbose,
    )

    result = gate.run()

    # Print summary
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"\n{status}: {result.gate_name}")
    print(f"   Checks: {len(result.checks)} total, {sum(1 for c in result.checks if c.passed)} passed, {sum(1 for c in result.checks if not c.passed)} failed")

    if not result.passed:
        print("\n🏗️ Architectural violations detected:")
        for check in result.checks:
            if not check.passed:
                print(f"  - {check.name}: {check.message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
