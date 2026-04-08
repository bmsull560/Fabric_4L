"""Tools API routes."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ...tools import create_default_registry
from ...tools.registry import ToolCategory, ToolRegistry, ToolSchema


router = APIRouter()


# Request/Response Models
class ToolListResponse(BaseModel):
    """Tool list response."""
    name: str
    category: str
    description: str
    timeout_seconds: int
    requires_auth: bool


class ToolInvokeRequest(BaseModel):
    """Tool invocation request."""
    tool_name: str = Field(..., description="Name of tool to invoke")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Tool input parameters")


class ToolInvokeResponse(BaseModel):
    """Tool invocation response."""
    tool_name: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def get_tool_registry() -> ToolRegistry:
    """Get tool registry instance."""
    return create_default_registry()


@router.get("/tools", response_model=List[ToolListResponse])
async def list_tools(
    category: Optional[str] = None,
    search: Optional[str] = None,
    registry: ToolRegistry = Depends(get_tool_registry)
) -> List[ToolListResponse]:
    """List available tools with optional filtering.
    
    Query Parameters:
        category: Filter by category (knowledge, calculation, crm, generation, integration, utility)
        search: Search in tool name/description
    """
    cat = None
    if category:
        try:
            cat = ToolCategory(category.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    tools = registry.list_tools(category=cat, search=search)
    
    return [
        ToolListResponse(
            name=t.name,
            category=t.category.value,
            description=t.description,
            timeout_seconds=t.timeout_seconds,
            requires_auth=t.requires_auth
        )
        for t in tools
    ]


@router.get("/tools/{tool_name}")
async def get_tool_schema(
    tool_name: str,
    registry: ToolRegistry = Depends(get_tool_registry)
) -> Dict[str, Any]:
    """Get detailed schema for a specific tool."""
    if not registry.has_tool(tool_name):
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    tool = registry.get(tool_name)
    schema = tool.get_schema()
    
    return {
        "name": schema.name,
        "category": schema.category.value,
        "description": schema.description,
        "input_schema": schema.input_schema,
        "output_schema": schema.output_schema,
        "timeout_seconds": schema.timeout_seconds,
        "requires_auth": schema.requires_auth,
        "examples": schema.examples
    }


@router.post("/tools/invoke", response_model=ToolInvokeResponse)
async def invoke_tool(
    request: ToolInvokeRequest,
    registry: ToolRegistry = Depends(get_tool_registry)
) -> ToolInvokeResponse:
    """Invoke a tool directly.
    
    Example:
        POST /v1/tools/invoke
        {
            "tool_name": "calculate_roi",
            "input_data": {
                "investment": 250000,
                "returns": [400000, 450000, 500000]
            }
        }
    """
    if not registry.has_tool(request.tool_name):
        raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found")
    
    try:
        result = await registry.execute(request.tool_name, request.input_data)
        
        return ToolInvokeResponse(
            tool_name=request.tool_name,
            success=True,
            result=result,
            error=None
        )
    
    except Exception as e:
        return ToolInvokeResponse(
            tool_name=request.tool_name,
            success=False,
            result=None,
            error=str(e)
        )


@router.get("/tools/categories")
async def list_tool_categories() -> Dict[str, Any]:
    """List available tool categories."""
    categories = [
        {"id": cat.value, "name": cat.value.replace("_", " ").title()}
        for cat in ToolCategory
    ]
    
    return {"categories": categories}
