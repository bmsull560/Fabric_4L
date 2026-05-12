from __future__ import annotations

import pytest
from pathlib import Path

from value_fabric.layer3.agents.roi_calculation import ROICalculationAgent
from value_fabric.layer3.analytics.similarity import SimilarityAnalyzer


@pytest.mark.security
@pytest.mark.unit
def test_similarity_methods_fail_closed_when_tenant_missing() -> None:
    analyzer = SimilarityAnalyzer()
    with pytest.raises(ValueError):
        analyzer._resolve_tenant_id(None)


@pytest.mark.security
@pytest.mark.unit
async def test_roi_operations_fail_closed_when_tenant_missing() -> None:
    agent = ROICalculationAgent(driver=None)
    with pytest.raises(ValueError):
        await agent._retrieve_formulas('uc-1', None)
    with pytest.raises(ValueError):
        await agent._get_formula('f-1', None)


@pytest.mark.security
@pytest.mark.unit
def test_similarity_queries_are_tenant_scoped_across_traversals() -> None:
    content = (Path(__file__).resolve().parents[2] / 'value_fabric/layer3/analytics/similarity.py').read_text(encoding='utf-8')
    assert 'AND common.tenant_id = $_tenant_id' in content
    assert 'all(node IN nodes(path) WHERE node.tenant_id = $_tenant_id)' in content


@pytest.mark.security
@pytest.mark.unit
def test_roi_queries_are_tenant_scoped_across_traversals() -> None:
    content = (Path(__file__).resolve().parents[2] / 'value_fabric/layer3/agents/roi_calculation.py').read_text(encoding='utf-8')
    assert 'MATCH (uc:UseCase {id: $use_case_id, tenant_id: $_tenant_id})-[:delivers]->(vd:ValueDriver {tenant_id: $_tenant_id})' in content
    assert 'OPTIONAL MATCH (vd)-[:measuredBy|calculatedBy]->(f:Formula {tenant_id: $_tenant_id})' in content
