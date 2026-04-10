"""Pydantic models for Layer 3 API."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal, Union
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, validator, constr, confloat, conint


# Health Check
class DependencyStatus(BaseModel):
    """Status of a service dependency."""
    
    name: constr(min_length=1, max_length=100) = Field(..., description="Dependency name")
    status: Literal["healthy", "unhealthy", "degraded"] = Field(..., description="Current status")
    response_time_ms: Optional[confloat(ge=0)] = Field(None, description="Response time in milliseconds")
    error: Optional[constr(max_length=500)] = Field(None, description="Error message if unhealthy")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional status details")


class ServiceMetrics(BaseModel):
    """System and service performance metrics."""
    
    uptime_seconds: confloat(ge=0) = Field(..., description="Service uptime in seconds")
    memory_usage_mb: Optional[confloat(ge=0)] = Field(None, description="Memory usage in MB")
    cpu_percent: Optional[confloat(ge=0, le=100)] = Field(None, description="CPU usage percentage")
    active_connections: conint(ge=0) = Field(..., description="Number of active connections")
    total_requests: conint(ge=0) = Field(..., description="Total requests processed")
    error_rate_percent: confloat(ge=0, le=100) = Field(..., description="Error rate percentage")


class HealthResponse(BaseModel):
    """Basic health check response."""
    
    status: Literal["healthy", "unhealthy", "degraded"] = Field(..., description="Overall service status")
    version: constr(min_length=1, max_length=20) = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    uptime_seconds: confloat(ge=0) = Field(..., description="Service uptime in seconds")
    dependencies: List[DependencyStatus] = Field(..., description="Dependency statuses")
    metrics: ServiceMetrics = Field(..., description="Service metrics")
    neo4j: Dict[str, Any] = Field(..., description="Neo4j health information")
    schema_status: Dict[str, Any] = Field(..., description="Database schema status")


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with system information."""
    
    status: Literal["healthy", "unhealthy", "degraded"] = Field(..., description="Overall service status")
    version: constr(min_length=1, max_length=20) = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    uptime_seconds: confloat(ge=0) = Field(..., description="Service uptime in seconds")
    dependencies: List[DependencyStatus] = Field(..., description="Dependency statuses")
    metrics: ServiceMetrics = Field(..., description="Service metrics")
    neo4j: Dict[str, Any] = Field(..., description="Neo4j health information")
    schema_status: Dict[str, Any] = Field(..., description="Database schema status")
    system_info: Dict[str, Any] = Field(..., description="System information")
    configuration: Dict[str, Any] = Field(..., description="Non-sensitive configuration")


# Ingestion Models
class IngestRequest(BaseModel):
    """Request for ingesting RDF data into the knowledge graph."""
    
    rdf_data: constr(min_length=1, max_length=1000000) = Field(
        ..., 
        description="RDF/Turtle data from Layer 2 (max 1MB)",
        example="<http://example.com/entity1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/Capability> ."
    )
    source_id: constr(min_length=1, max_length=255) = Field(
        ..., 
        description="Source document ID",
        example="doc-12345"
    )
    extraction_job_id: constr(min_length=1, max_length=255) = Field(
        ..., 
        description="Extraction job ID from Layer 2",
        example="job-67890"
    )
    content_hash: Optional[constr(min_length=32, max_length=128)] = Field(
        None, 
        description="SHA-256 hash for change detection",
        example="a1b2c3d4e5f6..."
    )
    
    @validator('content_hash')
    def validate_content_hash(cls, v):
        """Validate content hash format."""
        if v and not all(c in '0123456789abcdefABCDEF' for c in v):
            raise ValueError('Content hash must be a valid hexadecimal string')
        return v


class IngestResponse(BaseModel):
    """Response from RDF data ingestion."""
    
    status: Literal["success", "partial", "failed"] = Field(..., description="Ingestion status")
    source_id: constr(max_length=255) = Field(..., description="Source document ID")
    entities_loaded: conint(ge=0) = Field(..., description="Number of entities loaded")
    relationships_loaded: conint(ge=0) = Field(..., description="Number of relationships loaded")
    triples_processed: conint(ge=0) = Field(..., description="Total RDF triples processed")
    duration_seconds: Optional[confloat(ge=0)] = Field(None, description="Processing duration in seconds")
    error: Optional[constr(max_length=1000)] = Field(None, description="Error message if failed")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")


