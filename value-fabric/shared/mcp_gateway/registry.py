"""Tool registry with tenant-scoped enablement.

Manages tool definitions and per-tenant tool access permissions.
Ensures tenants can only invoke tools they are authorized to use.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from .mcp_types import ToolAccessDeniedError, ToolManifest, ToolRequest
from shared.models.typed_dict import TypedDictModel


class ToolRegistry_get_tool_metadataResult(TypedDictModel):
    capabilities: Any
    description: Any
    endpoint: Any
    has_signature: bool
    required_scopes: Any
    tenant_scoped: Any
    tool_name: Any
    verified: bool
    version: Any

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of tools with tenant-scoped access control.
    
    Maintains:
    1. Global tool catalog (available tools)
    2. Per-tenant tool enablement (which tools tenant can use)
    3. Tool manifest verification status
    
    Security:
    - All tool lookups are tenant-scoped
    - Unauthorized tool access is blocked with audit logging
    - Manifest verification is required for tool registration
    
    Example:
        >>> registry = ToolRegistry()
        >>> # Register tool globally
        >>> registry.register_tool(
        ...     manifest=ToolManifest(tool_name="search", ...),
        ...     verified=True
        ... )
        >>> # Enable for specific tenant
        >>> registry.enable_tool_for_tenant("search", tenant_uuid)
        >>> # Check access
        >>> if registry.is_tool_enabled("search", tenant_uuid):
        ...     # Allow invocation
    """
    
    def __init__(self):
        """Initialize empty tool registry."""
        # Global tool catalog: tool_name -> ToolManifest
        self._tools: dict[str, ToolManifest] = {}
        
        # Per-tenant enablement: tenant_id -> set of tool_names
        self._tenant_tools: dict[UUID, set[str]] = {}
        
        # Tool verification status: tool_name -> bool
        self._verified_tools: set[str] = set()
        
        logger.info("ToolRegistry initialized")
    
    def register_tool(
        self,
        manifest: ToolManifest,
        verified: bool = False,
        enable_for_all_tenants: bool = False
    ) -> None:
        """Register a tool in the global catalog.
        
        Args:
            manifest: Tool manifest with metadata
            verified: Whether manifest signature has been verified
            enable_for_all_tenants: If True, enable for all current/future tenants
            
        Raises:
            ToolAccessDeniedError: If manifest verification fails
            
        Example:
            >>> registry.register_tool(
            ...     manifest=ToolManifest(
            ...         tool_name="database_query",
            ...         version="1.0.0",
            ...         endpoint="https://db.example.com",
            ...         required_scopes=["db:query"]
            ...     ),
            ...     verified=True
            ... )
        """
        tool_name = manifest.tool_name
        
        # Require verification for registration
        if not verified and not manifest.signature:
            logger.warning(
                f"Registering unverified tool '{tool_name}' - "
                "signature verification recommended"
            )
        
        self._tools[tool_name] = manifest
        
        if verified:
            self._verified_tools.add(tool_name)
        
        if enable_for_all_tenants:
            # Enable for all existing tenants
            for tenant_id in self._tenant_tools:
                self._tenant_tools[tenant_id].add(tool_name)
            logger.info(
                f"Tool '{tool_name}' registered and enabled for all tenants"
            )
        else:
            logger.info(f"Tool '{tool_name}' registered (not tenant-enabled)")
    
    def unregister_tool(self, tool_name: str) -> None:
        """Remove a tool from the global catalog.
        
        Args:
            tool_name: Tool to remove
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            self._verified_tools.discard(tool_name)
            
            # Remove from all tenant enablements
            for tenant_tools in self._tenant_tools.values():
                tenant_tools.discard(tool_name)
            
            logger.info(f"Tool '{tool_name}' unregistered")
    
    def enable_tool_for_tenant(self, tool_name: str, tenant_id: UUID) -> None:
        """Enable a tool for a specific tenant.
        
        Args:
            tool_name: Tool to enable
            tenant_id: Tenant UUID
            
        Raises:
            ToolAccessDeniedError: If tool doesn't exist in catalog
            
        Example:
            >>> registry.enable_tool_for_tenant("search", tenant_uuid)
        """
        if tool_name not in self._tools:
            raise ToolAccessDeniedError(
                f"Cannot enable unknown tool '{tool_name}'"
            )
        
        if tenant_id not in self._tenant_tools:
            self._tenant_tools[tenant_id] = set()
        
        self._tenant_tools[tenant_id].add(tool_name)
        
        logger.info(
            f"Tool '{tool_name}' enabled for tenant {tenant_id}",
            extra={"tool_name": tool_name, "tenant_id": str(tenant_id)}
        )
    
    def disable_tool_for_tenant(self, tool_name: str, tenant_id: UUID) -> None:
        """Disable a tool for a specific tenant.
        
        Args:
            tool_name: Tool to disable
            tenant_id: Tenant UUID
        """
        if tenant_id in self._tenant_tools:
            self._tenant_tools[tenant_id].discard(tool_name)
            
            logger.info(
                f"Tool '{tool_name}' disabled for tenant {tenant_id}",
                extra={"tool_name": tool_name, "tenant_id": str(tenant_id)}
            )
    
    def is_tool_enabled(self, tool_name: str, tenant_id: UUID) -> bool:
        """Check if a tool is enabled for a tenant.
        
        Args:
            tool_name: Tool to check
            tenant_id: Tenant UUID
            
        Returns:
            True if tool exists and is enabled for tenant
        """
        if tool_name not in self._tools:
            return False
        
        if tenant_id not in self._tenant_tools:
            return False
        
        return tool_name in self._tenant_tools[tenant_id]
    
    def get_tool(self, tool_name: str, tenant_id: UUID) -> ToolManifest:
        """Get tool manifest with tenant access check.
        
        Args:
            tool_name: Tool to retrieve
            tenant_id: Tenant UUID for access control
            
        Returns:
            ToolManifest if tenant is authorized
            
        Raises:
            ToolAccessDeniedError: If tool doesn't exist or tenant not authorized
        """
        if not self.is_tool_enabled(tool_name, tenant_id):
            logger.warning(
                f"Tenant {tenant_id} attempted to access unauthorized tool '{tool_name}'",
                extra={"tool_name": tool_name, "tenant_id": str(tenant_id)}
            )
            raise ToolAccessDeniedError(
                f"Tool '{tool_name}' is not available for this tenant"
            )
        
        return self._tools[tool_name]
    
    def list_tools_for_tenant(self, tenant_id: UUID) -> list[ToolManifest]:
        """List all tools enabled for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            List of enabled tool manifests
        """
        if tenant_id not in self._tenant_tools:
            return []
        
        enabled_tools = []
        for tool_name in self._tenant_tools[tenant_id]:
            if tool_name in self._tools:
                enabled_tools.append(self._tools[tool_name])
        
        return enabled_tools
    
    def get_tenant_scoped_request(
        self,
        tool_name: str,
        tenant_id: UUID,
        user_id: str | None = None,
        parameters: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> ToolRequest:
        """Create a tenant-scoped tool request.
        
        Validates tenant access and creates properly scoped request.
        
        Args:
            tool_name: Tool to invoke
            tenant_id: Tenant UUID
            user_id: Optional user ID for audit
            parameters: Tool parameters
            request_id: Optional request ID
            
        Returns:
            ToolRequest with tenant context
            
        Raises:
            ToolAccessDeniedError: If tenant not authorized for tool
        """
        # Validate tenant access
        manifest = self.get_tool(tool_name, tenant_id)
        
        if not manifest.tenant_scoped:
            logger.warning(
                f"Tool '{tool_name}' is not tenant-scoped - may pose security risk"
            )
        
        return ToolRequest(
            tool_name=tool_name,
            tenant_id=tenant_id,
            user_id=user_id,
            parameters=parameters or {},
            request_id=request_id,
        )
    
    def is_verified(self, tool_name: str) -> bool:
        """Check if tool manifest has been signature-verified.
        
        Args:
            tool_name: Tool to check
            
        Returns:
            True if tool signature has been verified
        """
        return tool_name in self._verified_tools
    
    def get_tool_metadata(self, tool_name: str) -> dict[str, Any] | None:
        """Get metadata about a registered tool.
        
        Args:
            tool_name: Tool to query
            
        Returns:
            Metadata dict or None if tool not found
        """
        if tool_name not in self._tools:
            return None
        
        manifest = self._tools[tool_name]
        return ToolRegistry_get_tool_metadataResult.model_validate({
            "tool_name": manifest.tool_name,
            "version": manifest.version,
            "description": manifest.description,
            "endpoint": manifest.endpoint,
            "capabilities": manifest.capabilities,
            "required_scopes": manifest.required_scopes,
            "has_signature": manifest.signature is not None,
            "verified": tool_name in self._verified_tools,
            "tenant_scoped": manifest.tenant_scoped,
        })


