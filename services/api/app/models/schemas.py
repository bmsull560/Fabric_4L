from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

# ============================================================================
# Shared primitives
# ============================================================================

class AuditMeta(BaseModel):
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Literal["agent", "user", "system"] = "system"
    review_state: Literal["draft", "needs_review", "approved", "modified", "rejected", "published"] = "draft"
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    source: str = "system"

# ============================================================================
# Tenant & User
# ============================================================================

class Tenant(BaseModel):
    id: str
    name: str
    default_value_pack_id: Optional[str] = None
    plan: Literal["free", "team", "enterprise"] = "team"
    status: Literal["active", "suspended", "trial"] = "active"

class User(BaseModel):
    id: str
    tenant_id: str
    email: str
    name: str
    role: Literal["admin", "editor", "viewer"] = "editor"

# ============================================================================
# Account & Stakeholder
# ============================================================================

class Account(BaseModel):
    id: str
    tenant_id: str
    name: str
    industry: str
    segment: Optional[str] = None
    website: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    crm_stage: Optional[str] = None
    value_pack_id: Optional[str] = None
    summary: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Stakeholder(BaseModel):
    id: str
    account_id: str
    tenant_id: str
    name: str
    title: str
    persona_id: Optional[str] = None
    department: Optional[str] = None
    priorities: List[str] = Field(default_factory=list)
    pains: List[str] = Field(default_factory=list)
    influence_level: Literal["low", "medium", "high"] = "medium"
    decision_role: Literal["economic", "technical", "user", "champion", "none"] = "none"

# ============================================================================
# Value Pack
# ============================================================================

class ValuePack(BaseModel):
    id: str
    name: str
    industry: str
    description: Optional[str] = None
    status: Literal["draft", "published", "deprecated"] = "published"
    version: str = "1.0.0"
    formula_count: int = 0
    variable_count: int = 0
    entity_count: int = 0
    tags: List[str] = Field(default_factory=list)
    path: Optional[str] = None

# ============================================================================
# Signal & Evidence
# ============================================================================

class Signal(BaseModel):
    id: str
    account_id: str
    tenant_id: str
    source_document_id: Optional[str] = None
    signal_type: Literal["pain", "opportunity", "risk", "trend"] = "pain"
    title: str
    description: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    extracted_text: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    mapped_driver_ids: List[str] = Field(default_factory=list)
    status: Literal["new", "reviewed", "approved", "rejected"] = "new"
    audit: AuditMeta = Field(default_factory=AuditMeta)

class Evidence(BaseModel):
    id: str
    account_id: str
    tenant_id: str
    source_document_id: Optional[str] = None
    title: str
    excerpt: Optional[str] = None
    source_type: Literal["crm", "call_transcript", "pdf", "web", "case_study", "product_doc", "spreadsheet", "api"] = "web"
    url: Optional[str] = None
    page: Optional[int] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    tags: List[str] = Field(default_factory=list)
    supports_claim_ids: List[str] = Field(default_factory=list)
    audit: AuditMeta = Field(default_factory=AuditMeta)

# ============================================================================
# Hypothesis & Driver Tree
# ============================================================================

class ValueHypothesis(BaseModel):
    id: str
    account_id: str
    tenant_id: str
    title: str
    persona_id: Optional[str] = None
    driver_ids: List[str] = Field(default_factory=list)
    pain_signal_ids: List[str] = Field(default_factory=list)
    claim: Optional[str] = None
    expected_outcome: Optional[str] = None
    discovery_questions: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    status: Literal["generated", "approved", "modified", "skipped", "rejected"] = "generated"
    audit: AuditMeta = Field(default_factory=AuditMeta)

class ValueLever(BaseModel):
    id: str
    driver_id: str
    name: str
    description: Optional[str] = None
    formula_id: Optional[str] = None
    baseline_metric: Optional[float] = None
    target_metric: Optional[float] = None
    unit: Optional[str] = None
    assumption_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)

class ValueDriver(BaseModel):
    id: str
    account_id: str
    tenant_id: str
    name: str
    category: Literal["revenue_uplift", "cost_savings", "risk_reduction"] = "revenue_uplift"
    description: Optional[str] = None
    linked_signals: List[str] = Field(default_factory=list)
    linked_evidence: List[str] = Field(default_factory=list)
    levers: List[ValueLever] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    audit: AuditMeta = Field(default_factory=AuditMeta)

