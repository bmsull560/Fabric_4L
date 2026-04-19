"""Permission definitions and role mappings."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """User roles in the system."""

    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"
    READONLY = "readonly"


class Permission(str, Enum):
    """System permissions."""

    # Tenant permissions
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    
    # User permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # API key permissions
    API_KEY_CREATE = "api_key:create"
    API_KEY_READ = "api_key:read"
    API_KEY_REVOKE = "api_key:revoke"
    
    # Workflow permissions
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    
    # Formula permissions
    FORMULA_READ = "formula:read"
    FORMULA_WRITE = "formula:write"
    
    # Extraction permissions
    EXTRACTION_READ = "extraction:read"
    EXTRACTION_WRITE = "extraction:write"
    
    # Ingestion permissions
    INGESTION_READ = "ingestion:read"
    INGESTION_WRITE = "ingestion:write"
    
    # Knowledge permissions
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    
    # Model registry permissions
    READ_MODELS = "models:read"
    WRITE_MODELS = "models:write"
    ADMIN_MODELS = "models:admin"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[str, list[str]] = {
    Role.SUPER_ADMIN: [
        "*",  # All permissions
    ],
    Role.TENANT_ADMIN: [
        "tenant:read",
        "tenant:update",
        "user:create",
        "user:read",
        "user:update",
        "user:delete",
        "api_key:create",
        "api_key:read",
        "api_key:revoke",
        "workflow:create",
        "workflow:read",
        "workflow:update",
        "workflow:delete",
        "formula:read",
        "formula:write",
        "extraction:read",
        "extraction:write",
        "ingestion:read",
        "ingestion:write",
        "knowledge:read",
        "knowledge:write",
    ],
    Role.USER: [
        "tenant:read",
        "user:read",
        "api_key:create",
        "api_key:read",
        "api_key:revoke",
        "workflow:create",
        "workflow:read",
        "workflow:update",
        "formula:read",
        "extraction:read",
        "extraction:write",
        "ingestion:read",
        "ingestion:write",
        "knowledge:read",
    ],
    Role.READONLY: [
        "tenant:read",
        "user:read",
        "formula:read",
        "extraction:read",
        "ingestion:read",
        "knowledge:read",
    ],
}


def get_permissions_for_role(role: str) -> list[str]:
    """Get permissions for a role."""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    perms = get_permissions_for_role(role)
    if "*" in perms:
        return True
    return permission in perms
