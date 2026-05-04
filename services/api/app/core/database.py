"""
Persistence layer for the standalone API.

The in-memory implementation is retained for local demos and tests. When
``mock_persistence`` is disabled, the API now requires a durable database URL and
uses a SQLite-backed table facade that preserves the existing tenant-aware table
contract used by the standalone API routers.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar
from urllib.parse import urlparse

from pydantic import BaseModel

from app.core.config import get_settings
from app.models.schemas import (
    Account,
    AgentRun,
    AuditLogEvent,
    BusinessCase,
    Evidence,
    Formula,
    GovernanceGate,
    GroundTruthObject,
    ROICalculation,
    ReviewDecision,
    Scenario,
    Signal,
    Stakeholder,
    Tenant,
    ToolResult,
    User,
    ValueDriver,
    ValueHypothesis,
    ValuePack,
)

T = TypeVar("T")


class ProductionPersistenceNotConfigured(RuntimeError):
    """Raised when the API is asked to run without a durable persistence backend."""


class UnsupportedDatabaseURL(ProductionPersistenceNotConfigured):
    """Raised when ``database_url`` does not identify a supported durable backend."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _to_payload(obj: Any) -> dict[str, Any]:
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    raise TypeError(f"Unsupported persistence object type: {type(obj).__name__}")


def _tenant_from_obj(obj: Any, tenant_field: str) -> Optional[str]:
    if isinstance(obj, dict):
        value = obj.get(tenant_field)
    else:
        value = getattr(obj, tenant_field, None)
    return str(value) if value is not None else None


class InMemoryTable(Generic[T]):
    """Thread-safe, tenant-aware table used for local development and tests only."""

    def __init__(self, name: str, tenant_field: str = "tenant_id"):
        self.name = name
        self.tenant_field = tenant_field
        self._store: Dict[str, T] = {}
        self._lock = threading.Lock()

    def _get_tenant_id(self, obj: T) -> Optional[str]:
        return _tenant_from_obj(obj, self.tenant_field)

    def insert(self, id: str, obj: T) -> T:
        with self._lock:
            self._store[id] = obj
        return obj

    def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[T]:
        with self._lock:
            obj = self._store.get(id)
            if obj is None:
                return None
            if tenant_id and self._get_tenant_id(obj) != tenant_id:
                return None
            return obj

    def list(
        self,
        tenant_id: Optional[str] = None,
        filter_fn: Optional[Callable[[T], bool]] = None,
    ) -> List[T]:
        with self._lock:
            items = list(self._store.values())
        if tenant_id:
            items = [i for i in items if self._get_tenant_id(i) == tenant_id]
        if filter_fn:
            items = [i for i in items if filter_fn(i)]
        return items

    def update(self, id: str, tenant_id: Optional[str] = None, **fields: Any) -> Optional[T]:
        with self._lock:
            obj = self._store.get(id)
            if obj is None:
                return None
            if tenant_id and self._get_tenant_id(obj) != tenant_id:
                return None
            if isinstance(obj, dict):
                obj.update(fields)
                obj["updated_at"] = _now_iso()
            else:
                for key, value in fields.items():
                    setattr(obj, key, value)
                if hasattr(obj, "updated_at"):
                    obj.updated_at = _now_iso()
            return obj

    def delete(self, id: str, tenant_id: Optional[str] = None) -> bool:
        with self._lock:
            obj = self._store.get(id)
            if obj is None:
                return False
            if tenant_id and self._get_tenant_id(obj) != tenant_id:
                return False
            del self._store[id]
            return True


