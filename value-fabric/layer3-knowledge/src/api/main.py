"""FastAPI application for Layer 3: Knowledge Graph & Semantic Layer."""

import logging
import time
import uuid
import psutil
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

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
    from ..cache import initialize_cache, CacheConfig
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
    CentralityRequest,
    CentralityResponse,
    CommunityDetectionRequest,
    CommunityDetectionResponse,
    DependencyStatus,
    DetailedHealthResponse,
    EntityComparisonRequest,
    EntityComparisonResponse,
    EntityContextRequest,
    EntityContextResponse,
    GraphRAGQuery,
    GraphRAGResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    SchemaStatistics,
    SchemaStatus,
    SearchRequest,
    SearchResponse,
    ServiceMetrics,
    SimilarityRequest,
    SimilarityResponse,
    SyncStatusResponse,
    ValueTreeTraversal,
    ValueTreeResponse,
)

logger = get_logger(__name__)

# Track application startup time for uptime calculation
_app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Setup structured logging
    settings = get_settings()
    setup_logging(settings)
    logger.info("Starting Value Fabric Knowledge Graph API", 
                component="layer3-knowledge", 
                version="1.0.0")
    
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
    
    version_compatibility.register_migration_handler("v1->v2", migrate_v1_to_v2_search_request)
    version_compatibility.register_migration_handler("v1->v2", migrate_v1_to_v2_ingestion_request)
    version_compatibility.register_response_transformer("v1", "/v1/search", transform_v1_search_response)
    version_compatibility.register_response_transformer("v1", "/health", transform_v1_health_response)
    
    logger.info("API versioning system initialized")
    
    # Store managers in app state
    app.state.cache_manager = cache_manager
    app.state.metrics = metrics
    app.state.version_compatibility = version_compatibility
    
    # Add metrics middleware if available
    if metrics:
        metrics_middleware = MetricsMiddleware(metrics)
        app.middleware("http")(metrics_middleware)
    
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
    ],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID to logs and response headers."""
    settings = get_settings()
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
allow_origins = ["*"]
allow_credentials = False  # Must be False when using wildcard origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
add_security_middleware(app, strict_mode=True)

# Rate limiting middleware
settings = get_settings()
add_rate_limiting(
    app,
    requests_per_minute=settings.rate_limit_requests_per_minute,
    burst_size=settings.rate_limit_burst_size,
    enabled=settings.rate_limit_enabled,
)

# Versioning middleware
version_middleware = VersionMiddleware(get_version_compatibility())
app.middleware("http")(version_middleware)


# Exception handlers
@app.exception_handler(ValueFabricException)
async def value_fabric_exception_handler(request: Request, exc: ValueFabricException):
    """Handle Value Fabric custom exceptions."""
    logger.error(
        f"Value Fabric exception occurred: {exc.error_code} at {request.method} {request.url.path} - {exc.message}",
        exc_info=exc,
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
        exc_info=True,
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
    settings = get_settings()
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
    settings = get_settings()
    
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


def get_system_metrics() -> ServiceMetrics:
    """Collect system and application metrics."""
    uptime = time.time() - _app_start_time
    
    # System metrics
    memory_info = psutil.virtual_memory()
    memory_usage_mb = memory_info.used / (1024 * 1024)
    cpu_percent = psutil.cpu_percent()
    
    # Application metrics (simplified)
    active_connections = 0  # Would need connection tracking
    total_requests = 0  # Would need request counter
    error_rate_percent = 0.0  # Would need error tracking
    
    return ServiceMetrics(
        uptime_seconds=uptime,
        memory_usage_mb=memory_usage_mb,
        cpu_percent=cpu_percent,
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
@versioned_route(version="v1")
async def health_check(
    request: Request,
    schema_initializer=Depends(get_schema_initializer),
):
    """Check service health and Neo4j connectivity."""
    start_time = time.time()
    
    # Check dependencies
    dependencies = await check_dependencies()
    
    # Get metrics
    metrics = get_system_metrics()
    
    # Check Neo4j health
    neo4j_health = await schema_initializer.health_check()
    
    # Check schema status
    schema_status = await schema_initializer.verify_schema()
    
    # Determine overall status
    overall_status = "healthy"
    if any(dep.status == "unhealthy" for dep in dependencies):
        overall_status = "unhealthy"
    elif any(dep.status == "degraded" for dep in dependencies):
        overall_status = "degraded"
    
    # Create response data
    response_data = {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.utcnow(),
        "uptime_seconds": metrics.uptime_seconds,
        "dependencies": dependencies,
        "metrics": metrics,
        "neo4j": neo4j_health,
        "schema_status": schema_status
    }
    
    # Apply versioning
    version_compatibility = get_version_compatibility()
    versioned_response = version_compatibility.create_versioned_response(
        data=response_data,
        version=getattr(request.state, 'api_version', 'v1'),
        endpoint="/health"
    )
    
    return versioned_response


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
        "platform": psutil.platform.platform(),
        "python_version": psutil.platform.python_version(),
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
    await schema_initializer.initialize_schema(drop_existing=drop_existing)
    return {"status": "initialized", "drop_existing": drop_existing}


@app.get("/v1/schema/statistics", response_model=SchemaStatistics)
async def get_schema_statistics(
    schema_initializer=Depends(get_schema_initializer),
):
    """Get database statistics."""
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
# TODO: Consider unifying ID schemes in future; treat ingestion_id as source_id for now
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
@app.post("/v1/query/graph", response_model=GraphRAGResponse)
@app.post("/v1/query", response_model=GraphRAGResponse)
async def graph_rag_query(
    query: GraphRAGQuery,
    graph_rag=Depends(get_graph_rag),
):
    """Execute a GraphRAG query with multi-hop traversal.

    Notes:
    - Preferred route: `/v1/query/graph`
    - Legacy route retained: `/v1/query` (deprecate later)
    """
    start_time = time.time()

    try:
        result = await graph_rag.query(
            query_text=query.query,
            entity_type=query.entity_type,
            max_hops=query.max_hops,
            max_results=query.max_results,
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
    except Exception as e:
        logger.error(f"GraphRAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Search endpoints
# Canonical route. Legacy `/v1/search` remains for backward compatibility.
@app.post("/v1/search/hybrid", response_model=SearchResponse)
@app.post("/v1/search", response_model=SearchResponse)
async def hybrid_search(
    request: SearchRequest,
    hybrid_search=Depends(get_hybrid_search),
):
    """Execute hybrid search combining BM25, vector, and graph signals.

    Notes:
    - Preferred route: `/v1/search/hybrid`
    - Legacy route retained: `/v1/search` (deprecate later)
    """
    try:
        if request.search_type == "vector":
            results = await hybrid_search.semantic_search(
                request.query, request.entity_type, request.top_k
            )
        elif request.search_type == "fulltext":
            results = await hybrid_search.fulltext_search(
                request.query, request.entity_type, request.top_k
            )
        else:  # hybrid
            results = await hybrid_search.search(
                request.query,
                [request.entity_type] if request.entity_type else None,
                request.top_k,
                request.weights,
            )

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_type=request.search_type,
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
    graph_rag=Depends(get_graph_rag),
):
    """Get neighborhood context around an entity."""
    try:
        context = await graph_rag.get_entity_context(
            entity_id=entity_id,
            hops=hops,
            relationship_types=relationship_types,
        )

        if not context["center"]:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        return EntityContextResponse(
            entity_id=entity_id,
            center=context["center"],
            neighbors=context["neighbors"],
            relationships=context["relationships"],
            entity_count=context["entity_count"],
            relationship_count=context["relationship_count"],
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
