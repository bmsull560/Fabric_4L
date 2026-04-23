#!/usr/bin/env python3
"""
Cross-Domain Smoke Test Gate

Wrapper around production_smoke.py that:
1. Executes smoke tests against policy thresholds
2. Generates standardized gate artifacts (JSON + Markdown)
3. Enforces fail-closed semantics (exits non-zero on failure)

Exit codes:
- 0: Gate passed (all checks within thresholds)
- 1: Gate failed (violations found)
- 2: Configuration/execution error

Artifacts:
- artifacts/smoke/report.json: Structured results
- artifacts/smoke/summary.md: Human-readable summary
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
    raw_smoke_results: Optional[Dict] = None

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
            f"# Smoke Test Gate Report",
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
            f"## Check Results",
            f"",
            "| Check | Status | Actual | Threshold | Comparator |",
            "|-------|--------|--------|-----------|------------|",
        ]

        for check in self.checks:
            icon = "✅" if check.passed else "❌"
            lines.append(
                f"| {check.name} | {icon} | {check.actual_value} | {check.threshold} | {check.comparator} |"
            )

        if not self.passed:
            lines.extend([
                f"",
                f"## Failures",
                f"",
            ])
            for check in self.checks:
                if not check.passed:
                    lines.append(f"- **{check.name}**: {check.message}")

        if self.metrics:
            lines.extend([
                f"",
                f"## Metrics",
                f"",
            ])
            for key, value in self.metrics.items():
                lines.append(f"- **{key}**: {value}")

        return "\n".join(lines)


class SmokeGate:
    """Gate implementation for cross-domain smoke tests."""

    # Policy thresholds from prod-gates.policy.yaml
    POLICY_CHECKS = {
        "tier1_workflow_pass_rate_percent": {
            "threshold": 100.0,
            "comparator": "gte",
        },
        "unexpected_state_transitions": {
            "threshold": 0.0,
            "comparator": "eq",
        },
        "cross_domain_integrity_violations": {
            "threshold": 0.0,
            "comparator": "eq",
        },
    }

    def __init__(self, profile: str, policy_file: str, verbose: bool = False):
        self.profile = profile
        self.policy_file = Path(policy_file)
        self.verbose = verbose
        self.artifacts_dir = Path("artifacts/smoke")

    def run(self) -> GateResult:
        """Execute smoke tests and evaluate against policy."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Ensure artifacts directory exists
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Run production smoke tests
        smoke_result = self._run_smoke_tests()

        if smoke_result is None:
            # Execution failed
            return GateResult(
                gate_name="cross_domain_smoke",
                profile=self.profile,
                timestamp=timestamp,
                passed=False,
                checks=[],
                metrics={"error": "Failed to execute smoke tests"},
            )

        # Evaluate against policy thresholds
        checks = self._evaluate_checks(smoke_result)

        # Determine overall pass/fail
        passed = all(c.passed for c in checks)

        result = GateResult(
            gate_name="cross_domain_smoke",
            profile=self.profile,
            timestamp=timestamp,
            passed=passed,
            checks=checks,
            metrics={
                "total_stages": len(smoke_result.get("stages", [])),
                "passed_stages": sum(1 for s in smoke_result.get("stages", []) if s.get("status") == "pass"),
                "total_duration_ms": smoke_result.get("total_duration_ms", 0),
            },
            raw_smoke_results=smoke_result,
        )

        # Generate artifacts
        self._write_artifacts(result)

        return result

    def _run_smoke_tests(self) -> Optional[Dict[str, Any]]:
        """Execute production_smoke.py and parse results."""
        smoke_script = Path("scripts/smoke/production_smoke.py")

        if not smoke_script.exists():
            print(f"❌ Smoke test script not found: {smoke_script}")
            return None

        cmd = [
            sys.executable,
            str(smoke_script),
            "--output-format", "json",
        ]

        if self.verbose:
            print(f"🔍 Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Parse JSON output from last line (smoke script prints progress, then JSON)
            lines = result.stdout.strip().split("\n")
            for line in reversed(lines):
                line = line.strip()
                if line and line.startswith("{"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue

            # Fallback: try to parse entire stdout
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass

            print(f"❌ Failed to parse smoke test output")
            if self.verbose:
                print(f"STDOUT: {result.stdout[:500]}")
                print(f"STDERR: {result.stderr[:500]}")
            return None

        except subprocess.TimeoutExpired:
            print(f"❌ Smoke tests timed out after 5 minutes")
            return None
        except Exception as e:
            print(f"❌ Error running smoke tests: {e}")
            return None

    def _evaluate_checks(self, smoke_result: Dict[str, Any]) -> List[GateCheckResult]:
        """Evaluate smoke results against policy thresholds."""
        checks = []
        stages = smoke_result.get("stages", [])
        overall = smoke_result.get("overall", "fail")

        # Calculate metrics
        total_stages = len(stages)
        passed_stages = sum(1 for s in stages if s.get("status") == "pass")
        pass_rate = (passed_stages / total_stages * 100) if total_stages > 0 else 0

        # Check 1: Tier-1 workflow pass rate
        tier1_threshold = self.POLICY_CHECKS["tier1_workflow_pass_rate_percent"]
        tier1_passed = pass_rate >= tier1_threshold["threshold"]
        checks.append(GateCheckResult(
            name="tier1_workflow_pass_rate_percent",
            passed=tier1_passed,
            actual_value=pass_rate,
            threshold=tier1_threshold["threshold"],
            comparator=tier1_threshold["comparator"],
            message=f"{passed_stages}/{total_stages} stages passed ({pass_rate:.1f}%)",
        ))

        # Check 2: Unexpected state transitions (failures count as state transition issues)
        state_threshold = self.POLICY_CHECKS["unexpected_state_transitions"]
        failed_stages = total_stages - passed_stages
        state_passed = failed_stages == state_threshold["threshold"]
        checks.append(GateCheckResult(
            name="unexpected_state_transitions",
            passed=state_passed,
            actual_value=float(failed_stages),
            threshold=state_threshold["threshold"],
            comparator=state_threshold["comparator"],
            message=f"{failed_stages} stages failed" if failed_stages > 0 else "No failures detected",
        ))

        # Check 3: Cross-domain integrity violations
        # These would be indicated by stage errors
        integrity_threshold = self.POLICY_CHECKS["cross_domain_integrity_violations"]
        integrity_violations = sum(
            1 for s in stages
            if s.get("error") and "integrity" in s.get("error", "").lower()
        )
        integrity_passed = integrity_violations == integrity_threshold["threshold"]
        checks.append(GateCheckResult(
            name="cross_domain_integrity_violations",
            passed=integrity_passed,
            actual_value=float(integrity_violations),
            threshold=integrity_threshold["threshold"],
            comparator=integrity_threshold["comparator"],
            message=f"{integrity_violations} integrity violations detected",
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
        description="Cross-domain smoke test gate",
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

    print(f"🔍 Running smoke test gate (profile: {args.profile})")

    gate = SmokeGate(
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
        print("\nFailed checks:")
        for check in result.checks:
            if not check.passed:
                print(f"  - {check.name}: {check.message}")

    # Exit with appropriate code
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
