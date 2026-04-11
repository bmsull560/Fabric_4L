"""Tool input/output schemas.

Pydantic models defining the interface for all 24 tools in the registry.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ToolCategory(str, Enum):
    """Categories of tools."""
    KNOWLEDGE = "knowledge"
    CALCULATION = "calculation"
    CRM = "crm"
    GENERATION = "generation"
    INTEGRATION = "integration"
    UTILITY = "utility"


class ToolSchema(BaseModel):
    """Schema definition for a tool.
    
    Attributes:
        name: Tool identifier
        category: Tool category
        description: Human-readable description
        input_schema: Input parameter schema
        output_schema: Output result schema
        examples: Example inputs/outputs
    """
    name: str
    category: ToolCategory
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    timeout_seconds: int = 30
    requires_auth: bool = False


# ============================================================================
# KNOWLEDGE TOOLS (6)
# ============================================================================

class QueryGraphInput(BaseModel):
    """Input for query_graph tool."""
    cypher_query: str = Field(..., description="Cypher query to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    read_only: bool = True


class QueryGraphOutput(BaseModel):
    """Output from query_graph tool."""
    results: List[Dict[str, Any]] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0


class SemanticSearchInput(BaseModel):
    """Input for semantic_search tool."""
    query: str = Field(..., min_length=1)
    entity_types: Optional[List[str]] = None
    top_k: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class SemanticSearchOutput(BaseModel):
    """Output from semantic_search tool."""
    results: List[Dict[str, Any]] = Field(default_factory=list)
    total_matches: int = 0
    query_embedding_time_ms: int = 0


class GetEntityInput(BaseModel):
    """Input for get_entity tool."""
    entity_id: str
    include_relationships: bool = True
    depth: int = Field(default=1, ge=0, le=3)


class GetEntityOutput(BaseModel):
    """Output from get_entity tool."""
    entity: Optional[Dict[str, Any]] = None
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    found: bool = False


class GetRelationshipsInput(BaseModel):
    """Input for get_relationships tool."""
    entity_id: str
    predicate: Optional[str] = None
    direction: Literal["outgoing", "incoming", "both"] = "both"
    limit: int = Field(default=50, ge=1, le=500)


class GetRelationshipsOutput(BaseModel):
    """Output from get_relationships tool."""
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0


class TraverseTreeInput(BaseModel):
    """Input for traverse_tree tool."""
    start_entity_id: str
    path_pattern: str  # e.g., "(Capability)-[:ENABLES]->(UseCase)"
    max_depth: int = Field(default=3, ge=1, le=10)


class TraverseTreeOutput(BaseModel):
    """Output from traverse_tree tool."""
    paths: List[List[Dict[str, Any]]] = Field(default_factory=list)
    nodes_discovered: int = 0


class FindPathsInput(BaseModel):
    """Input for find_paths tool."""
    source_id: str
    target_id: str
    max_length: int = Field(default=6, ge=1, le=10)
    relationship_types: Optional[List[str]] = None


class FindPathsOutput(BaseModel):
    """Output from find_paths tool."""
    paths: List[Dict[str, Any]] = Field(default_factory=list)
    shortest_path_length: Optional[int] = None


# ============================================================================
# CALCULATION TOOLS (4)
# ============================================================================

class EvaluateFormulaInput(BaseModel):
    """Input for evaluate_formula tool."""
    formula: str = Field(..., min_length=1)
    variables: Dict[str, float] = Field(default_factory=dict)
    unit: str = "USD"

    @field_validator("formula")
    @classmethod
    def validate_formula_chars(cls, v: str) -> str:
        allowed = set("0123456789+-*/().{}_ ")
        invalid = set(v) - allowed
        if invalid:
            raise ValueError(f"Invalid characters in formula: {invalid}")
        return v


class EvaluateFormulaOutput(BaseModel):
    """Output from evaluate_formula tool."""
    result: Optional[float] = None
    substituted_formula: str = ""
    error: Optional[str] = None
    success: bool = False


class CalculateROIInput(BaseModel):
    """Input for calculate_roi tool."""
    investment: float = Field(..., ge=0)
    returns: List[float] = Field(default_factory=list)
    time_periods: int = Field(default=3, ge=1)
    discount_rate: float = Field(default=0.1, ge=0.0, le=1.0)


class CalculateROIOutput(BaseModel):
    """Output from calculate_roi tool."""
    simple_roi_percent: float
    npv: float
    irr: Optional[float] = None
    payback_period_months: Optional[float] = None
    total_return: float


class CompareBenchmarksInput(BaseModel):
    """Input for compare_benchmarks tool."""
    metric_name: str
    value: float
    industry: Optional[str] = None
    company_size: Optional[str] = None
    region: Optional[str] = None


class CompareBenchmarksOutput(BaseModel):
    """Output from compare_benchmarks tool."""
    percentile: float = Field(ge=0.0, le=100.0)
    industry_average: Optional[float] = None
    comparison_text: str
    confidence: float = Field(ge=0.0, le=1.0)


class SensitivityAnalysisInput(BaseModel):
    """Input for sensitivity_analysis tool."""
    base_formula: str
    base_variables: Dict[str, float]
    variable_ranges: Dict[str, tuple]  # {"var": (min, max, steps)}


class SensitivityAnalysisOutput(BaseModel):
    """Output from sensitivity_analysis tool."""
    scenarios: List[Dict[str, Any]] = Field(default_factory=list)
    tornado_data: List[Dict[str, Any]] = Field(default_factory=list)
    optimal_variables: Optional[Dict[str, float]] = None


# ============================================================================
# CRM TOOLS (4)
# ============================================================================

class GetProspectDataInput(BaseModel):
    """Input for get_prospect_data tool."""
    prospect_id: str
    data_types: List[str] = Field(default_factory=lambda: ["profile", "interactions", "opportunities"])


class GetProspectDataOutput(BaseModel):
    """Output from get_prospect_data tool."""
    profile: Dict[str, Any] = Field(default_factory=dict)
    interactions: List[Dict[str, Any]] = Field(default_factory=list)
    opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class UpdateOpportunityInput(BaseModel):
    """Input for update_opportunity tool."""
    opportunity_id: str
    updates: Dict[str, Any]
    notify_owner: bool = True


class UpdateOpportunityOutput(BaseModel):
    """Output from update_opportunity tool."""
    success: bool
    opportunity_id: str
    updated_fields: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class FetchInteractionHistoryInput(BaseModel):
    """Input for fetch_interaction_history tool."""
    prospect_id: str
    interaction_types: Optional[List[str]] = None
    since_date: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)


class FetchInteractionHistoryOutput(BaseModel):
    """Output from fetch_interaction_history tool."""
    interactions: List[Dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0
    summary: str = ""


class ScoreLeadInput(BaseModel):
    """Input for score_lead tool."""
    prospect_id: str
    scoring_model: str = "default"
    factors: Optional[List[str]] = None


class ScoreLeadOutput(BaseModel):
    """Output from score_lead tool."""
    score: float = Field(ge=0.0, le=100.0)
    grade: str  # "A", "B", "C", "D", "F"
    factors: Dict[str, float] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# GENERATION TOOLS (4)
# ============================================================================

class GenerateSectionInput(BaseModel):
    """Input for generate_section tool."""
    section_type: str  # "executive_summary", "roi_analysis", etc.
    context: Dict[str, Any] = Field(default_factory=dict)
    tone: str = "professional"
    max_length: int = Field(default=500, ge=100, le=2000)


class GenerateSectionOutput(BaseModel):
    """Output from generate_section tool."""
    content: str
    word_count: int
    key_points: List[str] = Field(default_factory=list)


class CreateChartInput(BaseModel):
    """Input for create_chart tool."""
    chart_type: Literal["bar", "line", "pie", "table", "funnel"]
    data: List[Dict[str, Any]]
    title: str
    config: Dict[str, Any] = Field(default_factory=dict)


class CreateChartOutput(BaseModel):
    """Output from create_chart tool."""
    chart_data: Dict[str, Any] = Field(default_factory=dict)
    image_data: Optional[bytes] = None
    image_url: Optional[str] = None


class FormatTableInput(BaseModel):
    """Input for format_table tool."""
    headers: List[str]
    rows: List[List[Any]]
    format: Literal["html", "markdown", "csv"] = "html"
    sort_column: Optional[int] = None


class FormatTableOutput(BaseModel):
    """Output from format_table tool."""
    formatted: str
    row_count: int


class AssembleDocumentInput(BaseModel):
    """Input for assemble_document tool."""
    sections: List[Dict[str, Any]]
    template: str = "business_case"
    output_format: Literal["pdf", "docx", "html"] = "pdf"
    branding: Optional[Dict[str, Any]] = None


class AssembleDocumentOutput(BaseModel):
    """Output from assemble_document tool."""
    document_bytes: Optional[bytes] = None
    document_url: Optional[str] = None
    page_count: int = 0
    file_size_bytes: int = 0


class ExportDocumentInput(BaseModel):
    """Input for export_document tool."""
    document_type: Literal["business_case", "audit_report", "roi_analysis"] = "business_case"
    business_case_data: Dict[str, Any] = Field(default_factory=dict, description="Structured business case data with title, organization, use_cases, etc.")
    template: Optional[str] = Field(None, description="Optional custom HTML template string")
    branding: Optional[Dict[str, str]] = Field(None, description="Branding config: logo_url, primary_color, company_name")


class ExportDocumentOutput(BaseModel):
    """Output from export_document tool."""
    pdf_bytes: Optional[bytes] = None
    content_type: str = "application/pdf"
    filename: str = "document.pdf"
    success: bool = False
    error: Optional[str] = None
    file_size_bytes: int = 0


# ============================================================================
# INTEGRATION TOOLS (4)
# ============================================================================

class SendNotificationInput(BaseModel):
    """Input for send_notification tool."""
    channel: Literal["email", "slack", "teams"]
    recipients: List[str]
    subject: str
    message: str
    attachments: Optional[List[Dict[str, Any]]] = None


class SendNotificationOutput(BaseModel):
    """Output from send_notification tool."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class CreateTaskInput(BaseModel):
    """Input for create_task tool."""
    title: str
    description: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: Literal["low", "medium", "high"] = "medium"
    related_to: Optional[Dict[str, str]] = None


