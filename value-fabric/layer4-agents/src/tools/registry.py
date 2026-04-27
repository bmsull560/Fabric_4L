"""Tool registry for managing and executing 24+ skills.

Provides centralized tool registration, discovery, and execution.
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any
from uuid import UUID

from shared.identity.context import RequestContext
from ..models.tool_schemas import ToolCategory, ToolSchema

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Raised when a tool execution fails."""

    pass


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found."""

    pass


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""

    pass


class BaseTool(ABC):
    """Base class for all tools.

    All tools must inherit from this class and implement:
    - name: Tool identifier
    - category: ToolCategory
    - description: Human-readable description
    - input_schema: Pydantic model class for input
    - output_schema: Pydantic model class for output
    - execute(): The actual tool implementation

    Example:
        class MyTool(BaseTool):
            name = "my_tool"
            category = ToolCategory.UTILITY
            description = "Does something useful"
            input_schema = MyToolInput
            output_schema = MyToolOutput

            async def execute(self, input_data: MyToolInput) -> MyToolOutput:
                # Implementation here
                return MyToolOutput(result="success")
    """

    name: str = ""
    category: ToolCategory = ToolCategory.UTILITY
    description: str = ""
    input_schema: type | None = None
    output_schema: type | None = None
    timeout_seconds: int = 30
    requires_auth: bool = False
    requires_tenant: bool = False  # Task 2.3: Tenant enforcement flag

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize tool with optional configuration.

        Args:
            config: Tool-specific configuration (may include tenant_id)
        """
        self.config = config or {}
        self._initialized = True

    def get_tenant_id(self) -> str | None:
        """Extract tenant_id from config (Task 2.3).

        Returns:
            Tenant ID if set in config, None otherwise
        """
        return self.config.get("tenant_id")

    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        """Execute the tool with validated input.

        Args:
            input_data: Validated input (input_schema instance)

        Returns:
            Output (output_schema instance)

        Raises:
            ToolError: If execution fails
        """
        pass

    def get_schema(self) -> ToolSchema:
        """Get the tool schema for registration."""
        return ToolSchema(
            name=self.name,
            category=self.category,
            description=self.description,
            input_schema=self.input_schema.model_json_schema() if self.input_schema else {},
            output_schema=self.output_schema.model_json_schema() if self.output_schema else {},
            timeout_seconds=self.timeout_seconds,
            requires_auth=self.requires_auth,
        )

    async def run(self, input_dict: dict[str, Any]) -> dict[str, Any]:
        """Run the tool with raw input dict (validates first).

        Args:
            input_dict: Raw input parameters

        Returns:
            Output as dictionary

        Raises:
            ToolValidationError: If input validation fails
            ToolError: If execution fails
        """
        if self.input_schema is None:
            raise ToolValidationError(f"Tool {self.name} has no input schema defined")

        try:
            # Validate input
            validated_input = self.input_schema(**input_dict)
        except Exception as e:
            raise ToolValidationError(f"Input validation failed: {e}")

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self.execute(validated_input), timeout=self.timeout_seconds
            )
        except TimeoutError:
            raise ToolError(f"Tool {self.name} timed out after {self.timeout_seconds}s")
        except Exception as e:
            raise ToolError(f"Tool execution failed: {e}")

        # Convert to dict
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result


class TenantAwareTool(BaseTool):
    """Base class for tools that require tenant context (Task 2.3).

    Tools that access tenant-scoped data (knowledge graph, CRM, etc.)
    should inherit from this class to ensure tenant isolation.

    Example:
        class QueryGraphTool(TenantAwareTool):
            name = "query_graph"
            requires_tenant = True

            async def execute(self, input_data: QueryInput) -> QueryOutput:
                tenant_id = self.get_tenant_id()
                # Use tenant_id for all queries
                ...
    """

    requires_tenant: bool = True

    def validate_tenant_context(self) -> str:
        """Validate that tenant context is present.

        Returns:
            Tenant ID if valid

        Raises:
            ToolValidationError: If tenant_id is missing and requires_tenant=True
        """
        tenant_id = self.get_tenant_id()
        if tenant_id:
            return tenant_id
        if self.requires_tenant:
            raise ToolValidationError(
                f"Tool '{self.name}' requires tenant context but no tenant_id provided"
            )
        return ""

    async def run(self, input_dict: dict[str, Any]) -> dict[str, Any]:
        """Run tool with tenant validation (Task 2.3).

        Validates tenant context before executing.
        """
        # Validate tenant context before execution
        self.validate_tenant_context()

        # Proceed with base run logic
        return await super().run(input_dict)