class SyncStatusResponse(BaseModel):
    """Response for synchronization status."""
    
    source_id: constr(max_length=255) = Field(..., description="Source document ID")
    last_extraction_job_id: Optional[constr(max_length=255)] = Field(
        None, 
        description="Last extraction job ID"
    )
    content_hash: Optional[constr(max_length=128)] = Field(None, description="Current content hash")
    synced_at: Optional[datetime] = Field(None, description="Last synchronization timestamp")
    status: Optional[Literal["synced", "pending", "failed", "outdated"]] = Field(
        None, 
        description="Synchronization status"
    )
    error: Optional[constr(max_length=1000)] = Field(None, description="Error message if failed")


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
    
    query: constr(min_length=1, max_length=1000) = Field(
        ..., 
        description="Natural language query",
        example="What capabilities enable automated invoice processing?"
    )
    entity_type: Optional[EntityType] = Field(None, description="Filter by entity type")
    max_hops: conint(ge=1, le=5) = Field(
        default=3, 
        description="Maximum graph traversal hops"
    )
    max_results: conint(ge=1, le=50) = Field(
        default=10, 
        description="Maximum number of results"
    )
    confidence_threshold: confloat(ge=0.0, le=1.0) = Field(
        default=0.7, 
        description="Minimum confidence score for results"
    )
    include_context: bool = Field(
        default=True, 
        description="Include surrounding context in results"
    )


class GraphRAGResponse(BaseModel):
    """Response from graph-based question answering."""
    
    query: constr(max_length=1000) = Field(..., description="Original query")
    entities: List[Dict[str, Any]] = Field(..., description="Relevant entities found")
    relationships: List[Dict[str, Any]] = Field(..., description="Relevant relationships found")
    context_graph: Dict[str, Any] = Field(..., description="Context graph structure")
    confidence_score: confloat(ge=0.0, le=1.0) = Field(..., description="Overall confidence score")
    sources: List[constr(max_length=500)] = Field(..., description="Source entities/IDs")
    processing_time_ms: Optional[confloat(ge=0)] = Field(None, description="Processing time in milliseconds")
    answer: Optional[constr(max_length=2000)] = Field(None, description="Generated answer")


# Search Models
class SearchRequest(BaseModel):
    """Request for entity search."""
    
    query: constr(min_length=1, max_length=500) = Field(
        ..., 
        description="Search query string",
        example="real-time analytics"
    )
    entity_type: Optional[EntityType] = Field(None, description="Filter by entity type")
    search_type: SearchType = Field(
        default=SearchType.HYBRID, 
        description="Search algorithm to use"
    )
    top_k: conint(ge=1, le=50) = Field(
        default=10, 
        description="Number of results to return"
    )
    weights: Optional[Dict[str, confloat(ge=0.0, le=1.0)]] = Field(
        None, 
        description="Search weights for hybrid search (bm25, vector, graph)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional search filters"
    )
    
    @validator('weights')
    def validate_weights(cls, v):
        """Validate search weights sum to 1.0."""
        if v:
            total = sum(v.values())
            if abs(total - 1.0) > 0.01:  # Allow small floating point errors
                raise ValueError('Search weights must sum to 1.0')
        return v


class SearchResult(BaseModel):
    """Individual search result."""
    
    entity_id: constr(min_length=1, max_length=255) = Field(..., description="Entity ID")
    entity_type: EntityType = Field(..., description="Entity type")
    name: constr(min_length=1, max_length=500) = Field(..., description="Entity name")
    bm25_score: confloat(ge=0.0) = Field(..., description="BM25 keyword similarity score")
    vector_score: confloat(ge=0.0) = Field(..., description="Vector similarity score")
    graph_score: confloat(ge=0.0) = Field(..., description="Graph traversal score")
    combined_score: confloat(ge=0.0, le=1.0) = Field(..., description="Combined relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional entity metadata")
    confidence: confloat(ge=0.0, le=1.0) = Field(..., description="Result confidence")