class SQLiteTable(Generic[T]):
    """Durable JSON-record table preserving the current standalone API table API.

    The table stores each Pydantic object as a JSON payload and keeps a separate
    tenant column for fail-closed tenant-scoped reads. This intentionally avoids
    importing lower-layer implementations or duplicating business logic across
    Fabric_4L layers while making the non-mock standalone API path executable.
    """

    def __init__(
        self,
        name: str,
        connection: sqlite3.Connection,
        lock: threading.RLock,
        model_cls: type[T] | None = None,
        tenant_field: str = "tenant_id",
    ):
        self.name = name
        self.tenant_field = tenant_field
        self._connection = connection
        self._lock = lock
        self._model_cls = model_cls

    def _deserialize(self, payload: str) -> T:
        data = json.loads(payload)
        if self._model_cls and issubclass(self._model_cls, BaseModel):
            return self._model_cls.model_validate(data)  # type: ignore[return-value]
        return data  # type: ignore[return-value]

    def _get_tenant_id(self, obj: T) -> Optional[str]:
        return _tenant_from_obj(obj, self.tenant_field)

    def insert(self, id: str, obj: T) -> T:
        payload = _to_payload(obj)
        tenant_id = _tenant_from_obj(payload, self.tenant_field)
        now = _now_iso()
        payload_json = json.dumps(payload, default=_json_default, sort_keys=True)
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO fabric_api_records(table_name, id, tenant_id, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(table_name, id) DO UPDATE SET
                    tenant_id = excluded.tenant_id,
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (self.name, id, tenant_id, payload_json, now, now),
            )
        return obj

    def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[T]:
        query = "SELECT payload FROM fabric_api_records WHERE table_name = ? AND id = ?"
        params: list[Any] = [self.name, id]
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        with self._lock:
            row = self._connection.execute(query, params).fetchone()
        if row is None:
            return None
        return self._deserialize(row[0])

    def list(
        self,
        tenant_id: Optional[str] = None,
        filter_fn: Optional[Callable[[T], bool]] = None,
    ) -> List[T]:
        query = "SELECT payload FROM fabric_api_records WHERE table_name = ?"
        params: list[Any] = [self.name]
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        query += " ORDER BY id"
        with self._lock:
            rows = self._connection.execute(query, params).fetchall()
        items = [self._deserialize(row[0]) for row in rows]
        if filter_fn:
            items = [item for item in items if filter_fn(item)]
        return items

    def update(self, id: str, tenant_id: Optional[str] = None, **fields: Any) -> Optional[T]:
        obj = self.get(id, tenant_id=tenant_id)
        if obj is None:
            return None
        if isinstance(obj, dict):
            obj.update(fields)
            obj["updated_at"] = _now_iso()
        else:
            for key, value in fields.items():
                setattr(obj, key, value)
            if hasattr(obj, "updated_at"):
                setattr(obj, "updated_at", _now_iso())
        self.insert(id, obj)
        return obj

    def delete(self, id: str, tenant_id: Optional[str] = None) -> bool:
        obj = self.get(id, tenant_id=tenant_id)
        if obj is None:
            return False
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM fabric_api_records WHERE table_name = ? AND id = ?",
                (self.name, id),
            )
        return cursor.rowcount > 0


class InMemoryDatabase:
    """Development-only database facade matching the current repository API."""

    def __init__(self):
        self.accounts = InMemoryTable("accounts", "tenant_id")
        self.stakeholders = InMemoryTable("stakeholders", "tenant_id")
        self.signals = InMemoryTable("signals", "tenant_id")
        self.evidence = InMemoryTable("evidence", "tenant_id")
        self.hypotheses = InMemoryTable("hypotheses", "tenant_id")
        self.drivers = InMemoryTable("drivers", "tenant_id")
        self.levers = InMemoryTable("levers", "tenant_id")
        self.formulas = InMemoryTable("formulas", "tenant_id")
        self.scenarios = InMemoryTable("scenarios", "tenant_id")
        self.roi_calculations = InMemoryTable("roi_calculations", "tenant_id")
        self.business_cases = InMemoryTable("business_cases", "tenant_id")
        self.ground_truth = InMemoryTable("ground_truth", "tenant_id")
        self.agent_runs = InMemoryTable("agent_runs", "tenant_id")
        self.tool_results = InMemoryTable("tool_results", "tenant_id")
        self.review_decisions = InMemoryTable("review_decisions", "tenant_id")
        self.audit_logs = InMemoryTable("audit_logs", "tenant_id")
        self.value_packs = InMemoryTable("value_packs", "tenant_id")
        self.governance_gates = InMemoryTable("governance_gates", "tenant_id")
        self.users = InMemoryTable("users", "tenant_id")
        self.tenants = InMemoryTable("tenants", "id")


