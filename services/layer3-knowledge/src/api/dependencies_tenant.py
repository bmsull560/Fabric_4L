"""Deprecated compatibility shim for Layer 3 tenant Neo4j dependencies.

Owner: layer3-knowledge
Deprecated since: 2026-05-18
Hard removal date: 2026-09-30

Canonical module: ``src.api.dependencies_tenant_secured``.
"""

from __future__ import annotations

import logging
import warnings
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from .dependencies_tenant_secured import (
    Neo4jTenantSession,
    create_neo4j_tenant_session,
    get_neo4j_secured,
    get_neo4j_with_tenant,
)

logger = logging.getLogger(__name__)

_REMOVAL_DATE = "2026-09-30"
_WARNING = (
    "src.api.dependencies_tenant is deprecated and will be removed on "
    f"{_REMOVAL_DATE}; use src.api.dependencies_tenant_secured instead."
)


def _warn_deprecated(symbol: str) -> None:
    logger.warning("DEPRECATION: %s (symbol=%s)", _WARNING, symbol)
    warnings.warn(_WARNING, DeprecationWarning, stacklevel=3)


T = TypeVar("T")


def _wrap_async(fn: Callable[..., Awaitable[T]], symbol: str) -> Callable[..., Awaitable[T]]:
    async def _inner(*args: Any, **kwargs: Any) -> T:
        _warn_deprecated(symbol)
        return await fn(*args, **kwargs)

    return _inner


create_neo4j_tenant_session = cast(
    Callable[..., Awaitable[Neo4jTenantSession]],
    _wrap_async(create_neo4j_tenant_session, "create_neo4j_tenant_session"),
)
get_neo4j_with_tenant = cast(
    Callable[..., Awaitable[Neo4jTenantSession]],
    _wrap_async(get_neo4j_with_tenant, "get_neo4j_with_tenant"),
)
get_neo4j_secured = cast(
    Callable[..., Awaitable[Neo4jTenantSession]],
    _wrap_async(get_neo4j_secured, "get_neo4j_secured"),
)

__all__ = [
    "Neo4jTenantSession",
    "create_neo4j_tenant_session",
    "get_neo4j_secured",
    "get_neo4j_with_tenant",
]
