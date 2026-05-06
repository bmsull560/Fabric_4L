import pytest

from src.api.app_factory import create_app
from src.api.startup import StartupCheckResult, check_database_ready, check_redis_ready, check_vault_ready


@pytest.mark.asyncio
async def test_dependency_checks_contract(monkeypatch):
    async def ok_db():
        return None

    async def ok_ping():
        return True

    class RedisStub:
        async def ping(self):
            return await ok_ping()

    monkeypatch.setattr("src.api.startup.init_db", ok_db)
    db_result = await check_database_ready()
    assert isinstance(db_result, StartupCheckResult)
    assert db_result.ok is True

    redis_result = await check_redis_ready(RedisStub())
    assert redis_result.name == "redis"
    assert redis_result.ok is True

    vault_result = await check_vault_ready(environment="development", vault_addr=None)
    assert vault_result.ok is True


@pytest.mark.asyncio
async def test_dependency_checks_fail_contract(monkeypatch):
    async def fail_db():
        raise RuntimeError("db down")

    monkeypatch.setattr("src.api.startup.init_db", fail_db)
    db_result = await check_database_ready()
    assert db_result.ok is False
    assert "db down" in (db_result.detail or "")


def test_route_table_integrity_after_refactor():
    app = create_app()
    paths = {route.path for route in app.routes}
    assert "/" in paths
    assert "/health" in paths
    assert "/metrics" in paths
    assert any(p.startswith("/v1/workflows") for p in paths)
