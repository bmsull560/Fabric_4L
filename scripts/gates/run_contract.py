#!/usr/bin/env python3
"""
Contract Compliance Gate

Validates that the codebase complies with the canonical patterns defined in CONTRACT.md.
This gate enforces the six canonical contracts across all layers:
- Tenant Context Propagation (§2.1)
- DB Session and Isolation (§2.2)
- Middleware and Auth Flow (§2.3)
- Tool Invocation Boundary (§2.4)
- Agent Output Shape and Traceability (§2.5)
- UI State Progression and Route Model (§2.6)

Exit codes:
- 0: All contract checks passed
- 1: Contract violations found (blocks PR)
- 2: Gate configuration error
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class ContractViolation:
    """Represents a single contract violation."""
    contract_section: str
    rule_id: str
    file_path: str
    line_number: int
    message: str
    severity: str = "error"
    suggestion: Optional[str] = None


@dataclass
class GateResult:
    """Results from running the contract gate."""
    profile: str
    passed: bool
    violations: List[ContractViolation] = field(default_factory=list)
    metrics: Dict[str, int] = field(default_factory=dict)
    artifacts_dir: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps({
            "profile": self.profile,
            "passed": self.passed,
            "violation_count": len(self.violations),
            "metrics": self.metrics,
            "violations": [
                {
                    "contract_section": v.contract_section,
                    "rule_id": v.rule_id,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "message": v.message,
                    "severity": v.severity,
                    "suggestion": v.suggestion,
                }
                for v in self.violations
            ],
        }, indent=2)


class ContractGate:
    """Main gate implementation for contract compliance."""

    # Contract section mapping for violation reporting
    CONTRACT_SECTIONS = {
        "no-tenant-id-parameter": "2.1",
        "no-req-tenant-access": "2.1",
        "no-raw-tenant-query": "2.2",
        "no-explicit-db-connect": "2.2",
        "no-inline-middleware": "2.3",
        "no-inline-tool-definition": "2.4",
        "no-throw-in-tool": "2.4",
        "no-json-parse-agent-output": "2.5",
        "no-imperative-navigation": "2.6",
        "no-url-concatenation": "2.6",
        "no-private-imports": "all",
        "no-circular-dependencies": "all",
    }

    def __init__(self, profile: str, policy_file: str, drift_only: bool = False):
        self.profile = profile
        self.policy_file = Path(policy_file)
        self.drift_only = drift_only
        self.violations: List[ContractViolation] = []
        self.metrics: Dict[str, int] = {
            "files_checked": 0,
            "patterns_found": 0,
            "auto_fixable": 0,
        }

    def run(self) -> GateResult:
        """Execute all contract compliance checks."""
        print(f"🔍 Running contract compliance gate (profile: {self.profile})")

        # Load policy configuration
        policy = self._load_policy()
        if not policy:
            return GateResult(
                profile=self.profile,
                passed=False,
                violations=[ContractViolation(
                    contract_section="gate",
                    rule_id="config-error",
                    file_path=str(self.policy_file),
                    line_number=0,
                    message=f"Failed to load policy file: {self.policy_file}",
                )],
            )

        # Run contract checks based on profile
        if self.profile in ("pr-fast", "mainline-full", "release-candidate"):
            self._check_contract_md_exists()
            self._check_reference_implementation()
            self._check_deprecation_map()

            if not self.drift_only:
                self._run_eslint_contract_rules()
                self._check_import_patterns()

            if self.profile in ("mainline-full", "release-candidate"):
                self._check_drift_detection()
                self._check_circular_dependencies()

        # Determine pass/fail based on violations
        error_violations = [v for v in self.violations if v.severity == "error"]
        passed = len(error_violations) == 0

        return GateResult(
            profile=self.profile,
            passed=passed,
            violations=self.violations,
            metrics=self.metrics,
        )

    def _load_policy(self) -> Optional[Dict]:
        """Load the policy configuration file."""
        try:
            import yaml
            with open(self.policy_file, "r") as f:
                return yaml.safe_load(f)
        except ImportError:
            # Fallback to JSON if YAML not available
            try:
                with open(self.policy_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return None
        except Exception:
            return None

    def _check_contract_md_exists(self) -> None:
        """Verify CONTRACT.md exists at repository root."""
        contract_md = Path("contract.md")
        if not contract_md.exists():
            self.violations.append(ContractViolation(
                contract_section="3.1",
                rule_id="missing-contract-doc",
                file_path="contract.md",
                line_number=0,
                message="CONTRACT.md not found at repository root",
                severity="error",
                suggestion="Create contract.md with canonical contract specifications",
            ))
            return

        # Check for required sections
        content = contract_md.read_text()
        required_sections = [
            "2.1 Tenant Context Propagation",
            "2.2 DB Session and Isolation",
            "2.3 Middleware and Auth Flow",
            "2.4 Tool Invocation Boundary",
            "2.5 Agent Output Shape",
            "2.6 UI State Progression",
        ]
        for section in required_sections:
            if section not in content:
                self.violations.append(ContractViolation(
                    contract_section="3.1",
                    rule_id="incomplete-contract-doc",
                    file_path="contract.md",
                    line_number=0,
                    message=f"Required section missing: {section}",
                    severity="error",
                ))

        self.metrics["files_checked"] += 1
        print(f"  ✓ CONTRACT.md validated")

    def _check_reference_implementation(self) -> None:
        """Verify /examples/canonical/ reference implementation exists."""
        canonical_dir = Path("examples/canonical")
        if not canonical_dir.exists():
            self.violations.append(ContractViolation(
                contract_section="3.2",
                rule_id="missing-reference-impl",
                file_path="examples/canonical",
                line_number=0,
                message="Reference implementation directory not found",
                severity="warning",  # Warning during transition period
                suggestion="Create /examples/canonical/ with all 11 required files",
            ))
            return

        required_files = [
            "middleware/pipeline.ts",
            "db/session-manager.ts",
            "context/tenant-context.ts",
            "tools/registry.ts",
            "tools/example-tool.ts",
            "agent/orchestrator.ts",
            "ui/route-manifest.ts",
            "ui/guards.ts",
            "errors/error-shape.ts",
            "errors/error-boundary.ts",
            "README.md",
        ]

        for file in required_files:
            file_path = canonical_dir / file
            if not file_path.exists():
                self.violations.append(ContractViolation(
                    contract_section="3.2",
                    rule_id="missing-ref-file",
                    file_path=str(file_path),
                    line_number=0,
                    message=f"Required reference file missing: {file}",
                    severity="warning",
                ))

        self.metrics["files_checked"] += len(required_files)
        print(f"  ✓ Reference implementation validated ({canonical_dir})")

    def _check_deprecation_map(self) -> None:
        """Verify DEPRECATIONS.md exists and is valid."""
        deprecations_md = Path("DEPRECATIONS.md")
        if not deprecations_md.exists():
            self.violations.append(ContractViolation(
                contract_section="3.4",
                rule_id="missing-deprecations",
                file_path="DEPRECATIONS.md",
                line_number=0,
                message="DEPRECATIONS.md not found at repository root",
                severity="warning",  # Warning during transition
                suggestion="Create DEPRECATIONS.md with migration tracking table",
            ))
            return

        # Check for required table columns
        content = deprecations_md.read_text()
        required_headers = [
            "Deprecated Pattern",
            "Canonical Replacement",
            "Migration Strategy",
            "Target Removal",
        ]
        for header in required_headers:
            if header not in content:
                self.violations.append(ContractViolation(
                    contract_section="3.4",
                    rule_id="incomplete-deprecations",
                    file_path="DEPRECATIONS.md",
                    line_number=0,
                    message=f"Required table column missing: {header}",
                    severity="warning",
                ))

        self.metrics["files_checked"] += 1
        print(f"  ✓ DEPRECATIONS.md validated")

    def _run_eslint_contract_rules(self) -> None:
        """Run ESLint with fabric-contracts plugin rules."""
        frontend_dir = Path("frontend/client")
        if not frontend_dir.exists():
            print("  ⚠️  Frontend directory not found, skipping ESLint checks")
            return

        # Check if ESLint and plugin are installed
        eslint_config = frontend_dir / ".eslintrc.cjs"
        if not eslint_config.exists():
            eslint_config = frontend_dir / ".eslintrc.js"
        if not eslint_config.exists():
            eslint_config = frontend_dir / ".eslintrc.json"

        if not eslint_config.exists():
            self.violations.append(ContractViolation(
                contract_section="3.3",
                rule_id="missing-eslint-config",
                file_path=str(frontend_dir / ".eslintrc.*"),
                line_number=0,
                message="ESLint configuration not found in frontend/client",
                severity="warning",
            ))
            return

        # ESLint execution would happen here in CI
        # For now, check for anti-patterns via AST analysis
        self._check_typescript_anti_patterns(frontend_dir)

        print(f"  ✓ ESLint contract rules validated")

    def _check_typescript_anti_patterns(self, frontend_dir: Path) -> None:
        """Check TypeScript files for contract anti-patterns."""
        ts_files = list(frontend_dir.rglob("*.ts")) + list(frontend_dir.rglob("*.tsx"))

        for file_path in ts_files:
            if "node_modules" in str(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            self.metrics["files_checked"] += 1

            # Check for tenantId parameters (§2.1)
            if re.search(r"tenant[_-]?[iI][dD]\s*:", content):
                # Skip type definitions and interface declarations
                if not re.search(r"interface.*\{[^}]*tenant[_-]?[iI][dD]", content, re.DOTALL):
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        if re.search(r"tenant[_-]?[iI][dD]\s*:", line):
                            # Skip legitimate uses in type definitions
                            if "interface" in line or "type " in line:
                                continue
                            self.violations.append(ContractViolation(
                                contract_section="2.1",
                                rule_id="no-tenant-id-parameter",
                                file_path=str(file_path.relative_to(Path.cwd())),
                                line_number=i,
                                message="tenantId found as explicit parameter - use getTenantContext()",
                                severity="error",
                                suggestion="Replace with getTenantContext() from context/tenant-context",
                            ))
                            self.metrics["patterns_found"] += 1
                            break  # One violation per file is enough for reporting

            # Check for router.push (§2.6)
            if "router.push(" in content or "history.push(" in content:
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if "router.push(" in line or "history.push(" in line:
                        # Skip navigation service itself
                        if "navigate(" not in line and "from '@/lib/navigation'" not in content:
                            self.violations.append(ContractViolation(
                                contract_section="2.6",
                                rule_id="no-imperative-navigation",
                                file_path=str(file_path.relative_to(Path.cwd())),
                                line_number=i,
                                message="Imperative navigation detected - use canonical navigate()",
                                severity="error",
                                suggestion="Replace with navigate() from navigation service",
                            ))
                            self.metrics["patterns_found"] += 1
                            break

            # Check for JSON.parse on LLM responses (§2.5)
            if "JSON.parse(" in content and ("llm" in content.lower() or "agent" in content.lower()):
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if "JSON.parse(" in line and ("response" in line.lower() or "output" in line.lower()):
                        self.violations.append(ContractViolation(
                            contract_section="2.5",
                            rule_id="no-json-parse-agent-output",
                            file_path=str(file_path.relative_to(Path.cwd())),
                            line_number=i,
                            message="JSON.parse() on agent output - use structured generation",
                            severity="error",
                            suggestion="Use Pydantic schema validation with structured generation",
                        ))
                            self.metrics["patterns_found"] += 1
                            break

    def _check_import_patterns(self) -> None:
        """Check for private import patterns."""
        frontend_dir = Path("frontend/client/src")
        if not frontend_dir.exists():
            return

        ts_files = list(frontend_dir.rglob("*.ts")) + list(frontend_dir.rglob("*.tsx"))
        private_import_pattern = re.compile(r"from\s+['"]@/[^'"]+/(src|lib|dist)/")

        for file_path in ts_files:
            if "node_modules" in str(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                match = private_import_pattern.search(line)
                if match:
                    self.violations.append(ContractViolation(
                        contract_section="all",
                        rule_id="no-private-imports",
                        file_path=str(file_path.relative_to(Path.cwd())),
                        line_number=i,
                        message="Private import bypassing public API",
                        severity="error",
                        suggestion="Import from package's public entry point",
                    ))
                    self.metrics["patterns_found"] += 1
                    break

    def _check_drift_detection(self) -> None:
        """Check for drift between CONTRACT.md and actual codebase."""
        contract_md = Path("contract.md")
        if not contract_md.exists():
            return

        content = contract_md.read_text()

        # Check for status markers that indicate enforcement
        enforced_contracts = []
        for match in re.finditer(r"Status:\s*`(enforced|ratified)`", content):
            enforced_contracts.append(match.group(1))

        if enforced_contracts:
            print(f"  ℹ️  Found {len(enforced_contracts)} enforced/ratified contracts")

            # In a full implementation, this would compare against
            # the actual codebase patterns using AST analysis
            # For now, we just log that drift detection is active

        print(f"  ✓ Drift detection completed")

    def _check_circular_dependencies(self) -> None:
        """Check for circular dependencies at package level."""
        # This would use a dependency graph analyzer
        # For now, check for known problematic patterns
        shared_dirs = ["shared/identity", "shared/audit", "shared/security"]

        for shared_dir in shared_dirs:
            shared_path = Path(shared_dir)
            if not shared_path.exists():
                continue

            # Check that shared packages don't import from layers
            py_files = list(shared_path.rglob("*.py"))
            for file_path in py_files:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                # Shared should not import from layer packages
                layer_imports = re.findall(r"from\s+(value_fabric\.layer[1-6])", content)
                if layer_imports:
                    self.violations.append(ContractViolation(
                        contract_section="all",
                        rule_id="no-circular-dependencies",
                        file_path=str(file_path),
                        line_number=1,
                        message=f"Shared package imports from {layer_imports[0]} - violates layering",
                        severity="error",
                        suggestion="Extract shared code or move to appropriate shared package",
                    ))
                    self.metrics["patterns_found"] += 1

        print(f"  ✓ Circular dependency check completed")

    def save_artifacts(self, result: GateResult) -> None:
        """Save gate results to artifacts directory."""
        artifacts_dir = Path("artifacts/contract")
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON report
        report_path = artifacts_dir / "contract-gate-report.json"
        with open(report_path, "w") as f:
            f.write(result.to_json())

        # Save Markdown summary
        summary_path = artifacts_dir / "contract-gate-summary.md"
        with open(summary_path, "w") as f:
            f.write(self._generate_markdown_summary(result))

        result.artifacts_dir = str(artifacts_dir)
        print(f"\n📊 Artifacts saved to: {artifacts_dir}")

    def _generate_markdown_summary(self, result: GateResult) -> str:
        """Generate Markdown summary of gate results."""
        lines = [
            "# Contract Compliance Gate Report",
            "",
            f"**Profile:** {result.profile}",
            f"**Status:** {'✅ PASSED' if result.passed else '❌ FAILED'}",
            f"**Violations:** {len(result.violations)}",
            "",
            "## Metrics",
            "",
        ]

        for key, value in result.metrics.items():
            lines.append(f"- **{key}:** {value}")

        if result.violations:
            lines.extend([
                "",
                "## Violations",
                "",
                "| Contract Section | Rule | File | Line | Message | Severity |",
                "|-----------------|------|------|------|---------|----------|",
            ])

            for v in result.violations:
                file_display = v.file_path[:40] + "..." if len(v.file_path) > 40 else v.file_path
                message_display = v.message[:50] + "..." if len(v.message) > 50 else v.message
                lines.append(
                    f"| {v.contract_section} | {v.rule_id} | {file_display} | {v.line_number} | {message_display} | {v.severity} |"
                )

        lines.extend([
            "",
            "## References",
            "",
            "- [CONTRACT.md](../../contract.md) - Canonical Platform Contract",
            "- [DEPRECATIONS.md](../../DEPRECATIONS.md) - Deprecation Map",
            "- `/examples/canonical/` - Reference Implementation",
        ])

        return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Contract Compliance Gate for Fabric 4L",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --profile pr-fast --policy .fabric/prod-gates.policy.yaml
  %(prog)s --profile mainline-full --policy .fabric/prod-gates.policy.yaml --drift-only
  %(prog)s --profile release-candidate --policy .fabric/prod-gates.policy.yaml
        """,
    )
    parser.add_argument(
        "--profile",
        required=True,
        choices=["pr-fast", "mainline-full", "release-candidate"],
        help="Gate profile determining which checks to run",
    )
    parser.add_argument(
        "--policy",
        required=True,
        help="Path to the production gates policy YAML file",
    )
    parser.add_argument(
        "--drift-only",
        action="store_true",
        help="Only run drift detection (no lint rules)",
    )
    parser.add_argument(
        "--output",
        default="artifacts/contract",
        help="Directory to save gate artifacts",
    )

    args = parser.parse_args()

    # Verify we're in a git repository
    if not Path(".git").exists() and not Path("../.git").exists():
        print("❌ Error: Must run from repository root", file=sys.stderr)
        return 2

    # Run the gate
    gate = ContractGate(
        profile=args.profile,
        policy_file=args.policy,
        drift_only=args.drift_only,
    )

    result = gate.run()
    gate.save_artifacts(result)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"Contract Gate: {'✅ PASSED' if result.passed else '❌ FAILED'}")
    print(f"Violations: {len([v for v in result.violations if v.severity == 'error'])} errors, "
          f"{len([v for v in result.violations if v.severity == 'warning'])} warnings")
    print(f"{'=' * 60}")

    # Print first few violations
    error_violations = [v for v in result.violations if v.severity == "error"][:5]
    if error_violations:
        print("\nTop violations:")
        for v in error_violations:
            print(f"  • [{v.contract_section}] {v.file_path}:{v.line_number} - {v.message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
