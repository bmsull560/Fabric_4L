from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException

from layer5_ground_truth.api.main import create_app
from layer5_ground_truth.integration.layer3_client import Layer3Client
from tests.conftest import TEST_ORG_ID


@pytest.mark.asyncio
async def test_layer3_entity_context_policy_denial_returns_none(monkeypatch) -> None:
    req = httpx.Request("GET", "http://layer3/api/v1/entities/e1")
    response = httpx.Response(403, request=req, json={"detail": "policy denied"})

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPStatusError("forbidden", request=req, response=response)
    monkeypatch.setattr("layer5_ground_truth.integration.layer3_client.Layer3Client._get_client", lambda self: mock_client)

    client = Layer3Client()
    result = await client.get_entity_context("e1", TEST_ORG_ID)
    assert result is None


@pytest.mark.asyncio
async def test_layer3_entity_context_timeout_returns_none(monkeypatch) -> None:
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ReadTimeout("timed out")
    monkeypatch.setattr("layer5_ground_truth.integration.layer3_client.Layer3Client._get_client", lambda self: mock_client)

    client = Layer3Client()
    result = await client.get_entity_context("e1", TEST_ORG_ID)
    assert result is None


@pytest.mark.asyncio
async def test_layer3_entity_context_malformed_contract_returns_none(monkeypatch) -> None:
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = ["unexpected-array"]
    mock_client.get.return_value = mock_response
    monkeypatch.setattr("layer5_ground_truth.integration.layer3_client.Layer3Client._get_client", lambda self: mock_client)

    client = Layer3Client()
    result = await client.get_entity_context("e1", TEST_ORG_ID)
    assert result is None


@pytest.mark.asyncio
async def test_layer3_entity_context_tenant_mismatch_returns_none(monkeypatch) -> None:
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"id": "e1", "tenant_id": str(uuid.uuid4())}
    mock_client.get.return_value = mock_response
    monkeypatch.setattr("layer5_ground_truth.integration.layer3_client.Layer3Client._get_client", lambda self: mock_client)

    client = Layer3Client()
    result = await client.get_entity_context("e1", TEST_ORG_ID)
    assert result is None


def test_security_http_exception_uses_explicit_security_error_payload() -> None:
    app = create_app()

    @app.get("/test/security-error")
    async def _route() -> None:
        raise HTTPException(status_code=403, detail={"error_code": "INSUFFICIENT_SCOPE", "message": "Denied"})

    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/test/security-error", headers={"X-Tenant-ID": str(TEST_ORG_ID)})

    assert response.status_code == 403
    assert response.json()["error"] == "security_error"
    assert response.json()["error_code"] == "INSUFFICIENT_SCOPE"
