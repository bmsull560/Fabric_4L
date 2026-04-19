"""Request context for identity and tenant information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class RequestContext:
    """Context for the current request including tenant and user info."""

    tenant_id: UUID | None = None
    user_id: UUID | None = None
    api_key_id: UUID | None = None
    roles: list[str] | None = None
    permissions: list[str] | None = None
    request_id: str | None = None

    def has_permission(self, permission: str) -> bool:
        """Check if context has specific permission."""
        if not self.permissions:
            return False
        return permission in self.permissions

    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        if not self.roles:
            return False
        return "super_admin" in self.roles

    def is_tenant_admin(self) -> bool:
        """Check if user is tenant admin."""
        if not self.roles:
            return False
        return "tenant_admin" in self.roles or "super_admin" in self.roles

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "api_key_id": str(self.api_key_id) if self.api_key_id else None,
            "roles": self.roles,
            "permissions": self.permissions,
            "request_id": self.request_id,
        }
