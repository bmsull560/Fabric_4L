"""Tool registry for managing and executing 24+ skills.

Provides centralized tool registration, discovery, and execution.
"""

import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type
from functools import wraps
import asyncio

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
    input_schema: Optional[Type] = None
    output_schema: Optional[Type] = None
    timeout_seconds: int = 30
    requires_auth: bool = False
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize tool with optional configuration.
        
        Args:
            config: Tool-specific configuration
        """
        self.config = config or {}
        self._initialized = True
    
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
            requires_auth=self.requires_auth
        )
    
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
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
                self.execute(validated_input),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise ToolError(f"Tool {self.name} timed out after {self.timeout_seconds}s")
        except Exception as e:
            raise ToolError(f"Tool execution failed: {e}")
        
        # Convert to dict
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result


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
        self._tools: Dict[str, BaseTool] = {}
    
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
    
    def register_batch(self, tools: List[BaseTool]) -> None:
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
    
    async def execute(self, tool_name: str, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name.
        
        Args:
            tool_name: Tool identifier
            input_dict: Raw input parameters
            
        Returns:
            Tool output as dictionary
            
        Raises:
            ToolNotFoundError: If tool not found
            ToolValidationError: If input validation fails
            ToolError: If execution fails
        """
        tool = self.get(tool_name)
        return await tool.run(input_dict)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        search: Optional[str] = None
    ) -> List[ToolSchema]:
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
                t for t in tools
                if search_lower in t.name.lower() or search_lower in t.description.lower()
            ]
        
        return [t.get_schema() for t in tools]
    
    def get_all_schemas(self) -> Dict[str, ToolSchema]:
        """Get all tool schemas as dictionary.
        
        Returns:
            Dict mapping tool names to schemas
        """
        return {name: tool.get_schema() for name, tool in self._tools.items()}
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


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
    input_schema: Type,
    output_schema: Type,
    timeout_seconds: int = 30
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
    def decorator(func: Callable) -> Type[BaseTool]:
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