class CreateTaskOutput(BaseModel):
    """Output from create_task tool."""
    task_id: Optional[str] = None
    success: bool
    url: Optional[str] = None


class ScheduleMeetingInput(BaseModel):
    """Input for schedule_meeting tool."""
    title: str
    attendees: List[str]
    duration_minutes: int = Field(default=30, ge=15, le=240)
    preferred_times: Optional[List[str]] = None
    description: Optional[str] = None


class ScheduleMeetingOutput(BaseModel):
    """Output from schedule_meeting tool."""
    meeting_id: Optional[str] = None
    scheduled_time: Optional[str] = None
    calendar_link: Optional[str] = None
    success: bool


class ExportToCRMInput(BaseModel):
    """Input for export_to_crm tool."""
    entity_type: Literal["note", "document", "activity"]
    entity_data: Dict[str, Any]
    prospect_id: str


class ExportToCRMOutput(BaseModel):
    """Output from export_to_crm tool."""
    crm_record_id: Optional[str] = None
    success: bool
    url: Optional[str] = None


# ============================================================================
# UTILITY TOOLS (2)
# ============================================================================

class ValidateInputInput(BaseModel):
    """Input for validate_input tool."""
    data: Dict[str, Any]
    schema_name: str
    strict: bool = True


class ValidateInputOutput(BaseModel):
    """Output from validate_input tool."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    normalized: Dict[str, Any] = Field(default_factory=dict)


class FormatCurrencyInput(BaseModel):
    """Input for format_currency tool."""
    amount: float
    currency: str = "USD"
    locale: str = "en_US"
    decimals: int = 0


class FormatCurrencyOutput(BaseModel):
    """Output from format_currency tool."""
    formatted: str
    numeric: float
    currency: str
