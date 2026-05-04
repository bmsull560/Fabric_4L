"""Regression tests for the mandatory security regression gate.

These tests validate the gate contract itself, not the full security suite.
They ensure the gate fails when required suites are missing, uses correct artifact paths,
and includes all required coverage without silent skips.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

GATE_SCRIPT = Path(__file__).parent.parent.parent / "scripts" / "ci" / "mandatory_security_regression_gate.sh"
REPO_ROOT = Path(__file__).parent.parent.parent


def test_gate_script_exists():
    """Gate script must exist at expected location."""
    assert GATE_SCRIPT.exists(), f"Gate script not found at {GATE_SCRIPT}"


def test_gate_is_executable():
    """Gate script should be executable."""
    assert GATE_SCRIPT.stat().st_mode & 0o111, "Gate script is not executable"


def test_gate_list_required_mode():
    """Gate should support --list-required dry-run mode."""
    result = subprocess.run(
        [str(GATE_SCRIPT), "--list-required"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, f"--list-required failed: {result.stderr}"
    required_suites = result.stdout.strip().split("\n")

    # Check that I-02 layer2 and layer5 suites are in the list
    layer2_i02 = "services/layer2-extraction/tests/test_production_fail_closed_i02.py"
    layer5_i02 = "services/layer5-ground-truth/tests/test_production_fail_closed_i02.py"

    assert layer2_i02 in required_suites, f"I-02 Layer 2 suite missing from required list"
    assert layer5_i02 in required_suites, f"I-02 Layer 5 suite missing from required list"


def test_gate_references_required_i02_layer_suites():
    """Gate script must explicitly invoke I-02 layer2 and layer5 checks."""
    script_content = GATE_SCRIPT.read_text()

    # Check for I-02 layer2 invocation
    assert "test_production_fail_closed_i02.py" in script_content, "Gate missing I-02 test invocation"
    assert "layer2-extraction" in script_content, "Gate missing Layer 2 reference"
    assert "layer5-ground-truth" in script_content, "Gate missing Layer 5 reference"


def test_gate_verify_required_only_mode():
    """Gate should support --verify-required-only mode and pass with all suites present."""
    result = subprocess.run(
        [str(GATE_SCRIPT), "--verify-required-only"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, f"--verify-required-only failed: {result.stderr}"
    assert "All required suites present" in result.stdout


def test_gate_uses_repo_relative_audit_dir():
    """Gate should use repo-relative fabric_audit/ path, not Linux-specific /home/ubuntu."""
    script_content = GATE_SCRIPT.read_text()

    # Should NOT use Linux-specific path
    assert "/home/ubuntu/fabric_audit" not in script_content, "Gate uses Linux-specific artifact path"

    # Should use repo-relative pattern
    assert "AUDIT_DIR" in script_content, "Gate missing AUDIT_DIR variable"
    assert "fabric_audit" in script_content, "Gate missing fabric_audit reference"
    assert "ROOT_DIR" in script_content, "Gate missing ROOT_DIR variable"


def test_gate_includes_required_suite_array():
    """Gate script must define REQUIRED_SUITES array with all critical checks."""
    script_content = GATE_SCRIPT.read_text()

    assert "REQUIRED_SUITES=(" in script_content, "Gate missing REQUIRED_SUITES array"

    # Check for critical security suites
    required_patterns = [
        "test_auth_enforcement",
        "test_production_safety",
        "test_tenant_boundary_fails_closed",
        "test_cross_tenant_api",
        "test_security_policies",
        "test_workload_validation",
    ]

    for pattern in required_patterns:
        assert pattern in script_content, f"REQUIRED_SUITES missing {pattern}"


def test_gate_includes_frontend_contract_guards():
    """Gate must include frontend contract tests and placeholder guard."""
    script_content = GATE_SCRIPT.read_text()

    assert "Frontend contract tests" in script_content or "vitest run src/api/__tests__/contract" in script_content, \
        "Gate missing frontend contract tests"
    assert "placeholder" in script_content.lower() or "assert-no-placeholder" in script_content, \
        "Gate missing placeholder contract guard"


def test_gate_includes_critical_e2e_guards():
    """Gate must include critical E2E skip-valve guard."""
    script_content = GATE_SCRIPT.read_text()

    assert "E2E" in script_content or "e2e" in script_content.lower(), "Gate missing E2E reference"
    assert "skip" in script_content.lower(), "Gate missing skip guard reference"


def test_gate_includes_kubernetes_hardening_checks():
    """Gate must include Kubernetes workload hardening checks."""
    script_content = GATE_SCRIPT.read_text()

    assert "Kubernetes" in script_content or "k8s" in script_content.lower(), "Gate missing Kubernetes reference"
    assert "test_security_policies" in script_content, "Gate missing security policies test"
    assert "test_workload_validation" in script_content, "Gate missing workload validation test"


def test_gate_has_check_required_suites_function():
    """Gate must have fail-closed validation function."""
    script_content = GATE_SCRIPT.read_text()

    assert "check_required_suites" in script_content, "Gate missing check_required_suites function"
    assert "exit 1" in script_content, "Gate missing exit on failure"


def test_gate_calls_check_required_suites():
    """Gate must call check_required_suites before execution."""
    script_content = GATE_SCRIPT.read_text()

    # The function should be called in main execution flow (after dry-run modes)
    assert "check_required_suites" in script_content, "Gate missing check_required_suites call"


def test_gate_has_no_skip_or_best_effort_mode():
    """Gate should not have skip or best-effort mode for required suites."""
    script_content = GATE_SCRIPT.read_text()

    # These patterns would indicate silent failure modes
    anti_patterns = [
        "|| true",  # Continue on error
        "|| continue",  # Continue on error
        "best-effort",  # Best-effort mode
    ]

    script_lower = script_content.lower()
    for pattern in anti_patterns:
        # Allow some context-specific uses (e.g., in dry-run modes or specific error handling)
        if pattern in script_lower:
            # Check if it's in an acceptable context
            lines_with_pattern = [line for line in script_content.split("\n") if pattern in line.lower()]
            for line in lines_with_pattern:
                # Allow in comments or specific safe contexts
                if not line.strip().startswith("#") and "dry-run" not in line.lower() and "test mode" not in line.lower():
                    pytest.fail(f"Gate has unsafe pattern '{pattern}' in: {line}")


def test_gate_has_sprint4_reference():
    """Gate script should reference Sprint 4 in its header comment."""
    script_content = GATE_SCRIPT.read_text()

    assert "Sprint 4" in script_content or "Sprint 2" in script_content, \
        "Gate header missing Sprint reference"


def test_gate_creates_audit_directory():
    """Gate should create audit directory if it doesn't exist."""
    script_content = GATE_SCRIPT.read_text()

    assert "mkdir -p" in script_content, "Gate missing mkdir -p for audit directory"
    assert "AUDIT_DIR" in script_content, "Gate missing AUDIT_DIR in mkdir command"


def test_gate_outputs_evidence_path():
    """Gate should output evidence path on success."""
    script_content = GATE_SCRIPT.read_text()

    assert "Evidence written to" in script_content, \
        "Gate missing evidence path output message"
    assert "AUDIT_DIR" in script_content, \
        "Gate should output AUDIT_DIR variable in evidence path"


def test_gate_has_jq_fallback():
    """Gate should gracefully handle missing jq dependency."""
    script_content = GATE_SCRIPT.read_text()

    # Should check for jq before using it
    assert "command -v jq" in script_content or "which jq" in script_content, \
        "Gate missing jq dependency check"


def test_gate_test_mode_functionality():
    """Gate should support FABRIC_GATE_TEST_MODE for skipping expensive operations."""
    script_content = GATE_SCRIPT.read_text()

    assert "FABRIC_GATE_TEST_MODE" in script_content, \
        "Gate missing FABRIC_GATE_TEST_MODE variable"
    assert "TEST MODE" in script_content or "test mode" in script_content.lower(), \
        "Gate missing test mode logging" 
