from __future__ import annotations

from typing import Any

import pytest
from value_fabric.layer4.services.context_gatherer import ContextGatheringService
from value_fabric.layer4.services.tenant_cypher import (
    TenantCypherValidationError,
    fetch_tenant_validated_records,
)


class MockRecord:
    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


class MockResult:
    def __init__(self, records: list[dict[str, Any]]):
        self._records = [MockRecord(record) for record in records]
        self.iterations = 0
        self._index = 0

    def __aiter__(self):
        self.iterations += 1
        self._index = 0
        return self

    async def __anext__(self) -> MockRecord:
        if self._index >= len(self._records):
            raise StopAsyncIteration
        record = self._records[self._index]
        self._index += 1
        return record

    async def single(self) -> MockRecord | None:
        return self._records[0] if self._records else None


class MockSession:
    def __init__(self, responses_by_tenant: dict[str, list[dict[str, Any]]] | None = None):
        self.responses_by_tenant = responses_by_tenant or {}
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.results: list[MockResult] = []

    async def __aenter__(self) -> MockSession:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    async def run(self, query: str, params: dict[str, Any]) -> MockResult:
        self.calls.append((query, dict(params)))
        result = MockResult(self.responses_by_tenant.get(params["tenant_id"], []))
        self.results.append(result)
        return result


class MockDriver:
    def __init__(self, session: MockSession):
        self._session = session

    def session(self) -> MockSession:
        return self._session


@pytest.mark.asyncio
async def test_get_account_hypotheses_maps_fields_without_duplicate_entries() -> None:
    session = MockSession(
        {
            "tenant-a": [
                {
                    "hypothesis": {
                        "id": "hyp-1",
                        "hypothesis_text": "Reduce churn with automation",
                        "status": "draft",
                        "confidence_score": 0.91,
                        "value_path_category": "revenue_protection",
                        "estimated_impact_usd": 125000,
                        "capability_name": "Renewal Risk Automation",
                        "signal_name": "Rising churn risk",
                    }
                },
                {"hypothesis": None},
                {
                    "hypothesis": {
                        "id": "hyp-2",
                        "hypothesis_text": "Improve onboarding efficiency",
                        "status": "validated",
                        "confidence_score": 0.83,
                        "value_path_category": "cost_reduction",
                        "estimated_impact_usd": 90000,
                        "capability_name": "Onboarding Workflow",
                        "signal_name": "Long implementation cycle",
                    }
                },
            ]
        }
    )
    service = ContextGatheringService(neo4j_driver=MockDriver(session))

    hypotheses = await service._get_account_hypotheses("acct-1", "tenant-a")

    assert [hypothesis["id"] for hypothesis in hypotheses] == ["hyp-1", "hyp-2"]
    assert hypotheses == [
        {
            "id": "hyp-1",
            "text": "Reduce churn with automation",
            "status": "draft",
            "confidence": 0.91,
            "value_path": "revenue_protection",
            "estimated_impact_usd": 125000,
            "capability": "Renewal Risk Automation",
            "signal": "Rising churn risk",
        },
        {
            "id": "hyp-2",
            "text": "Improve onboarding efficiency",
            "status": "validated",
            "confidence": 0.83,
            "value_path": "cost_reduction",
            "estimated_impact_usd": 90000,
            "capability": "Onboarding Workflow",
            "signal": "Long implementation cycle",
        },
    ]
    assert session.results[0].iterations == 1


@pytest.mark.asyncio
async def test_account_signals_and_hypotheses_are_scoped_to_context_tenant() -> None:
    session = MockSession(
        {
            "tenant-b": [
                {"signal": {"id": "sig-b", "name": "Tenant B signal"}},
                {"hypothesis": {"id": "hyp-b", "hypothesis_text": "Tenant B hypothesis"}},
            ],
            "tenant-a": [],
        }
    )
    service = ContextGatheringService(neo4j_driver=MockDriver(session))

    signals = await service._get_account_signals("acct-owned-by-tenant-b", "tenant-a")
    hypotheses = await service._get_account_hypotheses("acct-owned-by-tenant-b", "tenant-a")

    assert signals == []
    assert hypotheses == []
    assert [params["tenant_id"] for _query, params in session.calls] == ["tenant-a", "tenant-a"]


@pytest.mark.asyncio
async def test_tenant_validated_helper_rejects_mismatched_tenant_parameters() -> None:
    session = MockSession({"tenant-b": [{"signal": {"id": "sig-b"}}]})
    query = """
    MATCH (s:Signal {tenant_id: $tenant_id})
    RETURN s {.*} AS signal
    """

    with pytest.raises(TenantCypherValidationError):
        await fetch_tenant_validated_records(
            driver=MockDriver(session),
            query=query,
            params={"tenant_id": "tenant-b"},
            tenant_id="tenant-a",
            operation="hostile_tenant_probe",
        )

    assert session.calls == []
