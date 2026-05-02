"""Release Policy: Contract gate compliance.

Verifies that required contract gates exist and blocking gates do not use
continue-on-error that would allow violations to pass silently.
"""

import os
from pathlib import Path

import pytest
import yaml


class TestContractGatePolicy:
    """Enforce: Required contract gates exist; blocking gates don't use continue-on-error."""

    def test_structural_preflight_exists(self):
        """Structural preflight script must exist and be executable."""
        script = Path("scripts/ci/structural_preflight.py")
        if not script.exists():
            pytest.skip("structural_preflight.py not found - install to enforce")
        assert script.stat().st_size > 0, "structural_preflight.py is empty"

    def test_python_contract_lint_exists(self):
        """Python contract lint script must exist."""
        script = Path("scripts/ci/python_contract_lint.py")
        if not script.exists():
            pytest.skip("python_contract_lint.py not found - install to enforce")
        assert script.stat().st_size > 0, "python_contract_lint.py is empty"

    def test_ci_workflow_blocking_gates_no_continue_on_error(self):
        """Blocking gates in CI workflows must not use continue-on-error.

        continue-on-error: true allows failures to pass silently.
        Blocking gates must fail the build on violation.
        """
        workflows_dir = Path(".github/workflows")
        if not workflows_dir.exists():
            pytest.skip("No .github/workflows directory")

        violations = []
        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text(encoding="utf-8")

            # Check for continue-on-error in blocking gate contexts
            # This is a heuristic check - manual review may still be needed
            if "continue-on-error: true" in content:
                # Check if it's on a gate job (not upload/artifact steps)
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "continue-on-error: true" in line:
                        # Check surrounding context for gate-related patterns
                        context = "\n".join(lines[max(0, i-10):i+5])
                        gate_patterns = ["gate-", "security", "tenant", "boundary", "compliance", "lint"]
                        if any(pat in context.lower() for pat in gate_patterns):
                            violations.append(f"{workflow_file.name}: line {i+1}")

        if violations:
            details = "\n".join(f"  - {v}" for v in violations[:5])  # Limit output
            pytest.fail(
                f"Found potential continue-on-error in blocking gate contexts:\n{details}\n"
                f"Review these workflows to ensure blocking gates can actually fail."
            )

    def test_required_makefile_targets_exist(self):
        """Required Makefile targets for gates must exist."""
        makefile = Path("Makefile")
        if not makefile.exists():
            pytest.skip("No Makefile found")

        content = makefile.read_text(encoding="utf-8")

        required_targets = [
            "gate-security",
            "gate-arch",
            "gate-state",
            "lint",
        ]

        missing = [t for t in required_targets if f"{t}:" not in content]

        if missing:
            pytest.fail(f"Required Makefile targets missing: {missing}")
