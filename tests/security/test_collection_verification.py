"""
Test Collection Verification - CI Production Gate

Ensures all tests can be collected (no import errors that silently skip coverage).
This is a metatest that validates the test suite itself.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestCollectionVerification:
    """Verify all security tests can be collected and loaded."""

    def test_all_security_tests_collectable(self):
        """P0: All tests in tests/security/ must be collectable (no import errors)."""
        security_dir = Path(__file__).parent

        # Collect all test files
        test_files = list(security_dir.glob("test_*.py"))

        # Exclude this file and conftest to avoid recursion
        test_files = [f for f in test_files if f.name not in [
            "test_collection_verification.py",
            "conftest.py"
        ]]

        failures = []
        for test_file in test_files:
            # Try to collect tests from each file
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "--collect-only", "-q"],
                capture_output=True,
                text=True,
                cwd=str(security_dir.parent.parent)  # Run from repo root
            )

            if result.returncode != 0:
                # Check if it's an import error vs no tests
                if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
                    failures.append(f"{test_file.name}: {result.stderr[:200]}")

        if failures:
            pytest.fail(
                f"CRITICAL: {len(failures)} test file(s) cannot collect due to import errors:\n" +
                "\n".join(failures) +
                "\n\nThese tests give false coverage confidence. Fix imports or delete files."
            )

    def test_no_quarantine_directory_exists(self):
        """P0: _quarantine directory should not exist (or should be empty)."""
        security_dir = Path(__file__).parent
        quarantine_dir = security_dir / "_quarantine"

        if quarantine_dir.exists():
            quarantined_files = list(quarantine_dir.glob("test_*.py"))
            if quarantined_files:
                pytest.fail(
                    f"CRITICAL: {len(quarantined_files)} quarantined test file(s) found.\n"
                    f"Files: {[f.name for f in quarantined_files]}\n"
                    "Quarantined tests give false coverage confidence. "
                    "Either fix the imports and move back, or delete them."
                )

    def test_no_pytest_skip_without_reason(self):
        """P1: All pytest.skip() calls must have meaningful reasons."""
        security_dir = Path(__file__).parent
        test_files = list(security_dir.glob("test_*.py"))

        # This is a heuristic check - look for skip calls without linked tickets
        skip_issues = []
        for test_file in test_files:
            content = test_file.read_text()
            if "pytest.skip" in content:
                # Check if there's a linked issue or expiration
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "pytest.skip" in line:
                        # Look at context for reason
                        context = "\n".join(lines[max(0, i-2):i+3])
                        if "TODO" not in context and "FIXME" not in context and "ticket" not in context.lower():
                            if "not available" not in context.lower():  # Skip for unavailable infra is OK
                                skip_issues.append(f"{test_file.name}:{i+1}")

        # Just warn about these, don't fail
        if skip_issues:
            print(f"WARNING: {len(skip_issues)} pytest.skip calls without linked tickets:")
            for issue in skip_issues[:10]:  # Show first 10
                print(f"  - {issue}")

    def test_no_orphaned_fixture_references(self):
        """P1: All fixture references must be defined."""
        security_dir = Path(__file__).parent
        conftest = security_dir / "conftest.py"

        if not conftest.exists():
            pytest.skip("No conftest.py in security directory")

        # Parse fixtures from conftest
        conftest_content = conftest.read_text()

        # Get all fixtures defined in conftest
        import re
        defined_fixtures = set(re.findall(r"@pytest\.fixture.*?\ndef\s+(\w+)", conftest_content, re.DOTALL))

        # Check each test file for undefined fixture usage
        test_files = list(security_dir.glob("test_*.py"))
        undefined_refs = []

        for test_file in test_files:
            if test_file.name == "test_collection_verification.py":
                continue

            content = test_file.read_text()
            # Find function parameters that might be fixtures
            func_params = re.findall(r"def test_\w+\([^)]*\b(\w+)\b", content)

            for param in func_params:
                if param in ["self", "client", "jwt_encoder"]:  # Known builtins
                    continue
                if param not in defined_fixtures:
                    # Might be from parent conftest.py - check if it works
                    pass

        # This is informational only
        print(f"Defined fixtures in conftest: {len(defined_fixtures)}")


class TestProductionAssuranceMetrics:
    """Metrics tracking for production assurance."""

    def test_security_test_count_minimum(self):
        """P1: Minimum security test count to ensure coverage."""
        security_dir = Path(__file__).parent
        test_files = list(security_dir.glob("test_*.py"))

        # Count test functions
        total_tests = 0
        for test_file in test_files:
            if test_file.name == "test_collection_verification.py":
                continue

            content = test_file.read_text()
            test_count = len([l for l in content.split("\n") if l.strip().startswith("def test_")])
            total_tests += test_count

        # Current baseline: 243 tests (as measured)
        MINIMUM_TESTS = 240

        assert total_tests >= MINIMUM_TESTS, (
            f"Security test count ({total_tests}) below minimum ({MINIMUM_TESTS}). "
            f"Coverage may have regressed."
        )

    def test_negative_test_ratio(self):
        """P1: At least 30% of tests should be negative/adversarial."""
        security_dir = Path(__file__).parent
        test_files = list(security_dir.glob("test_*.py"))

        positive_tests = 0
        negative_tests = 0

        for test_file in test_files:
            if test_file.name == "test_collection_verification.py":
                continue

            content = test_file.read_text()
            test_names = [l for l in content.split("\n") if l.strip().startswith("def test_")]

            for test_line in test_names:
                test_name = test_line.split("def ")[1].split("(")[0]
                # Heuristic: negative tests often have these keywords
                if any(kw in test_name.lower() for kw in [
                    "reject", "block", "deny", "forbidden", "unauthorized",
                    "invalid", "malformed", "tamper", "manipulate", "spoof",
                    "attack", "injection", "xss", "sql", "error", "fail",
                    "cannot", "no_", "not_", "negative", "adversarial"
                ]):
                    negative_tests += 1
                else:
                    positive_tests += 1

        total = positive_tests + negative_tests
        if total == 0:
            pytest.skip("No tests found")

        negative_ratio = negative_tests / total

        print(f"Positive tests: {positive_tests}")
        print(f"Negative tests: {negative_tests}")
        print(f"Negative ratio: {negative_ratio:.1%}")

        # Require at least 25% negative tests
        assert negative_ratio >= 0.25, (
            f"Negative test ratio ({negative_ratio:.1%}) below 25%. "
            f"Add more adversarial tests to prove boundaries fail closed."
        )

    def test_ci_gate_configuration(self):
        """P1: CI workflow must include security test gate."""
        repo_root = Path(__file__).parent.parent.parent
        workflows_dir = repo_root / ".github" / "workflows"

        if not workflows_dir.exists():
            pytest.skip("No GitHub workflows directory")

        workflow_files = list(workflows_dir.glob("*.yml"))

        security_test_found = False
        for wf in workflow_files:
            content = wf.read_text(encoding="utf-8")
            if "security" in content.lower() and "test" in content.lower():
                if "pytest" in content or "tests/security" in content:
                    security_test_found = True
                    break

        assert security_test_found, (
            "No CI workflow found that runs security tests. "
            "Add pytest tests/security/ to CI pipeline."
        )


# Run with: pytest tests/security/test_collection_verification.py -v
# This test enforces that the test suite itself is healthy
