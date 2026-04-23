"""Tests for business-case SDES generation, persistence, and export references."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from src.engine.state_manager import StateManager
from src.models.agent_state import WorkflowStatus
from src.models.workflow_config import BUSINESS_CASE_WORKFLOW_CONFIG
from src.services.export_provenance import build_export_provenance_manifest
from src.workflows.business_case import BusinessCaseGeneratorWorkflow


def test_business_case_workflow_config_places_sdes_after_input_gathering() -> None:
    """SDES node must execute immediately after gather_inputs."""
    node_ids = [node.id for node in BUSINESS_CASE_WORKFLOW_CONFIG.nodes]
    assert "generate_sdes" in node_ids
    assert node_ids.index("generate_sdes") == node_ids.index("gather_inputs") + 1

    edges = {(edge.source, edge.target) for edge in BUSINESS_CASE_WORKFLOW_CONFIG.edges}
    assert ("gather_inputs", "generate_sdes") in edges
    assert ("generate_sdes", "run_roi") in edges


@pytest.mark.asyncio
async def test_generate_sdes_contains_required_fields_and_ids() -> None:
    """SDES generation should include signals, drivers, evidence, stakeholders."""
    registry = Mock()
    registry.execute = AsyncMock()
    workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)
    state = workflow.create_initial_state(
        {
            "prospect_id": "prospect-100",
            "sections_requested": ["executive_summary"],
            "custom_inputs": {
                "canonical_case_id": "case-canonical-001",
                "account_id": "acct-001",
            },
        }
    )
    state.output_data = {
        "gather_inputs": {
            "prospect": {
                "profile": {"name": "Acme Corp", "industry": "software"},
            },
            "interactions": {
                "interactions": [{"summary": "Positive technical validation", "timestamp": "2026-04-20"}]
            },
            "lead_score": {"score": 87, "confidence": 0.91},
        }
    }

    result = await workflow._execute_generate_sdes_bundle(state)

    assert result["canonical_case_id"] == "case-canonical-001"
    assert result["account_id"] == "acct-001"
    assert result["signals"]
    assert result["drivers"]
    assert result["evidence"]
    assert result["stakeholders"]


@pytest.mark.asyncio
async def test_sdes_persisted_and_retrievable_after_reload() -> None:
    """SDES bundle must survive state save/load (simulated restart)."""
    registry = Mock()
    registry.execute = AsyncMock()
    workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)
    state = workflow.create_initial_state(
        {
            "prospect_id": "prospect-200",
            "sections_requested": ["executive_summary"],
            "custom_inputs": {"canonical_case_id": "case-200", "account_id": "acct-200"},
        }
    )
    state.status = WorkflowStatus.COMPLETED
    state.output_data = {
        "generate_sdes": {
            "canonical_case_id": "case-200",
            "account_id": "acct-200",
            "signals": [{"id": "engagement_score"}],
            "drivers": [{"id": "revenue_growth"}],
            "evidence": [{"id": "account_profile"}],
            "stakeholders": [{"id": "primary_account"}],
        }
    }

    manager = StateManager()
    await manager.save_state(state.workflow_id, state)

    reloaded = await manager.load_state(state.workflow_id)

    assert reloaded is not None
    sdes = reloaded.output_data["generate_sdes"]
    assert sdes["canonical_case_id"] == "case-200"
    assert sdes["account_id"] == "acct-200"
    assert len(sdes["signals"]) == 1

    manifest = build_export_provenance_manifest(
        case_id="case-200",
        workflow_result={"workflow_id": state.workflow_id, "output": reloaded.output_data},
        actor_context=None,
        export_id="export-1",
    )
    assert manifest["sdes_references"]["canonical_case_id"] == "case-200"
    assert manifest["sdes_references"]["account_id"] == "acct-200"
    assert manifest["sdes_references"]["signals"] == ["engagement_score"]
