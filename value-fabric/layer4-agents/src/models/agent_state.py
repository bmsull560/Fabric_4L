"""Agent state definitions for LangGraph workflows.

Defines typed state schemas for all workflow types in Layer 4.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowType(str, Enum):
    """Types of supported workflows per spec."""
    # Existing workflows
    ROI_CALCULATOR = "roi_calculator"
    WHITESPACE_ANALYSIS = "whitespace_analysis"
    BUSINESS_CASE = "business_case"
    ORCHESTRATOR = "orchestrator"
    
    # Additional spec workflows
    WHITESPACE_ANALYSIS_WORKFLOW = "whitespace_analysis"  # Full workflow alias
    BUSINESS_CASE_GENERATION = "business_case_generation"
    DOCUMENT_INGESTION = "document_ingestion"
    FINANCIAL_EXTRACTION = "financial_extraction"
    VALUE_TREE_PROJECTION = "value_tree_projection"


class WorkflowNodeType(str, Enum):
    """Workflow node/states per spec definition."""
    # Document Ingestion
    DOCUMENT_INGESTION = "DOCUMENT_INGESTION"
    
    # Financial Extraction
    FINANCIAL_EXTRACTION = "FINANCIAL_EXTRACTION"
    
    # Value Tree Projection
    VALUE_TREE_PROJECTION = "VALUE_TREE_PROJECTION"
    
    # Whitespace Analysis
    WHITESPACE_IDENTIFICATION = "WHITESPACE_IDENTIFICATION"
    ACCOUNT_PLAN_GENERATION = "ACCOUNT_PLAN_GENERATION"
    
    # Business Case Generation
    OPPORTUNITY_EVALUATION = "OPPORTUNITY_EVALUATION"
    FORMULA_RETRIEVAL = "FORMULA_RETRIEVAL"
    METRIC_SUBSTITUTION = "METRIC_SUBSTITUTION"
    ROI_COMPUTATION = "ROI_COMPUTATION"
    SENSITIVITY_ANALYSIS = "SENSITIVITY_ANALYSIS"
    NARRATIVE_SYNTHESIS = "NARRATIVE_SYNTHESIS"
    OUTPUT_GENERATION = "OUTPUT_GENERATION"
    
    # Provenance
    PROVENANCE_RECORDING = "PROVENANCE_RECORDING"
    
    # Terminal states
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BaseAgentState(BaseModel):
    """Base state shared across all workflows.
    
    Attributes:
        workflow_id: Unique identifier for this workflow instance
        workflow_type: Type of workflow being executed
        status: Current execution status
        current_node: Name of the currently executing node
        input_data: Initial input parameters
        output_data: Accumulated results
        errors: List of errors encountered
        metadata: Additional execution metadata
    """
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_type: WorkflowType
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_node: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ROIInputData(BaseModel):
    """Input data for ROI calculation workflow.
    
    Attributes:
        prospect_id: CRM identifier for the prospect
        value_driver_ids: Value drivers to calculate ROI for
        prospect_data: Prospect-specific variables
        industry_vertical: Industry for benchmark lookup
        company_size: Company size category
    """
    prospect_id: str
    value_driver_ids: List[str]
    prospect_data: Dict[str, float] = Field(default_factory=dict)
    industry_vertical: Optional[str] = None
    company_size: Optional[str] = None
    use_benchmarks: bool = True
    
    @field_validator("value_driver_ids")
    @classmethod
    def validate_non_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one value_driver_id is required")
        return v


class ROIResult(BaseModel):
    """Result of a single ROI calculation.
    
    Attributes:
        value_driver_id: ID of the value driver calculated
        value_driver_name: Human-readable name
        formula: Formula string used
        substituted_formula: Formula with values substituted
        result: Calculated ROI value
        unit: Unit of measurement (USD, %, etc.)
        confidence: Confidence score 0.0-1.0
        variables_used: Variables and their values
        missing_variables: Variables that couldn't be resolved
    """
    value_driver_id: str
    value_driver_name: str
    formula: str
    substituted_formula: str
    result: float
    unit: str
    confidence: float = Field(ge=0.0, le=1.0)
    variables_used: Dict[str, float] = Field(default_factory=dict)
    missing_variables: List[str] = Field(default_factory=list)
    benchmark_comparison: Optional[Dict[str, Any]] = None


class ROIAgentState(BaseAgentState):
    """State for ROI Calculator workflow.
    
    Extends base state with ROI-specific fields.
    """
    workflow_type: WorkflowType = WorkflowType.ROI_CALCULATOR
    roi_input: Optional[ROIInputData] = None
    prospect_data_enriched: Dict[str, Any] = Field(default_factory=dict)
    benchmarks_fetched: Dict[str, Any] = Field(default_factory=dict)
    calculation_results: List[ROIResult] = Field(default_factory=list)
    aggregated_roi: Optional[Dict[str, Any]] = None


class WhitespaceInputData(BaseModel):
    """Input data for whitespace analysis workflow.
    
    Attributes:
        prospect_id: CRM identifier for the prospect
        prospect_needs: Description of prospect's stated needs
        solution_capabilities: Capabilities to match against
        analysis_depth: Level of analysis detail
    """
    prospect_id: str
    prospect_needs: str = Field(..., min_length=10)
    solution_capabilities: Optional[List[str]] = None
    analysis_depth: str = "standard"  # "quick", "standard", "deep"
    include_competitive: bool = True
    
    @field_validator("analysis_depth")
    @classmethod
    def validate_depth(cls, v: str) -> str:
        valid = {"quick", "standard", "deep"}
        if v not in valid:
            raise ValueError(f"analysis_depth must be one of {valid}")
        return v


class GapAnalysis(BaseModel):
    """Identified gap between need and capability.
    
    Attributes:
        need_statement: The prospect need identified
        matched_capability: Best matching capability (if any)
        match_score: Similarity score 0.0-1.0
        gap_type: Type of gap identified
        impact: Business impact assessment
        recommendation: Suggested action
    """
    need_statement: str
    matched_capability: Optional[str] = None
    match_score: float = Field(ge=0.0, le=1.0)
    gap_type: str  # "coverage", "capability", "maturity", "none"
    impact: str = "medium"  # "low", "medium", "high"
    recommendation: str


class WhitespaceAgentState(BaseAgentState):
    """State for Whitespace Analysis workflow."""
    workflow_type: WorkflowType = WorkflowType.WHITESPACE_ANALYSIS
    whitespace_input: Optional[WhitespaceInputData] = None
    extracted_needs: List[str] = Field(default_factory=list)
    capabilities_queried: List[Dict[str, Any]] = Field(default_factory=list)
    gap_analysis: List[GapAnalysis] = Field(default_factory=list)
    opportunity_score: Optional[float] = None
    recommendations: List[str] = Field(default_factory=list)


class BusinessCaseSection(BaseModel):
    """Section of a generated business case.
    
    Attributes:
        title: Section heading
        content: Generated text content
        charts: List of chart data for this section
        tables: List of table data for this section
    """
    title: str
    content: str
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)


class BusinessCaseInputData(BaseModel):
    """Input data for business case generation workflow.
    
    Attributes:
        prospect_id: CRM identifier
        opportunity_id: CRM opportunity identifier
        sections_requested: Which sections to include
        output_format: Desired output format
    """
    prospect_id: str
    opportunity_id: Optional[str] = None
    sections_requested: List[str] = Field(default_factory=lambda: [
        "executive_summary",
        "current_state",
        "proposed_solution",
        "roi_analysis",
        "implementation",
        "next_steps"
    ])
    output_format: str = "pdf"  # "pdf", "docx", "html"
    custom_inputs: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("output_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        valid = {"pdf", "docx", "html"}
        if v not in valid:
            raise ValueError(f"output_format must be one of {valid}")
        return v


class BusinessCaseAgentState(BaseAgentState):
    """State for Business Case Generator workflow."""
    workflow_type: WorkflowType = WorkflowType.BUSINESS_CASE
    case_input: Optional[BusinessCaseInputData] = None
    sections_generated: List[BusinessCaseSection] = Field(default_factory=list)
    roi_results: Optional[Dict[str, Any]] = None
    assembled_document: Optional[bytes] = None
    document_url: Optional[str] = None


class OrchestratorAgentState(BaseAgentState):
    """State for Multi-Agent Orchestrator workflow."""
    workflow_type: WorkflowType = WorkflowType.ORCHESTRATOR
    user_intent: Optional[str] = None
    identified_workflows: List[str] = Field(default_factory=list)
    sub_workflow_results: List[Dict[str, Any]] = Field(default_factory=list)
    aggregated_response: Optional[str] = None
    suggested_actions: List[str] = Field(default_factory=list)


# Union type for all workflow states
AgentState = ROIAgentState | WhitespaceAgentState | BusinessCaseAgentState | OrchestratorAgentState
