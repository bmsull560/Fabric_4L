"""Shared identity module for authentication, authorization, and tenant management."""

from .context import RequestContext
from .dependencies import require_tenant_admin, require_super_admin
from .feature_flags import init_feature_flags, is_enabled, register_feature_flag_lookup
from .hashing import extract_key_prefix, generate_api_key, hash_api_key
from .jwt import encode_jwt, decode_jwt
from .middleware import GovernanceMiddleware
from .models import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyModel,
    TenantCreateRequest,
    TenantModel,
    TenantStatus,
    TenantUpdateRequest,
    UserInviteRequest,
    UserModel,
    UserStatus,
    UserUpdateRequest,
)
from .oidc import OIDCClient, map_role_from_claims
from .oidc_config import OIDCProviderConfig
from .permissions import Role, ROLE_PERMISSIONS
from .rate_limiter import RedisRateLimiter
from .vault_check import check_vault_health, resolve_vault_secret

__all__ = [
    # Context
    "RequestContext",
    # Dependencies
    "require_tenant_admin",
    "require_super_admin",
    # Feature flags
    "init_feature_flags",
    "is_enabled",
    "register_feature_flag_lookup",
    # Hashing
    "extract_key_prefix",
    "generate_api_key",
    "hash_api_key",
    # JWT
    "encode_jwt",
    "decode_jwt",
    # Middleware
    "GovernanceMiddleware",
    # Models
    "APIKeyCreateRequest",
    "APIKeyCreateResponse",
    "APIKeyModel",
    "TenantCreateRequest",
    "TenantModel",
    "TenantStatus",
    "TenantUpdateRequest",
    "UserInviteRequest",
    "UserModel",
    "UserStatus",
    "UserUpdateRequest",
    # OIDC
    "OIDCClient",
    "map_role_from_claims",
    "OIDCProviderConfig",
    # Permissions
    "Role",
    "ROLE_PERMISSIONS",
    # Rate limiting
    "RedisRateLimiter",
    # Vault
    "check_vault_health",
    "resolve_vault_secret",
]
