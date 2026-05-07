"""DTOs for tool route contracts."""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel, Field

from ..models.tool_schemas import ToolCategory

JsonValue: TypeAlias = (
    str | int | float | bool | None | dict[str, "JsonValue"] | list["JsonValue"]
)
ToolSchemaDocument: TypeAlias = dict[str, JsonValue]


class ToolSchemaExample(BaseModel):
    """Single tool example preserving arbitrary JSON-shaped payloads."""

    input: ToolSchemaDocument = Field(default_factory=dict)
    output: ToolSchemaDocument = Field(default_factory=dict)


class ToolSchemaResponse(BaseModel):
    """Typed response model for a single tool schema."""

    name: str
    category: ToolCategory
    description: str
    input_schema: ToolSchemaDocument = Field(default_factory=dict)
    output_schema: ToolSchemaDocument = Field(default_factory=dict)
    examples: list[ToolSchemaExample] = Field(default_factory=list)
    timeout_seconds: int
    requires_auth: bool


class ToolCategoryItem(BaseModel):
    """Single tool category metadata item."""

    id: str
    name: str


class ToolCategoriesResponse(BaseModel):
    """Typed response model for categories listing."""

    categories: list[ToolCategoryItem]
