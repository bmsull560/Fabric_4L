"""Tool registry for managing and executing 24+ skills.

Provides centralized tool registration, discovery, and execution.
"""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from ..models.tool_schemas import ToolCategory, ToolSchema


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

        # Task 2.3: Log tenant context for tools that require it
        if tool.requires_tenant:
            tenant_id = tool.get_tenant_id() or input_dict.get("tenant_id")
            if tenant_id:
                logger.debug(f"Executing tenant-aware tool '{tool_name}' for tenant {tenant_id}")
            else:
                logger.warning(f"Executing tenant-aware tool '{tool_name}' without tenant context")

        return await tool.run(input_dict)

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
