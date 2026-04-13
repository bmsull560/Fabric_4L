"""FastAPI application for Layer 3: Knowledge Graph & Semantic Layer."""

import logging
import platform
import os
import time
import uuid
import psutil
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any, Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from ..config import get_settings
from ..logging_config import setup_logging, get_logger
from .middleware import add_security_middleware
from .rate_limiter import add_rate_limiting
from .exceptions import (
    ValueFabricException,
    ValidationError,
    DatabaseError,
    Neo4jError,
    VectorStoreError,
    IngestionError,
    SearchError,
    AnalyticsError,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ServiceUnavailableError,
    create_http_exception,
    create_validation_http_exception,
    create_not_found_http_exception,
    create_conflict_http_exception,
    create_rate_limit_http_exception,
    create_service_unavailable_http_exception,
)
from .dependencies import (
    AppState,
    close_app_state,
    get_app_state,
    get_centrality_analyzer,
    get_community_detector,
    get_graph_rag,
    get_hybrid_search,
    get_narrative_synthesis_agent,
    get_provenance_tracking_agent,
    get_roi_calculation_agent,
    get_schema_initializer,
    get_similarity_analyzer,
    get_sync_manager,
    get_value_tree_projection_agent,
    get_whitespace_analysis_agent,
    init_app_state,
)

# Import cache modules
try:
    from ..cache import initialize_cache, CacheConfig, cache_result, get_request_deduplicator, RequestDeduplicator
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

# Import metrics modules
try:
    from ..metrics import initialize_metrics, MetricsConfig, MetricsMiddleware
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

# Import versioning modules
from .versioning import (
    initialize_versioning,
    VersionMiddleware,
    get_version_compatibility,
    versioned_route,
    VersionedResponse,
)
from .models import (
    AuditLogEntry,
    AuditLogResponse,
    BatchAnalyticsRequest,
    BatchAnalyticsResponse,
    BatchEntityRequest,
    BatchEntityResponse,
    CentralityRequest,
    CentralityResponse,
    CommunityDetectionRequest,
    CommunityDetectionResponse,
    DependencyStatus,
    DetailedHealthResponse,
    DocumentExportRequest,
    DocumentExportResponse,
    EntityComparisonRequest,
    EntityComparisonResponse,
    EntityContextRequest,
    EntityContextResponse,
    GraphEdge,
    GraphNode,
    GraphRAGQuery,
    GraphRAGResponse,
    GraphRAGStreamEvent,
    GraphResponse,
    GraphStats,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    ProvenanceStep,
    ProvenanceTrailResponse,
    SchemaStatistics,
    SchemaStatus,
    SearchRequest,
    SearchResponse,
    SearchStreamEvent,
    ServiceMetrics,
    SimilarityRequest,
    SimilarityResponse,
    StreamEventType,
    SubgraphResponse,
    SyncStatusResponse,
    ValueTreeTraversal,
    ValueTreeResponse,
)

logger = get_logger(__name__)

# Track application startup time for uptime calculation
_app_start_time = time.time()


def _register_migration_handler_with_policy(
    version_compatibility: Any,
    *,
    from_version: str,
    to_version: str,
    handler: Any,
    required: bool,
) -> None:
    """Register migration handler with explicit startup failure policy."""
    expected_interface = "Callable[[Dict[str, Any]], Dict[str, Any]]"
    handler_name = getattr(handler, "__name__", repr(handler))
    actual_type = type(handler).__name__

    try:
        version_compatibility.register_migration_handler(from_version, to_version, handler)
    except Exception as exc:
        message = (
            "Migration handler registration failed "
            f"for {from_version}->{to_version}: handler='{handler_name}', "
            f"expected={expected_interface}, actual_type={actual_type}, error={exc}"
        )
        if required:
            logger.error(message, exc_info=True)
            raise RuntimeError(message) from exc

        logger.warning(message, exc_info=True)


