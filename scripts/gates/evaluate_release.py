#!/usr/bin/env python3
"""
Release Policy Evaluation Gate

Aggregate gate that evaluates all gate results against the release policy:
1. Blocker failures (must be 0)
2. Critical failures (must be 0)
3. Missing artifacts (must be 0)
4. Stale gate results (must be 0)

This gate is the FINAL AUTHORITY on release approval. It:
- Downloads/reads all gate artifacts
- Evaluates against policy thresholds
- Enforces block_on_missing_artifacts
- Enforces staleness checks
- Generates signed manifest (if signing available)
- Blocks release if any blocker/critical gate failed

Exit codes:
- 0: Release APPROVED
- 1: Release BLOCKED
- 2: Evaluation error

Artifacts:
- artifacts/release/policy-eval.json: Detailed evaluation results
- artifacts/release/manifest.json: Release manifest (signed if possible)
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone, timedelta


@dataclass
class GateEvaluation:
    """Evaluation of a single gate's results."""
    gate_name: str
    severity: str  # blocker, critical, warning
    passed: bool
    artifact_found: bool
    artifact_stale: bool
    check_results: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ReleaseEvaluation:
    """Complete release evaluation result."""
    timestamp: str
    profile: str
    approved: bool
    blocker_failures: int
    critical_failures: int
    missing_artifacts: int
    stale_results: int
    gate_evaluations: List[GateEvaluation] = field(default_factory=list)
    manifest: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "timestamp": self.timestamp,
            "profile": self.profile,
            "approved": self.approved,
            "blocker_failures": self.blocker_failures,
            "critical_failures": self.critical_failures,
            "missing_artifacts": self.missing_artifacts,
            "stale_results": self.stale_results,
            "gate_evaluations": [
                {
                    "gate_name": g.gate_name,
                    "severity": g.severity,
                    "passed": g.passed,
                    "artifact_found": g.artifact_found,
                    "artifact_stale": g.artifact_stale,
                    "check_results": g.check_results,
                }
                for g in self.gate_evaluations
            ],
            "manifest": self.manifest,
        }, indent=2)

    def to_markdown(self) -> str:
        status_icon = "✅ APPROVED" if self.approved else "❌ BLOCKED"
        lines = [
            f"# Release Policy Evaluation Report",
            f"",
            f"**Profile:** {self.profile}",
            f"**Timestamp:** {self.timestamp}",
            f"**Status:** {status_icon}",
            f"",
            f"## Summary",
            f"",
            f"- Blocker Failures: {self.blocker_failures}",
            f"- Critical Failures: {self.critical_failures}",
            f"- Missing Artifacts: {self.missing_artifacts}",
            f"- Stale Results: {self.stale_results}",
            f"",
            f"## Gate Evaluations",
            f"",
            "| Gate | Severity | Status | Artifact | Stale |",
            "|------|----------|--------|----------|-------|",
        ]

        for gate in self.gate_evaluations:
            status = "✅" if gate.passed else "❌"
            artifact = "✅" if gate.artifact_found else "❌"
            stale = "⚠️" if gate.artifact_stale else "✅"
            lines.append(
                f"| {gate.gate_name} | {gate.severity} | {status} | {artifact} | {stale} |"
            )

        # Blockers section
        blocking_issues = []
        if self.blocker_failures > 0:
            blocking_issues.append(f"{self.blocker_failures} blocker gate(s) failed")
        if self.critical_failures > 0:
            blocking_issues.append(f"{self.critical_failures} critical gate(s) failed")
        if self.missing_artifacts > 0:
            blocking_issues.append(f"{self.missing_artifacts} required artifact(s) missing")
        if self.stale_results > 0:
            blocking_issues.append(f"{self.stale_results} stale gate result(s)")

        if blocking_issues:
            lines.extend([
                f"",
                f"## Blocking Issues",
                f"",
            ])
            for issue in blocking_issues:
                lines.append(f"- ❌ {issue}")

            lines.extend([
                f"",
                f"## Required Actions",
                f"",
                f"1. Fix all blocker and critical gate failures",
                f"2. Ensure all required artifacts are generated",
                f"3. Re-run gates within the staleness window",
                f"4. Re-run this evaluation",
            ])
        else:
            lines.extend([
                f"",
                f"## ✅ Release Approved",
                f"",
                f"All gates passed, all artifacts present, all results fresh.",
                f"This release candidate is approved for deployment.",
            ])

        return "\n".join(lines)


