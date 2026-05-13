from __future__ import annotations

import pytest


@pytest.mark.anyio
async def test_ready_when_db_reachable_and_schema_aligned(client, monkeypatch) -> None:
    from layer5_ground_truth.api import main as main_module

    async def _aligned() -> tuple[bool, str]:
        return True, "aligned"

    monkeypatch.setattr(main_module, "_check_schema_migration_alignment", _aligned)

    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


@pytest.mark.anyio
async def test_not_ready_when_db_reachable_but_schema_drift(client, monkeypatch) -> None:
    from layer5_ground_truth.api import main as main_module

    async def _drifted() -> tuple[bool, str]:
        return False, "behind"

    monkeypatch.setattr(main_module, "_check_schema_migration_alignment", _drifted)

    response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": "ok",
        "schema": "behind",
    }


@pytest.mark.anyio
async def test_not_ready_when_db_unreachable(client, monkeypatch) -> None:
    from layer5_ground_truth.api import main as main_module

    async def _raise(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(main_module, "_check_schema_migration_alignment", _raise)

    response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}
