"""Pydantic models for Layer 3 API."""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


# Health Check
class DependencyStatus(BaseModel):
    """Status of a service dependency."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Dependency name"
    )
    status: Literal["healthy", "unhealthy", "degraded"] = Field(
        ..., description="Current status"
    )
    response_time_ms: float | None = Field(
        None, ge=0, description="Response time in milliseconds"
    )
    error: str | None = Field(
        None, max_length=500, description="Error message if unhealthy"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional status details"
    )


class ServiceMetrics(BaseModel):
    """System and service performance metrics."""

    uptime_seconds: float = Field(..., ge=0, description="Service uptime in seconds")
    memory_usage_mb: float | None = Field(
        None, ge=0, description="Memory usage in MB"
    )
    cpu_percent: float | None = Field(
        None, ge=0, le=100, description="CPU usage percentage"
    )
    active_connections: int = Field(
        ..., ge=0, description="Number of active connections"
    )
    total_requests: int = Field(..., ge=0, description="Total requests processed")
    error_rate_percent: float = Field(
        ..., ge=0, le=100, description="Error rate percentage"
    )


class HealthResponse(BaseModel):
    """Basic health check response."""

    status: Literal["healthy", "unhealthy", "degraded"] = Field(
        ..., description="Overall service status"
    )
    version: str = Field(..., min_length=1, max_length=20, description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )
    uptime_seconds: float = Field(..., ge=0, description="Service uptime in seconds")
    dependencies: list[DependencyStatus] = Field(..., description="Dependency statuses")
    metrics: ServiceMetrics = Field(..., description="Service metrics")
    neo4j: dict[str, Any] = Field(..., description="Neo4j health information")
    schema_status: dict[str, Any] = Field(..., description="Database schema status")


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with system information."""

    status: Literal["healthy", "unhealthy", "degraded"] = Field(
        ..., description="Overall service status"
    )
    version: str = Field(..., min_length=1, max_length=20, description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )
    uptime_seconds: float = Field(..., ge=0, description="Service uptime in seconds")
    dependencies: list[DependencyStatus] = Field(..., description="Dependency statuses")
    metrics: ServiceMetrics = Field(..., description="Service metrics")
    neo4j: dict[str, Any] = Field(..., description="Neo4j health information")
    schema_status: dict[str, Any] = Field(..., description="Database schema status")
    system_info: dict[str, Any] = Field(..., description="System information")
    configuration: dict[str, Any] = Field(
        ..., description="Non-sensitive configuration"
    )


# Ingestion Models
class IngestRequest(BaseModel):
    """Request for ingesting RDF data into the knowledge graph."""

    rdf_data: str = Field(
        ...,
        min_length=1,
        max_length=1000000,
        description="RDF/Turtle data from Layer 2 (max 1MB)",
        examples=["<http://example.com/entity1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/Capability> ."],
    )
    source_id: str = Field(
        ..., min_length=1, max_length=255, description="Source document ID", examples=["doc-12345"]
    )
    extraction_job_id: str = Field(
        ..., min_length=1, max_length=255, description="Extraction job ID from Layer 2", examples=["job-67890"]
    )
    content_hash: str | None = Field(
        None, min_length=32, max_length=128, description="SHA-256 hash for change detection", examples=["a1b2c3d4e5f6..."]
    )
    tenant_id: str | None = Field(
        None, min_length=1, max_length=255, description="Tenant ID for data isolation (extracted from X-Tenant-ID header if not provided)", examples=["tenant-abc123"]
    )

    @field_validator("content_hash")
    @classmethod
    def validate_content_hash(cls, v):
        """Validate content hash format."""
        if v and not all(c in "0123456789abcdefABCDEF" for c in v):
            raise ValueError("Content hash must be a valid hexadecimal string")
        return v


class IngestResponse(BaseModel):
    """Response from RDF data ingestion."""

    status: Literal["success", "partial", "failed"] = Field(
        ..., description="Ingestion status"
    )
    source_id: str = Field(..., max_length=255, description="Source document ID")
    entities_loaded: int = Field(..., ge=0, description="Number of entities loaded")
    relationships_loaded: int = Field(
        ..., ge=0, description="Number of relationships loaded"
    )
    triples_processed: int = Field(
        ..., ge=0, description="Total RDF triples processed"
    )
    duration_seconds: float | None = Field(
        None, ge=0, description="Processing duration in seconds"
    )
    error: str | None = Field(
        None, max_length=1000, description="Error message if failed"
    )
    warnings: list[str] = Field(default_factory=list, description="Processing warnings")


