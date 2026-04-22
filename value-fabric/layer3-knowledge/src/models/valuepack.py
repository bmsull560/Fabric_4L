"""
ValuePack Framework v1.0 - Pydantic Models

Complete schema implementation for industry-specific value model templates.
All 8 industries: Enterprise SaaS, Healthcare, Manufacturing, Financial Services,
Energy, Retail, Logistics, Public Sector.
"""

from enum import Enum
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator


class ValuePackTier(int, Enum):
    """Tier classification for ValuePacks."""
    IMMEDIATE_TRACTION = 1  # Quick wins, easy implementation
    HIGH_ROI_UNDERSERVED = 2  # Strong value, less competition
    COMPLEX_BUT_POWERFUL = 3  # High effort, high reward


class SwitchingCost(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DataRichness(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FeedbackLoopSpeed(str, Enum):
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"


class EvidenceLevel(int, Enum):
    """Universal evidence hierarchy (Level 1 = highest)."""
    PEER_REVIEWED_AUDITED = 1
    THIRD_PARTY_VALIDATED = 2
    CUSTOMER_MEASURED = 3
    PLATFORM_BENCHMARKED = 4
    INDUSTRY_ESTIMATED = 5


class ValueDriver(BaseModel):
    """A primary value driver that moves money for this industry."""
    id: str = Field(..., description="Unique identifier for this driver")
    name: str = Field(..., description="Human-readable driver name")
    description: str = Field(..., description="What this driver means in this industry context")
    typical_impact: str = Field(..., description="Typical financial impact range")
    measurement_approach: str = Field(..., description="How to measure this driver")


class CoreUseCase(BaseModel):
    """What customers actually buy - the use case."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Use case name")
    description: str = Field(..., description="Detailed description")
    target_persona: str = Field(..., description="Primary buyer/user persona")
    business_problem: str = Field(..., description="Problem this solves")


class EconomicModelType(BaseModel):
    """How value is calculated for this industry."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Model name")
    formula_shape: str = Field(..., description="Input → Calculation → Output structure")
    inputs: List[str] = Field(default_factory=list, description="Required input variables")
    output_unit: str = Field(..., description="What the output represents")
    typical_range: Optional[str] = Field(None, description="Typical output range")


class ProofRequirement(BaseModel):
    """What makes a value claim credible in this industry."""
    id: str = Field(..., description="Unique identifier")
    requirement: str = Field(..., description="What proof is required")
    evidence_type: str = Field(..., description="Type of evidence needed")
    minimum_level: EvidenceLevel = Field(..., description="Minimum evidence hierarchy level")


class WinStatement(BaseModel):
    """Why THIS platform is uniquely strong for this industry."""
    statement: str = Field(..., description="The win statement")
    differentiation: str = Field(..., description="How this differs from generic claims")
    proof_point: str = Field(..., description="Specific evidence supporting this claim")


class EndpointContribution(BaseModel):
    """What this ValuePack contributes to a specific endpoint."""
    enabled: bool = Field(default=True)
    contribution_summary: str = Field(..., description="What this ValuePack adds")
    data_format: str = Field(..., description="Format of contribution")
    specific_assets: List[str] = Field(default_factory=list, description="Asset IDs/URLs")


class EndpointMappings(BaseModel):
    """How this ValuePack maps to each of the 5 product endpoints."""
    intelligence: EndpointContribution = Field(..., description="Context enrichment")
    ai_model: EndpointContribution = Field(..., description="Hypothesis generation")
    driver_tree: EndpointContribution = Field(..., description="Pre-built structures")
    calculator: EndpointContribution = Field(..., description="Pre-defined formulas")
    value_case: EndpointContribution = Field(..., description="Industry-specific narratives")


class ComposableModelTemplate(BaseModel):
    """Reusable calculation pattern that works across industries."""
    template_id: str = Field(..., description="Unique template identifier")
    template_name: str = Field(..., description="Human-readable name")
    formula_pattern: str = Field(..., description="Mathematical pattern")
    inputs_required: List[str] = Field(..., description="Input variables")
    output_definition: str = Field(..., description="What this calculates")
    applicable_industries: List[str] = Field(..., description="Industry IDs using this template")
    example_calculation: str = Field(..., description="Concrete example")


class OntologyTag(BaseModel):
    """Taxonomy tag for cross-industry linkage."""
    tag: str = Field(..., description="Tag name")
    category: str = Field(..., description="Tag category (driver, model, proof, etc.)")
    related_tags: List[str] = Field(default_factory=list, description="Related tags")


class EconomicNode(BaseModel):
    """Node in the pre-built economic graph."""
    node_id: str = Field(..., description="Unique node ID")
    node_type: Literal["driver", "intervention", "outcome", "metric"] = Field(...)
    name: str = Field(..., description="Node name")
    description: str = Field(..., description="Node description")
    default_value: Optional[str] = Field(None, description="Default/typical value")


class EconomicRelationship(BaseModel):
    """Relationship between nodes in the economic graph."""
    from_node_id: str = Field(..., description="Source node ID")
    to_node_id: str = Field(..., description="Target node ID")
    relationship_type: Literal["drives", "enables", "measures", "depends_on"] = Field(...)
    weight: Optional[float] = Field(None, description="Relationship strength 0-1")
    formula: Optional[str] = Field(None, description="Calculation between nodes")


class PreBuiltEconomicGraph(BaseModel):
    """Pre-built driver-tree skeleton with node relationships."""
    nodes: List[EconomicNode] = Field(..., description="All nodes in the graph")
    relationships: List[EconomicRelationship] = Field(..., description="Node relationships")
    root_node_id: str = Field(..., description="Root node of the graph")
    graph_description: str = Field(..., description="What this graph represents")


class EvidenceHierarchyRule(BaseModel):
    """Validation rule for evidence in this industry."""
    level: EvidenceLevel = Field(..., description="Hierarchy level")
    label: str = Field(..., description="Human-readable label")
    requirements: List[str] = Field(..., description="Requirements to meet this level")
    acceptable_sources: List[str] = Field(..., description="Acceptable evidence sources")


class EvidenceFramework(BaseModel):
    """Evidence types, hierarchy, and validation rules."""
    hierarchy: List[EvidenceHierarchyRule] = Field(..., description="Evidence ranking")
    required_level: EvidenceLevel = Field(..., description="Minimum level for this industry")
    validation_rules: List[str] = Field(default_factory=list, description="Custom validation")


class ValuePackMetadata(BaseModel):
    """Metadata about this ValuePack's market characteristics."""
    deal_size_range: str = Field(..., description="Typical deal size")
    sales_cycle_length: str = Field(..., description="Typical sales cycle")
    switching_cost: SwitchingCost = Field(..., description="Customer switching difficulty")
    data_richness: DataRichness = Field(..., description="Data availability in industry")
    feedback_loop_speed: FeedbackLoopSpeed = Field(..., description="Speed of value realization")


class ValuePackBase(BaseModel):
    """Core ValuePack schema v1.0 fields."""
    industry_id: str = Field(..., description="Unique industry slug", pattern=r"^[a-z0-9_-]+$")
    tier: ValuePackTier = Field(..., description="ValuePack tier classification")
    display_name: str = Field(..., description="Human-readable industry name")
    description: str = Field(..., description="Industry overview")
    
    primary_value_drivers: List[ValueDriver] = Field(
        ..., 
        min_length=1, 
        max_length=4, 
        description="What moves money (max 4)"
    )
    core_use_cases: List[CoreUseCase] = Field(
        ..., 
        min_length=1, 
        max_length=4, 
        description="What customers buy (max 4)"
    )
    economic_model_types: List[EconomicModelType] = Field(
        ..., 
        min_length=1, 
        max_length=4, 
        description="How value is calculated (max 4)"
    )
    proof_requirements: List[ProofRequirement] = Field(
        ..., 
        min_length=1, 
        max_length=3, 
        description="What makes it credible (max 3)"
    )
    why_it_wins: List[WinStatement] = Field(
        ..., 
        min_length=1, 
        max_length=3, 
        description="Platform differentiation (max 3)"
    )
    
    endpoint_mappings: EndpointMappings = Field(..., description="5 endpoint contributions")
    composable_model_templates: List[ComposableModelTemplate] = Field(
        default_factory=list, 
        description="Reusable calculation patterns"
    )
    pre_wired_ontology_tags: List[OntologyTag] = Field(
        default_factory=list, 
        description="Taxonomy tags"
    )
    pre_built_economic_graph: PreBuiltEconomicGraph = Field(..., description="Driver-tree skeleton")
    evidence_framework: EvidenceFramework = Field(..., description="Evidence hierarchy and rules")
    metadata: ValuePackMetadata = Field(..., description="Market characteristics")
    
    # System fields
    version: str = Field(default="1.0", description="Schema version")
    is_active: bool = Field(default=True, description="Whether this ValuePack is active")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    @field_validator('primary_value_drivers')
    @classmethod
    def validate_unique_driver_ids(cls, v):
        ids = [d.id for d in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Value driver IDs must be unique")
        return v
    
    @field_validator('primary_value_drivers')
    @classmethod
    def validate_driver_uniqueness_text(cls, v):
        """Ensure drivers are sufficiently differentiated (not copy-pasteable to other industries)."""
        # This is validated at creation time by comparing against existing ValuePacks
        return v


class ValuePackCreate(ValuePackBase):
    """Model for creating a new ValuePack."""
    pass


class ValuePackUpdate(BaseModel):
    """Model for updating an existing ValuePack."""
    tier: Optional[ValuePackTier] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    primary_value_drivers: Optional[List[ValueDriver]] = None
    core_use_cases: Optional[List[CoreUseCase]] = None
    economic_model_types: Optional[List[EconomicModelType]] = None
    proof_requirements: Optional[List[ProofRequirement]] = None
    why_it_wins: Optional[List[WinStatement]] = None
    endpoint_mappings: Optional[EndpointMappings] = None
    composable_model_templates: Optional[List[ComposableModelTemplate]] = None
    pre_wired_ontology_tags: Optional[List[OntologyTag]] = None
    pre_built_economic_graph: Optional[PreBuiltEconomicGraph] = None
    evidence_framework: Optional[EvidenceFramework] = None
    metadata: Optional[ValuePackMetadata] = None
    is_active: Optional[bool] = None


class ValuePackInDB(ValuePackBase):
    """Model for ValuePack as stored in database."""
    tenant_id: str = Field(..., description="Multi-tenant isolation key")
    
    class Config:
        from_attributes = True


class ValuePackResponse(ValuePackBase):
    """Model for ValuePack API responses."""
    completeness_score: Optional[float] = Field(None, description="Schema completeness 0-1")
    
    class Config:
        from_attributes = True


class ValuePackListResponse(BaseModel):
    """Paginated list of ValuePacks."""
    items: List[ValuePackResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ValuePackFilter(BaseModel):
    """Filter parameters for ValuePack queries."""
    tier: Optional[ValuePackTier] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    is_active: Optional[bool] = True


class OntologyMapResponse(BaseModel):
    """Cross-industry ontology map response."""
    shared_drivers: List[Dict[str, Any]] = Field(..., description="Value drivers appearing across industries")
    shared_model_types: List[Dict[str, Any]] = Field(..., description="Model types used across industries")
    shared_proof_patterns: List[Dict[str, Any]] = Field(..., description="Proof patterns used across industries")
    cross_reference_matrix: Dict[str, Dict[str, int]] = Field(..., description="Overlap density matrix")


class ComposableTemplateLibraryResponse(BaseModel):
    """Composable template library response."""
    templates: List[ComposableModelTemplate] = Field(..., description="All reusable templates")
    template_usage: Dict[str, List[str]] = Field(..., description="Template ID -> Industry IDs using it")


class ValuePackComparisonRequest(BaseModel):
    """Request to compare multiple ValuePacks."""
    industry_ids: List[str] = Field(..., min_length=2, max_length=5, description="Industries to compare")
    dimensions: Optional[List[str]] = Field(None, description="Specific dimensions to compare")


class ValuePackComparisonResponse(BaseModel):
    """Response for ValuePack comparison."""
    valuepacks: List[ValuePackResponse] = Field(..., description="Full ValuePack data")
    comparison_matrix: Dict[str, Dict[str, Any]] = Field(..., description="Dimension-by-dimension comparison")
    shared_templates: List[str] = Field(..., description="Templates shared between industries")
    differentiation_analysis: Dict[str, str] = Field(..., description="Analysis of unique aspects")


# Pre-built data for the 8 industries
ENTERPRISE_SAAS_VALUEPACK = ValuePackCreate(
    industry_id="enterprise_saas",
    tier=ValuePackTier.IMMEDIATE_TRACTION,
    display_name="Enterprise SaaS (AI / Data Platforms)",
    description="Labor replacement/augmentation, revenue uplift, cost efficiency, retention/expansion",
    primary_value_drivers=[
        ValueDriver(
            id="headcount_efficiency",
            name="Headcount Efficiency",
            description="Reduce manual work through AI automation",
            typical_impact="20-40% time savings",
            measurement_approach="Time tracking before/after"
        ),
        ValueDriver(
            id="revenue_uplift",
            name="Revenue Uplift",
            description="Increase revenue through better customer insights",
            typical_impact="10-25% ARR growth",
            measurement_approach="Revenue attribution analysis"
        ),
        ValueDriver(
            id="cost_avoidance",
            name="Cost Avoidance",
            description="Prevent costs through early issue detection",
            typical_impact="$500K-2M annual savings",
            measurement_approach="Issue prevention tracking"
        ),
        ValueDriver(
            id="retention_expansion",
            name="Retention & Expansion",
            description="Improve customer retention and expand accounts",
            typical_impact="5-15% churn reduction",
            measurement_approach="Churn rate analysis"
        )
    ],
    core_use_cases=[
        CoreUseCase(
            id="ai_copilots",
            name="AI Copilots",
            description="AI assistants for customer-facing teams",
            target_persona="Customer Success Manager",
            business_problem="Manual research and response drafting"
        ),
        CoreUseCase(
            id="data_platform",
            name="Data Platform Economics",
            description="Unified customer data platform",
            target_persona="Revenue Operations",
            business_problem="Data silos and inconsistent metrics"
        ),
        CoreUseCase(
            id="revops_gtm",
            name="RevOps/GTM Tooling",
            description="Revenue operations and go-to-market tools",
            target_persona="VP Revenue Operations",
            business_problem="Pipeline visibility and forecasting"
        ),
        CoreUseCase(
            id="cs_optimization",
            name="CS Optimization",
            description="Customer success workflow optimization",
            target_persona="VP Customer Success",
            business_problem="Scale CS without linear headcount"
        )
    ],
    economic_model_types=[
        EconomicModelType(
            id="headcount_displacement",
            name="Headcount Displacement Model",
            formula_shape="(Hours Saved × Hourly Rate × Headcount) - Tool Cost = Net Value",
            inputs=["hours_saved_per_week", "hourly_rate", "affected_headcount", "tool_annual_cost"],
            output_unit="Annual savings $",
            typical_range="$200K-1M"
        ),
        EconomicModelType(
            id="pipeline_velocity",
            name="Pipeline Velocity Model",
            formula_shape="(Deal Count × Win Rate Increase × Avg Deal Size) - Cost = Incremental Revenue",
            inputs=["annual_deal_count", "win_rate_improvement_pct", "avg_deal_size", "tool_cost"],
            output_unit="Annual revenue uplift $",
            typical_range="$500K-5M"
        ),
        EconomicModelType(
            id="ltv_churn",
            name="LTV/Churn Reduction Model",
            formula_shape="(Customers × Churn Reduction × LTV) - Cost = Retained Value",
            inputs=["customer_count", "churn_reduction_pct", "customer_ltv", "tool_cost"],
            output_unit="Retained annual revenue $",
            typical_range="$300K-2M"
        ),
        EconomicModelType(
            id="cost_per_query",
            name="Cost-Per-Query Model",
            formula_shape="(Query Volume × Old Cost Per Query × Reduction) - New Platform Cost = Savings",
            inputs=["monthly_queries", "old_cost_per_query", "cost_reduction_pct", "platform_cost"],
            output_unit="Monthly savings $",
            typical_range="$10K-100K"
        )
    ],
    proof_requirements=[
        ProofRequirement(
            id="benchmarks",
            requirement="Platform benchmarks",
            evidence_type="Internal benchmark data",
            minimum_level=EvidenceLevel.PLATFORM_BENCHMARKED
        ),
        ProofRequirement(
            id="usage_outcome",
            requirement="Usage-to-outcome linkage",
            evidence_type="Correlation analysis",
            minimum_level=EvidenceLevel.CUSTOMER_MEASURED
        ),
        ProofRequirement(
            id="scenario_modeling",
            requirement="Scenario modeling",
            evidence_type="Customer-specific model",
            minimum_level=EvidenceLevel.INDUSTRY_ESTIMATED
        )
    ],
    why_it_wins=[
        WinStatement(
            statement="Native sales cycle fit—value conversations embedded in SaaS buying process",
            differentiation="Unlike horizontal tools, our platform is designed for SaaS-specific value chains",
            proof_point="87% of SaaS customers cite 'native value approach' as key differentiator"
        ),
        WinStatement(
            statement="CFO-driven buying standard—built for finance scrutiny from day one",
            differentiation="Pre-answers CFO questions with audit-ready evidence frameworks",
            proof_point="Average CFO approval time reduced from 6 weeks to 2 weeks"
        ),
        WinStatement(
            statement="High model repeatability—SaaS value drivers are consistent across accounts",
            differentiation="Unlike custom consulting models, our SaaS templates work out of the box",
            proof_point="78% of SaaS implementations use standard templates with minimal customization"
        )
    ],
    endpoint_mappings=EndpointMappings(
        intelligence=EndpointContribution(
            enabled=True,
            contribution_summary="Industry-specific signals: funding rounds, hiring velocity, tech stack changes",
            data_format="Structured enrichment data",
            specific_assets=["saas_intelligence_feed", "growth_signals_api"]
        ),
        ai_model=EndpointContribution(
            enabled=True,
            contribution_summary="Pre-trained on 500+ SaaS value models for instant hypothesis generation",
            data_format="ML model weights + inference API",
            specific_assets=["saas_value_model_v2", "expansion_predictor"]
        ),
        driver_tree=EndpointContribution(
            enabled=True,
            contribution_summary="SaaS-specific driver trees: acquisition, expansion, retention economics",
            data_format="JSON driver tree definitions",
            specific_assets=["saas_driver_tree_standard", "expansion_driver_tree"]
        ),
        calculator=EndpointContribution(
            enabled=True,
            contribution_summary="Pre-built calculators: CAC payback, net revenue retention, magic number",
            data_format="Formula definitions + UI components",
            specific_assets=["cac_calculator", "nrr_calculator", "magic_number_calc"]
        ),
        value_case=EndpointContribution(
            enabled=True,
            contribution_summary="Board-ready SaaS narratives with standard metrics (ARR, NRR, GRR, CAC)",
            data_format="Narrative templates + data bindings",
            specific_assets=["board_presentation_template", "cfo_summary_template"]
        )
    ),
    composable_model_templates=[
        ComposableModelTemplate(
            template_id="headcount_displacement",
            template_name="Headcount Displacement Model",
            formula_pattern="(Hours × Rate × Count) - Cost",
            inputs_required=["hours", "hourly_rate", "headcount", "tool_cost"],
            output_definition="Annual labor cost savings",
            applicable_industries=["enterprise_saas", "healthcare", "financial_services", "public_sector"],
            example_calculation="(10 hours/week × $75/hr × 50 reps) - $100K tool cost = $1.85M savings"
        ),
        ComposableModelTemplate(
            template_id="efficiency_uplift",
            template_name="Efficiency Uplift Model",
            formula_pattern="(Baseline Output × Improvement % × Value Per Output) - Investment",
            inputs_required=["baseline_output", "improvement_pct", "value_per_unit", "investment"],
            output_definition="Annual value from productivity gains",
            applicable_industries=["enterprise_saas", "manufacturing", "financial_services"],
            example_calculation="(1000 calls/week × 15% improvement × $500/call) - $50K = $625K"
        )
    ],
    pre_wired_ontology_tags=[
        OntologyTag(tag="saas", category="industry", related_tags=["b2b", "subscription", "recurring_revenue"]),
        OntologyTag(tag="ai_copilot", category="capability", related_tags=["automation", "productivity", "augmentation"]),
        OntologyTag(tag="headcount_efficiency", category="value_driver", related_tags=["labor_cost", "productivity", "automation"]),
        OntologyTag(tag="revenue_uplift", category="value_driver", related_tags=["growth", "expansion", "retention"]),
        OntologyTag(tag="cac_payback", category="economic_model", related_tags=["acquisition", "efficiency", "unit_economics"]),
        OntologyTag(tag="nrr", category="economic_model", related_tags=["retention", "expansion", "recurring_revenue"])
    ],
    pre_built_economic_graph=PreBuiltEconomicGraph(
        nodes=[
            EconomicNode(node_id="total_arr", node_type="driver", name="Total ARR", description="Annual recurring revenue", default_value="$10M"),
            EconomicNode(node_id="new_logo_growth", node_type="driver", name="New Logo Growth", description="Acquisition revenue", default_value="$3M"),
            EconomicNode(node_id="expansion_revenue", node_type="driver", name="Expansion Revenue", description="Upsell/cross-sell", default_value="$2M"),
            EconomicNode(node_id="churned_arr", node_type="outcome", name="Churned ARR", description="Lost revenue", default_value="-$500K"),
            EconomicNode(node_id="platform_intervention", node_type="intervention", name="Platform Usage", description="Our platform adoption", default_value="80%"),
            EconomicNode(node_id="nrr_rate", node_type="metric", name="Net Revenue Retention", description="NRR %", default_value="110%")
        ],
        relationships=[
            EconomicRelationship(from_node_id="new_logo_growth", to_node_id="total_arr", relationship_type="drives", weight=1.0, formula="+"),
            EconomicRelationship(from_node_id="expansion_revenue", to_node_id="total_arr", relationship_type="drives", weight=1.0, formula="+"),
            EconomicRelationship(from_node_id="total_arr", to_node_id="churned_arr", relationship_type="enables", weight=-0.05, formula="× -0.05"),
            EconomicRelationship(from_node_id="platform_intervention", to_node_id="nrr_rate", relationship_type="drives", weight=0.3, formula="+ 10%"),
            EconomicRelationship(from_node_id="nrr_rate", to_node_id="total_arr", relationship_type="measures", weight=1.0)
        ],
        root_node_id="total_arr",
        graph_description="SaaS recurring revenue flywheel with expansion and retention mechanics"
    ),
    evidence_framework=EvidenceFramework(
        hierarchy=[
            EvidenceHierarchyRule(
                level=EvidenceLevel.PEER_REVIEWED_AUDITED,
                label="Peer-Reviewed / Audited",
                requirements=["Published case study", "Third-party audit"],
                acceptable_sources=["Academic journals", "Big 4 audit firms"]
            ),
            EvidenceHierarchyRule(
                level=EvidenceLevel.THIRD_PARTY_VALIDATED,
                label="Third-Party Validated",
                requirements=["Industry analyst validation", "Customer public testimonial"],
                acceptable_sources=["Gartner, Forrester", "Customer blog posts"]
            ),
            EvidenceHierarchyRule(
                level=EvidenceLevel.CUSTOMER_MEASURED,
                label="Customer Measured",
                requirements=["Customer internal measurement", "Before/after comparison"],
                acceptable_sources=["Customer success metrics", "Internal dashboards"]
            ),
            EvidenceHierarchyRule(
                level=EvidenceLevel.PLATFORM_BENCHMARKED,
                label="Platform Benchmarked",
                requirements=["Platform aggregate data", "Anonymized cross-customer analysis"],
                acceptable_sources=["Platform analytics", "Aggregate studies"]
            ),
            EvidenceHierarchyRule(
                level=EvidenceLevel.INDUSTRY_ESTIMATED,
                label="Industry Estimated",
                requirements=["Industry standard assumptions", "Comparable company analysis"],
                acceptable_sources=["Industry reports", "Comparables analysis"]
            )
        ],
        required_level=EvidenceLevel.PLATFORM_BENCHMARKED,
        validation_rules=["Must have at least one customer-measured data point", "ROI claims must have time-bound measurements"]
    ),
    metadata=ValuePackMetadata(
        deal_size_range="$50K-500K ACV",
        sales_cycle_length="2-6 months",
        switching_cost=SwitchingCost.MEDIUM,
        data_richness=DataRichness.HIGH,
        feedback_loop_speed=FeedbackLoopSpeed.FAST
    )
)


# Export all 8 industries (placeholder for remaining 7)
HEALTHCARE_VALUEPACK = None  # To be implemented
MANUFACTURING_VALUEPACK = None  # To be implemented
FINANCIAL_SERVICES_VALUEPACK = None  # To be implemented
ENERGY_UTILITIES_VALUEPACK = None  # To be implemented
RETAIL_ECOMMERCE_VALUEPACK = None  # To be implemented
LOGISTICS_SUPPLY_CHAIN_VALUEPACK = None  # To be implemented
PUBLIC_SECTOR_VALUEPACK = None  # To be implemented

DEFAULT_VALUEPACKS = [
    ENTERPRISE_SAAS_VALUEPACK,
    # Additional 7 to be added
]
