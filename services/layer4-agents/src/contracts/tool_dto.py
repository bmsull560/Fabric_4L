"""DTOs for tool route contracts."""

from typing import Any

from pydantic import BaseModel, Field

from ..models.tool_schemas import ToolCategory


class ToolSchemaResponse(BaseModel):
    """Typed response model for a single tool schema."""

    name: str
    category: ToolCategory
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    examples: list[dict[str, Any]] = Field(default_factory=list)
    timeout_seconds: int
    requires_auth: bool


class ToolCategoryItem(BaseModel):
    """Single tool category metadata item."""

    id: str
    name: str


class ToolCategoriesResponse(BaseModel):
    """Typed response model for categories listing."""

    categories: list[ToolCategoryItem]
