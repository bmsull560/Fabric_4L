"""Core ontology models for Value Fabric extraction pipeline.

Defines the 4 core entity types: Capability, UseCase, Persona, ValueDriver
using Pydantic v2 with strict validation.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4, UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class RoleType(str, Enum):
    """Valid persona role types in the enterprise buying process."""
    ECONOMIC_BUYER = "economic_buyer"
    OPERATIONAL_USER = "operational_user"
    STAKEHOLDER = "stakeholder"


class ValueCategory(str, Enum):
    """Categories of value drivers in enterprise software."""
    REVENUE = "revenue"
    COST = "cost"
    RISK = "risk"
    CAPITAL = "capital"


class Capability(BaseModel):
    """A technical capability or feature of a product/service.
    
    Capabilities are the building blocks that enable use cases and
    contribute to value drivers.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Human-readable capability name
        description: Detailed description of what the capability does
        technical_features: List of specific technical features
        api_endpoints: List of API endpoints if applicable
        integrations: List of supported integrations
        apqc_mapping: APQC Process Classification Framework code
        source_refs: URLs where this capability was extracted from
        confidence: LLM confidence score (0.0-1.0)
        extracted_at: Timestamp of extraction
        extraction_job_id: Reference to extraction job
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    technical_features: List[str] = Field(default_factory=list)
    api_endpoints: List[str] = Field(default_factory=list)
    integrations: List[str] = Field(default_factory=list)
    apqc_mapping: Optional[str] = None
    source_refs: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_job_id: Optional[str] = None
    
    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Normalize name for matching while preserving original in display."""
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Real-Time Data Ingestion",
                "description": "Stream data from multiple sources with sub-second latency",
                "technical_features": [
                    "Kafka streaming",
                    "Change data capture",
                    "Schema registry"
                ],
                "confidence": 0.92
            }
        }


class UseCase(BaseModel):
    """A business use case that solves a specific problem.
    
    Use cases represent how capabilities are applied to solve business
    problems for specific personas.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Human-readable use case name
        description: Detailed description of the use case
        industry_context: Industries where this applies
        required_capabilities: IDs of capabilities needed
        workflow_steps: Ordered steps in the workflow
        kpis: Key performance indicators for this use case
        confidence: LLM confidence score
        extracted_at: Timestamp of extraction
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    industry_context: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    workflow_steps: List[str] = Field(default_factory=list)
    kpis: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_job_id: Optional[str] = None

    @field_validator("required_capabilities")
    @classmethod
    def validate_capability_refs(cls, v: List[str]) -> List[str]:
        """Ensure all capability references are valid UUID strings."""
        for ref in v:
            try:
                UUID(ref)
            except ValueError:
                raise ValueError(f"Invalid capability reference: {ref}")
        return v


class Persona(BaseModel):
    """A stakeholder or user persona in the enterprise buying process.
    
    Personas represent the people involved in decisions, their pain points,
    and what drives value for them.
    
    Attributes:
        id: Unique identifier (UUID)
        role_type: Type of role in buying process
        title: Job title
        department: Department/organization
        pain_points: List of problems this persona faces
        success_metrics: How they measure success
        influenced_by: Other persona IDs that influence this one
        confidence: LLM confidence score
        extracted_at: Timestamp of extraction
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    role_type: RoleType
    title: str = Field(..., min_length=1, max_length=255)
    department: str = Field(..., min_length=1, max_length=255)
    pain_points: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    influenced_by: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_job_id: Optional[str] = None

    @field_validator("influenced_by")
    @classmethod
    def validate_persona_refs(cls, v: List[str]) -> List[str]:
        """Ensure all persona references are valid UUID strings."""
        for ref in v:
            try:
                UUID(ref)
            except ValueError:
                raise ValueError(f"Invalid persona reference: {ref}")
        return v


class ValueDriver(BaseModel):
    """A quantifiable business value that drives ROI.
    
    Value drivers connect capabilities to business outcomes with
    mathematical formulas for calculating ROI.
    
    Attributes:
        id: Unique identifier (UUID)
        category: Type of value (revenue, cost, risk, capital)
        name: Human-readable value driver name
        description: Detailed description
        metrics: List of specific metrics
        formula_string: Mathematical formula for calculation
        unit: Unit of measurement (USD, percentage, hours, etc.)
        time_to_value: Expected time to realize value
        confidence: LLM confidence score
        extracted_at: Timestamp of extraction
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: ValueCategory
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    metrics: List[str] = Field(default_factory=list)
    formula_string: Optional[str] = None
    unit: str = Field(..., min_length=1, max_length=50)
    time_to_value: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_job_id: Optional[str] = None
    
    @field_validator("formula_string")
    @classmethod
    def validate_formula(cls, v: Optional[str]) -> Optional[str]:
        """Basic validation that formula uses only allowed characters."""
        if v is None:
            return v
        # Allow: variables in {}, numbers, operators, parentheses, whitespace
        allowed = set("0123456789+-*/().{}_ ")
        invalid_chars = set(v) - allowed
        if invalid_chars:
            raise ValueError(
                f"Formula contains invalid characters: {invalid_chars}. "
                f"Only numbers, operators, parentheses, and {{variables}} allowed."
            )
        return v


class Feature(BaseModel):
    """A product feature that implements a capability.
    
    Features represent concrete product functionality that delivers
    one or more capabilities. They sit between raw capabilities
    and user-facing use cases in the ontology hierarchy.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Human-readable feature name
        description: Detailed description of what the feature does
        parent_capability_id: ID of the capability this feature implements
        technical_spec: Technical specification details
        implementation_status: Current status (planned, beta, ga, deprecated)
        source_refs: URLs where this feature was extracted from
        confidence: LLM confidence score (0.0-1.0)
        extracted_at: Timestamp of extraction
        extraction_job_id: Reference to extraction job
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    parent_capability_id: Optional[str] = None
    technical_spec: Optional[str] = None
    implementation_status: str = Field(default="ga", pattern="^(planned|beta|ga|deprecated)$")
    source_refs: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_job_id: Optional[str] = None
    
    @field_validator("parent_capability_id")
    @classmethod
    def validate_capability_ref(cls, v: Optional[str]) -> Optional[str]:
        """Ensure capability reference is valid UUID if provided."""
        if v is None:
            return v
        try:
            UUID(v)
        except ValueError:
            raise ValueError(f"Invalid capability reference: {v}")
        return v
    
    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Normalize name for matching while preserving original in display."""
        return v.strip()


class ExtractionResult(BaseModel):
    """Complete result from an extraction job.
    
    Contains all entities and relationships extracted from a document
    with provenance metadata.
    """
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    source_url: str
    source_content_id: Optional[str] = None
    capabilities: List[Capability] = Field(default_factory=list)
    use_cases: List[UseCase] = Field(default_factory=list)
    personas: List[Persona] = Field(default_factory=list)
    value_drivers: List[ValueDriver] = Field(default_factory=list)
    features: List[Feature] = Field(default_factory=list)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    chunks_processed: int = 0
    errors: List[str] = Field(default_factory=list)

    def get_all_entities(self) -> List[BaseModel]:
        """Return all extracted entities as a flat list."""
        return (
            self.capabilities +
            self.use_cases +
            self.personas +
            self.value_drivers +
            self.features
        )
    
    def get_entity_by_id(self, entity_id: str) -> Optional[BaseModel]:
        """Find an entity by its ID across all types."""
        for entity in self.get_all_entities():
            if entity.id == entity_id:
                return entity
        return None
