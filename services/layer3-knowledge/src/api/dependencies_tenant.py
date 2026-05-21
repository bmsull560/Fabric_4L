<<<<<<< HEAD
"""Deprecated compatibility shim for Layer 3 tenant Neo4j dependencies.

Owner: layer3-knowledge
Deprecated since: 2026-05-19
Hard removal date: 2026-09-30
Reason: tenant-aware Neo4j dependencies moved to ``dependencies_tenant_secured``.
=======
"""Deprecated compatibility shim for Layer 3 Neo4j tenant dependencies.

Canonical module: ``src.api.dependencies_tenant_secured``.
Hard removal date: 2026-09-30.

This module intentionally contains no tenant/session implementation. It exists
only to keep legacy imports working during the deprecation window while route
code migrates to the secured dependency wrapper.
>>>>>>> 315e84c14c9306363c718c22c8cb7a292d514eee
"""

from __future__ import annotations

import logging
import warnings
<<<<<<< HEAD
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from .dependencies_tenant_secured import (
    Neo4jTenantSession,
    create_neo4j_tenant_session as _create_neo4j_tenant_session,
    get_neo4j_secured as _get_neo4j_secured,
    get_neo4j_with_tenant as _get_neo4j_with_tenant,
)

logger = logging.getLogger(__name__)

_REMOVAL_DATE = "2026-09-30"
_WARNING = (
    "src.api.dependencies_tenant is deprecated and will be removed on "
    f"{_REMOVAL_DATE}; use src.api.dependencies_tenant_secured instead."
)

T = TypeVar("T")


def _warn_deprecated(symbol: str) -> None:
    logger.warning("DEPRECATION: %s (symbol=%s)", _WARNING, symbol)
    warnings.warn(_WARNING, DeprecationWarning, stacklevel=3)


def _wrap_async(fn: Callable[..., Awaitable[T]], symbol: str) -> Callable[..., Awaitable[T]]:
    async def _inner(*args: Any, **kwargs: Any) -> T:
        _warn_deprecated(symbol)
        return await fn(*args, **kwargs)

    return _inner


create_neo4j_tenant_session = cast(
    Callable[..., Awaitable[Neo4jTenantSession]],
    _wrap_async(_create_neo4j_tenant_session, "create_neo4j_tenant_session"),
)
get_neo4j_with_tenant = cast(
    Callable[..., Awaitable[Neo4jTenantSession]],
    _wrap_async(_get_neo4j_with_tenant, "get_neo4j_with_tenant"),
)
get_neo4j_secured = cast(
    Callable[..., Awaitable[Neo4jTenantSession]],
    _wrap_async(_get_neo4j_secured, "get_neo4j_secured"),
=======

_REMOVAL_DATE = "2026-09-30"
_CANONICAL_MODULE = "src.api.dependencies_tenant_secured"
_MESSAGE = (
    "src.api.dependencies_tenant is deprecated and will be removed on "
    f"{_REMOVAL_DATE}; import {_CANONICAL_MODULE} instead."
)

logger = logging.getLogger(__name__)
logger.warning(_MESSAGE)
warnings.warn(_MESSAGE, DeprecationWarning, stacklevel=2)

from .dependencies_tenant_secured import (  # noqa: E402,F401
    Neo4jTenantSession,
    Neo4jTenantSessionSecured,
    Neo4jTenantValidatedSession,
    create_neo4j_tenant_session,
    get_neo4j_secured,
    get_neo4j_with_optional_tenant,
    get_neo4j_with_tenant,
    get_neo4j_with_validation,
    get_query_validator,
    require_tenant_header_for_internal,
>>>>>>> 315e84c14c9306363c718c22c8cb7a292d514eee
)

__all__ = [
    "Neo4jTenantSession",
<<<<<<< HEAD
    "create_neo4j_tenant_session",
    "get_neo4j_secured",
    "get_neo4j_with_tenant",
=======
    "Neo4jTenantSessionSecured",
    "Neo4jTenantValidatedSession",
    "create_neo4j_tenant_session",
    "get_neo4j_secured",
    "get_neo4j_with_optional_tenant",
    "get_neo4j_with_tenant",
    "get_neo4j_with_validation",
    "get_query_validator",
    "require_tenant_header_for_internal",
>>>>>>> 315e84c14c9306363c718c22c8cb7a292d514eee
]
