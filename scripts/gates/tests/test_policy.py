"""Tests for policy engine."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from policy.engine import PolicyEngine
from policy.loader import PolicyLoader
from policy.models import GatePolicy, GateSeverity, PolicyThreshold
from sdk.models import CheckResult, GateExecution, GateProfile, GateResult, GateSeverity as SdkSeverity


@pytest.fixture
def sample_policy_yaml(tmp_path):
    policy_content = """
version: "1.0"
enforcement_mode: "fail-closed"
block_on_missing_artifacts: true

stale_gate_results:
  pr-fast: 24
  mainline-full: 12
  release-candidate: 6

gates:
  mock:
    severity: "blocker"
    owner: "test-team"
    description: "Mock gate for testing"
    checks:
      - name: "test_check"
        expected: true
        comparator: "eq"
        max_allowed_failures: 0
    artifacts:
      - "mock/report.json"
    fail_on_error: true
    max_allowed_failures: 0
    matrix:
      pr-fast:
        enabled: true
      mainline-full:
        enabled: true
      release-candidate:
        enabled: true

profiles:
  pr-fast:
    description: "Fast checks for PRs"
    timeout_minutes: 15
  mainline-full:
    description: "Full test suite"
    timeout_minutes: 45
  release-candidate:
    description: "Release candidate validation"
    timeout_minutes: 60
"""
    policy_file = tmp_path / "test-policy.yaml"
    policy_file.write_text(policy_content)
    return policy_file


@pytest.fixture
def engine(sample_policy_yaml):
    return PolicyEngine(policy_path=str(sample_policy_yaml))


@pytest.fixture
def mock_execution():
    return GateExecution(
        execution_id=uuid4(),
        gate_id="mock",
        profile=GateProfile.PR_FAST,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        results=[
            CheckResult(
                name="test_check",
                result=GateResult.PASS,
                value=True,
                threshold=True,
                comparator="eq",
            )
        ],
    )


def test_load_policy(engine):
    assert engine.config is not None
    assert engine.config.version == "1.0"
    assert len(engine.config.gates) == 1


def test_evaluate_passing_gate(engine, mock_execution):
    verdict = engine.evaluate(mock_execution)
    
    assert verdict.result == GateResult.PASS
    assert not verdict.blocks_release


def test_evaluate_failing_gate(engine, mock_execution):
    mock_execution.results[0].result = GateResult.FAIL
    
    verdict = engine.evaluate(mock_execution)
    
    assert verdict.result == GateResult.FAIL
    assert verdict.blocks_release  # Blocker severity


def test_evaluate_with_errors(engine, mock_execution):
    mock_execution.results[0].result = GateResult.ERROR
    
    verdict = engine.evaluate(mock_execution)
    
    assert verdict.result == GateResult.ERROR
    assert verdict.blocks_release


def test_evaluate_release_no_gates(engine):
    result = engine.evaluate_release([], profile="pr-fast")
    
    assert result["result"] == "approved"
    assert not result["blocks_release"]


def test_evaluate_release_stale_results(engine):
    stale_execution = GateExecution(
        execution_id=uuid4(),
        gate_id="mock",
        profile=GateProfile.PR_FAST,
        started_at=datetime.utcnow() - timedelta(hours=25),
        finished_at=datetime.utcnow() - timedelta(hours=25),
        results=[],
    )
    
    result = engine.evaluate_release([stale_execution], stale_threshold_hours=24)
    
    assert result["result"] == "blocked"
    assert result["blocks_release"]
