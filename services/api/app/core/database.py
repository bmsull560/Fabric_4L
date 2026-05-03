"""
Mock database layer for MVP.
Uses in-memory stores with RLS-ready patterns.
In production, replace with PostgreSQL + SQLAlchemy/asyncpg.
"""

from typing import Dict, List, TypeVar, Generic, Optional, Callable
from datetime import datetime, timezone
import threading

T = TypeVar("T")


class MockTable(Generic[T]):
    def __init__(self, name: str, tenant_field: str = "tenant_id"):
        self.name = name
        self.tenant_field = tenant_field
        self._store: Dict[str, T] = {}
        self._lock = threading.Lock()

    def _get_tenant_id(self, obj: T) -> Optional[str]:
        if isinstance(obj, dict):
            return obj.get(self.tenant_field)
        return getattr(obj, self.tenant_field, None)

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

    def list(self, tenant_id: Optional[str] = None, filter_fn: Optional[Callable[[T], bool]] = None) -> List[T]:
        with self._lock:
            items = list(self._store.values())
        if tenant_id:
            items = [i for i in items if self._get_tenant_id(i) == tenant_id]
        if filter_fn:
            items = [i for i in items if filter_fn(i)]
        return items

    def update(self, id: str, tenant_id: Optional[str] = None, **fields) -> Optional[T]:
        with self._lock:
            obj = self._store.get(id)
            if obj is None:
                return None
            if tenant_id and self._get_tenant_id(obj) != tenant_id:
                return None
            if isinstance(obj, dict):
                obj.update(fields)
                obj["updated_at"] = datetime.now(timezone.utc).isoformat()
            else:
                for k, v in fields.items():
                    setattr(obj, k, v)
                if hasattr(obj, "updated_at"):
                    obj.updated_at = datetime.now(timezone.utc).isoformat()
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


class MockDatabase:
    def __init__(self):
        self.accounts = MockTable("accounts", "tenant_id")
        self.stakeholders = MockTable("stakeholders", "tenant_id")
        self.signals = MockTable("signals", "tenant_id")
        self.evidence = MockTable("evidence", "tenant_id")
        self.hypotheses = MockTable("hypotheses", "tenant_id")
        self.drivers = MockTable("drivers", "tenant_id")
        self.levers = MockTable("levers", "tenant_id")
        self.formulas = MockTable("formulas", "tenant_id")
        self.scenarios = MockTable("scenarios", "tenant_id")
        self.roi_calculations = MockTable("roi_calculations", "tenant_id")
        self.business_cases = MockTable("business_cases", "tenant_id")
        self.ground_truth = MockTable("ground_truth", "tenant_id")
        self.agent_runs = MockTable("agent_runs", "tenant_id")
        self.tool_results = MockTable("tool_results", "tenant_id")
        self.review_decisions = MockTable("review_decisions", "tenant_id")
        self.audit_logs = MockTable("audit_logs", "tenant_id")
        self.value_packs = MockTable("value_packs", "tenant_id")
        self.governance_gates = MockTable("governance_gates", "tenant_id")
        self.users = MockTable("users", "tenant_id")
        self.tenants = MockTable("tenants", "id")


db = MockDatabase()
