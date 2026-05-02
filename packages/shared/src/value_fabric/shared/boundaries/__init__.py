"""Boundary enforcement modules for cross-cutting security concerns.

This package provides runtime guards and enforcement mechanisms for
tenant isolation, authentication boundaries, and security contracts.
"""

# Delay imports to avoid FastAPI/Request circular import issues
def __getattr__(name):
    from .tenant_boundary import (
        TenantBoundaryError,
        get_tenant_context,
        require_tenant_context,
        require_tenant_from_request,
        get_tenant_id,
        require_tenant_id,
    )
    if name == "TenantBoundaryError":
        return TenantBoundaryError
    if name == "get_tenant_context":
        return get_tenant_context
    if name == "require_tenant_context":
        return require_tenant_context
    if name == "require_tenant_from_request":
        return require_tenant_from_request
    if name == "get_tenant_id":
        return get_tenant_id
    if name == "require_tenant_id":
        return require_tenant_id
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "TenantBoundaryError",
    "get_tenant_context",
    "require_tenant_context",
    "require_tenant_from_request",
    "get_tenant_id",
    "require_tenant_id",
]
