from unittest.mock import AsyncMock, MagicMock

import pytest

from value_fabric.layer4.interfaces.formula_governance import FormulaStatus
from value_fabric.layer4.services.formula_governance_service import Neo4jFormulaGovernanceService
from value_fabric.layer4.services.value_pack_service import Neo4jValuePackService


@pytest.mark.asyncio
async def test_value_pack_get_pack_enforces_tenant_filter():
    driver = MagicMock()
    session = AsyncMock()
    driver.session.return_value.__aenter__.return_value = session
    result = AsyncMock()
    result.single = AsyncMock(return_value=None)
    session.run = AsyncMock(return_value=result)

    svc = Neo4jValuePackService(driver)
    pack = await svc.get_pack("pack-1", tenant_id="tenant-a")

    assert pack is None
    _, kwargs = session.run.call_args
    assert kwargs["tenant_id"] == "tenant-a"


@pytest.mark.asyncio
async def test_formula_governance_cross_tenant_formula_not_visible():
    driver = MagicMock()
    session = AsyncMock()
    driver.session.return_value.__aenter__.return_value = session
    result = AsyncMock()
    result.single = AsyncMock(return_value=None)
    session.run = AsyncMock(return_value=result)

    svc = Neo4jFormulaGovernanceService(driver)
    governance = await svc.get_governance("formula-b", tenant_id="tenant-a")

    assert governance is None
    _, kwargs = session.run.call_args
    assert kwargs["tenant_id"] == "tenant-a"


@pytest.mark.asyncio
async def test_formula_id_in_tenant_b_not_visible_from_tenant_a_regression():
    driver = MagicMock()
    session = AsyncMock()
    driver.session.return_value.__aenter__.return_value = session

    check_result = AsyncMock()
    check_result.single = AsyncMock(return_value=None)
    session.run = AsyncMock(return_value=check_result)

    svc = Neo4jFormulaGovernanceService(driver)
    resp = await svc.activate(
        request=type("Req", (), {"formula_id": "shared-formula", "version": "1.0.0", "requested_by": "u1", "effective_date": None})(),
        tenant_id="tenant-a",
    )

    assert resp.success is False
    assert resp.new_status == FormulaStatus.DRAFT
    _, kwargs = session.run.call_args
    assert kwargs["tenant_id"] == "tenant-a"