def _get_settings_with_fallback() -> Any:
    try:
        return get_settings()
    except Exception:
        return SimpleNamespace(
            log_request_id_header="X-Request-ID",
            log_level="INFO",
            neo4j_uri="bolt://localhost:7687",
            neo4j_database="neo4j",
            pinecone_api_key=None,
            pinecone_index="value-fabric",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Setup structured logging
    settings = get_settings()
    setup_logging(settings)
    logger.info("Starting Value Fabric Knowledge Graph API",
                extra={"component": "layer3-knowledge",
                       "version": "1.0.0"})
    
    # Initialize cache if enabled
    cache_manager = None
    if CACHE_AVAILABLE and settings.cache_enabled:
        try:
            cache_config = CacheConfig(
                default_ttl=settings.cache_default_ttl,
                max_ttl=settings.cache_max_ttl,
                key_prefix=settings.cache_key_prefix,
                serializer=settings.cache_serializer,
                compression=settings.cache_compression,
            )
            cache_manager = initialize_cache(
                redis_url=settings.cache_redis_url,
                config=cache_config
            )
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            cache_manager = None
    
    # Initialize metrics if enabled
    metrics = None
    if METRICS_AVAILABLE and settings.metrics_enabled:
        try:
            metrics_config = MetricsConfig(
                enabled=True,
                prefix=settings.metrics_prefix,
                label_namespace=settings.metrics_namespace,
            )
            metrics = initialize_metrics(metrics_config)
            logger.info("Prometheus metrics initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Prometheus metrics: {e}")
            metrics = None
    
    # Initialize versioning system
    version_compatibility = initialize_versioning("v1")
    
    # Register migration handlers
    from .versioning import migrate_v1_to_v2_search_request, migrate_v1_to_v2_ingestion_request
    from .versioning import transform_v1_search_response, transform_v1_health_response
    
    _register_migration_handler_with_policy(
        version_compatibility,
        from_version="v1",
        to_version="v2",
        handler=migrate_v1_to_v2_search_request,
        required=True,
    )
    _register_migration_handler_with_policy(
        version_compatibility,
        from_version="v1",
        to_version="v2",
        handler=migrate_v1_to_v2_ingestion_request,
        required=True,
    )
    version_compatibility.register_response_transformer("v1", "/v1/search", transform_v1_search_response)
    version_compatibility.register_response_transformer("v1", "/health", transform_v1_health_response)
    
    logger.info("API versioning system initialized")
    
    # Store managers in app state
    app.state.cache_manager = cache_manager
    app.state.metrics = metrics
    app.state.version_compatibility = version_compatibility
    
    # Set global metrics reference for health check access
    set_app_metrics(metrics)
    
    # Add metrics middleware if available
    if metrics and not getattr(app.state, "_metrics_middleware_installed", False):
        metrics_middleware = MetricsMiddleware(metrics)
        try:
            app.middleware("http")(metrics_middleware)
            app.state._metrics_middleware_installed = True
        except RuntimeError as exc:
            logger.warning(f"Skipping metrics middleware registration at startup: {exc}")
    
    # Startup
    await init_app_state(app)
    yield
    
    # Shutdown
    logger.info("Shutting down Value Fabric Knowledge Graph API")
    
    # Disconnect cache
    if cache_manager:
        try:
            await cache_manager.disconnect()
            logger.info("Redis cache disconnected")
        except Exception as e:
            logger.warning(f"Error disconnecting cache: {e}")
    
    await close_app_state(app)


# Initialize FastAPI app
app = FastAPI(
    title="Value Fabric - Knowledge Graph & Semantic Layer",
    description="""
    ## Layer 3: Knowledge Graph & Semantic Layer API
    
    The Value Fabric Knowledge Graph API provides intelligent semantic search, 
    graph-based retrieval, and analytics capabilities for enterprise AI workflows.
    
    ### Key Features
    - **GraphRAG Retrieval**: Context-aware graph-based question answering
    - **Hybrid Search**: Combined vector, keyword, and graph traversal search
    - **Entity Analytics**: Community detection, centrality analysis, and similarity metrics
    - **Schema Management**: Dynamic Neo4j schema initialization and monitoring
    - **Real-time Ingestion**: RDF/OWL data ingestion with provenance tracking
    
    ### Architecture
    - **Database**: Neo4j 5.x for graph storage and relationships
    - **Vector Store**: Pinecone for semantic similarity search
    - **Embeddings**: OpenAI text-embedding-3-large (768 dimensions)
    - **Analytics**: NetworkX for graph algorithms and community detection
    
    ### Authentication & Security
    - Rate limiting (configurable per endpoint)
    - Input validation and sanitization
    - Request tracking with unique IDs
    - Comprehensive security headers
    
    ### Getting Started
    1. Explore the `/health` endpoint to verify service status
    2. Check `/v1/schema/status` to ensure database schema is ready
    3. Try `/v1/search` for basic entity discovery
    4. Use `/v1/graphrag` for complex question answering
    
    ### Rate Limits
    - Default: 100 requests/minute, 200 burst
    - Health endpoints: 300 requests/minute
    - Search endpoints: 200 requests/minute  
    - Schema operations: 10-60 requests/minute
    
    Check response headers `X-RateLimit-*` for current limits.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Value Fabric Team",
        "email": "value-fabric@example.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://valuefabric.com/license",
    },
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Health",
            "description": "Service health monitoring and diagnostics",
        },
        {
            "name": "Schema",
            "description": "Database schema management and validation",
        },
        {
            "name": "Search",
            "description": "Entity search and discovery endpoints",
        },
        {
            "name": "GraphRAG",
            "description": "Graph-based question answering and retrieval",
        },
        {
            "name": "Analytics",
            "description": "Graph analytics and community detection",
        },
        {
            "name": "Ingestion",
            "description": "Data ingestion and synchronization",
        },
        {
            "name": "Value Trees",
            "description": "Value tree traversal and exploration",
        },
        {
            "name": "Formulas",
            "description": "Formula evaluation and variable registry",
        },
        {
            "name": "Graph",
            "description": "Graph visualization endpoints",
        },
    ],
)


# Include routers from routes modules
from .routes import value_trees, formulas, value_packs, formula_governance, variables

app.include_router(value_trees.router, prefix="/v1")
app.include_router(formulas.router, prefix="/v1")
app.include_router(value_packs.router, prefix="/v1")
app.include_router(formula_governance.router, prefix="/v1")
app.include_router(variables.router, prefix="/v1")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID to logs and response headers."""
    settings = _get_settings_with_fallback()
    request_id = request.headers.get(settings.log_request_id_header) or str(uuid.uuid4())
    
    # Add request ID to logger context
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    try:
        response = await call_next(request)
        response.headers[settings.log_request_id_header] = request_id
        return response
    finally:
        logging.setLogRecordFactory(old_factory)


# CORS middleware
# Note: allow_origins=["*"] cannot be used with allow_credentials=True per browser security spec
# In production, specify exact origins or use environment variable
allow_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
allow_credentials = False  # Must be False when using wildcard origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GovernanceMiddleware — provides verified JWT + API-key auth for L3.
# Replaces the existing AuthenticationMiddleware in auth/middleware.py.
# api_key_resolver is None here; plug in the DB-backed resolver from L4's
# tenant service if L3 is given access to the same Postgres instance.
try:
    from shared.identity.middleware import GovernanceMiddleware
    app.add_middleware(GovernanceMiddleware, api_key_resolver=None)
except ImportError:
    logger.warning(
        "shared.identity not importable — GovernanceMiddleware skipped in L3. "
        "Ensure the shared package is installed."
    )

# Security middleware
add_security_middleware(app, strict_mode=True)

# Rate limiting middleware
try:
    settings = get_settings()
except Exception:
    logger.warning("Falling back to default rate-limit settings during import")
    settings = None

add_rate_limiting(
    app,
    requests_per_minute=settings.rate_limit_requests_per_minute if settings else 100,
    burst_size=settings.rate_limit_burst_size if settings else 200,
    enabled=settings.rate_limit_enabled if settings else False,
)

# Versioning middleware
version_middleware = VersionMiddleware(get_version_compatibility())
app.middleware("http")(version_middleware)


def _exception_trace(exc: Exception):
    """Return explicit exception tuple for logger.exc_info."""
    return (type(exc), exc, exc.__traceback__)


# Exception handlers
@app.exception_handler(ValueFabricException)
async def value_fabric_exception_handler(request: Request, exc: ValueFabricException):
    """Handle Value Fabric custom exceptions."""
    logger.error(
        f"Value Fabric exception occurred: {exc.error_code} at {request.method} {request.url.path} - {exc.message}",
        exc_info=_exception_trace(exc),
    )
    
    # Record error metrics
    metrics = getattr(request.app.state, 'metrics', None)
    if metrics:
        metrics.increment_errors(
            error_type=exc.error_code,
            component="api",
            namespace="layer3"
        )
    
    # Determine appropriate status code based on exception type
    status_code = 500  # Default to internal server error
    
    if isinstance(exc, ValidationError):
        status_code = 400
    elif isinstance(exc, (AuthenticationError, AuthorizationError)):
        status_code = 401 if isinstance(exc, AuthenticationError) else 403
    elif exc.error_code == "NOT_FOUND":
        status_code = 404
    elif exc.error_code == "CONFLICT":
        status_code = 409
    elif isinstance(exc, RateLimitError):
        status_code = 429
    elif isinstance(exc, ServiceUnavailableError):
        status_code = 503
    
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions with structured logging."""
    logger.warning(
        f"HTTP exception {exc.status_code} at {request.method} {request.url.path}: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        f"Unhandled {type(exc).__name__} at {request.method} {request.url.path}: {str(exc)}",
        exc_info=_exception_trace(exc),
    )
    
    # Record error metrics
    metrics = getattr(request.app.state, 'metrics', None)
    if metrics:
        metrics.increment_errors(
            error_type=type(exc).__name__,
            component="api",
            namespace="layer3"
        )
    
    # Create a generic error response
    error_response = {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
        "type": type(exc).__name__,
        "request_id": getattr(request.state, "request_id", None),
    }
    
    # In development, include more details
    settings = _get_settings_with_fallback()
    if settings.log_level.upper() == "DEBUG":
        error_response["debug_info"] = {
            "exception": str(exc),
            "traceback": str(exc.__traceback__) if exc.__traceback__ else None,
        }
    
    return JSONResponse(
        status_code=500,
        content=error_response,
    )


# Metrics endpoint
@app.get(
    "/metrics",
    tags=["Monitoring"],
    summary="Prometheus Metrics",
    description="""
    Export Prometheus metrics for monitoring.
    
    This endpoint provides metrics in Prometheus format for:
    - HTTP requests and response times
    - Database operations
    - Cache performance
    - Search queries
    - System resources
    - Error rates
    
    **Usage:**
    Configure Prometheus to scrape this endpoint:
    ```yaml
    scrape_configs:
      - job_name: 'value-fabric-layer3'
        static_configs:
          - targets: ['localhost:8001']
        metrics_path: '/metrics'
    ```
    
    **Response Headers:**
    - `Content-Type`: `text/plain; version=0.0.4; charset=utf-8`
    
    **Status Codes:**
    - `200`: Metrics exported successfully
    - `503`: Metrics collection disabled
    """,
    responses={
        200: {
            "description": "Prometheus metrics exported successfully",
            "content": {
                "text/plain": {
                    "example": """# HELP value_fabric_http_requests_total Total HTTP requests
# TYPE value_fabric_http_requests_total counter
value_fabric_http_requests_total{method="GET",endpoint="/health",status_code="200",namespace="layer3"} 42
# HELP value_fabric_http_request_duration_seconds HTTP request duration in seconds
# TYPE value_fabric_http_request_duration_seconds histogram
value_fabric_http_request_duration_seconds_bucket{method="GET",endpoint="/health",namespace="layer3",le="0.1"} 40
value_fabric_http_request_duration_seconds_bucket{method="GET",endpoint="/health",namespace="layer3",le="0.25"} 41
value_fabric_http_request_duration_seconds_bucket{method="GET",endpoint="/health",namespace="layer3",le="0.5"} 42
value_fabric_http_request_duration_seconds_bucket{method="GET",endpoint="/health",namespace="layer3",le="+Inf"} 42
value_fabric_http_request_duration_seconds_sum{method="GET",endpoint="/health",namespace="layer3"} 8.5
value_fabric_http_request_duration_seconds_count{method="GET",endpoint="/health",namespace="layer3"} 42"""
                }
            }
        },
        503: {
            "description": "Metrics collection disabled",
            "content": {
                "text/plain": {
                    "example": "Metrics collection is disabled"
                }
            }
        }
    }
)
async def get_metrics(request: Request):
    """Get Prometheus metrics."""
    metrics = getattr(request.app.state, 'metrics', None)
    
    if not metrics:
        return Response(
            content="Metrics collection is disabled",
            status_code=503,
            media_type="text/plain"
        )
    
    try:
        metrics_data = metrics.get_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content="Error generating metrics",
            status_code=500,
            media_type="text/plain"
        )


async def check_dependencies() -> List[DependencyStatus]:
    """Check health of all dependencies."""
    dependencies = []
    settings = _get_settings_with_fallback()
    
    # Check Neo4j
    try:
        from ..schema.initializer import SchemaInitializer
        neo4j_checker = SchemaInitializer()
        start_time = time.time()
        neo4j_health = await neo4j_checker.health_check()
        response_time = (time.time() - start_time) * 1000
        
        dependencies.append(DependencyStatus(
            name="neo4j",
            status=neo4j_health["status"],
            response_time_ms=response_time,
            error=neo4j_health.get("error"),
            details={
                "uri": settings.neo4j_uri,
                "database": settings.neo4j_database
            }
        ))
        await neo4j_checker.close()
    except Exception as e:
        dependencies.append(DependencyStatus(
            name="neo4j",
            status="unhealthy",
            error=str(e),
            details={"uri": settings.neo4j_uri}
        ))
    
    # Check Pinecone (if configured)
    if settings.pinecone_api_key:
        try:
            start_time = time.time()
            # Simple Pinecone health check would go here
            # For now, just check if API key is present
            response_time = (time.time() - start_time) * 1000
            dependencies.append(DependencyStatus(
                name="pinecone",
                status="healthy",
                response_time_ms=response_time,
                details={"index": settings.pinecone_index}
            ))
        except Exception as e:
            dependencies.append(DependencyStatus(
                name="pinecone",
                status="unhealthy",
                error=str(e)
            ))
    
    return dependencies


_app_metrics: Optional[Any] = None


def set_app_metrics(metrics: Optional[Any]) -> None:
    """Set the global metrics instance for health check access."""
    global _app_metrics
    _app_metrics = metrics


def get_system_metrics() -> ServiceMetrics:
    """Collect system and application metrics from Prometheus.
    
    Extracts real counter values from the Prometheus registry by iterating
    through collected metrics and summing sample values for counters.
    """
    uptime = time.time() - _app_start_time

    # System metrics from psutil
    memory_info = psutil.virtual_memory()
    memory_usage_mb = memory_info.used / (1024 * 1024)
    cpu_percent = psutil.cpu_percent(interval=None)

    # Application metrics from Prometheus registry
    total_requests = 0
    total_errors = 0
    active_connections = 0
    error_rate_percent = 0.0
    metrics_instance = _app_metrics
    
    if metrics_instance is not None:
        try:
            registry = metrics_instance.config.registry
            prefix = metrics_instance.config.prefix
            
            # Iterate through all metrics in registry and extract values
            for metric in registry.collect():
                if metric.name == f"{prefix}active_connections":
                    # Gauge: take the value directly (connection_type="total")
                    for sample in metric.samples:
                        if sample.labels.get("connection_type") == "total":
                            active_connections = int(sample.value)
                            break
                
                elif metric.name == f"{prefix}http_requests_total":
                    # Counter: sum all sample values across all labels
                    for sample in metric.samples:
                        total_requests += int(sample.value)
                
                elif metric.name == f"{prefix}errors_total":
                    # Counter: sum all error samples across all labels
                    for sample in metric.samples:
                        total_errors += int(sample.value)
            
            # Calculate error rate as percentage
            if total_requests > 0:
                error_rate_percent = round((total_errors / total_requests) * 100, 2)
                
        except Exception as e:
            logger.warning(f"Failed to extract Prometheus metrics: {e}")
            # Keep default zero values on any extraction failure

    return ServiceMetrics(
        uptime_seconds=uptime,
        memory_usage_mb=round(memory_usage_mb, 2),
        cpu_percent=round(cpu_percent, 2),
        active_connections=active_connections,
        total_requests=total_requests,
        error_rate_percent=error_rate_percent
    )


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Basic Health Check",
    description="""
    Perform a basic health check of the service and its dependencies.
    
    This endpoint checks:
    - Neo4j database connectivity
    - Overall service status
    - Basic system metrics
    - Schema validation status
    
    Returns a simplified health status suitable for load balancers and monitoring systems.
    
    **Response Headers:**
    - `X-RateLimit-*`: Current rate limiting information
    - `X-API-Version`: API version used
    - `X-Supported-Versions`: Supported API versions
    
    **Status Codes:**
    - `200`: Service is healthy
    - `503`: Service or dependencies are unhealthy
    """,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "timestamp": "2024-01-01T12:00:00.000Z",
                        "uptime_seconds": 3600.0,
                        "dependencies": [
                            {
                                "name": "neo4j",
                                "status": "healthy",
                                "response_time_ms": 15.5,
                                "error": None,
                                "details": {
                                    "uri": "bolt://localhost:7687",
                                    "database": "neo4j"
                                }
                            }
                        ],
                        "metrics": {
                            "uptime_seconds": 3600.0,
                            "memory_usage_mb": 1024.5,
                            "cpu_percent": 25.0,
                            "active_connections": 10,
                            "total_requests": 1500,
                            "error_rate_percent": 0.1
                        },
                        "neo4j": {
                            "status": "healthy",
                            "database": "neo4j",
                            "uri": "bolt://localhost:7687"
                        },
                        "schema_status": {
                            "constraints": {"expected": 10, "found": 10, "missing": []},
                            "indexes": {"expected": 15, "found": 15, "missing": []},
                            "valid": True
                        }
                    }
                }
            }
        },
        503: {
            "description": "Service or dependencies are unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "version": "1.0.0",
                        "timestamp": "2024-01-01T12:00:00.000Z",
                        "uptime_seconds": 3600.0,
                        "dependencies": [
                            {
                                "name": "neo4j",
                                "status": "unhealthy",
                                "response_time_ms": None,
                                "error": "Connection timeout",
                                "details": {
                                    "uri": "bolt://localhost:7687",
                                    "database": "neo4j"
                                }
                            }
                        ],
                        "metrics": {
                            "uptime_seconds": 3600.0,
                            "memory_usage_mb": 1024.5,
                            "cpu_percent": 25.0,
                            "active_connections": 0,
                            "total_requests": 1500,
                            "error_rate_percent": 5.2
                        },
                        "neo4j": {
                            "status": "unhealthy",
                            "database": "neo4j",
                            "uri": "bolt://localhost:7687",
                            "error": "Connection timeout"
                        },
                        "schema_status": {
                            "constraints": {"expected": 10, "found": 8, "missing": ["constraint_1", "constraint_2"]},
                            "indexes": {"expected": 15, "found": 15, "missing": []},
                            "valid": False
                        }
                    }
                }
            }
        }
    }
)
async def health_check(
    request: Request,
    schema_initializer=Depends(get_schema_initializer),
):
    """Check service health and Neo4j connectivity."""
    start_time = time.time()
    request_id = getattr(request.state, 'request_id', 'unknown')

    # Check dependencies
    dependencies = await check_dependencies()

    # Get metrics
    metrics = get_system_metrics()

    # Check Neo4j health (handle case where schema_initializer is None)
    neo4j_health = {"status": "unavailable", "message": "Neo4j not initialized"}
    schema_status = {"status": "unknown", "message": "Schema initializer not available"}

    if schema_initializer is not None:
        try:
            neo4j_health = await schema_initializer.health_check()
            schema_status = await schema_initializer.verify_schema()
        except Exception:
            logger.warning(
                "Health check failed for Neo4j",
                exc_info=True,
                extra={"health_request_id": request_id},
            )
            error_msg = "Neo4j health check failed"
            neo4j_health = {"status": "error", "message": error_msg}
            schema_status = {"status": "error", "message": error_msg}

    # Determine overall status (priority: unhealthy > degraded > healthy)
    overall_status = "healthy"
    if schema_initializer is None:
        overall_status = "degraded"
    elif any(dep.status == "unhealthy" for dep in dependencies):
        overall_status = "unhealthy"
    elif any(dep.status == "degraded" for dep in dependencies):
        overall_status = "degraded"

    response_time_ms = (time.time() - start_time) * 1000

    logger.info(
        "Health check completed",
        extra={
            "health_request_id": request_id,
            "status": overall_status,
            "response_time_ms": round(response_time_ms, 2),
            "neo4j_status": neo4j_health.get("status"),
        },
    )

    # Create response data
    response_data = {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.utcnow(),
        "uptime_seconds": metrics.uptime_seconds,
        "response_time_ms": round(response_time_ms, 2),
        "dependencies": dependencies,
        "metrics": metrics,
        "neo4j": neo4j_health,
        "schema_status": schema_status
    }

    # Response model expects health payload directly (version headers are applied by middleware).
    return response_data


@app.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    tags=["Health"],
    summary="Detailed Health Check",
    description="""
    Perform a comprehensive health check with detailed system information.
    
    This endpoint provides complete health information including:
    - All dependency status with response times
    - Detailed system metrics and resource usage
    - Configuration information (non-sensitive)
    - System information and platform details
    - Full schema validation results
    
    Use this endpoint for detailed diagnostics and troubleshooting.
    
    **Response Headers:**
    - `X-RateLimit-*`: Current rate limiting information
    
    **Status Codes:**
    - `200`: Detailed health information returned
    - `503`: Service or dependencies are unhealthy
    """,
    responses={
        200: {
            "description": "Detailed health information",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "timestamp": "2024-01-01T12:00:00.000Z",
                        "uptime_seconds": 3600.0,
                        "dependencies": [
                            {
                                "name": "neo4j",
                                "status": "healthy",
                                "response_time_ms": 15.5,
                                "error": None,
                                "details": {
                                    "uri": "bolt://localhost:7687",
                                    "database": "neo4j"
                                }
                            },
                            {
                                "name": "pinecone",
                                "status": "healthy",
                                "response_time_ms": 25.2,
                                "error": None,
                                "details": {
                                    "index": "value-fabric"
                                }
                            }
                        ],
                        "metrics": {
                            "uptime_seconds": 3600.0,
                            "memory_usage_mb": 1024.5,
                            "cpu_percent": 25.0,
                            "active_connections": 10,
                            "total_requests": 1500,
                            "error_rate_percent": 0.1
                        },
                        "neo4j": {
                            "status": "healthy",
                            "database": "neo4j",
                            "uri": "bolt://localhost:7687"
                        },
                        "schema_status": {
                            "constraints": {"expected": 10, "found": 10, "missing": []},
                            "indexes": {"expected": 15, "found": 15, "missing": []},
                            "valid": True
                        },
                        "system_info": {
                            "platform": "Windows-10-10.0.19041-SP0",
                            "python_version": "3.11.0",
                            "cpu_count": 8,
                            "memory_total_gb": 16.0,
                            "disk_usage_gb": 250.5
                        },
                        "configuration": {
                            "api_host": "0.0.0.0",
                            "api_port": 8001,
                            "log_level": "INFO",
                            "log_format": "json",
                            "neo4j_database": "neo4j",
                            "neo4j_max_pool_size": 50,
                            "pinecone_configured": True
                        }
                    }
                }
            }
        }
    }
)
async def detailed_health_check(
    schema_initializer=Depends(get_schema_initializer),
    app_state: AppState = Depends(get_app_state),
):
    """Get detailed health information with system info and configuration."""
    start_time = time.time()
    
    # Basic health check
    dependencies = await check_dependencies()
    metrics = get_system_metrics()
    neo4j_health = await schema_initializer.health_check()
    schema_status = await schema_initializer.verify_schema()
    
    # Determine overall status
    overall_status = "healthy"
    if any(dep.status == "unhealthy" for dep in dependencies):
        overall_status = "unhealthy"
    elif any(dep.status == "degraded" for dep in dependencies):
        overall_status = "degraded"
    
    # System information
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": psutil.virtual_memory().total / (1024**3),
        "disk_usage_gb": psutil.disk_usage('/').used / (1024**3),
    }
    
    # Configuration (non-sensitive)
    settings = get_settings()
    configuration = {
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "neo4j_database": settings.neo4j_database,
        "neo4j_max_pool_size": settings.neo4j_max_pool_size,
        "pinecone_configured": bool(settings.pinecone_api_key),
    }
    
    return DetailedHealthResponse(
        status=overall_status,
        version="1.0.0",
        uptime_seconds=metrics.uptime_seconds,
        dependencies=dependencies,
        metrics=metrics,
        neo4j=neo4j_health,
        schema_status=schema_status,
        system_info=system_info,
        configuration=configuration
    )


# Schema endpoints
@app.get(
    "/v1/schema/status",
    response_model=SchemaStatus,
    tags=["Schema"],
    summary="Get Schema Status",
    description="""
    Retrieve the current status of Neo4j schema elements.
    
    This endpoint checks:
    - Constraint creation and validation
    - Index creation and status
    - Overall schema health
    - Missing elements that need attention
    
    Use this endpoint to verify database schema integrity before operations.
    
    **Response Headers:**
    - `X-RateLimit-*`: Current rate limiting information
    
    **Status Codes:**
    - `200`: Schema status retrieved successfully
    - `503`: Database connection issues
    """,
    responses={
        200: {
            "description": "Schema status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "constraints": {
                            "expected": 10,
                            "found": 10,
                            "missing": []
                        },
                        "indexes": {
                            "expected": 15,
                            "found": 15,
                            "missing": []
                        },
                        "valid": True
                    }
                }
            }
        }
    }
)
async def get_schema_status(
    schema_initializer=Depends(get_schema_initializer),
):
    """Get schema initialization status."""
    if schema_initializer is None:
        return SchemaStatus(
            constraints={},
            indexes={},
            valid=False,
        )
    verification = await schema_initializer.verify_schema()
    return SchemaStatus(
        constraints=verification["constraints"],
        indexes=verification["indexes"],
        valid=verification["valid"],
    )


@app.post("/v1/schema/init")
async def init_schema(
    drop_existing: bool = False,
    schema_initializer=Depends(get_schema_initializer),
):
    """Initialize or reinitialize schema."""
    if schema_initializer is None:
        raise HTTPException(status_code=503, detail="Schema initializer not available")
    await schema_initializer.initialize_schema(drop_existing=drop_existing)
    return {"status": "initialized", "drop_existing": drop_existing}


@app.get("/v1/schema/statistics", response_model=SchemaStatistics)
async def get_schema_statistics(
    schema_initializer=Depends(get_schema_initializer),
):
    """Get database statistics."""
    if schema_initializer is None:
        raise HTTPException(status_code=503, detail="Schema initializer not available")
    stats = await schema_initializer.get_statistics()
    return SchemaStatistics(
        nodes=stats["nodes"],
        relationships=stats["relationships"],
        total_nodes=stats["total_nodes"],
        total_relationships=stats["total_relationships"],
    )


# Ingestion endpoints
@app.post("/v1/ingest", response_model=IngestResponse)
async def ingest_rdf(
    request: IngestRequest,
    sync_manager=Depends(get_sync_manager),
):
    """Ingest RDF data from Layer 2 extraction pipeline."""
    try:
        stats = await sync_manager.sync_extraction_result(
            rdf_data=request.rdf_data,
            source_id=request.source_id,
            extraction_job_id=request.extraction_job_id,
            content_hash=request.content_hash,
        )

        raw_status = stats.get("status", "unknown")
        status = "success" if raw_status in {"synced", "success"} else raw_status
        if status not in {"success", "partial", "failed"}:
            status = "failed"

        return IngestResponse(
            status=status,
            source_id=request.source_id,
            entities_loaded=stats.get("entities_loaded", 0),
            relationships_loaded=stats.get("relationships_loaded", 0),
            triples_processed=stats.get("triples_processed", 0),
            duration_seconds=stats.get("duration_seconds"),
            error=stats.get("error"),
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/ingest/status/{source_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    source_id: str,
    sync_manager=Depends(get_sync_manager),
):
    """Get synchronization status for a source."""
    status = await sync_manager.get_sync_status(source_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    return SyncStatusResponse(
        source_id=source_id,
        last_extraction_job_id=status.get("last_extraction_job_id"),
        content_hash=status.get("content_hash"),
        synced_at=status.get("synced_at"),
        status=status.get("status"),
        error=status.get("error"),
    )


# Alias for L2 client compatibility (canonical route is /v1/ingest/status/{source_id})
# DESIGN NOTE: L2 uses ingestion_id, L3 uses source_id. They are treated as equivalent
# for sync status lookups. If ID schemes diverge in future, add mapping layer here.
@app.get("/v1/ingest/{source_id}/status", response_model=SyncStatusResponse)
async def get_sync_status_alias(
    source_id: str,
    sync_manager=Depends(get_sync_manager),
):
    """Get synchronization status for a source (backward-compatible alias)."""
    return await get_sync_status(source_id, sync_manager)


@app.delete("/v1/ingest/{source_id}")
async def delete_source(
    source_id: str,
    sync_manager=Depends(get_sync_manager),
):
    """Delete all data from a source."""
    stats = await sync_manager.delete_source(source_id)
    return {
        "status": "deleted",
        "source_id": source_id,
        "entities_deleted": stats["entities_deleted"],
        "relationships_deleted": stats["relationships_deleted"],
    }


# Query endpoints
# Canonical route. Legacy `/v1/query` remains for backward compatibility.

async def _execute_graph_rag_query(
    graph_rag,
    query_text: str,
    entity_type: Optional[str],
    max_hops: int,
    max_results: int,
) -> GraphRAGResponse:
    """Execute GraphRAG query (extracted for caching/deduplication)."""
    start_time = time.time()

    result = await graph_rag.query(
        query_text=query_text,
        entity_type=entity_type,
        max_hops=max_hops,
        max_results=max_results,
    )

    processing_time = (time.time() - start_time) * 1000

    return GraphRAGResponse(
        query=result.query,
        entities=result.entities,
        relationships=result.relationships,
        context_graph=result.context_graph,
        confidence_score=result.confidence_score,
        sources=result.sources,
        processing_time_ms=processing_time,
    )


@app.post("/v1/query/graph", response_model=GraphRAGResponse)
@app.post("/v1/query", response_model=GraphRAGResponse)
async def graph_rag_query(
    query: GraphRAGQuery,
    graph_rag=Depends(get_graph_rag),
):
    """Execute a GraphRAG query with multi-hop traversal.

    Uses request deduplication to prevent redundant computation for
    identical concurrent queries. Results are cached for 60 seconds.

    Notes:
    - Preferred route: `/v1/query/graph`
    - Legacy route retained: `/v1/query` (deprecate later)
    """
    try:
        deduplicator = get_request_deduplicator()

        if deduplicator:
            # Use request deduplication for identical concurrent queries
            params = {
                "query": query.query,
                "entity_type": query.entity_type,
                "max_hops": query.max_hops,
                "max_results": query.max_results,
            }
            return await deduplicator.execute(
                operation="graph_rag_query",
                params=params,
                executor=_execute_graph_rag_query,
                ttl=60,  # 60 second deduplication window
                graph_rag=graph_rag,
                query_text=query.query,
                entity_type=query.entity_type,
                max_hops=query.max_hops,
                max_results=query.max_results,
            )
        else:
            # Fallback to direct execution
            return await _execute_graph_rag_query(
                graph_rag,
                query.query,
                query.entity_type,
                query.max_hops,
                query.max_results,
            )
    except Exception as e:
        logger.error(f"GraphRAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/query/graph/stream")
async def graph_rag_query_stream(
    query: GraphRAGQuery,
    graph_rag=Depends(get_graph_rag),
):
    """Execute a streaming GraphRAG query with progressive results.

    Uses Server-Sent Events (SSE) to stream results as they are discovered:
    - start: Query initialization
    - seed_entity: Initial matching entities found
    - context_node: Entities discovered during graph traversal
    - context_edge: Relationships discovered
    - progress: Periodic progress updates
    - result: Final aggregated result
    - complete: Stream completion

    Example usage with curl:
        curl -N -H "Accept: text/event-stream" \
             -X POST http://localhost:8000/v1/query/graph/stream \
             -H "Content-Type: application/json" \
             -d '{"query": "What capabilities enable automated invoice processing?"}'
    """
    import json
    from datetime import datetime

    async def event_generator():
        try:
            async for event in graph_rag.query_stream(
                query_text=query.query,
                entity_type=query.entity_type,
                max_hops=query.max_hops,
                max_results=query.max_results,
            ):
                # Convert to SSE format
                event_data = {
                    "event_type": event["event_type"],
                    "data": event["data"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "progress_percent": event.get("progress_percent", 0.0),
                }
                yield f"data: {json.dumps(event_data)}\n\n"
        except Exception as e:
            logger.error(f"Streaming GraphRAG query failed: {e}")
            error_event = {
                "event_type": "error",
                "data": {"message": str(e)},
                "timestamp": datetime.utcnow().isoformat(),
                "progress_percent": 100.0,
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for SSE
        },
    )


# Search endpoints
# Canonical route. Legacy `/v1/search` remains for backward compatibility.

async def _execute_hybrid_search(
    hybrid_search,
    query: str,
    entity_type: Optional[str],
    search_type: str,
    top_k: int,
    weights: Optional[Dict],
) -> SearchResponse:
    """Execute hybrid search (extracted for caching/deduplication)."""
    if search_type == "vector":
        results = await hybrid_search.semantic_search(
            query, entity_type, top_k
        )
    elif search_type == "fulltext":
        results = await hybrid_search.fulltext_search(
            query, entity_type, top_k
        )
    else:  # hybrid
        results = await hybrid_search.search(
            query,
            [entity_type] if entity_type else None,
            top_k,
            weights,
        )

    return SearchResponse(
        query=query,
        results=results,
        total_results=len(results),
        search_type=search_type,
    )


@app.post("/v1/search/hybrid", response_model=SearchResponse)
@app.post("/v1/search", response_model=SearchResponse)
async def hybrid_search(
    request: SearchRequest,
    hybrid_search=Depends(get_hybrid_search),
):
    """Execute hybrid search combining BM25, vector, and graph signals.

    Uses request deduplication to prevent redundant computation for
    identical concurrent searches.

    Notes:
    - Preferred route: `/v1/search/hybrid`
    - Legacy route retained: `/v1/search` (deprecate later)
    """
    try:
        deduplicator = get_request_deduplicator()

        if deduplicator:
            # Use request deduplication for identical concurrent searches
            params = {
                "query": request.query,
                "entity_type": request.entity_type,
                "search_type": request.search_type,
                "top_k": request.top_k,
                "weights": request.weights,
            }
            return await deduplicator.execute(
                operation="hybrid_search",
                params=params,
                executor=_execute_hybrid_search,
                ttl=30,  # 30 second deduplication window
                hybrid_search=hybrid_search,
                query=request.query,
                entity_type=request.entity_type,
                search_type=request.search_type,
                top_k=request.top_k,
                weights=request.weights,
            )
        else:
            # Fallback to direct execution
            return await _execute_hybrid_search(
                hybrid_search,
                request.query,
                request.entity_type,
                request.search_type,
                request.top_k,
                request.weights,
            )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Entity endpoints
@app.get("/v1/entity/{entity_id}/context", response_model=EntityContextResponse)
async def get_entity_context(
    entity_id: str,
    hops: int = 2,
    relationship_types: Optional[List[str]] = None,
    fields: Optional[str] = Query(None, description="Comma-separated fields to include (e.g., 'id,name,type')"),
    cursor: Optional[str] = Query(None, description="Pagination cursor for neighbors"),
    limit: int = Query(100, ge=1, le=500, description="Max neighbors to return"),
    graph_rag=Depends(get_graph_rag),
):
    """Get neighborhood context around an entity.

    Supports field selection (?fields=id,name,type) to reduce payload size,
    and cursor-based pagination (?cursor=xyz&limit=50) for large neighborhoods.
    """
    try:
        context = await graph_rag.get_entity_context(
            entity_id=entity_id,
            hops=hops,
            relationship_types=relationship_types,
        )

        if not context["center"]:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        # Apply field selection if requested
        if fields:
            field_list = [f.strip() for f in fields.split(",")]
            center = {k: v for k, v in context["center"].items() if k in field_list or k == "id"}
            neighbors = [
                {k: v for k, v in n.items() if k in field_list or k == "id"}
                for n in context["neighbors"]
            ]
            relationships = [
                {k: v for k, v in r.items() if k in field_list or k in ["source", "target", "type"]}
                for r in context["relationships"]
            ]
        else:
            center = context["center"]
            neighbors = context["neighbors"]
            relationships = context["relationships"]

        # Apply pagination to neighbors
        pagination_info = None
        if cursor or len(neighbors) > limit:
            # Simple offset-based pagination (can be enhanced to cursor-based)
            offset = int(cursor) if cursor and cursor.isdigit() else 0
            total_neighbors = len(neighbors)
            paginated_neighbors = neighbors[offset:offset + limit]
            has_more = (offset + limit) < total_neighbors

            pagination_info = {
                "returned_count": len(paginated_neighbors),
                "total_neighbors": total_neighbors,
                "has_more": has_more,
                "next_cursor": str(offset + limit) if has_more else None,
            }
            neighbors = paginated_neighbors

        return EntityContextResponse(
            entity_id=entity_id,
            center=center,
            neighbors=neighbors,
            relationships=relationships,
            entity_count=context["entity_count"],
            relationship_count=context["relationship_count"],
            pagination=pagination_info,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/entity/traverse", response_model=ValueTreeResponse)
async def traverse_value_tree(
    request: ValueTreeTraversal,
    graph_rag=Depends(get_graph_rag),
):
    """Traverse the 4-layer value tree from an entity."""
    try:
        result = await graph_rag.traverse_value_tree(
            start_entity_id=request.entity_id,
            direction=request.direction,
        )

        return ValueTreeResponse(
            start_entity_id=result["start_entity_id"],
            direction=result["direction"],
            paths=result["paths"],
            path_count=result["path_count"],
        )
    except Exception as e:
        logger.error(f"Value tree traversal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@app.post("/v1/analytics/communities", response_model=CommunityDetectionResponse)
async def detect_communities(
    request: CommunityDetectionRequest,
    community_detector=Depends(get_community_detector),
):
    """Detect communities in the knowledge graph."""
    try:
        if request.algorithm == "louvain":
            result = await community_detector.detect_louvain(
                node_labels=request.entity_types,
                relationship_types=request.relationship_types,
                min_community_size=request.min_community_size,
            )
        elif request.algorithm == "leiden":
            result = await community_detector.detect_leiden(
                node_labels=request.entity_types,
                relationship_types=request.relationship_types,
                min_community_size=request.min_community_size,
            )
        elif request.algorithm == "value_tree":
            result = await community_detector.detect_by_value_tree()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown algorithm: {request.algorithm}")

        return CommunityDetectionResponse(
            algorithm=result["algorithm"],
            total_communities=result["total_communities"],
            valid_communities=result.get("valid_communities", result["total_communities"]),
            total_nodes=result.get("total_nodes", 0),
            communities=[
                Community(id=c["id"], size=c["size"], members=c["members"])
                for c in result["communities"]
            ],
            modularity=result.get("modularity"),
        )
    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/analytics/centrality", response_model=CentralityResponse)
async def calculate_centrality(
    request: CentralityRequest,
    centrality_analyzer=Depends(get_centrality_analyzer),
):
    """Calculate centrality metrics for entities."""
    try:
        if request.algorithm == "pagerank":
            result = await centrality_analyzer.calculate_pagerank(
                node_labels=request.entity_types,
                top_k=request.top_k,
            )
        elif request.algorithm == "betweenness":
            result = await centrality_analyzer.calculate_betweenness(
                node_labels=request.entity_types,
                top_k=request.top_k,
            )
        elif request.algorithm == "degree":
            result = await centrality_analyzer.calculate_degree_centrality(
                node_labels=request.entity_types,
                top_k=request.top_k,
            )
        elif request.algorithm == "value_tree":
            result = await centrality_analyzer.get_value_tree_centrality()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown algorithm: {request.algorithm}")

        return CentralityResponse(
            algorithm=result["algorithm"],
            total_ranked=result["total_ranked"],
            top_entities=result["top_entities"],
            by_layer=result.get("by_layer"),
            key_connectors=result.get("key_connectors"),
        )
    except Exception as e:
        logger.error(f"Centrality calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/analytics/similar", response_model=SimilarityResponse)
async def find_similar_entities(
    request: SimilarityRequest,
    similarity_analyzer=Depends(get_similarity_analyzer),
):
    """Find similar entities using multiple methods."""
    try:
        if request.target_type:
            results = await similarity_analyzer.find_similar_by_type(
                entity_id=request.entity_id,
                target_type=request.target_type,
                top_k=request.top_k,
            )
        else:
            results = await similarity_analyzer.find_similar(
                entity_id=request.entity_id,
                method=request.method,
                top_k=request.top_k,
            )

        return SimilarityResponse(
            entity_id=request.entity_id,
            method=request.method,
            similar_entities=results,
        )
    except Exception as e:
        logger.error(f"Similarity analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/analytics/compare", response_model=EntityComparisonResponse)
async def compare_entities(
    request: EntityComparisonRequest,
    similarity_analyzer=Depends(get_similarity_analyzer),
):
    """Compare two entities and return similarity metrics."""
    try:
        result = await similarity_analyzer.compare_entities(
            entity_id1=request.entity_id1,
            entity_id2=request.entity_id2,
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return EntityComparisonResponse(
            entity1=result["entity1"],
            entity2=result["entity2"],
            same_type=result["same_type"],
            jaccard_similarity=result["jaccard_similarity"],
            common_neighbors=result["common_neighbors"],
            path_info=result["path_info"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Batch Operations Endpoints
@app.post("/v1/batch/entities", response_model=BatchEntityResponse)
async def batch_entity_operations(
    request: BatchEntityRequest,
    neo4j_driver=Depends(get_neo4j_driver),
):
    """Execute batch entity operations (create/update/delete).

    Reduces round-trips for bulk operations from the frontend.
    Supports atomic mode where all operations succeed or all fail.
    """
    results = []
    successful = 0
    failed = 0
    atomic_rollback = False

    # For atomic mode, we'll track and rollback if needed
    created_entities = []

    try:
        for i, operation in enumerate(request.operations):
            try:
                if operation.operation == "create":
                    # Create entity
                    result = await _create_entity(neo4j_driver, operation)
                    if result["success"]:
                        successful += 1
                        created_entities.append(result["entity_id"])
                    else:
                        failed += 1
                    results.append({
                        "index": i,
                        "operation": "create",
                        "entity_id": result.get("entity_id"),
                        "success": result["success"],
                        "error": result.get("error"),
                    })

                elif operation.operation == "update":
                    # Update entity
                    result = await _update_entity(neo4j_driver, operation)
                    if result["success"]:
                        successful += 1
                    else:
                        failed += 1
                    results.append({
                        "index": i,
                        "operation": "update",
                        "entity_id": operation.entity_id,
                        "success": result["success"],
                        "error": result.get("error"),
                    })

                elif operation.operation == "delete":
                    # Delete entity
                    result = await _delete_entity(neo4j_driver, operation)
                    if result["success"]:
                        successful += 1
                    else:
                        failed += 1
                    results.append({
                        "index": i,
                        "operation": "delete",
                        "entity_id": operation.entity_id,
                        "success": result["success"],
                        "error": result.get("error"),
                    })

            except Exception as e:
                failed += 1
                results.append({
                    "index": i,
                    "operation": operation.operation,
                    "entity_id": operation.entity_id,
                    "success": False,
                    "error": str(e),
                })

        # Atomic rollback if requested and any failures occurred
        if request.atomic and failed > 0 and created_entities:
            atomic_rollback = True
            logger.warning(f"Atomic rollback: deleting {len(created_entities)} created entities")
            for entity_id in created_entities:
                try:
                    await _delete_entity_by_id(neo4j_driver, entity_id)
                except Exception as e:
                    logger.error(f"Rollback error for entity {entity_id}: {e}")

        return BatchEntityResponse(
            total_operations=len(request.operations),
            successful=successful if not (request.atomic and failed > 0) else 0,
            failed=failed,
            results=results,
            atomic_rollback=atomic_rollback if request.atomic else None,
        )

    except Exception as e:
        logger.error(f"Batch entity operations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/batch/analytics", response_model=BatchAnalyticsResponse)
async def batch_analytics(
    request: BatchAnalyticsRequest,
    centrality_analyzer=Depends(get_centrality_analyzer),
    graph_rag=Depends(get_graph_rag),
):
    """Execute batch analytics on multiple entities.

    Runs analytics (centrality, community context) on each entity's
    neighborhood subgraph efficiently.
    """
    results = []
    successful = 0
    failed = 0
    all_scores = []

    try:
        for entity_id in request.entity_ids:
            try:
                # Get entity context first
                context = await graph_rag.get_entity_context(
                    entity_id=entity_id,
                    hops=request.max_hops,
                )

                if not context.get("center"):
                    results.append({
                        "entity_id": entity_id,
                        "success": False,
                        "error": "Entity not found",
                    })
                    failed += 1
                    continue

                # Run appropriate analytics based on algorithm
                if request.algorithm in ["centrality", "pagerank"]:
                    # Get centrality for this entity's subgraph
                    metrics = {
                        "entity_count": context["entity_count"],
                        "relationship_count": context["relationship_count"],
                        "center_entity": context["center"],
                        "neighbors": len(context.get("neighbors", [])),
                    }
                    all_scores.append(context["entity_count"])
                else:
                    metrics = {"context": context}

                results.append({
                    "entity_id": entity_id,
                    "success": True,
                    "metrics": metrics,
                })
                successful += 1

            except Exception as e:
                logger.warning(f"Batch analytics failed for {entity_id}: {e}")
                results.append({
                    "entity_id": entity_id,
                    "success": False,
                    "error": str(e),
                })
                failed += 1

        # Calculate aggregate metrics
        aggregate = None
        if all_scores:
            aggregate = {
                "avg_entities_per_context": sum(all_scores) / len(all_scores),
                "max_entities": max(all_scores),
                "min_entities": min(all_scores),
                "total_entities_analyzed": sum(all_scores),
            }

        return BatchAnalyticsResponse(
            total_analyzed=len(request.entity_ids),
            successful=successful,
            failed=failed,
            results=results,
            aggregate_metrics=aggregate,
        )

    except Exception as e:
        logger.error(f"Batch analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions for batch operations
async def _create_entity(driver, operation: BatchEntityOperation) -> Dict[str, Any]:
    """Create a single entity in Neo4j.

    Args:
        driver: Neo4j async driver
        operation: Batch entity operation with entity_type and properties

    Returns:
        Dict with success flag and entity_id or error message
    """
    try:
        entity_id = str(uuid.uuid4())

        async with driver.session() as session:
            query = """
            CREATE (n:Entity {
                id: $id,
                entity_type: $entity_type,
                created_at: datetime(),
                updated_at: datetime()
            })
            SET n += $properties
            RETURN n.id as entity_id
            """
            result = await session.run(
                query,
                {
                    "id": entity_id,
                    "entity_type": operation.entity_type.value if operation.entity_type else "Unknown",
                    "properties": operation.properties or {},
                }
            )
            record = await result.single()
            if record:
                return {"success": True, "entity_id": record["entity_id"]}
            return {"success": False, "error": "Failed to create entity"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _update_entity(driver, operation: BatchEntityOperation) -> Dict[str, Any]:
    """Update a single entity in Neo4j.

    Args:
        driver: Neo4j async driver
        operation: Batch entity operation with entity_id and properties

    Returns:
        Dict with success flag or error message
    """
    try:
        async with driver.session() as session:
            query = """
            MATCH (n {id: $entity_id})
            SET n += $properties, n.updated_at = datetime()
            RETURN n.id as entity_id
            """
            result = await session.run(
                query,
                {
                    "entity_id": operation.entity_id,
                    "properties": operation.properties or {},
                }
            )
            record = await result.single()
            if record:
                return {"success": True}
            return {"success": False, "error": "Entity not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _delete_entity(driver, operation: BatchEntityOperation) -> Dict[str, Any]:
    """Delete a single entity from Neo4j.

    Args:
        driver: Neo4j async driver
        operation: Batch entity operation with entity_id

    Returns:
        Dict with success flag or error message
    """
    try:
        async with driver.session() as session:
            query = """
            MATCH (n {id: $entity_id})
            DETACH DELETE n
            RETURN count(n) as deleted
            """
            result = await session.run(query, {"entity_id": operation.entity_id})
            record = await result.single()
            if record and record["deleted"] > 0:
                return {"success": True}
            return {"success": False, "error": "Entity not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _delete_entity_by_id(driver, entity_id: str) -> None:
    """Delete entity by ID (used for atomic rollback).

    Args:
        driver: Neo4j async driver
        entity_id: Entity ID to delete
    """
    async with driver.session() as session:
        query = "MATCH (n {id: $entity_id}) DETACH DELETE n"
        await session.run(query, {"entity_id": entity_id})


# Agent endpoints (from value_fabric_backend_logic_specifications.md)
@app.post("/v1/agents/value-tree-projection")
async def value_tree_projection(
    request: Dict[str, Any],
    agent=Depends(get_value_tree_projection_agent),
):
    """Execute value tree projection agent for traversal and semantic matching."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, 'to_dict') else result.__dict__
    except Exception as e:
        logger.error(f"Value tree projection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/agents/whitespace-analysis")
async def whitespace_analysis(
    request: Dict[str, Any],
    agent=Depends(get_whitespace_analysis_agent),
):
    """Execute whitespace analysis agent for gap identification and account planning."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, 'to_dict') else result.__dict__
    except Exception as e:
        logger.error(f"Whitespace analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/agents/roi-calculation")
async def roi_calculation(
    request: Dict[str, Any],
    agent=Depends(get_roi_calculation_agent),
):
    """Execute ROI calculation agent for formula execution and sensitivity analysis."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, 'to_dict') else result.__dict__
    except Exception as e:
        logger.error(f"ROI calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/agents/narrative-synthesis")
async def narrative_synthesis(
    request: Dict[str, Any],
    agent=Depends(get_narrative_synthesis_agent),
):
    """Execute narrative synthesis agent for report generation."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, 'to_dict') else result.__dict__
    except Exception as e:
        logger.error(f"Narrative synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/agents/provenance-tracking")
async def provenance_tracking(
    request: Dict[str, Any],
    agent=Depends(get_provenance_tracking_agent),
):
    """Execute provenance tracking agent for lineage and decision traces."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, 'to_dict') else result.__dict__
    except Exception as e:
        logger.error(f"Provenance tracking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/agents/workflow")
async def agent_workflow(
    workflow_type: str,
    context: Dict[str, Any],
    value_tree_agent=Depends(get_value_tree_projection_agent),
    whitespace_agent=Depends(get_whitespace_analysis_agent),
    roi_agent=Depends(get_roi_calculation_agent),
    narrative_agent=Depends(get_narrative_synthesis_agent),
    provenance_agent=Depends(get_provenance_tracking_agent),
):
    """Execute multi-agent workflow for end-to-end business case generation.
    
    Supported workflows:
    - whitespace_analysis: Gap identification -> Account plan
    - business_case: Opportunity eval -> ROI calc -> Narrative synthesis
    """
    try:
        results = []
        
        if workflow_type == "whitespace_analysis":
            # Step 1: Gap identification
            gap_result = await whitespace_agent.execute({
                "operation": "gap_analysis",
                **context
            })
            results.append({"step": 1, "agent": "WhitespaceAnalysisAgent", "result": gap_result})
            
            # Step 2: Account plan synthesis
            plan_result = await whitespace_agent.execute({
                "operation": "account_plan",
                **context
            })
            results.append({"step": 2, "agent": "WhitespaceAnalysisAgent", "result": plan_result})
            
            # Step 3: Record provenance
            await provenance_agent.execute({
                "operation": "create_decision_trace",
                "workflow_id": "whitespace_analysis_v1",
                "workflow_instance_id": f"ws-{datetime.utcnow().timestamp()}",
                "output_type": "account_plan",
                "output_id": plan_result.output.get("plan_id", "unknown"),
                "steps": results,
            })
            
        elif workflow_type == "business_case":
            # Step 1: Value tree projection
            vt_result = await value_tree_agent.execute({
                "operation": "upward_traversal",
                **context
            })
            results.append({"step": 1, "agent": "ValueTreeProjectionAgent", "result": vt_result})
            
            # Step 2: ROI calculation
            roi_result = await roi_agent.execute({
                "operation": "calculate",
                **context
            })
            results.append({"step": 2, "agent": "ROICalculationAgent", "result": roi_result})
            
            # Step 3: Narrative synthesis
            narrative_result = await narrative_agent.execute({
                "operation": "generate_executive_summary",
                **context
            })
            results.append({"step": 3, "agent": "NarrativeSynthesisAgent", "result": narrative_result})
            
            # Step 4: Record provenance
            await provenance_agent.execute({
                "operation": "create_decision_trace",
                "workflow_id": "business_case_v1",
                "workflow_instance_id": f"bc-{datetime.utcnow().timestamp()}",
                "output_type": "business_case",
                "output_id": narrative_result.output.get("narrative_id", "unknown"),
                "steps": results,
            })
        else:
            raise HTTPException(status_code=400, detail=f"Unknown workflow type: {workflow_type}")
        
        return {
            "workflow_type": workflow_type,
            "steps_completed": len(results),
            "results": results,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PROVENANCE & AUDIT ENDPOINTS
# =============================================================================

@app.get(
    "/v1/provenance/{entity_id}",
    response_model=ProvenanceTrailResponse,
    tags=["Provenance"],
    summary="Get Entity Provenance Trail",
    description="Returns full audit trail and provenance chain for an entity",
)
async def get_provenance(
    entity_id: str,
    app_state: AppState = Depends(get_app_state),
):
    """Get full provenance trail for an entity."""
    # Validate entity_id
    if not entity_id or not entity_id.strip():
        raise HTTPException(status_code=400, detail="entity_id is required")
    
    # Sanitize entity_id to prevent injection
    entity_id = entity_id.strip()
    if len(entity_id) > 255:
        raise HTTPException(status_code=400, detail="entity_id too long (max 255 chars)")
    
    try:
        # Query Neo4j for entity and its provenance
        neo4j = app_state.neo4j_manager
        if not neo4j:
            raise HTTPException(status_code=503, detail="Neo4j not available")

        # Get entity details with parameterized query (safe from injection)
        entity_query = """
        MATCH (e:Entity {id: $entity_id})
        RETURN e.id as entity_id, e.type as entity_type, e.name as entity_name,
               e.created_at as created_at, e.source as source,
               e.extraction_job_id as extraction_job_id, e.confidence as confidence_score
        LIMIT 1
        """
        entity_result = await neo4j.execute_query(entity_query, {"entity_id": entity_id})

        if not entity_result:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        record = entity_result[0]

        # Build provenance steps from related audit events (OPTIONAL MATCH handles missing schema)
        steps_query = """
        MATCH (e:Entity {id: $entity_id})
        OPTIONAL MATCH (e)-[:AUDIT_OF]->(a:AuditEvent)
        WITH a
        WHERE a IS NOT NULL
        RETURN a.step as step, a.label as label, a.detail as detail,
               a.timestamp as timestamp, a.agent as agent, a.entity_id as step_entity_id
        ORDER BY a.step
        """
        steps_result = await neo4j.execute_query(steps_query, {"entity_id": entity_id})

        steps = [
            ProvenanceStep(
                step=s.get("step", i + 1),
                label=s.get("label", f"Step {i + 1}"),
                detail=s.get("detail", ""),
                timestamp=s.get("timestamp", datetime.utcnow()),
                agent=s.get("agent"),
                entity_id=s.get("step_entity_id"),
            )
            for i, s in enumerate(steps_result)
        ]

        # If no steps found, provide default extraction steps
        if not steps:
            steps = [
                ProvenanceStep(
                    step=1,
                    label="Entity Created",
                    detail=f"Entity {entity_id} created from source",
                    timestamp=record.get("created_at", datetime.utcnow()),
                    agent="ExtractionEngine-v2.1",
                )
            ]

        return ProvenanceTrailResponse(
            entity_id=record.get("entity_id", entity_id),
            entity_type=record.get("entity_type", "Unknown"),
            entity_name=record.get("entity_name", "Unknown"),
            created_at=record.get("created_at", datetime.utcnow()),
            source=record.get("source", "unknown"),
            extraction_job_id=record.get("extraction_job_id"),
            steps=steps,
            confidence_score=record.get("confidence_score"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Provenance query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/v1/audit/logs",
    response_model=AuditLogResponse,
    tags=["Audit"],
    summary="List Audit Logs",
    description="Query system audit events from Neo4j provenance or API access logs",
)
async def list_audit_logs(
    source: Literal["all", "provenance", "access"] = Query("all", description="Source: 'provenance', 'access', or 'all'"),
    from_date: Optional[datetime] = Query(None, description="Start date filter"),
    to_date: Optional[datetime] = Query(None, description="End date filter"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Entries per page"),
    app_state: AppState = Depends(get_app_state),
):
    """List audit log entries with filtering."""
    try:
        entries: List[AuditLogEntry] = []

        # Query Neo4j provenance if source is 'provenance' or 'all'
        if source in ("provenance", "all"):
            neo4j = app_state.neo4j_manager
            if neo4j:
                try:
                    # Use OPTIONAL MATCH to handle case where AuditEvent nodes don't exist yet
                    query = """
                    OPTIONAL MATCH (a:AuditEvent)
                    WHERE ($from_date IS NULL OR a.timestamp >= $from_date)
                      AND ($to_date IS NULL OR a.timestamp <= $to_date)
                      AND ($entity_type IS NULL OR a.entity_type = $entity_type)
                      AND ($event_type IS NULL OR a.event_type = $event_type)
                      AND ($agent IS NULL OR a.agent = $agent)
                    WITH a
                    WHERE a IS NOT NULL
                    RETURN a.id as id, a.timestamp as timestamp, a.event_type as event_type,
                           a.entity_id as entity_id, a.entity_type as entity_type,
                           a.action as action, a.agent as agent, a.details as details
                    ORDER BY a.timestamp DESC
                    SKIP $skip LIMIT $limit
                    """
                    params = {
                        "from_date": from_date.isoformat() if from_date else None,
                        "to_date": to_date.isoformat() if to_date else None,
                        "entity_type": entity_type,
                        "event_type": event_type,
                        "agent": agent,
                        "skip": (page - 1) * per_page,
                        "limit": per_page,
                    }

                    result = await neo4j.execute_query(query, params)
                    for r in result:
                        if r.get("id"):  # Only add valid records
                            entries.append(
                                AuditLogEntry(
                                    id=r.get("id", str(uuid.uuid4())),
                                    timestamp=r.get("timestamp", datetime.utcnow()),
                                    source="provenance",
                                    event_type=r.get("event_type", "unknown"),
                                    entity_id=r.get("entity_id"),
                                    entity_type=r.get("entity_type"),
                                    action=r.get("action", "unknown"),
                                    agent=r.get("agent", "system"),
                                    details=r.get("details") or {},
                                )
                            )
                except Exception as neo4j_error:
                    logger.warning(f"Neo4j audit query failed (schema may not exist yet): {neo4j_error}")
                    # Continue with empty entries - don't fail the whole request

        # NOTE: API access log querying not yet implemented.
        # When access logging table is available, extend this endpoint to query
        # from both provenance (Neo4j) and access logs for unified audit view.

        # Sort by timestamp descending (already sorted from Neo4j but ensure consistency)
        entries.sort(key=lambda x: x.timestamp, reverse=True)

        return AuditLogResponse(
            entries=entries,
            total=len(entries),
            page=page,
            per_page=per_page,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit log query failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to query audit logs")


@app.post(
    "/v1/documents/export",
    response_model=DocumentExportResponse,
    tags=["Documents"],
    summary="Export Document",
    description="Generate PDF from business case via L4 workflow",
)
async def export_document(
    request: DocumentExportRequest,
    app_state: AppState = Depends(get_app_state),
):
    """Export business case to PDF via L4 workflow."""
    try:
        # Trigger L4 workflow for document generation
        export_id = f"exp-{uuid.uuid4().hex[:8]}"

        # NOTE: L4 workflow integration pending. Endpoint returns explicit placeholder.
        # When L4 is available, replace this block with actual workflow call.
        logger.warning(
            f"Document export requested but L4 workflow not integrated. "
            f"Returning placeholder for export_id={export_id}"
        )
        return DocumentExportResponse(
            export_id=export_id,
            status="not_implemented",
            download_url=None,
            format=request.format,
            expires_at=None,
            message="Document export via L4 workflow is not yet implemented",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GRAPH VISUALIZATION ENDPOINTS
# =============================================================================

@app.get(
    "/graph",
    response_model=GraphResponse,
    tags=["Graph"],
    summary="Get Full Graph",
    description="Returns the complete knowledge graph with nodes, edges, and statistics for visualization.",
    responses={
        200: {
            "description": "Graph data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "nodes": [
                            {"id": "cap-1", "label": "CRM Integration", "type": "Capability", "confidence": 0.95},
                            {"id": "uc-1", "label": "Pipeline Forecast", "type": "UseCase", "confidence": 0.88}
                        ],
                        "edges": [
                            {"source": "cap-1", "target": "uc-1", "type": "ENABLES", "weight": 1.0}
                        ],
                        "stats": {
                            "total_nodes": 8532,
                            "total_edges": 24156,
                            "node_types": {"Capability": 2847, "UseCase": 1923},
                            "communities": 47,
                            "density": 0.03
                        }
                    }
                }
            }
        },
        503: {"description": "Database unavailable"}
    }
)
async def get_full_graph(
    limit: int = 1000,
    app_state: AppState = Depends(get_app_state),
) -> GraphResponse:
    """Get the full knowledge graph for visualization.

    Returns nodes, edges, and statistics. Results are limited for performance.
    """
    try:
        neo4j = app_state.neo4j_manager
        if not neo4j:
            raise HTTPException(status_code=503, detail="Neo4j not available")

        # Query for nodes with limit
        nodes_query = """
        MATCH (n)
        WHERE n.id IS NOT NULL
        RETURN n.id as id, n.name as label, n.type as type,
               n.confidence as confidence, n.x as x, n.y as y
        LIMIT $limit
        """
        nodes_result = await neo4j.execute_query(nodes_query, {"limit": limit})

        nodes = []
        node_ids = set()
        node_types: Dict[str, int] = {}

        for r in nodes_result:
            node_type = r.get("type", "Unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

            node = GraphNode(
                id=r.get("id"),
                label=r.get("label") or r.get("id"),
                type=node_type,
                confidence=r.get("confidence") or 0.8,
                x=r.get("x"),
                y=r.get("y"),
                properties={"name": r.get("label")}
            )
            nodes.append(node)
            node_ids.add(r.get("id"))

        # Query for edges between returned nodes
        edges_query = """
        MATCH (a)-[r]->(b)
        WHERE a.id IN $node_ids AND b.id IN $node_ids
        RETURN a.id as source, b.id as target, type(r) as rel_type,
               r.weight as weight
        """
        edges_result = await neo4j.execute_query(edges_query, {"node_ids": list(node_ids)})

        edges = []
        for r in edges_result:
            edges.append(GraphEdge(
                source=r.get("source"),
                target=r.get("target"),
                type=r.get("rel_type", "RELATED_TO"),
                weight=r.get("weight") or 1.0
            ))

        # Calculate stats
        total_nodes_query = "MATCH (n) RETURN count(n) as total"
        total_edges_query = "MATCH ()-[r]->() RETURN count(r) as total"

        total_nodes_result = await neo4j.execute_query(total_nodes_query)
        total_edges_result = await neo4j.execute_query(total_edges_query)

        total_nodes = total_nodes_result[0].get("total", 0) if total_nodes_result else 0
        total_edges = total_edges_result[0].get("total", 0) if total_edges_result else 0

        # Calculate density: 2*E / (N*(N-1)) for directed graph
        density = 0.0
        if total_nodes > 1:
            density = (2 * total_edges) / (total_nodes * (total_nodes - 1))

        stats = GraphStats(
            total_nodes=total_nodes,
            total_edges=total_edges,
            node_types=node_types,
            communities=0,  # Would require running community detection
            density=round(density, 4)
        )

        return GraphResponse(nodes=nodes, edges=edges, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve graph: {str(e)}")


@app.get(
    "/entities/{entity_id}/subgraph",
    response_model=SubgraphResponse,
    tags=["Graph"],
    summary="Get Entity Subgraph",
    description="Returns a subgraph centered on the specified entity with connected nodes up to the specified depth.",
    responses={
        200: {
            "description": "Subgraph retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "root_entity_id": "cap-1",
                        "nodes": [
                            {"id": "cap-1", "label": "CRM Integration", "type": "Capability"},
                            {"id": "uc-1", "label": "Pipeline Forecast", "type": "UseCase"}
                        ],
                        "edges": [
                            {"source": "cap-1", "target": "uc-1", "type": "ENABLES"}
                        ],
                        "depth": 2,
                        "stats": {
                            "total_nodes": 15,
                            "total_edges": 22,
                            "node_types": {"Capability": 1, "UseCase": 3}
                        }
                    }
                }
            }
        },
        404: {"description": "Entity not found"},
        503: {"description": "Database unavailable"}
    }
)
async def get_entity_subgraph(
    entity_id: str,
    depth: int = 2,
    app_state: AppState = Depends(get_app_state),
) -> SubgraphResponse:
    """Get subgraph centered on a specific entity.

    - **entity_id**: ID of the central entity
    - **depth**: How many hops to traverse (1-5, default 2)
    """
    try:
        neo4j = app_state.neo4j_manager
        if not neo4j:
            raise HTTPException(status_code=503, detail="Neo4j not available")

        # Clamp depth
        depth = max(1, min(depth, 5))

        # Query for root entity
        root_query = """
        MATCH (n {id: $entity_id})
        RETURN n.id as id, n.name as label, n.type as type,
               n.confidence as confidence
        """
        root_result = await neo4j.execute_query(root_query, {"entity_id": entity_id})

        if not root_result:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        root_record = root_result[0]

        # Query for connected nodes up to depth
        subgraph_query = """
        MATCH path = (root {id: $entity_id})-[*1..$depth]-(connected)
        WHERE root.id IS NOT NULL AND connected.id IS NOT NULL
        RETURN root, connected, relationships(path) as rels,
               length(path) as path_length
        """
        subgraph_result = await neo4j.execute_query(
            subgraph_query,
            {"entity_id": entity_id, "depth": depth}
        )

        # Collect unique nodes and edges
        nodes_map: Dict[str, GraphNode] = {}
        edges_map: Dict[str, GraphEdge] = {}
        node_types: Dict[str, int] = {}

        # Add root node
        root_type = root_record.get("type", "Unknown")
        node_types[root_type] = node_types.get(root_type, 0) + 1
        nodes_map[entity_id] = GraphNode(
            id=entity_id,
            label=root_record.get("label") or entity_id,
            type=root_type,
            confidence=root_record.get("confidence") or 0.8,
            properties={"is_root": True}
        )

        # Process subgraph results
        for r in subgraph_result:
            connected = r.get("connected")
            rels = r.get("rels", [])

            if connected and connected.get("id"):
                conn_id = connected.get("id")
                conn_type = connected.get("type", "Unknown")

                if conn_id not in nodes_map:
                    node_types[conn_type] = node_types.get(conn_type, 0) + 1
                    nodes_map[conn_id] = GraphNode(
                        id=conn_id,
                        label=connected.get("name") or conn_id,
                        type=conn_type,
                        confidence=connected.get("confidence") or 0.8,
                        properties={}
                    )

                # Add relationships
                for rel in rels:
                    start_id = rel.get("start_node", {}).get("id")
                    end_id = rel.get("end_node", {}).get("id")
                    rel_type = rel.get("type", "RELATED_TO")

                    if start_id and end_id:
                        edge_key = f"{start_id}-{end_id}-{rel_type}"
                        if edge_key not in edges_map:
                            edges_map[edge_key] = GraphEdge(
                                source=start_id,
                                target=end_id,
                                type=rel_type,
                                weight=rel.get("weight", 1.0)
                            )

        nodes = list(nodes_map.values())
        edges = list(edges_map.values())

        stats = GraphStats(
            total_nodes=len(nodes),
            total_edges=len(edges),
            node_types=node_types,
            communities=0,
            density=0.0 if len(nodes) <= 1 else (2 * len(edges)) / (len(nodes) * (len(nodes) - 1))
        )

        return SubgraphResponse(
            root_entity_id=entity_id,
            nodes=nodes,
            edges=edges,
            depth=depth,
            stats=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve subgraph for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve subgraph: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
    )
