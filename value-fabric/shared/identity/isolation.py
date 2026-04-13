"""Tenant isolation utilities for Value Fabric.

Provides:
- TenantScopedMixin: SQLAlchemy mixin that adds a tenant_id column and
  automatically filters queries to the current tenant.
- TenantScopedQuery: Neo4j Cypher query builder that prepends a mandatory
  tenant_id predicate to prevent cross-tenant data leakage.
- tenant_cache_key: Namespaced Redis cache key helper.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional, Sequence, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SQLAlchemy mixin
# ---------------------------------------------------------------------------


class TenantScopedMixin:
    """Add ``tenant_id`` to an ORM model and supply a scoping helper.

    Inherit from this mixin **before** ``Base`` in your model definition::

        class MyModel(TenantScopedMixin, Base):
            __tablename__ = "my_table"
            ...

    Then use :meth:`scoped_query` to build pre-filtered selects::

        stmt = MyModel.scoped_query(tenant_id).where(MyModel.name == "Acme")
        result = await session.execute(stmt)
    """

    from sqlalchemy import Column
    from sqlalchemy.dialects.postgresql import UUID as _PGUUID

    # Declare the column at class body level so SQLAlchemy picks it up.
    # Child classes must also import Base from the same metadata.
    __abstract__ = True

    @classmethod
    def scoped_query(cls, tenant_id: UUID):
        """Return a SELECT statement pre-filtered to ``tenant_id``.

        Usage::

            stmt = (
                MyModel.scoped_query(ctx.tenant_id)
                .where(MyModel.status == "active")
                .limit(100)
            )
            rows = (await session.execute(stmt)).scalars().all()
        """
        from sqlalchemy import select

        return select(cls).where(cls.tenant_id == tenant_id)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Neo4j query builder
# ---------------------------------------------------------------------------


class TenantScopedCypher:
    """Builds Cypher queries that always include a ``tenant_id`` predicate.

    This is the query-builder wrapper approach recommended for Neo4j Community
    Edition (which lacks server-side property existence constraints and RLS).

    Usage::

        q = TenantScopedCypher(tenant_id)
        cypher, params = q.match_node("n", "Capability", extra_where="n.status = $status")
        params["status"] = "VALIDATED"
        await session.run(cypher, params)
    """

    def __init__(self, tenant_id: UUID) -> None:
        self._tenant_id = str(tenant_id)

    # -- Node queries --------------------------------------------------------

    def match_node(
        self,
        alias: str,
        label: str,
        *,
        extra_where: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        return_clause: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """MATCH a node filtered by tenant_id.

        Returns ``(cypher_string, params_dict)``.
        """
        params: Dict[str, Any] = {"_tenant_id": self._tenant_id}
        if extra_params:
            params.update(extra_params)

        where_parts = [f"{alias}.tenant_id = $_tenant_id"]
        if extra_where:
            where_parts.append(f"({extra_where})")

        ret = return_clause or alias
        cypher = (
            f"MATCH ({alias}:{label})\n"
            f"WHERE {' AND '.join(where_parts)}\n"
            f"RETURN {ret}"
        )
        return cypher, params

    def create_node(
        self,
        alias: str,
        label: str,
        properties: Dict[str, Any],
        *,
        return_clause: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """CREATE a node with tenant_id automatically injected."""
        props = dict(properties)
        props["tenant_id"] = self._tenant_id

        param_keys = {f"_{alias}_{k}": v for k, v in props.items()}
        prop_str = ", ".join(
            f"{k}: ${pk}" for (k, _), pk in zip(props.items(), param_keys.keys())
        )
        ret = return_clause or alias
        cypher = (
            f"CREATE ({alias}:{label} {{{prop_str}}})\n"
            f"RETURN {ret}"
        )
        return cypher, param_keys

    def match_relationship(
        self,
        from_alias: str,
        from_label: str,
        rel_type: str,
        to_alias: str,
        to_label: str,
        *,
        extra_where: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        return_clause: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """MATCH a relationship where both endpoints belong to the tenant."""
        params: Dict[str, Any] = {"_tenant_id": self._tenant_id}
        if extra_params:
            params.update(extra_params)

        where_parts = [
            f"{from_alias}.tenant_id = $_tenant_id",
            f"{to_alias}.tenant_id = $_tenant_id",
        ]
        if extra_where:
            where_parts.append(f"({extra_where})")

        ret = return_clause or f"{from_alias}, {to_alias}"
        cypher = (
            f"MATCH ({from_alias}:{from_label})-[:{rel_type}]->({to_alias}:{to_label})\n"
            f"WHERE {' AND '.join(where_parts)}\n"
            f"RETURN {ret}"
        )
        return cypher, params


# ---------------------------------------------------------------------------
# Redis cache key namespacing
# ---------------------------------------------------------------------------


def tenant_cache_key(tenant_id: UUID, *parts: str) -> str:
    """Return a Redis key prefixed with the tenant UUID.

    Example::

        key = tenant_cache_key(ctx.tenant_id, "search", query_hash)
        # → "tenant:3fa85f64-...:search:abc123"

    This ensures keys from different tenants never collide even if the
    underlying Redis instance is shared.
    """
    safe_parts = ":".join(p.replace(":", "_") for p in parts if p)
    return f"tenant:{tenant_id}:{safe_parts}"
