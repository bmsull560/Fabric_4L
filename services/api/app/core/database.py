"""
Development persistence layer for the standalone API.

The in-memory implementation exists only for local demos and tests. Production-like
runtime configuration is validated in app.core.config and will fail startup before
this module can silently provide non-durable storage.
"""

from datetime import datetime, timezone
import threading
from typing import Callable, Dict, Generic, List, Optional, TypeVar

from app.core.config import get_settings

T = TypeVar("T")


class ProductionPersistenceNotConfigured(RuntimeError):
    """Raised when the API is asked to run without a production persistence backend."""


class InMemoryTable(Generic[T]):
    """Thread-safe, tenant-aware table used for local development and tests only."""

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
                for key, value in fields.items():
                    setattr(obj, key, value)
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


# Backward-compatible aliases for existing tests and imports. New code should use
# the explicit InMemory* names to avoid implying production persistence.
MockTable = InMemoryTable
MockDatabase = InMemoryDatabase


def create_database() -> InMemoryDatabase:
    settings = get_settings()
    if not settings.mock_persistence:
        raise ProductionPersistenceNotConfigured(
            "No production database repository is configured for services/api. "
            "Set mock_persistence=true only for local/test use, or wire a durable "
            "database implementation before enabling this service."
        )
    if settings.is_production_like:
        raise ProductionPersistenceNotConfigured(
            "In-memory persistence is disabled in production-like environments."
        )
    return InMemoryDatabase()


db = create_database()
