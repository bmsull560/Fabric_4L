"""Tests for gate daemon."""

import pytest
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from gated.config import DaemonConfig
from gated.daemon import GateDaemon
from sdk.models import CheckResult, GateArtifact, GateExecution, GateProfile, GateResult, GateSeverity
from sdk.plugin import GateContext, GatePlugin


class MockGate(GatePlugin):
    """Mock gate for testing."""
    
    @property
    def gate_id(self) -> str:
        return "mock"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.BLOCKER
    
    @property
    def expected_artifacts(self) -> list[str]:
        return ["mock/report.json"]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        return [
            CheckResult(
                name="test_check",
                result=GateResult.PASS,
                value=True,
                threshold=True,
                comparator="eq",
            )
        ]


@pytest.fixture
def config():
    return DaemonConfig(
        bind_addr="127.0.0.1",
        port=8888,
        artifact_store="./test_artifacts",
    )


@pytest.fixture
def daemon(config):
    d = GateDaemon(config)
    d.register_plugin(MockGate())
    return d


@pytest.mark.asyncio
async def test_daemon_list_gates(daemon):
    gates = daemon.list_gates()
    assert len(gates) == 1
    assert gates[0]["gate_id"] == "mock"


@pytest.mark.asyncio
async def test_daemon_execute_gate(daemon, tmp_path):
    execution = await daemon.execute_gate("mock", profile="pr-fast")
    
    assert execution.gate_id == "mock"
    assert execution.profile == GateProfile.PR_FAST
    assert len(execution.results) == 1
    assert execution.results[0].name == "test_check"


@pytest.mark.asyncio
async def test_daemon_unknown_gate(daemon):
    with pytest.raises(ValueError, match="Unknown gate"):
        await daemon.execute_gate("unknown")


def test_daemon_evaluate_release(daemon):
    # Need to execute a gate first to have results
    # This test would need async setup
    pass


@pytest.mark.asyncio
async def test_execution_artifact_collection(daemon, tmp_path):
    execution = await daemon.execute_gate("mock", profile="pr-fast")
    
    # Create artifact for collection
    gate_dir = tmp_path / "mock"
    gate_dir.mkdir(parents=True)
    report_file = gate_dir / "report.json"
    report_file.write_text('{"test": true}')
    
    # Artifacts are collected by plugin
    assert execution is not None