class SyncStatusResponse(BaseModel):
    """Response for synchronization status."""

    source_id: str = Field(..., max_length=255, description="Source document ID")
    last_extraction_job_id: str | None = Field(
        None, max_length=255, description="Last extraction job ID"
    )
    content_hash: str | None = Field(
        None, max_length=128, description="Current content hash"
    )
    synced_at: datetime | None = Field(
        None, description="Last synchronization timestamp"
    )
    status: Literal["synced", "pending", "failed", "outdated"] | None = Field(
        None, description="Synchronization status"
    )
    error: str | None = Field(
        None, max_length=1000, description="Error message if failed"
    )


# Query Models
class EntityType(str, Enum):
    """Supported entity types for filtering (aligned with ontology schema spec)."""

    # Primary Business Concepts
    CAPABILITY = "Capability"
    USECASE = "UseCase"
    PERSONA = "Persona"
    VALUEDRIVER = "ValueDriver"
    VALUEMETRIC = "ValueMetric"
    # Product & Solution Domain
    PRODUCT = "Product"
    FEATURE = "Feature"
    SERVICE = "Service"
    SOLUTION = "Solution"
    TECHNOLOGY = "Technology"
    # Organizational Context
    ORGANIZATION = "Organization"
    BUSINESSUNIT = "BusinessUnit"
    PROCESS = "Process"
    ACTIVITY = "Activity"
    # Industry Reference Model Mappings
    APQCPROCESS = "APQCProcess"
    BIANSERVICEDOMAIN = "BIANServiceDomain"
    FIBOENTITY = "FIBOEntity"
    # Supporting Concepts
    INDUSTRY = "Industry"
    MARKETSEGMENT = "MarketSegment"
    GEOGRAPHY = "Geography"
    REGULATION = "Regulation"
    # Metadata & Provenance
    DATASOURCE = "DataSource"
    EXTRACTIONEVENT = "ExtractionEvent"
    CONFIDENCESCORE = "ConfidenceScore"


class SearchType(str, Enum):
    """Supported search types."""

    HYBRID = "hybrid"
    VECTOR = "vector"
    FULLTEXT = "fulltext"
    GRAPH = "graph"