class SQLiteDatabase:
    """SQLite-backed durable database facade for the standalone API."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._connection = sqlite3.connect(
            _sqlite_path_from_url(database_url),
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._initialize_schema()

        self.accounts = self._table("accounts", Account, "tenant_id")
        self.stakeholders = self._table("stakeholders", Stakeholder, "tenant_id")
        self.signals = self._table("signals", Signal, "tenant_id")
        self.evidence = self._table("evidence", Evidence, "tenant_id")
        self.hypotheses = self._table("hypotheses", ValueHypothesis, "tenant_id")
        self.drivers = self._table("drivers", ValueDriver, "tenant_id")
        self.levers = self._table("levers", None, "tenant_id")
        self.formulas = self._table("formulas", Formula, "tenant_id")
        self.scenarios = self._table("scenarios", Scenario, "tenant_id")
        self.roi_calculations = self._table("roi_calculations", ROICalculation, "tenant_id")
        self.business_cases = self._table("business_cases", BusinessCase, "tenant_id")
        self.ground_truth = self._table("ground_truth", GroundTruthObject, "tenant_id")
        self.agent_runs = self._table("agent_runs", AgentRun, "tenant_id")
        self.tool_results = self._table("tool_results", ToolResult, "tenant_id")
        self.review_decisions = self._table("review_decisions", ReviewDecision, "tenant_id")
        self.audit_logs = self._table("audit_logs", AuditLogEvent, "tenant_id")
        self.value_packs = self._table("value_packs", ValuePack, "tenant_id")
        self.governance_gates = self._table("governance_gates", GovernanceGate, "tenant_id")
        self.users = self._table("users", User, "tenant_id")
        self.tenants = self._table("tenants", Tenant, "id")

    def _initialize_schema(self) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS fabric_api_records (
                    table_name TEXT NOT NULL,
                    id TEXT NOT NULL,
                    tenant_id TEXT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (table_name, id)
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_fabric_api_records_tenant
                ON fabric_api_records(table_name, tenant_id)
                """
            )

    def _table(
        self,
        name: str,
        model_cls: type[T] | None,
        tenant_field: str,
    ) -> SQLiteTable[T]:
        return SQLiteTable(name, self._connection, self._lock, model_cls, tenant_field)

    def close(self) -> None:
        with self._lock:
            self._connection.close()


def _sqlite_path_from_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise UnsupportedDatabaseURL(
            "services/api durable persistence currently supports sqlite database_url values. "
            "Use a URL such as sqlite:////var/lib/fabric_4l/api.db for controlled pilot deployments."
        )
    if parsed.path in {"", "/"}:
        raise UnsupportedDatabaseURL("sqlite database_url must include a database file path")
    if parsed.path == "/:memory:":
        return ":memory:"
    db_path = Path(parsed.path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)


# Backward-compatible aliases for existing tests and imports. New code should use
# the explicit InMemory* names to avoid implying production persistence.
MockTable = InMemoryTable
MockDatabase = InMemoryDatabase


def create_database() -> InMemoryDatabase | SQLiteDatabase:
    settings = get_settings()
    if settings.mock_persistence:
        if settings.is_production_like:
            raise ProductionPersistenceNotConfigured(
                "In-memory persistence is disabled in production-like environments."
            )
        return InMemoryDatabase()
    if not settings.database_url:
        raise ProductionPersistenceNotConfigured(
            "database_url must be configured when mock_persistence is false."
        )
    return SQLiteDatabase(settings.database_url)


db = create_database()
