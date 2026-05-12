import json
from pathlib import Path

import pytest
from httpx import AsyncClient

SNAPSHOT_PATH = Path(__file__).resolve().parent / "snapshots" / "layer5_response_shapes.json"


def _shape(value):
    if isinstance(value, dict):
        return {k: _shape(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        if not value:
            return []
        return [_shape(value[0])]
    return type(value).__name__


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint,snapshot_key",
    [
        ("/health", "health"),
        ("/api/v1/maturity-ladder", "maturity_ladder"),
        ("/api/v1/truths/freshness-summary", "freshness_summary"),
    ],
)
async def test_layer5_response_shape_snapshots(client: AsyncClient, endpoint: str, snapshot_key: str):
    response = await client.get(endpoint)
    assert response.status_code == 200

    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot_key in snapshot
    assert _shape(response.json()) == snapshot[snapshot_key]