class GraphRAGQuery(BaseModel):
    """Request for graph-based question answering."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language query",
        examples=["What capabilities enable automated invoice processing?"],
    )
    entity_type: EntityType | None = Field(None, description="Filter by entity type")
    max_hops: int = Field(
        default=3, ge=1, le=5, description="Maximum graph traversal hops"
    )
    max_results: int = Field(
        default=10, ge=1, le=50, description="Maximum number of results"
    )
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence score for results"
    )
    include_context: bool = Field(
        default=True, description="Include surrounding context in results"
    )


class GraphRAGResponse(BaseModel):
    """Response from graph-based question answering."""

    query: str = Field(..., max_length=1000, description="Original query")
    entities: list[dict[str, Any]] = Field(..., description="Relevant entities found")
    relationships: list[dict[str, Any]] = Field(
        ..., description="Relevant relationships found"
    )
    context_graph: dict[str, Any] = Field(..., description="Context graph structure")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score"
    )
    sources: list[Annotated[str, Field(max_length=500)]] = Field(
        ..., description="Source entities/IDs"
    )
    processing_time_ms: float | None = Field(
        None, ge=0, description="Processing time in milliseconds"
    )
    answer: str | None = Field(None, max_length=2000, description="Generated answer")


# Search Models
class SearchRequest(BaseModel):
    """Request for entity search."""

    query: str = Field(
        ..., min_length=1, max_length=500, description="Search query string", examples=["real-time analytics"]
    )
    entity_type: EntityType | None = Field(None, description="Filter by entity type")
    search_type: SearchType = Field(
        default=SearchType.HYBRID, description="Search algorithm to use"
    )
    top_k: int = Field(
        default=10, ge=1, le=50, description="Number of results to return"
    )
    weights: dict[str, Annotated[float, Field(ge=0.0, le=1.0)]] | None = Field(
        None, description="Search weights for hybrid search (bm25, vector, graph)"
    )
    filters: dict[str, Any] | None = Field(
        None, description="Additional search filters"
    )

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v):
        """Validate search weights sum to 1.0."""
        if v:
            total = sum(v.values())
            if abs(total - 1.0) > 0.01:  # Allow small floating point errors
                raise ValueError("Search weights must sum to 1.0")
        return v


class SearchResult(BaseModel):
    """Individual search result."""

    entity_id: str = Field(
        ..., min_length=1, max_length=255, description="Entity ID"
    )
    entity_type: EntityType = Field(..., description="Entity type")
    name: str = Field(..., min_length=1, max_length=500, description="Entity name")
    bm25_score: float = Field(
        ..., ge=0.0, description="BM25 keyword similarity score"
    )
    vector_score: float = Field(..., ge=0.0, description="Vector similarity score")
    graph_score: float = Field(..., ge=0.0, description="Graph traversal score")
    combined_score: float = Field(
        ..., ge=0.0, le=1.0, description="Combined relevance score"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional entity metadata"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Result confidence")


class SearchResponse(BaseModel):
    """Response from entity search."""

    query: str = Field(..., max_length=500, description="Original search query")
    results: list[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., ge=0, description="Total results found")
    search_type: SearchType = Field(..., description="Search type used")
    processing_time_ms: float | None = Field(
        None, ge=0, description="Processing time in milliseconds"
    )


# Streaming Models
class StreamEventType(str, Enum):
    """Event types for streaming responses."""

    START = "start"
    SEED_ENTITY = "seed_entity"
    CONTEXT_NODE = "context_node"
    CONTEXT_EDGE = "context_edge"
    PROGRESS = "progress"
    RESULT = "result"
    ERROR = "error"
    COMPLETE = "complete"


class GraphRAGStreamEvent(BaseModel):
    """Individual streaming event from GraphRAG query."""

    event_type: StreamEventType = Field(..., description="Type of streaming event")
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    progress_percent: float | None = Field(
        None, ge=0, le=100, description="Query progress percentage"
    )


class SearchStreamEvent(BaseModel):
    """Individual streaming event from search query."""

    event_type: StreamEventType = Field(..., description="Type of streaming event")
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    progress_percent: float | None = Field(
        None, ge=0, le=100, description="Search progress percentage"
    )


# Entity Models
class EntityContextRequest(BaseModel):
    hops: int = Field(default=2, ge=1, le=4)
    relationship_types: list[str] | None = None
    fields: list[str] | None = Field(
        None,
        description="Specific fields to include in response (field selection for reduced payload)",
    )
    cursor: str | None = Field(
        None, description="Pagination cursor for neighbor entities"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of neighbor entities to return",
    )


class EntityContextResponse(BaseModel):
    entity_id: str
    center: dict[str, Any]
    neighbors: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    entity_count: int
    relationship_count: int
    pagination: dict[str, Any] | None = Field(
        None, description="Pagination info: {has_more, next_cursor, returned_count}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Canonical Entity Models (Entity Browser Contract)
# ═══════════════════════════════════════════════════════════════════════════════

EntityStatus = Literal["validated", "pending", "draft", "deprecated"]
ConfidenceLabel = Literal["high", "medium", "low"]


class EntitySummary(BaseModel):
    """Canonical entity summary for browser table views.

    Optimized for: Fast list rendering, filtering, sorting.
    Provides explicit, authoritative fields for UI consumption.
    """

    id: str = Field(
        ..., min_length=1, max_length=255, description="Canonical entity identifier (stable UUID)"
    )
    name: str = Field(
        ..., min_length=1, max_length=500, description="Human-readable entity name"
    )
    entity_type: EntityType = Field(..., description="Entity classification from ontology")

    # Authoritative business fields (not inferred by UI)
    domain: str | None = Field(
        None, max_length=100, description="Business domain/vertical (e.g., 'Finance', 'Healthcare')"
    )
    status: EntityStatus = Field(
        ..., description="Entity lifecycle status: validated, pending, draft, deprecated"
    )

    # Confidence with explicit semantics
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Extraction confidence score (0.0 to 1.0)"
    )
    confidence_label: ConfidenceLabel = Field(
        ..., description="Human-readable confidence tier derived from score"
    )

    # Metadata for display
    description: str | None = Field(
        None, max_length=1000, description="Brief entity description"
    )
    updated_at: datetime = Field(
        ..., description="Last modification timestamp (ISO 8601)"
    )

    # Provenance (for UI attribution)
    source_name: str | None = Field(
        None, max_length=255, description="Source system where entity was extracted"
    )
    extraction_job_id: str | None = Field(
        None, max_length=255, description="Originating extraction job ID"
    )

    @model_validator(mode="before")
    @classmethod
    def derive_confidence_and_status(cls, data: Any) -> Any:
        """Derive confidence_label and status from confidence score if not provided."""
        if isinstance(data, dict):
            confidence = data.get("confidence", 0.0)
            if data.get("confidence_label") is None:
                if confidence >= 0.9:
                    data["confidence_label"] = "high"
                elif confidence >= 0.7:
                    data["confidence_label"] = "medium"
                else:
                    data["confidence_label"] = "low"
            if data.get("status") is None:
                if confidence >= 0.9:
                    data["status"] = "validated"
                elif confidence >= 0.7:
                    data["status"] = "pending"
                else:
                    data["status"] = "draft"
        return data


class RelationshipPreview(BaseModel):
    """Lightweight relationship for preview lists in entity detail."""

    relationship_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of relationship (e.g., ENABLES, DEPENDS_ON)"
    )
    target_entity_id: str = Field(
        ..., min_length=1, max_length=255, description="ID of related entity"
    )
    target_entity_name: str = Field(
        ..., min_length=1, max_length=500, description="Name of related entity"
    )
    target_entity_type: EntityType = Field(..., description="Type of related entity")


class EntityRelationships(BaseModel):
    """Relationship counts and samples for quick navigation."""

    total_count: Annotated[int, Field(ge=0, description="Total relationships (in + out)")] = 0
    incoming: list[RelationshipPreview] = Field(
        default_factory=list, max_length=5, description="Sample of incoming relationships"
    )
    outgoing: list[RelationshipPreview] = Field(
        default_factory=list, max_length=5, description="Sample of outgoing relationships"
    )


class ProvenanceEvent(BaseModel):
    """Single event in entity provenance chain."""

    event_type: Literal["extracted", "validated", "modified", "merged", "deprecated"] = Field(
        ..., description="Type of provenance event"
    )
    timestamp: datetime = Field(..., description="When the event occurred")
    actor: str = Field(
        ..., min_length=1, max_length=255, description="User ID, system component, or job ID that performed the action"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional event-specific data"
    )


class EntityDetail(BaseModel):
    """Canonical entity detail for inspection/drawer views.

    Extends EntitySummary with relationships and full provenance.
    Optimized for: Deep inspection, relationship navigation.
    """

    # ═════════════════════════════════════════════════════════════════════════
    # All EntitySummary fields (ensuring consistency between summary/detail)
    # ═════════════════════════════════════════════════════════════════════════
    id: str = Field(..., min_length=1, max_length=255, description="Entity ID")
    name: str = Field(..., min_length=1, max_length=500, description="Entity name")
    entity_type: EntityType = Field(..., description="Entity type")
    domain: str | None = Field(None, max_length=100, description="Business domain")
    status: EntityStatus = Field(..., description="Lifecycle status")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence 0-1")
    confidence_label: ConfidenceLabel = Field(..., description="Confidence tier")
    description: str | None = Field(None, max_length=1000, description="Description")
    updated_at: datetime = Field(..., description="Last update timestamp")
    source_name: str | None = Field(None, max_length=255, description="Source system")
    extraction_job_id: str | None = Field(
        None, max_length=255, description="Extraction job ID"
    )

    @model_validator(mode="before")
    @classmethod
    def derive_confidence_and_status(cls, data: Any) -> Any:
        """Derive confidence_label and status from confidence score if not provided."""
        if isinstance(data, dict):
            confidence = data.get("confidence", 0.0)
            if data.get("confidence_label") is None:
                if confidence >= 0.9:
                    data["confidence_label"] = "high"
                elif confidence >= 0.7:
                    data["confidence_label"] = "medium"
                else:
                    data["confidence_label"] = "low"
            if data.get("status") is None:
                if confidence >= 0.9:
                    data["status"] = "validated"
                elif confidence >= 0.7:
                    data["status"] = "pending"
                else:
                    data["status"] = "draft"
        return data

    # ═════════════════════════════════════════════════════════════════════════
    # Extended fields for detail view
    # ═════════════════════════════════════════════════════════════════════════
    created_at: datetime = Field(..., description="Entity creation timestamp")
    created_by: str | None = Field(
        None, max_length=255, description="User or system that created the entity"
    )

    # Full provenance chain
    provenance: list[ProvenanceEvent] = Field(
        default_factory=list, description="Audit trail of entity changes"
    )

    # Relationships (for graph navigation)
    relationships: EntityRelationships = Field(
        default_factory=lambda: EntityRelationships(),
        description="Related entities and relationship counts"
    )

    # Raw properties (for advanced inspection)
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Raw extracted properties (internal use)"
    )

    # Validation state
    validation_errors: list[Annotated[str, Field(max_length=500)]] = Field(
        default_factory=list, description="Schema validation errors if any"
    )
    last_validated_at: datetime | None = Field(
        None, description="When entity was last validated"
    )


class EntityFilterRequest(BaseModel):
    """Server-backed entity filtering request.

    The API applies these filters natively in Neo4j Cypher queries.
    This eliminates the need for client-side filtering of large result sets.
    """

    # Text search (across name, description, properties)
    search_text: str | None = Field(
        None, max_length=200, description="Search across name, description, and properties"
    )

    # Exact match filters (AND logic between different filter types)
    entity_types: list[EntityType] | None = Field(
        None, description="Include only these entity types"
    )
    domains: list[Annotated[str, Field(max_length=100)]] | None = Field(
        None, description="Include only these domains"
    )
    statuses: list[EntityStatus] | None = Field(
        None, description="Include only these lifecycle statuses"
    )

    # Confidence range
    min_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Minimum confidence score (inclusive)"
    )
    max_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Maximum confidence score (inclusive)"
    )

    # Provenance filters
    source_names: list[Annotated[str, Field(max_length=255)]] | None = Field(
        None, description="Filter by source systems"
    )
    extraction_job_ids: list[Annotated[str, Field(max_length=255)]] | None = Field(
        None, description="Filter by originating extraction job"
    )

    # Time range
    updated_after: datetime | None = Field(None, description="Updated after this time")
    updated_before: datetime | None = Field(None, description="Updated before this time")

    # Pagination and sorting
    limit: int = Field(25, ge=1, le=100, description="Max results to return")
    offset: int = Field(0, ge=0, description="Results to skip (for pagination)")
    sort_by: Literal["name", "updated_at", "confidence", "entity_type", "status"] = Field(
        "updated_at", description="Field to sort by"
    )
    sort_order: Literal["asc", "desc"] = Field(
        "desc", description="Sort direction (ascending or descending)"
    )


class EntityListResponse(BaseModel):
    """Paginated list of entity summaries with filter metadata."""

    results: list[EntitySummary] = Field(..., description="Entity summaries")
    total_count: int = Field(..., ge=0, description="Total entities in database")
    filtered_count: int = Field(
        ..., ge=0, description="Entities matching filters (before pagination)"
    )

    # Pagination metadata
    limit: int = Field(..., ge=1, description="Limit applied to this query")
    offset: int = Field(..., ge=0, description="Offset applied to this query")
    has_more: bool = Field(..., description="Whether more results available")

    # Available filter values (for UI dropdown population)
    available_domains: list[str] = Field(
        default_factory=list, description="Domains present in current filtered set"
    )
    available_sources: list[str] = Field(
        default_factory=list, description="Source names present in current filtered set"
    )


# ═══════════════════════════════════════════════════════════════════════════════

class ValueTreeTraversal(BaseModel):
    entity_id: str
    direction: str = Field(default="both", description="up, down, or both")


class ValueTreeResponse(BaseModel):
    start_entity_id: str
    direction: str
    paths: list[dict[str, Any]]
    path_count: int


# Analytics Models
class CommunityDetectionRequest(BaseModel):
    algorithm: str = Field(
        default="louvain", description="louvain, leiden, or value_tree"
    )
    entity_types: list[str] | None = None
    min_community_size: int = Field(default=3, ge=2)
    relationship_types: list[str] | None = None


class Community(BaseModel):
    id: int
    size: int
    members: list[dict[str, Any]]


class CommunityDetectionResponse(BaseModel):
    algorithm: str
    total_communities: int
    valid_communities: int
    total_nodes: int
    communities: list[Community]
    modularity: float | None


class CentralityRequest(BaseModel):
    algorithm: str = Field(
        default="pagerank", description="pagerank, betweenness, degree, or value_tree"
    )
    entity_types: list[str] | None = None
    top_k: int = Field(default=20, ge=1, le=100)


class CentralityResult(BaseModel):
    id: str
    name: str
    type: str
    score: float


class CentralityResponse(BaseModel):
    algorithm: str
    total_ranked: int
    top_entities: list[CentralityResult]
    by_layer: dict[str, list[dict]] | None
    key_connectors: list[dict] | None


class SimilarityRequest(BaseModel):
    entity_id: str
    method: str = Field(
        default="combined",
        description="jaccard, adamic_adar, vector, path, or combined",
    )
    top_k: int = Field(default=10, ge=1, le=50)
    target_type: str | None = None


class SimilarityResult(BaseModel):
    id: str
    name: str
    type: str
    score: float
    method: str
    shared_neighbors: list[str] | None
    shared_value_drivers: list[str] | None
    component_scores: dict[str, float] | None


class SimilarityResponse(BaseModel):
    entity_id: str
    method: str
    similar_entities: list[SimilarityResult]


class EntityComparisonRequest(BaseModel):
    entity_id1: str
    entity_id2: str


class EntityComparisonResponse(BaseModel):
    entity1: dict[str, Any]
    entity2: dict[str, Any]
    same_type: bool
    jaccard_similarity: float
    common_neighbors: int
    path_info: dict[str, Any]


# Schema Models
class SchemaStatus(BaseModel):
    constraints: dict[str, Any]
    indexes: dict[str, Any]
    valid: bool


class SchemaStatistics(BaseModel):
    nodes: dict[str, int]
    relationships: dict[str, int]
    total_nodes: int
    total_relationships: int


# Provenance Models
class ProvenanceStep(BaseModel):
    """Single step in a provenance chain."""

    step: int = Field(..., description="Step sequence number")
    label: str = Field(..., description="Step label")
    detail: str = Field(..., description="Step detail description")
    timestamp: datetime = Field(..., description="When step occurred")
    agent: str | None = Field(None, description="Agent responsible for step")
    entity_id: str | None = Field(None, description="Entity ID if applicable")


class ProvenanceTrailResponse(BaseModel):
    """Full provenance trail for an entity."""

    entity_id: str = Field(..., description="Entity ID")
    entity_type: str = Field(..., description="Entity type")
    entity_name: str = Field(..., description="Entity name")
    created_at: datetime = Field(..., description="When entity was created")
    source: str = Field(..., description="Source document or system")
    extraction_job_id: str | None = Field(None, description="L2 extraction job ID")
    steps: list[ProvenanceStep] = Field(..., description="Provenance steps")
    confidence_score: float | None = Field(None, description="Overall confidence")


class AuditLogEntry(BaseModel):
    """Single audit log entry."""

    id: str = Field(..., description="Audit event ID")
    timestamp: datetime = Field(..., description="When event occurred")
    source: str = Field(..., description="Source: 'provenance' or 'access_log'")
    event_type: str = Field(..., description="Event type")
    entity_id: str | None = Field(None, description="Related entity ID")
    entity_type: str | None = Field(None, description="Entity type")
    action: str = Field(..., description="Action performed")
    agent: str = Field(..., description="Agent (user, system, or AI)")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional details"
    )


class AuditLogFilter(BaseModel):
    """Filter parameters for audit log queries."""

    source: str | None = Field(
        None, description="Filter by source: 'provenance', 'access', or 'all'"
    )
    from_date: datetime | None = Field(None, description="Start date filter")
    to_date: datetime | None = Field(None, description="End date filter")
    entity_type: str | None = Field(None, description="Filter by entity type")
    event_type: str | None = Field(None, description="Filter by event type")
    agent: str | None = Field(None, description="Filter by agent")


class AuditLogResponse(BaseModel):
    """Audit log query response."""

    entries: list[AuditLogEntry] = Field(..., description="Audit log entries")
    total: int = Field(..., description="Total entries matching filter")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Entries per page")


class DocumentExportRequest(BaseModel):
    """Request for document export."""

    document_type: str = Field(
        "business_case", description="Type of document to export"
    )
    business_case_id: str = Field(..., description="Business case ID")
    format: str = Field("pdf", description="Export format: pdf, html")
    include_provenance: bool = Field(True, description="Include provenance information")


class DocumentExportResponse(BaseModel):
    """Response from document export request."""

    export_id: str = Field(..., description="Export job ID")
    status: str = Field(
        ..., description="Export status: pending, completed, failed, not_implemented"
    )
    download_url: str | None = Field(None, description="Download URL when ready")
    format: str = Field(..., description="Export format")
    expires_at: datetime | None = Field(None, description="URL expiration time")
    message: str | None = Field(None, description="Human-readable status message")


# Batch Operations Models
class BatchEntityOperation(BaseModel):
    """Single entity operation in a batch."""

    operation: Literal["create", "update", "delete"] = Field(
        ..., description="Operation type"
    )
    entity_id: str | None = Field(
        None, description="Entity ID (required for update/delete)"
    )
    entity_type: EntityType | None = Field(
        None, description="Entity type (required for create)"
    )
    properties: dict[str, Any] | None = Field(None, description="Entity properties")


class BatchEntityRequest(BaseModel):
    """Request for batch entity operations."""

    operations: list[BatchEntityOperation] = Field(
        ..., min_length=1, max_length=100, description="Entity operations to perform"
    )
    atomic: bool = Field(
        default=True, description="If true, all operations succeed or all fail"
    )


class BatchEntityResult(BaseModel):
    """Result of a single entity operation."""

    index: int = Field(..., description="Operation index in batch")
    operation: str = Field(..., description="Operation type")
    entity_id: str | None = Field(None, description="Entity ID")
    success: bool = Field(..., description="Whether operation succeeded")
    error: str | None = Field(None, description="Error message if failed")


class BatchEntityResponse(BaseModel):
    """Response from batch entity operations."""

    total_operations: int = Field(..., description="Total operations submitted")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    results: list[BatchEntityResult] = Field(
        ..., description="Individual operation results"
    )
    atomic_rollback: bool | None = Field(
        None, description="Whether atomic rollback was performed"
    )


class BatchAnalyticsRequest(BaseModel):
    """Request for batch analytics operations."""

    entity_ids: list[str] = Field(
        ..., min_length=1, max_length=50, description="Entity IDs to analyze"
    )
    algorithm: str = Field(
        default="centrality", description="Algorithm to run on each entity context"
    )
    max_hops: int = Field(
        default=2, ge=1, le=3, description="Context size for each analysis"
    )


class BatchAnalyticsResult(BaseModel):
    """Result of analytics for a single entity."""

    entity_id: str = Field(..., description="Entity ID")
    success: bool = Field(..., description="Whether analysis succeeded")
    metrics: dict[str, Any] | None = None
    error: str | None = None


class BatchAnalyticsResponse(BaseModel):
    """Response from batch analytics operations."""

    total_analyzed: int = Field(..., description="Total entities analyzed")
    successful: int = Field(..., description="Number of successful analyses")
    failed: int = Field(..., description="Number of failed analyses")
    results: list[BatchAnalyticsResult] = Field(
        ..., description="Individual analysis results"
    )
    aggregate_metrics: dict[str, Any] | None = Field(
        None, description="Aggregated metrics across all analyses"
    )


# Graph Models
# Mapping of alias field names to their source property names
GraphNodeAliasMap: dict[str, str] = {
    "name": "label",
    "entity_type": "type",
    "confidence_score": "confidence",
}


class GraphNode(BaseModel):
    """Node in the knowledge graph.

    NOTE: This model provides backward-compatible field aliases for frontend contract stability:
    - 'name' is an alias for 'label' (frontend expects 'name')
    - 'entity_type' is an alias for 'type' (frontend expects 'entity_type')
    - 'confidence_score' is an alias for 'confidence' (frontend expects 'confidence_score')

    The legacy fields (label, type, confidence) are preserved for backward compatibility.
    TODO: Deprecate legacy fields once all consumers migrate to new field names.
    """

    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label (legacy: use 'name')")
    type: str = Field(..., description="Node type (legacy: use 'entity_type')")
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence score (legacy: use 'confidence_score')"
    )
    x: float | None = Field(None, description="X position for visualization")
    y: float | None = Field(None, description="Y position for visualization")
    r: float | None = Field(None, description="Radius for visualization")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Additional node properties"
    )

    # ═════════════════════════════════════════════════════════════════════════
    # Backward-compatible alias fields for frontend contract alignment
    # ═════════════════════════════════════════════════════════════════════════

    @property
    def name(self) -> str:
        """Frontend-compatible alias for 'label'."""
        import warnings
        warnings.warn(
            "GraphNode.name is deprecated; use GraphNode.label instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.label

    @property
    def entity_type(self) -> str:
        """Frontend-compatible alias for 'type'."""
        import warnings
        warnings.warn(
            "GraphNode.entity_type is deprecated; use GraphNode.type instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.type

    @property
    def confidence_score(self) -> float:
        """Frontend-compatible alias for 'confidence'."""
        import warnings
        warnings.warn(
            "GraphNode.confidence_score is deprecated; use GraphNode.confidence instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.confidence

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to include computed alias fields in serialization."""
        data = super().model_dump(**kwargs)
        # Dynamically add alias fields using the mapping
        for alias, source in GraphNodeAliasMap.items():
            data[alias] = getattr(self, alias)
        return data


