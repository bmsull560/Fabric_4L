"""Tools API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...tools import create_default_registry
from ...tools.registry import ToolCategory, ToolRegistry

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
    input_data: dict[str, Any] = Field(default_factory=dict, description="Tool input parameters")


class ToolInvokeResponse(BaseModel):
    """Tool invocation response."""

    tool_name: str
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None


def get_tool_registry() -> ToolRegistry:
    """Get tool registry instance."""
    return create_default_registry()


@router.get("/tools", response_model=list[ToolListResponse])
async def list_tools(
    category: str | None = None,
    search: str | None = None,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> list[ToolListResponse]:
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
            requires_auth=t.requires_auth,
        )
        for t in tools
    ]


@router.get("/tools/{tool_name}")
async def get_tool_schema(
    tool_name: str, registry: ToolRegistry = Depends(get_tool_registry)
) -> dict[str, Any]:
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
        "examples": schema.examples,
    }


@router.post("/tools/invoke", response_model=ToolInvokeResponse)
async def invoke_tool(
    request: ToolInvokeRequest, registry: ToolRegistry = Depends(get_tool_registry)
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
        # SECURITY: registry.execute() is an orchestration method, not SQL execution.
        # Tool name is validated above; input_data is validated via Pydantic schemas.
        result = await registry.execute(request.tool_name, request.input_data)

        return ToolInvokeResponse(
            tool_name=request.tool_name, success=True, result=result, error=None
        )

    except Exception as e:
        return ToolInvokeResponse(
            tool_name=request.tool_name, success=False, result=None, error=str(e)
        )


# Document Export Models
class DocumentExportRequest(BaseModel):
    """Request for document export via DocumentExportTool."""

    document_type: str = Field("business_case", description="Type of document to export")
    business_case_id: str = Field(..., description="Business case ID to export")
    format: str = Field("pdf", description="Export format: pdf, html")
    include_provenance: bool = Field(True, description="Include provenance information")


class DocumentExportResponse(BaseModel):
    """Response from document export."""

    success: bool
    download_url: str | None = None
    filename: str | None = None
    file_size_bytes: int | None = None
    format: str = "pdf"
    error: str | None = None


@router.post("/tools/export-document", response_model=DocumentExportResponse)
async def export_document_tool(
    request: DocumentExportRequest,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> DocumentExportResponse:
    """Export a business case to PDF using DocumentExportTool.

    This endpoint triggers PDF generation from business case data.
    Returns the generated PDF for download.

    Example:
        POST /v1/tools/export-document
        {
            "document_type": "business_case",
            "business_case_id": "bc-123",
            "format": "pdf",
            "include_provenance": true
        }
    """
    try:
        # Get business case data from workflow executor
        from .main import workflow_executor

        if not workflow_executor:
            raise HTTPException(status_code=503, detail="Workflow executor not available")

        result = await workflow_executor.get_result(request.business_case_id)

        if not result:
            raise HTTPException(
                status_code=404, detail=f"Business case {request.business_case_id} not found"
            )

        # Extract business case data
        output = result.get("output", {})
        assemble_data = output.get("assemble_document", {})
        narrative_data = output.get("synthesize_narrative", {})

        business_case_data = {
            "title": assemble_data.get("title", "Business Case"),
            "organization": assemble_data.get("organization", "Acme Corp"),
            "use_cases": assemble_data.get("use_cases", []),
            "executive_summary": assemble_data.get(
                "executive_summary", narrative_data.get("narrative", "")
            ),
            "methodology": assemble_data.get(
                "methodology",
                "Value estimation based on industry benchmarks and organizational data.",
            ),
        }

        # Prepare tool input
        tool_input = {
            "document_type": request.document_type,
            "business_case_data": business_case_data,
            "format": request.format,
            "include_provenance": request.include_provenance,
        }

        # Execute DocumentExportTool
        # SECURITY: registry.execute() is an orchestration method, not SQL execution.
        # Tool name is hardcoded; tool_input is constructed from validated request data.
        tool_result = await registry.execute("export_document", tool_input)

        if not tool_result.get("success"):
            return DocumentExportResponse(
                success=False,
                error=tool_result.get("error", "PDF generation failed"),
            )

        # For now, return the PDF bytes as base64 in download_url (simplified)
        # In production, this would upload to S3/MinIO and return a presigned URL
        import base64

        pdf_bytes = tool_result.get("pdf_bytes", b"")
        filename = tool_result.get("filename", f"business_case_{request.business_case_id}.pdf")

        # Create data URL for inline download
        download_url = f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}"

        return DocumentExportResponse(
            success=True,
            download_url=download_url,
            filename=filename,
            file_size_bytes=tool_result.get("file_size_bytes"),
            format=request.format,
        )

    except HTTPException:
        raise
    except Exception as e:
        return DocumentExportResponse(success=False, error=str(e))


@router.get("/tools/categories")
async def list_tool_categories() -> dict[str, Any]:
    """List available tool categories."""
    categories = [
        {"id": cat.value, "name": cat.value.replace("_", " ").title()} for cat in ToolCategory
    ]

    return {"categories": categories}
