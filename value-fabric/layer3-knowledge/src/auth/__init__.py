"""Authentication package initialization."""

from .api_keys import (
    Permission,
    Role,
    APIKey,
    APIKeyCreateRequest,
    APIKeyResponse,
    APIKeyCreateResponse,
    APIKeyUpdateRequest,
    AuthenticationResult,
    APIKeyManager,
    AuthorizationChecker,
    get_api_key_manager,
    get_authorization_checker,
    initialize_authentication,
    ROLE_PERMISSIONS,
)

__all__ = [
    "Permission",
    "Role",
    "APIKey",
    "APIKeyCreateRequest",
    "APIKeyResponse",
    "APIKeyCreateResponse",
    "APIKeyUpdateRequest",
    "AuthenticationResult",
    "APIKeyManager",
    "AuthorizationChecker",
    "get_api_key_manager",
    "get_authorization_checker",
    "initialize_authentication",
    "ROLE_PERMISSIONS",
]
