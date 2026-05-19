"""Backward-compatibility shim for cypher_scope_guard (GOV-L3-006).

The canonical implementation has moved to:
    value_fabric.layer3.utils.cypher_security

This module re-exports the public API so existing callers do not need
immediate updates. Migrate callers to import directly from
``value_fabric.layer3.utils.cypher_security`` and remove this shim once
all consumers are updated.
"""

from __future__ import annotations

from value_fabric.layer3.utils.cypher_security import (  # noqa: F401
    TENANT_OWNED_LABELS,
    validate_tenant_scoped_cypher,
)

__all__ = ["TENANT_OWNED_LABELS", "validate_tenant_scoped_cypher"]