class SearchResponse(BaseModel):
    """Response from entity search."""
    
    query: constr(max_length=500) = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: conint(ge=0) = Field(..., description="Total results found")
    search_type: SearchType = Field(..., description="Search type used")
    processing_time_ms: Optional[confloat(ge=0)] = Field(None, description="Processing time in milliseconds")


# Entity Models
class EntityContextRequest(BaseModel):
    hops: int = Field(default=2, ge=1, le=4)
    relationship_types: Optional[List[str]] = None


class EntityContextResponse(BaseModel):
    entity_id: str
    center: Dict[str, Any]
    neighbors: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    entity_count: int
    relationship_count: int


class ValueTreeTraversal(BaseModel):
    entity_id: str
    direction: str = Field(default="both", description="up, down, or both")


class ValueTreeResponse(BaseModel):
    start_entity_id: str
    direction: str
    paths: List[Dict[str, Any]]
    path_count: int


# Analytics Models
class CommunityDetectionRequest(BaseModel):
    algorithm: str = Field(default="louvain", description="louvain, leiden, or value_tree")
    entity_types: Optional[List[str]] = None
    min_community_size: int = Field(default=3, ge=2)
    relationship_types: Optional[List[str]] = None


class Community(BaseModel):
    id: int
    size: int
    members: List[Dict[str, Any]]


class CommunityDetectionResponse(BaseModel):
    algorithm: str
    total_communities: int
    valid_communities: int
    total_nodes: int
    communities: List[Community]
    modularity: Optional[float]


class CentralityRequest(BaseModel):
    algorithm: str = Field(default="pagerank", description="pagerank, betweenness, degree, or value_tree")
    entity_types: Optional[List[str]] = None
    top_k: int = Field(default=20, ge=1, le=100)


class CentralityResult(BaseModel):
    id: str
    name: str
    type: str
    score: float


class CentralityResponse(BaseModel):
    algorithm: str
    total_ranked: int
    top_entities: List[CentralityResult]
    by_layer: Optional[Dict[str, List[Dict]]]
    key_connectors: Optional[List[Dict]]


class SimilarityRequest(BaseModel):
    entity_id: str
    method: str = Field(default="combined", description="jaccard, adamic_adar, vector, path, or combined")
    top_k: int = Field(default=10, ge=1, le=50)
    target_type: Optional[str] = None


class SimilarityResult(BaseModel):
    id: str
    name: str
    type: str
    score: float
    method: str
    shared_neighbors: Optional[List[str]]
    shared_value_drivers: Optional[List[str]]
    component_scores: Optional[Dict[str, float]]


class SimilarityResponse(BaseModel):
    entity_id: str
    method: str
    similar_entities: List[SimilarityResult]


class EntityComparisonRequest(BaseModel):
    entity_id1: str
    entity_id2: str


class EntityComparisonResponse(BaseModel):
    entity1: Dict[str, Any]
    entity2: Dict[str, Any]
    same_type: bool
    jaccard_similarity: float
    common_neighbors: int
    path_info: Dict[str, Any]


# Schema Models
class SchemaStatus(BaseModel):
    constraints: Dict[str, Any]
    indexes: Dict[str, Any]
    valid: bool


class SchemaStatistics(BaseModel):
    nodes: Dict[str, int]
    relationships: Dict[str, int]
    total_nodes: int
    total_relationships: int


# Provenance Models
class ProvenanceStep(BaseModel):
    """Single step in a provenance chain."""
    step: int = Field(..., description="Step sequence number")
    label: str = Field(..., description="Step label")
    detail: str = Field(..., description="Step detail description")
    timestamp: datetime = Field(..., description="When step occurred")
    agent: Optional[str] = Field(None, description="Agent responsible for step")
    entity_id: Optional[str] = Field(None, description="Entity ID if applicable")


