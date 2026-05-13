from __future__ import annotations

import pytest

from app.core.database import InMemoryTable, SQLiteDatabase
from value_fabric.shared.database import MissingTenantContextError


def test_inmemory_table_denies_unscoped_reads_and_writes() -> None:
    table = InMemoryTable("accounts", "tenant_id")
    table.insert("acct-1", {"id": "acct-1", "tenant_id": "tenant-a", "name": "A"})

    with pytest.raises(MissingTenantContextError):
        table.get("acct-1")

    with pytest.raises(MissingTenantContextError):
        table.list()

    with pytest.raises(MissingTenantContextError):
        table.update("acct-1", name="updated")

    with pytest.raises(MissingTenantContextError):
        table.delete("acct-1")


def test_inmemory_table_requires_tenant_on_insert_and_scopes_results() -> None:
    table = InMemoryTable("accounts", "tenant_id")

    with pytest.raises(MissingTenantContextError):
        table.insert("acct-missing", {"id": "acct-missing", "name": "missing-tenant"})

    table.insert("acct-a", {"id": "acct-a", "tenant_id": "tenant-a", "name": "A"})
    table.insert("acct-b", {"id": "acct-b", "tenant_id": "tenant-b", "name": "B"})

    assert table.get("acct-a", tenant_id="tenant-a") == {
        "id": "acct-a",
        "tenant_id": "tenant-a",
        "name": "A",
    }
    assert table.get("acct-a", tenant_id="tenant-b") is None
    assert table.list(tenant_id="tenant-a") == [
        {"id": "acct-a", "tenant_id": "tenant-a", "name": "A"}
    ]


def test_sqlite_table_denies_missing_tenant_and_keeps_scope(tmp_path) -> None:
    db = SQLiteDatabase(f"sqlite:///{tmp_path / 'tenant-boundary.db'}")
    table = db.accounts

    table.insert("acct-a", {"id": "acct-a", "tenant_id": "tenant-a", "name": "A"})
    table.insert("acct-b", {"id": "acct-b", "tenant_id": "tenant-b", "name": "B"})

    with pytest.raises(MissingTenantContextError):
        table.get("acct-a")

    with pytest.raises(MissingTenantContextError):
        table.list()

    assert table.get("acct-a", tenant_id="tenant-a")["tenant_id"] == "tenant-a"
    assert table.get("acct-a", tenant_id="tenant-b") is None
    assert [item["id"] for item in table.list(tenant_id="tenant-a")] == ["acct-a"]

    db.close()
