from __future__ import annotations

<<<<<<< HEAD
import pytest

from src.services.context_gatherer import ContextGatheringService
from src.services.tenant_query_helper import run_tenant_validated_query


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


class _SingleAccessRecord(dict):
    def __init__(self, payload: dict):
        super().__init__({"hypothesis": payload})
        self.hypothesis_get_count = 0

    def get(self, key, default=None):
        if key == "hypothesis":
            self.hypothesis_get_count += 1
        return super().get(key, default)


@pytest.mark.asyncio
async def test_get_account_hypotheses_maps_fields_once_without_duplicates():
    payload = {
        "id": "h1",
        "hypothesis_text": "Reduce cycle time",
        "status": "draft",
        "confidence_score": 0.72,
        "value_path_category": "efficiency",
        "estimated_impact_usd": 240000,
        "capability_name": "Workflow automation",
        "signal_name": "Backlog growth",
    }
    record = _SingleAccessRecord(payload)
    service = ContextGatheringService(neo4j_driver=_FakeDriver([record]))

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
    assert record.hypothesis_get_count == 1


@pytest.mark.asyncio
async def test_get_account_hypotheses_uses_authenticated_tenant_context():
    driver = _FakeDriver([])
    service = ContextGatheringService(neo4j_driver=driver)

    hypotheses = await service._get_account_hypotheses("acct-1", "tenant-a")

    assert hypotheses == []
    assert driver.calls
    assert driver.calls[0]["params"]["tenant_id"] == "tenant-a"
    assert driver.calls[0]["params"]["account_id"] == "acct-1"


@pytest.mark.asyncio
async def test_run_tenant_validated_query_rejects_mismatched_tenant_context():
    driver = _FakeDriver([])

    with pytest.raises(ValueError, match="Tenant context mismatch"):
        await run_tenant_validated_query(
            driver=driver,
            query="RETURN 1",
            tenant_id="tenant-a",
            params={"tenant_id": "tenant-b"},
        )

<<<<<<< ours
    assert driver.calls == []
=======
=======
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

>>>>>>> 315e84c14c9306363c718c22c8cb7a292d514eee
    assert session.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("operation", "query", "params"),
    [
        (
            "context_gatherer.account_signals",
            """
            MATCH (s:Signal {tenant_id: $tenant_id})
            WHERE s.account_id = $account_id OR s.target_account_id = $account_id
            RETURN s {.*} AS signal
            """,
            {"tenant_id": "tenant-b", "account_id": "acct-1"},
        ),
        (
            "context_gatherer.account_hypotheses",
            """
            MATCH (vh:ValueHypothesis {tenant_id: $tenant_id, account_id: $account_id})
            RETURN vh {.*} AS hypothesis
            """,
            {"tenant_id": "tenant-b", "account_id": "acct-1"},
        ),
    ],
)
async def test_context_queries_reject_mismatched_tenant_context(
    operation: str,
    query: str,
    params: dict[str, Any],
) -> None:
    session = MockSession({"tenant-b": [{"signal": {"id": "sig-b"}}]})

    with pytest.raises(TenantCypherValidationError):
        await fetch_tenant_validated_records(
            driver=MockDriver(session),
            query=query,
            params=params,
            tenant_id="tenant-a",
            operation=operation,
        )

    assert session.calls == []
<<<<<<< HEAD
>>>>>>> theirs
=======
>>>>>>> 315e84c14c9306363c718c22c8cb7a292d514eee
