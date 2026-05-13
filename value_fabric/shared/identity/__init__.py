"""Compatibility exports for shared identity helpers."""

from .context import *  # noqa: F401,F403
from .permissions import Permission, Role, ROLE_PERMISSIONS, normalize_role_claims
from .dependencies import (  # noqa: F401
    get_current_context,
    get_optional_context,
    require_authenticated,
    require_tenant,
    require_tenant_context,
    require_role,
    require_permission,
    require_any_permission,
    require_all_permissions,
    require_action,
    require_admin,
    require_privileged_access,
    require_super_admin,
    require_tenant_admin,
    require_content_admin,
    require_analyst,
    validate_jwt_config,
)
from .policy_registry import ACTION_POLICIES, authorize_action, get_action_policy, get_tool_action, list_action_policies

__all__ = [
    "Permission",
    "Role",
    "ROLE_PERMISSIONS",
    "normalize_role_claims",
    "get_current_context",
    "get_optional_context",
    "require_authenticated",
    "require_tenant",
    "require_tenant_context",
    "require_role",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "require_action",
    "require_admin",
    "require_privileged_access",
    "require_super_admin",
    "require_tenant_admin",
    "require_content_admin",
    "require_analyst",
    "validate_jwt_config",
    "ACTION_POLICIES",
    "authorize_action",
    "get_action_policy",
    "get_tool_action",
    "list_action_policies",
]