# Mapping for GraphEdge alias fields
GraphEdgeAliasMap: dict[str, str] = {
    "relationship_type": "type",
}


class GraphEdge(BaseModel):
    """Edge/relationship in the knowledge graph.

    NOTE: Provides backward-compatible alias 'relationship_type' for 'type'.
    TODO: Deprecate 'type' field once consumers migrate.
    """

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Relationship type/label (legacy: use 'relationship_type')")
    weight: float = Field(default=1.0, ge=0.0, description="Edge weight/strength")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Additional edge properties"
    )

    # ═════════════════════════════════════════════════════════════════════════
    # Backward-compatible alias fields
    # ═════════════════════════════════════════════════════════════════════════

    @property
    def relationship_type(self) -> str:
        """Frontend-compatible alias for 'type'."""
        import warnings
        warnings.warn(
            "GraphEdge.relationship_type is deprecated; use GraphEdge.type instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.type

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to include computed alias fields in serialization."""
        data = super().model_dump(**kwargs)
        # Dynamically add alias fields using the mapping
        for alias, source in GraphEdgeAliasMap.items():
            data[alias] = getattr(self, alias)
        return data


class GraphStats(BaseModel):
    """Statistics for the knowledge graph."""

    total_nodes: int = Field(..., ge=0, description="Total number of nodes")
    total_edges: int = Field(..., ge=0, description="Total number of edges")
    node_types: dict[str, int] = Field(
        default_factory=dict, description="Count by node type"
    )
    communities: int = Field(
        default=0, ge=0, description="Number of detected communities"
    )
    density: float = Field(default=0.0, ge=0.0, description="Graph density")


class GraphResponse(BaseModel):
    """Full graph response for visualization."""

    nodes: list[GraphNode] = Field(..., description="Graph nodes")
    edges: list[GraphEdge] = Field(..., description="Graph edges")
    stats: GraphStats = Field(..., description="Graph statistics")


class SubgraphResponse(BaseModel):
    """Subgraph centered on a specific entity."""

    root_entity_id: str = Field(..., description="ID of the central entity")
    nodes: list[GraphNode] = Field(..., description="Connected nodes including root")
    edges: list[GraphEdge] = Field(..., description="Edges between returned nodes")
    depth: int = Field(..., ge=1, le=5, description="Traversal depth used")
    stats: GraphStats = Field(..., description="Subgraph statistics")