class ToolRegistry:
    """Central registry for all tools.

    Manages tool registration, discovery, and execution.

    Example:
        registry = ToolRegistry()

        # Register tools
        registry.register(MyTool())
        registry.register_batch([ToolA(), ToolB()])

        # Execute tool
        result = await registry.execute("my_tool", {"param": "value"})

        # List available tools
        tools = registry.list_tools()
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a single tool.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool with same name already registered
        """
        if not tool.name:
            raise ValueError("Tool must have a name")

        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool

    def register_batch(self, tools: list[BaseTool]) -> None:
        """Register multiple tools at once.

        Args:
            tools: List of tool instances
        """
        for tool in tools:
            self.register(tool)

    def unregister(self, tool_name: str) -> None:
        """Remove a tool from registry.

        Args:
            tool_name: Name of tool to remove
        """
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get(self, tool_name: str) -> BaseTool:
        """Get a tool by name.

        Args:
            tool_name: Tool identifier

        Returns:
            Tool instance

        Raises:
            ToolNotFoundError: If tool not found
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")
        return self._tools[tool_name]

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered.

        Args:
            tool_name: Tool identifier

        Returns:
            True if tool exists
        """
        return tool_name in self._tools

    async def execute(self, tool_name: str, input_dict: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name.

        SECURITY: This is an orchestration method that dispatches to tool implementations.
        It does NOT execute SQL. The tool_name is validated against registered tools,
        and input_dict is validated via Pydantic schemas before reaching tool logic.

        When ``AUDIT_LEDGER_MODE=enabled``, emits a ``TOOL_INVOCATION`` audit event
        with request/response hashing for the GATE audit ledger.

        Args:
            tool_name: Tool identifier (validated against registry)
            input_dict: Raw input parameters (validated via Pydantic schemas)

        Returns:
            Tool output as dictionary

        Raises:
            ToolNotFoundError: If tool not found
            ToolValidationError: If input validation fails
            ToolError: If execution fails
        """
        tool = self.get(tool_name)
        tenant_id = tool.get_tenant_id() or input_dict.get("tenant_id")
        trace_id = input_dict.get("trace_id")

        # Task 2.3: Log tenant context for tools that require it
        if tool.requires_tenant:
            if tenant_id:
                logger.debug(f"Executing tenant-aware tool '{tool_name}' for tenant {tenant_id}")
            else:
                logger.warning(f"Executing tenant-aware tool '{tool_name}' without tenant context")

        # GATE Phase 1: Instrument with TOOL_INVOCATION audit events
        ledger_enabled = os.getenv("AUDIT_LEDGER_MODE") == "enabled"
        request_hash: str | None = None
        start_time: float = 0.0

        if ledger_enabled:
            from shared.crypto.canonical import canonical_hash
            request_hash = canonical_hash({"tool_name": tool_name, "input": input_dict})
            start_time = asyncio.get_running_loop().time()

        outcome = "success"
        response_hash: str | None = None

        try:
            result = await tool.run(input_dict)
            if ledger_enabled:
                from shared.crypto.canonical import canonical_hash as _ch
                response_hash = _ch(result)
            return result
        except Exception:
            outcome = "failure"
            raise
        finally:
            if ledger_enabled:
                elapsed_ms = int((asyncio.get_running_loop().time() - start_time) * 1000)
                self._emit_tool_invocation_audit(
                    tool_name=tool_name,
                    tool=tool,
                    request_hash=request_hash,
                    response_hash=response_hash,
                    elapsed_ms=elapsed_ms,
                    outcome=outcome,
                    tenant_id=tenant_id,
                    trace_id=trace_id,
                )

    @staticmethod
    def _emit_tool_invocation_audit(
        tool_name: str,
        tool: "BaseTool",
        request_hash: str | None,
        response_hash: str | None,
        elapsed_ms: int,
        outcome: str,
        tenant_id: str | None,
        trace_id: str | None,
    ) -> None:
        """Fire-and-forget TOOL_INVOCATION audit event."""
        from shared.audit.emitter import emit_audit_event
        from shared.audit.models import (
            AuditAction,
            AuditOutcome,
            ToolInvocationRecord,
        )

        record = ToolInvocationRecord(
            tool_name=tool_name,
            tool_manifest_hash=getattr(tool, "manifest_hash", None),
            request_hash=request_hash or "",
            response_hash=response_hash,
            execution_time_ms=elapsed_ms,
            tenant_id=tenant_id,
            trace_id=trace_id,
        )
        asyncio.create_task(
            emit_audit_event(
                action=AuditAction.TOOL_INVOCATION,
                outcome=AuditOutcome.SUCCESS if outcome == "success" else AuditOutcome.FAILURE,
                resource_type="tool",
                resource_id=tool_name,
                tenant_id=UUID(tenant_id) if tenant_id else None,
                request_id=trace_id,
                details=record.model_dump(),
                chain_id=f"{tenant_id or 'global'}:{tool_name}",
            )
        )

    def list_tools(
        self, category: ToolCategory | None = None, search: str | None = None
    ) -> list[ToolSchema]:
        """List available tools with optional filtering.

        Args:
            category: Filter by category
            search: Filter by name/description search term

        Returns:
            List of tool schemas
        """
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if search:
            search_lower = search.lower()
            tools = [
                t
                for t in tools
                if search_lower in t.name.lower() or search_lower in t.description.lower()
            ]

        return [t.get_schema() for t in tools]

    def get_all_schemas(self) -> dict[str, ToolSchema]:
        """Get all tool schemas as dictionary.

        Returns:
            Dict mapping tool names to schemas
        """
        return {name: tool.get_schema() for name, tool in self._tools.items()}

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()


# Global registry instance
_global_registry: ToolRegistry | None = None


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry (creates if needed)."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def reset_global_registry() -> None:
    """Reset the global registry (useful for testing)."""
    global _global_registry
    _global_registry = None


def tool(
    name: str,
    category: ToolCategory,
    description: str,
    input_schema: type,
    output_schema: type,
    timeout_seconds: int = 30,
):
    """Decorator to create a tool from a function.

    Example:
        @tool(
            name="multiply",
            category=ToolCategory.CALCULATION,
            description="Multiply two numbers",
            input_schema=MultiplyInput,
            output_schema=MultiplyOutput
        )
        async def multiply(input_data: MultiplyInput) -> MultiplyOutput:
            return MultiplyOutput(result=input_data.a * input_data.b)
    """

    def decorator(func: Callable) -> type[BaseTool]:
        class DynamicTool(BaseTool):
            _name = name
            _category = category
            _description = description
            _input_schema = input_schema
            _output_schema = output_schema
            _timeout = timeout_seconds

            async def execute(self, input_data: Any) -> Any:
                return await func(input_data)

        # Set class attributes
        DynamicTool.name = name
        DynamicTool.category = category
        DynamicTool.description = description
        DynamicTool.input_schema = input_schema
        DynamicTool.output_schema = output_schema
        DynamicTool.timeout_seconds = timeout_seconds

        return DynamicTool

    return decorator


# ═══════════════════════════════════════════════════════════════════════════
# Helper Methods for Testing and Discovery
# ═══════════════════════════════════════════════════════════════════════════


def get_all_tools(registry: "ToolRegistry") -> dict[str, Callable]:
    """Get all registered tools.
    
    Args:
        registry: ToolRegistry instance
    
    Returns:
        Dictionary mapping tool names to tool functions
    """
    tools = {}
    for tool_class in registry._tools.values():
        # Create instance and get execute method
        tool_instance = tool_class()
        tools[tool_class.name] = tool_instance.execute
    return tools


def get_tool_metadata(registry: "ToolRegistry", tool_name: str) -> dict:
    """Get metadata for a tool.
    
    Args:
        registry: ToolRegistry instance
        tool_name: Name of tool
    
    Returns:
        Tool metadata including tenant_scoped flag
    """
    if tool_name not in registry._tools:
        raise ToolNotFoundError(f"Tool {tool_name} not found")
    
    tool_class = registry._tools[tool_name]
    
    # Check if tool is tenant-scoped (has tenant_id parameter)
    import inspect
    sig = inspect.signature(tool_class().execute)
    tenant_scoped = "tenant_id" in sig.parameters
    
    return {
        "name": tool_class.name,
        "category": tool_class.category,
        "description": tool_class.description,
        "tenant_scoped": tenant_scoped,
    }


def get_available_tools(registry: "ToolRegistry", context: RequestContext) -> list[str]:
    """Get tools available to user based on permissions.
    
    Args:
        registry: ToolRegistry instance
        context: Request context with permissions
    
    Returns:
        List of tool names user can access
    """
    available = []
    
    for tool_name, tool_class in registry._tools.items():
        metadata = get_tool_metadata(registry, tool_name)
        
        # Admin-only tools
        admin_tools = {"delete_tenant", "suspend_tenant", "grant_permission"}
        if tool_name in admin_tools:
            if "admin" in context.permissions:
                available.append(tool_name)
            continue
        
        # Write tools
        write_tools = {"update_entity", "delete_entity"}
        if tool_name in write_tools:
            if "write" in context.permissions or "admin" in context.permissions:
                available.append(tool_name)
            continue
        
        # Read tools (available to all authenticated users)
        available.append(tool_name)
    
    return available


# Monkey-patch methods onto ToolRegistry class
ToolRegistry.get_all_tools = lambda self: get_all_tools(self)
ToolRegistry.get_tool_metadata = lambda self, name: get_tool_metadata(self, name)
ToolRegistry.get_available_tools = lambda self, context: get_available_tools(self, context)
