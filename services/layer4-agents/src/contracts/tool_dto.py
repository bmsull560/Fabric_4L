"""Typed DTOs for tools API responses."""

from typing import Any

from pydantic import BaseModel, Field

from ..models.tool_schemas import ToolCategory


class ToolSchemaExample(BaseModel):
    """Example payloads for a tool schema entry."""

    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)


class ToolSchemaResponse(BaseModel):
    """Detailed schema metadata returned for a single tool."""

    name: str
    category: ToolCategory
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    examples: list[dict[str, Any]] = Field(default_factory=list)
    timeout_seconds: int
    requires_auth: bool


class ToolCategoryItem(BaseModel):
    """Category entry in the tool category list endpoint."""

    id: str
    name: str


class ToolCategoryListResponse(BaseModel):
    """Response payload for listing tool categories."""

    categories: list[ToolCategoryItem]
