# Canonical tool invocation boundary for Fabric 4L.
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel


class BaseTool(ABC):
    """Base class for all agent tools/skills."""
    name: str = ""
    input_schema: type[BaseModel] | None = None
    output_schema: type[BaseModel] | None = None

    async def run(self, input_dict: dict[str, Any]) -> dict[str, Any]:
        """Entry point called by the registry / workflow engine."""
        ...

    @abstractmethod
    async def execute(self, validated_input: BaseModel) -> BaseModel | dict[str, Any]:
        """Tool-specific logic. Must return a Pydantic model or dict."""
        ...


class ToolRegistry:
    """Canonical registry for tool discovery and invocation."""

    def register(self, tool: BaseTool) -> None:
        ...

    def get(self, name: str) -> BaseTool:
        ...

    async def execute(self, name: str, input_dict: dict[str, Any]) -> dict[str, Any]:
        ...

    def list_tools(self) -> list[dict[str, Any]]:
        ...
