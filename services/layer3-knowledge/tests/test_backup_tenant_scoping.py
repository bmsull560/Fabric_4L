import json

import pytest

from value_fabric.layer3.backup.backup_manager import BackupConfig, BackupManager, BackupType


class _AsyncIter:
    def __init__(self, rows):
        self._rows = iter(rows)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._rows)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class _FakeSession:
    def __init__(self):
        self.queries = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def run(self, query, **params):
        self.queries.append((query, params))
        normalized = " ".join(query.split())
        if "RETURN n, labels(n) as types, id(n) as node_id" in normalized:
            return _AsyncIter(
                [{"n": {"id": "n1", "tenant_id": "tenant-a", "name": "A"}, "types": ["Entity"], "node_id": 1}]
            )
        if "RETURN n.id as source_id, m.id as target_id" in normalized:
            return _AsyncIter(
                [{"source_id": "n1", "target_id": "n2", "rel_type": "LINKS_TO", "rel_props": {"tenant_id": "tenant-a"}}]
            )
        return _AsyncIter([])


class _FakeDriver:
    def __init__(self, session):
        self._session = session

    def session(self):
        return self._session


@pytest.mark.asyncio
async def test_default_full_backup_scopes_nodes_and_edges_to_tenant(tmp_path):
    session = _FakeSession()
    manager = BackupManager(
        BackupConfig(backup_directory=str(tmp_path)),
        neo4j_driver=_FakeDriver(session),
    )

    raw = await manager._generate_backup_data(backup_type=BackupType.FULL, tenant_id="tenant-a")
    payload = json.loads(raw.decode("utf-8"))

    assert payload["metadata"]["entity_count"] == 1
    assert payload["metadata"]["relationship_count"] == 1
    assert "MATCH (n {tenant_id: $tenant_id})" in session.queries[0][0]
    assert "MATCH (n {tenant_id: $tenant_id})-[r]->(m {tenant_id: $tenant_id})" in session.queries[1][0]
    assert session.queries[0][1]["tenant_id"] == "tenant-a"
    assert session.queries[1][1]["tenant_id"] == "tenant-a"


@pytest.mark.asyncio
async def test_non_admin_cannot_trigger_global_export(tmp_path):
    session = _FakeSession()

    async def deny():
        return False

    async def audit(_event):
        return None

    manager = BackupManager(
        BackupConfig(backup_directory=str(tmp_path)),
        neo4j_driver=_FakeDriver(session),
        global_backup_authorizer=deny,
        immutable_audit_logger=audit,
    )

    with pytest.raises(PermissionError, match="not authorized"):
        await manager._generate_backup_data(backup_type=BackupType.FULL, global_export=True)