class ProvenanceTrailResponse(BaseModel):
    """Full provenance trail for an entity."""
    entity_id: str = Field(..., description="Entity ID")
    entity_type: str = Field(..., description="Entity type")
    entity_name: str = Field(..., description="Entity name")
    created_at: datetime = Field(..., description="When entity was created")
    source: str = Field(..., description="Source document or system")
    extraction_job_id: Optional[str] = Field(None, description="L2 extraction job ID")
    steps: List[ProvenanceStep] = Field(..., description="Provenance steps")
    confidence_score: Optional[float] = Field(None, description="Overall confidence")


class AuditLogEntry(BaseModel):
    """Single audit log entry."""
    id: str = Field(..., description="Audit event ID")
    timestamp: datetime = Field(..., description="When event occurred")
    source: str = Field(..., description="Source: 'provenance' or 'access_log'")
    event_type: str = Field(..., description="Event type")
    entity_id: Optional[str] = Field(None, description="Related entity ID")
    entity_type: Optional[str] = Field(None, description="Entity type")
    action: str = Field(..., description="Action performed")
    agent: str = Field(..., description="Agent (user, system, or AI)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class AuditLogFilter(BaseModel):
    """Filter parameters for audit log queries."""
    source: Optional[str] = Field(None, description="Filter by source: 'provenance', 'access', or 'all'")
    from_date: Optional[datetime] = Field(None, description="Start date filter")
    to_date: Optional[datetime] = Field(None, description="End date filter")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    event_type: Optional[str] = Field(None, description="Filter by event type")
    agent: Optional[str] = Field(None, description="Filter by agent")


class AuditLogResponse(BaseModel):
    """Audit log query response."""
    entries: List[AuditLogEntry] = Field(..., description="Audit log entries")
    total: int = Field(..., description="Total entries matching filter")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Entries per page")


class DocumentExportRequest(BaseModel):
    """Request for document export."""
    document_type: str = Field("business_case", description="Type of document to export")
    business_case_id: str = Field(..., description="Business case ID")
    format: str = Field("pdf", description="Export format: pdf, html")
    include_provenance: bool = Field(True, description="Include provenance information")


class DocumentExportResponse(BaseModel):
    """Response from document export request."""
    export_id: str = Field(..., description="Export job ID")
    status: str = Field(..., description="Export status: pending, completed, failed")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    format: str = Field(..., description="Export format")
    expires_at: Optional[datetime] = Field(None, description="URL expiration time")


# Graph Models
class GraphNode(BaseModel):
    """Node in the knowledge graph."""
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label")
    type: str = Field(..., description="Node type (Capability, UseCase, Persona, ValueDriver)")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score")
    x: Optional[float] = Field(None, description="X position for visualization")
    y: Optional[float] = Field(None, description="Y position for visualization")
    r: Optional[float] = Field(None, description="Radius for visualization")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional node properties")


class GraphEdge(BaseModel):
    """Edge/relationship in the knowledge graph."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Relationship type (ENABLES, BENEFITS, DRIVES)")
    weight: float = Field(default=1.0, ge=0.0, description="Edge weight/strength")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional edge properties")


class GraphStats(BaseModel):
    """Statistics for the knowledge graph."""
    total_nodes: int = Field(..., ge=0, description="Total number of nodes")
    total_edges: int = Field(..., ge=0, description="Total number of edges")
    node_types: Dict[str, int] = Field(default_factory=dict, description="Count by node type")
    communities: int = Field(default=0, ge=0, description="Number of detected communities")
    density: float = Field(default=0.0, ge=0.0, description="Graph density")


class GraphResponse(BaseModel):
    """Full graph response for visualization."""
    nodes: List[GraphNode] = Field(..., description="Graph nodes")
    edges: List[GraphEdge] = Field(..., description="Graph edges")
    stats: GraphStats = Field(..., description="Graph statistics")


class SubgraphResponse(BaseModel):
    """Subgraph centered on a specific entity."""
    root_entity_id: str = Field(..., description="ID of the central entity")
    nodes: List[GraphNode] = Field(..., description="Connected nodes including root")
    edges: List[GraphEdge] = Field(..., description="Edges between returned nodes")
    depth: int = Field(..., ge=1, le=5, description="Traversal depth used")
    stats: GraphStats = Field(..., description="Subgraph statistics")