class ReleaseEvaluator:
    """Evaluates release readiness based on all gate results."""

    # Staleness windows from policy (hours)
    STALENESS_WINDOWS = {
        "pr-fast": 24,
        "mainline-full": 24,
        "release-candidate": 12,
    }

    # Gate artifact paths
    GATE_ARTIFACTS = {
        "arch_conformance": "artifacts/arch/report.json",
        "security_isolation": "artifacts/security/report.json",
        "dependency_chaos": "artifacts/chaos/report.json",
        "cross_domain_smoke": "artifacts/smoke/report.json",
        "agent_provenance": "artifacts/agent/report.json",
        "state_consistency": "artifacts/state/report.json",
        "observability_readiness": "artifacts/obs/report.json",
        "contract_drift": "artifacts/contract/contract-gate-report.json",
    }

    def __init__(self, profile: str, policy_file: str, verbose: bool = False, allow_stale: bool = False):
        self.profile = profile
        self.policy_file = Path(policy_file)
        self.verbose = verbose
        self.allow_stale = allow_stale
        self.artifacts_dir = Path("artifacts/release")
        self.policy = self._load_policy()

    def _load_policy(self) -> Dict[str, Any]:
        """Load the gate policy file."""
        try:
            import yaml
            with open(self.policy_file) as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Failed to load policy: {e}")
            sys.exit(2)

    def evaluate(self) -> ReleaseEvaluation:
        """Execute release evaluation."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Ensure artifacts directory exists
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Get enabled gates for this profile
        enabled_gates = self._get_enabled_gates()

        # Evaluate each gate
        gate_evaluations = []
        blocker_failures = 0
        critical_failures = 0
        missing_artifacts = 0
        stale_results = 0

        for gate_name in enabled_gates:
            eval_result = self._evaluate_gate(gate_name)
            gate_evaluations.append(eval_result)

            if not eval_result.passed:
                if eval_result.severity == "blocker":
                    blocker_failures += 1
                elif eval_result.severity == "critical":
                    critical_failures += 1

            if not eval_result.artifact_found:
                missing_artifacts += 1

            if eval_result.artifact_stale:
                stale_results += 1

        # Determine approval
        approved = self._determine_approval(
            blocker_failures, critical_failures, missing_artifacts, stale_results
        )

        # Generate manifest
        manifest = self._generate_manifest(gate_evaluations, approved)

        evaluation = ReleaseEvaluation(
            timestamp=timestamp,
            profile=self.profile,
            approved=approved,
            blocker_failures=blocker_failures,
            critical_failures=critical_failures,
            missing_artifacts=missing_artifacts,
            stale_results=stale_results,
            gate_evaluations=gate_evaluations,
            manifest=manifest,
        )

        # Write artifacts
        self._write_artifacts(evaluation)

        return evaluation

    def _get_enabled_gates(self) -> List[str]:
        """Get list of gates enabled for this profile."""
        profiles = self.policy.get("profiles", {})
        profile_config = profiles.get(self.profile, {})
        return profile_config.get("enabled_gates", [])

    def _evaluate_gate(self, gate_name: str) -> GateEvaluation:
        """Evaluate a single gate's results."""
        # Get gate severity from policy
        gates = self.policy.get("gates", {})
        gate_config = gates.get(gate_name, {})
        severity = gate_config.get("severity", "warning")

        # Find and load artifact
        artifact_path = Path(self.GATE_ARTIFACTS.get(gate_name, f"artifacts/{gate_name}/report.json"))
        artifact_found = artifact_path.exists()

        if not artifact_found:
            return GateEvaluation(
                gate_name=gate_name,
                severity=severity,
                passed=False,  # Missing artifact = fail
                artifact_found=False,
                artifact_stale=False,
                check_results=[{"error": "Artifact not found"}],
            )

        # Check staleness
        artifact_stale = self._check_staleness(artifact_path)

        # Load and evaluate artifact
        try:
            with open(artifact_path) as f:
                artifact_data = json.load(f)

            gate_passed = artifact_data.get("passed", False)
            check_results = artifact_data.get("checks", [])

            return GateEvaluation(
                gate_name=gate_name,
                severity=severity,
                passed=gate_passed and not (artifact_stale and not self.allow_stale),
                artifact_found=True,
                artifact_stale=artifact_stale,
                check_results=check_results,
            )

        except Exception as e:
            return GateEvaluation(
                gate_name=gate_name,
                severity=severity,
                passed=False,
                artifact_found=True,
                artifact_stale=artifact_stale,
                check_results=[{"error": f"Failed to parse artifact: {e}"}],
            )

    def _check_staleness(self, artifact_path: Path) -> bool:
        """Check if an artifact is stale based on policy."""
        try:
            mtime = datetime.fromtimestamp(artifact_path.stat().st_mtime, tz=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600

            max_age = self.STALENESS_WINDOWS.get(self.profile, 24)
            return age_hours > max_age
        except Exception:
            return True  # Assume stale if we can't check

    def _determine_approval(
        self,
        blocker_failures: int,
        critical_failures: int,
        missing_artifacts: int,
        stale_results: int
    ) -> bool:
        """Determine if release is approved based on policy."""
        enforcement = self.policy.get("enforcement", {})

        # Check blocker failures (always block)
        if blocker_failures > 0:
            return False

        # Check critical failures (always block per policy)
        if critical_failures > 0:
            return False

        # Check missing artifacts if enforced
        if enforcement.get("block_on_missing_artifacts", True) and missing_artifacts > 0:
            return False

        # Check staleness (unless allowed)
        if not self.allow_stale and stale_results > 0:
            return False

        return True

    def _generate_manifest(self, gate_evaluations: List[GateEvaluation], approved: bool) -> Dict[str, Any]:
        """Generate release manifest."""
        return {
            "version": self.policy.get("version", "unknown"),
            "profile": self.profile,
            "approved": approved,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gates": {
                g.gate_name: {
                    "passed": g.passed,
                    "severity": g.severity,
                    "artifact_found": g.artifact_found,
                    "artifact_stale": g.artifact_stale,
                }
                for g in gate_evaluations
            },
            "signatures": [],  # Would be populated by sign_manifest.py
        }

    def _write_artifacts(self, evaluation: ReleaseEvaluation) -> None:
        """Write evaluation artifacts."""
        # JSON evaluation report
        eval_path = self.artifacts_dir / "policy-eval.json"
        with open(eval_path, "w") as f:
            f.write(evaluation.to_json())

        # Markdown summary
        summary_path = self.artifacts_dir / "summary.md"
        with open(summary_path, "w") as f:
            f.write(evaluation.to_markdown())

        # Manifest
        manifest_path = self.artifacts_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(evaluation.manifest, f, indent=2)

        if self.verbose:
            print(f"📝 Artifacts written to {self.artifacts_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate release policy compliance",
    )
    parser.add_argument(
        "--profile",
        required=True,
        choices=["pr-fast", "mainline-full", "release-candidate"],
        help="Release profile to evaluate",
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
    parser.add_argument(
        "--allow-stale",
        action="store_true",
        help="Allow stale gate results (not recommended for production)",
    )

    args = parser.parse_args()

    print(f"🔍 Evaluating release policy (profile: {args.profile})")
    print(f"   Policy: {args.policy}")

    evaluator = ReleaseEvaluator(
        profile=args.profile,
        policy_file=args.policy,
        verbose=args.verbose,
        allow_stale=args.allow_stale,
    )

    evaluation = evaluator.evaluate()

    # Print summary
    print()
    if evaluation.approved:
        print("✅ RELEASE APPROVED")
        print()
        print(f"All {len(evaluation.gate_evaluations)} gates passed.")
        print("This release candidate is cleared for deployment.")
    else:
        print("❌ RELEASE BLOCKED")
        print()
        if evaluation.blocker_failures > 0:
            print(f"- Blocker failures: {evaluation.blocker_failures}")
        if evaluation.critical_failures > 0:
            print(f"- Critical failures: {evaluation.critical_failures}")
        if evaluation.missing_artifacts > 0:
            print(f"- Missing artifacts: {evaluation.missing_artifacts}")
        if evaluation.stale_results > 0:
            print(f"- Stale results: {evaluation.stale_results}")
        print()
        print("Fix all blocking issues and re-run evaluation.")

    return 0 if evaluation.approved else 1


if __name__ == "__main__":
    sys.exit(main())