# ============================================================================
# Formula & Scenario
# ============================================================================

class FormulaInput(BaseModel):
    name: str
    display_name: str
    type: Literal["currency", "integer", "float", "percent", "string"] = "float"
    unit: Optional[str] = None
    default_value: Optional[float] = None
    valid_range: Optional[Dict[str, float]] = None
    description: Optional[str] = None

class FormulaOutput(BaseModel):
    name: str
    unit: Optional[str] = None
    description: Optional[str] = None

class Formula(BaseModel):
    id: str
    value_pack_id: Optional[str] = None
    name: str
    category: Literal["revenue_uplift", "cost_savings", "risk_reduction", "productivity"] = "revenue_uplift"
    expression: str
    inputs: List[FormulaInput] = Field(default_factory=list)
    outputs: List[FormulaOutput] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    benchmark_ids: List[str] = Field(default_factory=list)
    validation_status: Literal["draft", "validated", "approved", "deprecated"] = "draft"
    version: str = "1.0.0"
    audit: AuditMeta = Field(default_factory=AuditMeta)

class Scenario(BaseModel):
    id: str
    account_id: str
    tenant_id: str
    name: Literal["conservative", "expected", "optimistic", "custom"] = "expected"
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    roi_summary: Optional[Dict[str, Any]] = None
    payback_months: Optional[float] = None
    npv: Optional[float] = None
    irr: Optional[float] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)

# ============================================================================
# ROI & Business Case
# ============================================================================

class ROICalculation(BaseModel):
    id: str
    account_id: str
    tenant_id: str
    scenario_id: str
    revenue_uplift: float = 0.0
    cost_savings: float = 0.0
    risk_reduction: float = 0.0
    total_benefit: float = 0.0
    solution_cost: float = 0.0
    net_benefit: float = 0.0
    roi_percent: float = 0.0
    payback_months: float = 0.0
    calculation_trace: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    assumption_ids: List[str] = Field(default_factory=list)
    audit: AuditMeta = Field(default_factory=AuditMeta)

class BusinessCase(BaseModel):
    id: str
    account_id: str
    tenant_id: str
    title: str
    executive_summary: Optional[str] = None
    value_narrative: Optional[str] = None
    roi_calculation_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommendation: Optional[str] = None
    status: Literal["draft", "review", "approved", "published", "archived"] = "draft"
    audit: AuditMeta = Field(default_factory=AuditMeta)

# ============================================================================
# Ground Truth & Governance
# ============================================================================

class GroundTruthObject(BaseModel):
    id: str
    tenant_id: str
    object_type: str
    object_id: str
    claim: str
    validated_by: Optional[str] = None
    validation_status: Literal["pending", "verified", "disputed", "deprecated"] = "pending"
    evidence_ids: List[str] = Field(default_factory=list)
    review_decision_ids: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ReviewDecision(BaseModel):
    id: str
    tenant_id: str
    object_type: str
    object_id: str
    decision: Literal["approve", "reject", "modify", "escalate"] = "approve"
    reason: Optional[str] = None
    reviewer_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AuditLogEvent(BaseModel):
    id: str
    tenant_id: str
    actor_type: Literal["user", "agent", "system"] = "system"
    actor_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GovernanceGate(BaseModel):
    id: str
    tenant_id: str
    name: str
    category: Literal["architecture", "security", "tenant_isolation", "contract_drift", "observability", "agent_safety", "smoke_tests", "data_provenance", "human_review"] = "security"
    status: Literal["pending", "passed", "failed", "waived"] = "pending"
    evidence: Optional[str] = None
    checked_at: Optional[str] = None

# ============================================================================
# Agents
# ============================================================================

class ToolResult(BaseModel):
    id: str
    agent_run_id: str
    tool_name: str
    status: Literal["success", "error", "partial", "skipped"] = "success"
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

class AgentRun(BaseModel):
    id: str
    tenant_id: str
    account_id: Optional[str] = None
    workflow_type: str
    status: Literal["pending", "running", "paused", "completed", "failed", "cancelled"] = "pending"
    current_step: Optional[str] = None
    checkpoint_id: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    tool_results: List[ToolResult] = Field(default_factory=list)
    review_required: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
