from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from canonical.tool_boundary import (
    BaseTool,
    ToolNotFoundError,
    ToolRegistrationError,
    ToolRegistry,
    ToolValidationError,
)


class EchoInput(BaseModel):
    message: str


class EchoOutput(BaseModel):
    echoed: str


class EchoTool(BaseTool):
    name = "echo"
    input_schema = EchoInput
    output_schema = EchoOutput

    async def execute(self, validated_input: EchoInput) -> EchoOutput:
        return EchoOutput(echoed=validated_input.message)


class DictEchoTool(EchoTool):
    name = "dict-echo"

    async def execute(self, validated_input: EchoInput) -> dict[str, Any]:
        return {"echoed": validated_input.message}


class MissingInputSchemaTool(BaseTool):
    name = "missing-input"
    output_schema = EchoOutput

    async def execute(self, validated_input: BaseModel) -> EchoOutput:
        return EchoOutput(echoed="unused")


class MissingOutputSchemaTool(BaseTool):
    name = "missing-output"
    input_schema = EchoInput

    async def execute(self, validated_input: EchoInput) -> dict[str, str]:
        return {"echoed": validated_input.message}


class InvalidOutputTool(EchoTool):
    name = "invalid-output"

    async def execute(self, validated_input: EchoInput) -> str:
        return validated_input.message


class UnimplementedTool(BaseTool):
    name = "unimplemented"
    input_schema = EchoInput
    output_schema = EchoOutput


def test_tool_registry_registers_gets_and_lists_tools() -> None:
    registry = ToolRegistry()
    tool = EchoTool()

    registry.register(tool)

    listed = registry.list_tools()

    assert registry.get("echo") is tool
    assert listed[0]["name"] == "echo"
    assert listed[0]["input_schema"]["properties"]["message"]["type"] == "string"
    assert listed[0]["output_schema"]["properties"]["echoed"]["type"] == "string"


def test_tool_registry_rejects_duplicate_names() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    with pytest.raises(
        ToolRegistrationError,
        match="Tool 'echo' is already registered",
    ):
        registry.register(EchoTool())


@pytest.mark.asyncio
async def test_tool_run_validates_input_and_dumps_model_output() -> None:
    result = await EchoTool().run({"message": "hello"})

    assert result == {"echoed": "hello"}


@pytest.mark.asyncio
async def test_tool_run_accepts_dict_output_and_validates_it() -> None:
    result = await DictEchoTool().run({"message": "hi"})

    assert result == {"echoed": "hi"}


@pytest.mark.asyncio
async def test_tool_registry_execute_routes_to_registered_tool() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    result = await registry.execute("echo", {"message": "contracts"})

    assert result == {"echoed": "contracts"}


@pytest.mark.asyncio
async def test_tool_boundary_negative_messages_are_actionable() -> None:
    with pytest.raises(
        ToolValidationError,
        match="Input validation failed",
    ):
        await EchoTool().run({"message": 123})

    with pytest.raises(
        ToolValidationError,
        match="Tool missing-input has no input schema defined",
    ):
        await MissingInputSchemaTool().run({"message": "hello"})

    with pytest.raises(
        ToolValidationError,
        match="Tool missing-output has no output schema defined",
    ):
        await MissingOutputSchemaTool().run({"message": "hello"})

    with pytest.raises(
        ToolValidationError,
        match="Must return a Pydantic model or dict",
    ):
        await InvalidOutputTool().run({"message": "hello"})


def test_tool_registry_unknown_tool_message_is_actionable() -> None:
    registry = ToolRegistry()

    with pytest.raises(
        ToolNotFoundError,
        match="Tool 'missing' is not registered",
    ):
        registry.get("missing")


def test_base_tool_is_explicit_non_runtime_abstraction() -> None:
    with pytest.raises(TypeError, match="Can't instantiate abstract class UnimplementedTool"):
        UnimplementedTool()
