from __future__ import annotations

import pytest

from src.services.context_gatherer import ContextGatheringService


class _FakeResult:
    def __init__(self, records):
        self._records = records
        self._idx = 0

    def __aiter__(self):
        self._idx = 0
        return self

    async def __anext__(self):
        if self._idx >= len(self._records):
            raise StopAsyncIteration
        value = self._records[self._idx]
        self._idx += 1
        return value


class _FakeSession:
    def __init__(self, records, calls):
        self._records = records
        self._calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def run(self, query, params):
        self._calls.append({"query": query, "params": params})
        return _FakeResult(self._records)


class _FakeDriver:
    def __init__(self, records):
        self.calls = []
        self._records = records

    def session(self):
        return _FakeSession(self._records, self.calls)


@pytest.mark.asyncio
async def test_get_account_hypotheses_maps_fields_once_without_duplicates():
    records = [
        {
            "hypothesis": {
                "id": "h1",
                "hypothesis_text": "Reduce cycle time",
                "status": "draft",
                "confidence_score": 0.72,
                "value_path_category": "efficiency",
                "estimated_impact_usd": 240000,
                "capability_name": "Workflow automation",
                "signal_name": "Backlog growth",
            }
        }
    ]
    service = ContextGatheringService(neo4j_driver=_FakeDriver(records))

    result = await service._get_account_hypotheses("acct-1", "tenant-a")

    assert result == [
        {
            "id": "h1",
            "text": "Reduce cycle time",
            "status": "draft",
            "confidence": 0.72,
            "value_path": "efficiency",
            "estimated_impact_usd": 240000,
            "capability": "Workflow automation",
            "signal": "Backlog growth",
        }
    ]


@pytest.mark.asyncio
async def test_get_account_hypotheses_rejects_mismatched_tenant_context():
    driver = _FakeDriver([])
    service = ContextGatheringService(neo4j_driver=driver)

    hypotheses = await service._get_account_hypotheses("acct-1", "tenant-a")

    assert hypotheses == []
    assert driver.calls
    assert driver.calls[0]["params"]["tenant_id"] == "tenant-a"
    assert driver.calls[0]["params"]["account_id"] == "acct-1"

    from src.services.tenant_query_helper import run_tenant_validated_query

    with pytest.raises(ValueError, match="Tenant context mismatch"):
        await run_tenant_validated_query(
            driver=driver,
            query="RETURN 1",
            tenant_id="tenant-a",
            params={"tenant_id": "tenant-b"},
        )
