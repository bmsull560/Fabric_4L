"""Layer 2 startup dependencies module."""

from __future__ import annotations

from layer2_extraction.startup.dependency_verifier import (
    DependencyRule,
)
from layer2_extraction.startup.dependency_verifier import (
    verify_startup_dependencies as _verify_startup_dependencies,
)


def require_tenant_context(ctx: object) -> str:
    """Fail-closed guard: Tenant context required for all data access."""
    tenant_id = getattr(ctx, "tenant_id", None)
    if not tenant_id:
        raise ValueError("Tenant context required")
    return tenant_id


def verify_startup_dependencies(environment: str = "development") -> None:
    """Verify Layer 2 startup dependencies."""
    rules = [
        DependencyRule("redis", required_in_prod=True, remediation="pip install redis"),
    ]
    _verify_startup_dependencies(rules, environment=environment)


# Canonical tenant propagation pattern used in repository calls:
#   tenant_id = require_tenant_context(ctx)
#   repo.method(..., tenant_id=ctx.tenant_id)
