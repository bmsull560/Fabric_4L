"""Canonical tool invocation boundary for Fabric 4L."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolContractError(RuntimeError):
    """Base error for canonical tool boundary violations."""


class ToolRegistrationError(ToolContractError):
    """Raised when tool registration violates the contract."""


class ToolNotFoundError(ToolContractError):
    """Raised when a requested tool is not registered."""


class ToolValidationError(ToolContractError):
    """Raised when tool input or output validation fails."""


def _validate_model(schema: type[BaseModel], payload: Any) -> BaseModel:
    if hasattr(schema, "model_validate"):
        return schema.model_validate(payload)
    return schema(**payload)


def _dump_model(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _schema_json(schema: type[BaseModel]) -> dict[str, Any]:
    if hasattr(schema, "model_json_schema"):
        return schema.model_json_schema()
    return schema.schema()


class BaseTool(ABC):
    """Base class for all agent tools/skills."""
    name: str = ""
    input_schema: type[BaseModel] | None = None
    output_schema: type[BaseModel] | None = None

    async def run(self, input_dict: dict[str, Any]) -> dict[str, Any]:
        """Entry point called by the registry / workflow engine."""
        if self.input_schema is None:
            raise ToolValidationError(
                f"Tool {self.name} has no input schema defined"
            )
        if self.output_schema is None:
            raise ToolValidationError(
                f"Tool {self.name} has no output schema defined"
            )

        try:
            validated_input = _validate_model(self.input_schema, input_dict)
        except Exception as exc:
            raise ToolValidationError(f"Input validation failed: {exc}") from exc

        result = await self.execute(validated_input)

        if isinstance(result, BaseModel):
            validated_output = result
        elif isinstance(result, dict):
            try:
                validated_output = _validate_model(self.output_schema, result)
            except Exception as exc:
                raise ToolValidationError(f"Output validation failed: {exc}") from exc
        else:
            raise ToolValidationError(
                f"Tool {self.name} returned invalid output. Must return a Pydantic model or dict."
            )

        return _dump_model(validated_output)

    @abstractmethod
    async def execute(self, validated_input: BaseModel) -> BaseModel | dict[str, Any]:
        """Tool-specific logic. Must return a Pydantic model or dict."""
        raise NotImplementedError


class ToolRegistry:
    """Canonical registry for tool discovery and invocation."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not tool.name:
            raise ToolRegistrationError("Tool must have a name")
        if tool.name in self._tools:
            raise ToolRegistrationError(
                f"Tool '{tool.name}' is already registered"
            )
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' is not registered")
        return self._tools[name]

    async def execute(self, name: str, input_dict: dict[str, Any]) -> dict[str, Any]:
        return await self.get(name).run(input_dict)

    def list_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for name, tool in sorted(self._tools.items()):
            tools.append(
                {
                    "name": name,
                    "input_schema": (
                        _schema_json(tool.input_schema)
                        if tool.input_schema is not None
                        else None
                    ),
                    "output_schema": (
                        _schema_json(tool.output_schema)
                        if tool.output_schema is not None
                        else None
                    ),
                }
            )
        return tools
