"""Deprecated compatibility shim for Layer 3 Neo4j tenant dependencies.

Canonical module: ``src.api.dependencies_tenant_secured``.
Hard removal date: 2026-09-30.

This module intentionally contains no tenant/session implementation. It exists
only to keep legacy imports working during the deprecation window while route
code migrates to the secured dependency wrapper.
"""

from __future__ import annotations

import logging
import warnings

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
)

__all__ = [
    "Neo4jTenantSession",
    "Neo4jTenantSessionSecured",
    "Neo4jTenantValidatedSession",
    "create_neo4j_tenant_session",
    "get_neo4j_secured",
    "get_neo4j_with_optional_tenant",
    "get_neo4j_with_tenant",
    "get_neo4j_with_validation",
    "get_query_validator",
    "require_tenant_header_for_internal",
]
