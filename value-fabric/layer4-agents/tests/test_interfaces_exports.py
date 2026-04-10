"""Tests for Layer 4 interfaces package exports and basic interface behavior.

NOTE: These imports rely on pytest configuration in pyproject.toml:
    pythonpath = [".", "src"]
This adds the src/ directory to the path, allowing 'from src.interfaces' imports.
Run tests from the layer4-agents/ directory for imports to resolve correctly.
"""

import pytest

from src.interfaces import (
    ActivationRequest,
    BenchmarkDataset,
    ComparisonRequest,
    FormulaGovernance,
    FormulaStatus,
    GovernanceTransitionResult,
    HTTPBenchmarkClient,
    IBenchmarkClient,
    IFormulaApprovalWorkflow,
    IFormulaGovernanceService,
    IGroundTruthVariableBridge,
    IValuePackService,
    IVariableRegistry,
    PackExecutionRequest,
    PackStatus,
    ResolutionContext,
    ValuePack,
    Variable,
    VariableDataType,
    VariableSourceType,
)


def test_interfaces_module_exports_core_symbols():
    assert IBenchmarkClient is not None
    assert HTTPBenchmarkClient is not None
    assert IValuePackService is not None
    assert IFormulaGovernanceService is not None
    assert IFormulaApprovalWorkflow is not None
    assert IVariableRegistry is not None
    assert IGroundTruthVariableBridge is not None


def test_http_benchmark_client_normalizes_base_url():
    client = HTTPBenchmarkClient(base_url="http://localhost:8006/")
    assert client.base_url == "http://localhost:8006"


@pytest.mark.asyncio
async def test_http_benchmark_client_close_is_safe_without_open_client():
    client = HTTPBenchmarkClient(base_url="http://localhost:8006")
    await client.close()
    assert client._client is None


def test_interface_dataclasses_construct_with_expected_types():
    pack = ValuePack(
        pack_id="pack-1",
        name="Manufacturing Pack",
        description="desc",
        industry="manufacturing",
        segment=None,
        status=PackStatus.DRAFT,
        version="1.0.0",
    )
    req = PackExecutionRequest(
        pack_id=pack.pack_id,
        workspace_id="ws-1",
        variables={"revenue": 1000},
    )
    gov = FormulaGovernance(
        formula_id="f-1",
        current_version="1.0.0",
        status=FormulaStatus.DRAFT,
    )
    activation = ActivationRequest(
        formula_id="f-1",
        version="1.0.0",
        requested_by="user-1",
        justification="go live",
    )
    transition = GovernanceTransitionResult(
        success=True,
        formula_id="f-1",
        old_status=FormulaStatus.DRAFT,
        new_status=FormulaStatus.ACTIVE,
    )
    variable = Variable(
        variable_id="v-1",
        name="Annual Revenue",
        description="Revenue in USD",
        data_type=VariableDataType.DECIMAL,
    )
    context = ResolutionContext(workspace_id="ws-1")
    dataset = BenchmarkDataset(
        id="ds-1",
        name="Bench",
        industry="manufacturing",
        segment=None,
        metrics=["revenue"],
        statistical_profile={"p50": 123},
    )
    comparison = ComparisonRequest(
        dataset_id=dataset.id,
        metric="revenue",
        company_value=100,
        industry="manufacturing",
    )

    assert req.pack_id == pack.pack_id
    assert activation.formula_id == gov.formula_id
    assert transition.new_status == FormulaStatus.ACTIVE
    assert variable.data_type == VariableDataType.DECIMAL
    assert context.workspace_id == "ws-1"
    assert comparison.dataset_id == dataset.id
    assert VariableSourceType.BENCHMARK_LOOKUP.value == "benchmark_lookup"
