"""Shared identity and governance library for Value Fabric.

This package is imported by all layers (L1–L4) and provides:
- Canonical Role/Permission enums
- Pydantic models for Tenant, User, APIKey
- Verified JWT encode/decode
- Unified RequestContext propagated via ContextVar
- GovernanceMiddleware (single replacement for L3 AuthMiddleware + L4 TenantMiddleware)
- FastAPI dependency helpers
"""

from .context import RequestContext, get_request_context, set_request_context, require_context
from .hashing import generate_api_key, hash_api_key, verify_api_key, extract_key_prefix
from .isolation import TenantScopedCypher, TenantScopedMixin, tenant_cache_key
from .jwt import TokenClaims, decode_jwt, encode_jwt
from .dependencies import (
    get_current_context,
    require_authenticated,
    require_role,
    require_permission,
    require_any_permission,
    require_all_permissions,
    require_tenant,
    get_optional_context,
)
from .middleware import GovernanceMiddleware
from .models import APIKeyModel, TenantModel, UserModel
from .permissions import Permission, Role, ROLE_PERMISSIONS

__all__ = [
    # Context
    "RequestContext",
    "get_request_context",
    "set_request_context",
    "require_context",
    # Hashing
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "extract_key_prefix",
    # Isolation
    "TenantScopedCypher",
    "TenantScopedMixin",
    "tenant_cache_key",
    # JWT
    "TokenClaims",
    "decode_jwt",
    "encode_jwt",
    # Dependencies
    "get_current_context",
    "require_authenticated",
    "require_role",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "require_tenant",
    "get_optional_context",
    # Middleware
    "GovernanceMiddleware",
    # Models
    "APIKeyModel",
    "TenantModel",
    "UserModel",
    # Permissions
    "Permission",
    "Role",
    "ROLE_PERMISSIONS",
]
