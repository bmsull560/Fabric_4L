"""FastAPI application for Layer 3: Knowledge Graph & Semantic Layer.

P1-29: OpenTelemetry tracing integration for observability.
"""

import json
import logging
import os
import platform
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

import httpx
import psutil
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from value_fabric.layer3.config import get_settings
from value_fabric.layer3.logging_config import get_logger, setup_logging
from value_fabric.shared.identity import RequestContext, require_authenticated
from value_fabric.shared.fastapi_framework import (
    RouterMount,
    add_governance_middleware,
    add_security_validation_middleware,
    include_router_mounts,
    resolve_cors_policy,
)
from value_fabric.shared.security import validate_production_safety
from value_fabric.shared.models.typed_dict import TypedDictModel

from .dependencies import (
    AppState,
    close_app_state,
    get_app_state,
    get_centrality_analyzer,
    get_community_detector,
    get_graph_rag,
    get_hybrid_search,
    get_narrative_synthesis_agent,
    get_neo4j_driver,
    get_provenance_tracking_agent,
    get_roi_calculation_agent,
    get_schema_initializer,
    get_similarity_analyzer,
    get_sync_manager,
    get_value_tree_projection_agent,
    get_whitespace_analysis_agent,
    init_app_state,
)

# P1-29: OpenTelemetry imports for distributed tracing
from .main_fix import (
    OTEL_AVAILABLE,
    SERVICE_NAME,
    BatchSpanProcessor,
    FastAPIInstrumentor,
    OTLPSpanExporter,
    Resource,
    TracerProvider,
    trace,
)

# Neo4j tenant-aware dependencies (Sprint 5)
try:
    from . import dependencies_tenant as _dependencies_tenant  # noqa: F401
    NEO4J_TENANT_AVAILABLE = True
except ImportError:
    NEO4J_TENANT_AVAILABLE = False


def _extract_tenant_id(request: Request | None) -> str | None:
    """Extract tenant_id from request context for multi-tenant security.
    
    Sprint 5: Centralized helper to eliminate code duplication across endpoints.
    Returns None if tenant context is unavailable or NEO4J_TENANT_AVAILABLE is False.
    
    Args:
        request: FastAPI Request object with optional state.context
        
    Returns:
        Normalized tenant_id string or None
    """
    if not request or not NEO4J_TENANT_AVAILABLE:
        return None
    ctx = getattr(request.state, "context", None)
    if ctx and ctx.tenant_id:
        return str(ctx.tenant_id)
    return None
from value_fabric.shared.error_handling import RequestIDMiddleware
from value_fabric.shared.identity.vault_check import is_vault_healthy

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
    ValueFabricException,
)

SHARED_ERROR_HANDLING_AVAILABLE = True
# Import dataclass utilities
from dataclasses import asdict

from .rate_limiter import add_rate_limiting

# Import cache modules
try:
    from ..cache import (
        CacheConfig,
        get_request_deduplicator,
        initialize_cache,
    )

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

# Import metrics modules
try:
    from ..metrics import MetricsConfig, MetricsMiddleware, initialize_metrics

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

# Import versioning modules
from .models import (
    AuditLogEntry,
    AuditLogResponse,
    BatchAnalyticsRequest,
    BatchAnalyticsResponse,
    BatchEntityOperation,
    BatchEntityRequest,
    BatchEntityResponse,
    CentralityRequest,
    CentralityResponse,
    Community,
    CommunityDetectionRequest,
    CommunityDetectionResponse,
    DependencyStatus,
    DetailedHealthResponse,
    DocumentExportRequest,
    DocumentExportResponse,
    EntityComparisonRequest,
    EntityComparisonResponse,
    EntityContextResponse,
    # Canonical Entity Browser Models (new contract)
    EntityDetail,
    EntityFilterRequest,
    EntityListResponse,
    EntityRelationships,
    EntitySummary,
    GraphEdge,
    GraphNode,
    GraphRAGQuery,
    GraphRAGResponse,
    GraphResponse,
    GraphStats,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    ProvenanceStep,
    ProvenanceTrailResponse,
    RelationshipPreview,
    SchemaStatistics,
    SchemaStatus,
    SearchRequest,
    SearchResponse,
    SearchResult,
    ServiceMetrics,
    SimilarityRequest,
    SimilarityResponse,
    SubgraphResponse,
    SyncStatusResponse,
    ValueTreeResponse,
    ValueTreeTraversal,
)
from .versioning import (
    VersionMiddleware,
    get_version_compatibility,
    initialize_versioning,
)

logger = get_logger(__name__)

# =============================================================================
# DEPRECATION REGISTER
# =============================================================================


class _load_deprecation_registerResult(TypedDictModel):
    deprecations: list[Any]


def _load_deprecation_register() -> dict:
    """Load deprecation register from docs/deprecation_register.json."""
    try:
        repo_root = Path(__file__).parent.parent.parent.parent.parent
        register_path = repo_root / "docs" / "deprecation_register.json"
        if register_path.exists():
            with open(register_path, encoding="utf-8") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to load deprecation register: %s", e)
    return _load_deprecation_registerResult.model_validate({"deprecations": []})


def _check_deprecation_warnings(register: dict) -> None:
    """Log warnings for overdue or upcoming deprecations."""
    now = datetime.now(UTC)
    for item in register.get("deprecations", []):
        target_removal = item.get("target_removal")
        if not target_removal:
            continue
        try:
            removal_date = datetime.fromisoformat(target_removal.replace("Z", "+00:00"))
            if removal_date <= now:
                logger.warning(
                    "Deprecation overdue",
                    feature=item.get("feature"),
                    target_removal=target_removal,
                    owner=item.get("owner"),
                    path=item.get("path"),
                )
            else:
                days_until = (removal_date - now).days
                if days_until <= 7:
                    logger.warning(
                        "Deprecation expiring soon",
                        feature=item.get("feature"),
                        days_until=days_until,
                        target_removal=target_removal,
                    )
        except ValueError:
            continue


# Load deprecation register at startup
_deprecation_register = _load_deprecation_register()
_check_deprecation_warnings(_deprecation_register)


def _add_deprecation_headers(response: Response, endpoint_path: str) -> None:
    """Add deprecation headers if endpoint matches a deprecated feature."""
    for item in _deprecation_register.get("deprecations", []):
        if endpoint_path in item.get("path", ""):
            deprecated_since = item.get("deprecated_since", "")
            target_removal = item.get("target_removal", "")
            owner = item.get("owner", "")

            if deprecated_since:
                response.headers["X-Deprecated-Since"] = deprecated_since
            if target_removal:
                response.headers["X-Target-Removal-Date"] = target_removal
            if owner:
                response.headers["X-Deprecation-Owner"] = owner
            # RFC 7234 Warning header
            response.headers["Warning"] = f'299 - "Deprecated since {deprecated_since}"'
            break


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
        version_compatibility.register_migration_handler(
            from_version, to_version, handler
        )
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
    except (ImportError, RuntimeError, ValueError) as e:
        logger.warning(f"Settings unavailable, using fallback: {e}")
        return SimpleNamespace(
            log_request_id_header="X-Request-ID",
            log_level="INFO",
            neo4j_uri="bolt://localhost:7687",
            neo4j_database="neo4j",
            pinecone_api_key=None,
            pinecone_index="value-fabric",
        )


# P1-29: OpenTelemetry tracer provider (initialized on startup)
_tracer_provider: Any | None = None


def init_telemetry() -> Any | None:
    """Initialize OpenTelemetry tracing if endpoint configured.

    P1-29: OpenTelemetry integration for distributed tracing.
    """
    if not OTEL_AVAILABLE:
        logger.debug("OpenTelemetry not available (module not installed)")
        return None

    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otel_endpoint:
        return None

    resource = Resource.create({SERVICE_NAME: "layer3-knowledge"})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=f"{otel_endpoint}/v1/traces"
    )
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return provider


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _tracer_provider

    validate_production_safety()

    # P1-29: Initialize OpenTelemetry
    _tracer_provider = init_telemetry()
    if _tracer_provider:
        logger.info("L3: OpenTelemetry tracing initialized")

    # Setup structured logging
    settings = get_settings()
    setup_logging(settings)
    logger.info(
        "Starting Value Fabric Knowledge Graph API",
        extra={"component": "layer3-knowledge", "version": "1.0.0"},
    )

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
                redis_url=settings.cache_redis_url, config=cache_config
            )
            logger.info("Redis cache initialized successfully")
        except (ConnectionError, TimeoutError, OSError) as e:
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
        except (ConnectionError, RuntimeError, ValueError) as e:
            logger.warning(f"Failed to initialize Prometheus metrics: {e}")
            metrics = None

    # Initialize versioning system
    version_compatibility = initialize_versioning("v1")

    # Register migration handlers
    from .versioning import (
        migrate_v1_to_v2_ingestion_request,
        migrate_v1_to_v2_search_request,
        transform_v1_health_response,
        transform_v1_search_response,
    )

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
    version_compatibility.register_response_transformer(
        "v1", "/v1/search", transform_v1_search_response
    )
    version_compatibility.register_response_transformer(
        "v1", "/health", transform_v1_health_response
    )

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
            logger.warning(
                f"Skipping metrics middleware registration at startup: {exc}"
            )

    # Production Vault smoke gate
    if os.getenv("ENVIRONMENT", "development") == "production":
        vault_addr = os.getenv("VAULT_ADDR")
        if vault_addr and is_vault_healthy:
            logger.info("L3: Checking Vault connectivity", extra={"vault_addr": vault_addr})
            ok = await is_vault_healthy(vault_addr)
            if not ok:
                logger.error(
                    "L3: Vault unreachable — cannot start in production without secrets backend",
                    extra={"vault_addr": vault_addr}
                )
                raise RuntimeError("Vault unreachable — cannot start in production without secrets backend")
            logger.info("L3: Vault connectivity verified")

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
        {
            "name": "Models",
            "description": "Value model management and organization",
        },
    ],
)

# P1-29: Instrument FastAPI with OpenTelemetry (after app creation)
if OTEL_AVAILABLE and os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
    FastAPIInstrumentor.instrument_app(app)
    logger.info("L3: FastAPI instrumented with OpenTelemetry")


# Include routers from routes modules
from .routes import (
    benchmarks,
    competitive_intel,
    entities,
    evidence,
    formula_governance,
    formulas,
    models,
    products,
    roi_calculator,
    system,
    value_packs,
    value_trees,
    variables,
)

# Include modular routers (decomposition in progress - Weakness #3)
include_router_mounts(
    app,
    [
        RouterMount(value_trees.router, prefix="/v1"),
        RouterMount(formulas.router, prefix="/v1"),
        RouterMount(value_packs.router, prefix="/v1"),
        RouterMount(formula_governance.router, prefix="/v1"),
        RouterMount(variables.router, prefix="/v1"),
        RouterMount(models.router, prefix="/v1"),
        RouterMount(entities.router, prefix="/v1"),
        RouterMount(products.router, prefix="/v1"),
        RouterMount(evidence.router, prefix="/v1"),
        RouterMount(competitive_intel.router, prefix="/v1"),
        RouterMount(roi_calculator.router, prefix="/v1"),
        RouterMount(benchmarks.router, prefix="/v1/roi"),
        RouterMount(system.router),
    ],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # HSTS (uncomment when HTTPS is enforced)
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID to logs and response headers."""
    settings = _get_settings_with_fallback()
    request_id = request.headers.get(settings.log_request_id_header) or str(
        uuid.uuid4()
    )

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


# CORS middleware with production validation (P0-20)
# Note: allow_origins=["*"] cannot be used with allow_credentials=True per browser security spec
_cors_policy = resolve_cors_policy()

app.add_middleware(
    CORSMiddleware,
    **_cors_policy.as_kwargs(),
)

# Request ID middleware (Task 61: Request Correlation IDs)
# Must be after CORS but before request processing
if SHARED_ERROR_HANDLING_AVAILABLE:
    app.add_middleware(RequestIDMiddleware)
    logger.info("RequestIDMiddleware enabled for trace correlation")

# Security middleware — runs before auth to validate input
# P1-14 FIX: Removed /v1/query paths from skip list
# All untrusted input must pass through SecurityMiddleware validation
_security_config_l3 = add_security_validation_middleware(
    app,
    skip_validation_paths={
        "/health",
        "/metrics",
    },
    strict_mode=True,
)

class init_schemaResult(TypedDictModel):
    drop_existing: Any
    status: str

class delete_sourceResult(TypedDictModel):
    entities_deleted: Any
    relationships_deleted: Any
    source_id: Any
    status: str

class agent_workflowResult(TypedDictModel):
    results: Any
    steps_completed: Any
    workflow_type: Any

class _create_entityResult(TypedDictModel):
    entity_id: Any
    error: str | None = None
    success: bool

class _update_entityResult(TypedDictModel):
    error: str | None = None
    success: bool

class _delete_entityResult(TypedDictModel):
    error: str | None = None
    success: bool

add_governance_middleware(app)

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
    """Handle Value Fabric custom exceptions with shared error handling."""
    # Use shared handler for standardized response (Task 60: Error Hardening)
    if SHARED_ERROR_HANDLING_AVAILABLE:
        from value_fabric.shared.error_handling.handlers import (
            value_fabric_exception_handler as shared_handler,
        )
        response = await shared_handler(request, exc)
    else:
        # Fallback to legacy handler
        status_code = 500
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
        response = JSONResponse(status_code=status_code, content=exc.to_dict())

    # Preserve layer-specific metrics and logging
    logger.error(
        f"Value Fabric exception: {exc.error_code} at {request.method} {request.url.path} - {exc.message}",
        exc_info=_exception_trace(exc),
        extra={"trace_id": getattr(request.state, "trace_id", None)},
    )
    metrics = getattr(request.app.state, "metrics", None)
    if metrics:
        metrics.increment_errors(
            error_type=exc.error_code, component="api", namespace="layer3"
        )

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions with shared error handling."""
    # Use shared handler for standardized response (Task 60: Error Hardening)
    if SHARED_ERROR_HANDLING_AVAILABLE:
        from value_fabric.shared.error_handling.handlers import (
            http_exception_handler as shared_handler,
        )
        response = await shared_handler(request, exc)
    else:
        response = JSONResponse(status_code=exc.status_code, content=exc.detail)

    # Preserve layer-specific logging
    logger.warning(
        f"HTTP exception {exc.status_code} at {request.method} {request.url.path}: {exc.detail}",
        extra={"trace_id": getattr(request.state, "trace_id", None)},
    )

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with shared error handling."""
    # Use shared handler for standardized response (Task 60: Error Hardening)
    if SHARED_ERROR_HANDLING_AVAILABLE:
        from value_fabric.shared.error_handling.handlers import (
            global_exception_handler as shared_handler,
        )
        response = await shared_handler(request, exc)
    else:
        # Legacy fallback
        error_response = {
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "type": type(exc).__name__,
            "request_id": getattr(request.state, "request_id", None),
        }
        settings = _get_settings_with_fallback()
        if settings.log_level.upper() == "DEBUG":
            error_response["debug_info"] = {
                "exception": str(exc),
                "traceback": str(exc.__traceback__) if exc.__traceback__ else None,
            }
        response = JSONResponse(status_code=500, content=error_response)

    # Preserve layer-specific logging and metrics
    logger.error(
        f"Unhandled {type(exc).__name__} at {request.method} {request.url.path}: {str(exc)}",
        exc_info=_exception_trace(exc),
        extra={"trace_id": getattr(request.state, "trace_id", None)},
    )
    metrics = getattr(request.app.state, "metrics", None)
    if metrics:
        metrics.increment_errors(
            error_type=type(exc).__name__, component="api", namespace="layer3"
        )

    return response


async def check_dependencies(schema_initializer: Any | None = None) -> list[DependencyStatus]:
    """Check health of all dependencies.

    When startup has already placed the service in degraded mode because Neo4j
    is unavailable, avoid creating a new SchemaInitializer during the health
    probe. Docker health checks must be lightweight and must not spend the
    entire retry window opening fresh Bolt connections.
    """
    dependencies = []
    settings = _get_settings_with_fallback()

    # Check Neo4j
    try:
        if schema_initializer is not None and getattr(schema_initializer, "_driver", None) is None:
            dependencies.append(
                DependencyStatus(
                    name="neo4j",
                    status="degraded",
                    error="Neo4j not initialized",
                    details={
                        "uri": settings.neo4j_uri,
                        "database": settings.neo4j_database,
                    },
                )
            )
        else:
            from ..schema.initializer import SchemaInitializer

            neo4j_checker = schema_initializer if schema_initializer is not None else SchemaInitializer()
            # Mark ad-hoc checkers as non-owning so close() won't destroy the shared singleton driver
            if schema_initializer is None:
                neo4j_checker._owned_driver = False
            start_time = time.time()
            neo4j_health = await neo4j_checker.health_check()
            response_time = (time.time() - start_time) * 1000

            dependencies.append(
                DependencyStatus(
                    name="neo4j",
                    status=neo4j_health["status"],
                    response_time_ms=response_time,
                    error=neo4j_health.get("error"),
                    details={
                        "uri": settings.neo4j_uri,
                        "database": settings.neo4j_database,
                    },
                )
            )
    except Exception as e:
        dependencies.append(
            DependencyStatus(
                name="neo4j",
                status="unhealthy",
                error=str(e),
                details={"uri": settings.neo4j_uri},
            )
        )

    # Check Pinecone (if configured)
    if settings.pinecone_api_key:
        try:
            start_time = time.time()
            # Simple Pinecone health check would go here
            # For now, just check if API key is present
            response_time = (time.time() - start_time) * 1000
            dependencies.append(
                DependencyStatus(
                    name="pinecone",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"index": settings.pinecone_index},
                )
            )
        except Exception as e:
            dependencies.append(
                DependencyStatus(name="pinecone", status="unhealthy", error=str(e))
            )

    return dependencies


_app_metrics: Any | None = None


def set_app_metrics(metrics: Any | None) -> None:
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
        error_rate_percent=error_rate_percent,
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
                                    "database": "neo4j",
                                },
                            }
                        ],
                        "metrics": {
                            "uptime_seconds": 3600.0,
                            "memory_usage_mb": 1024.5,
                            "cpu_percent": 25.0,
                            "active_connections": 10,
                            "total_requests": 1500,
                            "error_rate_percent": 0.1,
                        },
                        "neo4j": {
                            "status": "healthy",
                            "database": "neo4j",
                            "uri": "bolt://localhost:7687",
                        },
                        "schema_status": {
                            "constraints": {"expected": 10, "found": 10, "missing": []},
                            "indexes": {"expected": 15, "found": 15, "missing": []},
                            "valid": True,
                        },
                    }
                }
            },
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
                                    "database": "neo4j",
                                },
                            }
                        ],
                        "metrics": {
                            "uptime_seconds": 3600.0,
                            "memory_usage_mb": 1024.5,
                            "cpu_percent": 25.0,
                            "active_connections": 0,
                            "total_requests": 1500,
                            "error_rate_percent": 5.2,
                        },
                        "neo4j": {
                            "status": "unhealthy",
                            "database": "neo4j",
                            "uri": "bolt://localhost:7687",
                            "error": "Connection timeout",
                        },
                        "schema_status": {
                            "constraints": {
                                "expected": 10,
                                "found": 8,
                                "missing": ["constraint_1", "constraint_2"],
                            },
                            "indexes": {"expected": 15, "found": 15, "missing": []},
                            "valid": False,
                        },
                    }
                }
            },
        },
    },
)
async def health_check(
    request: Request,
    schema_initializer=Depends(get_schema_initializer),
):
    """Check service health and Neo4j connectivity."""
    start_time = time.time()
    request_id = getattr(request.state, "request_id", "unknown")

    # Check dependencies
    dependencies = await check_dependencies(schema_initializer=schema_initializer)

    # Get metrics
    metrics = get_system_metrics()

    # Check Neo4j health (handle case where schema_initializer is None)
    neo4j_health = {"status": "unavailable", "message": "Neo4j not initialized"}
    schema_status = {"status": "unknown", "message": "Schema initializer not available"}

    if schema_initializer is not None:
        try:
            if getattr(schema_initializer, "_driver", None) is None:
                neo4j_health = {"status": "unavailable", "message": "Neo4j not initialized"}
                schema_status = {"status": "degraded", "message": "Schema initializer has no Neo4j driver"}
            else:
                health_result = await schema_initializer.health_check()
                neo4j_health = health_result.model_dump() if health_result else None
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
    if schema_initializer is None or (schema_initializer is not None and getattr(schema_initializer, "_driver", None) is None):
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
        "schema_status": schema_status,
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
                                    "database": "neo4j",
                                },
                            },
                            {
                                "name": "pinecone",
                                "status": "healthy",
                                "response_time_ms": 25.2,
                                "error": None,
                                "details": {"index": "value-fabric"},
                            },
                        ],
                        "metrics": {
                            "uptime_seconds": 3600.0,
                            "memory_usage_mb": 1024.5,
                            "cpu_percent": 25.0,
                            "active_connections": 10,
                            "total_requests": 1500,
                            "error_rate_percent": 0.1,
                        },
                        "neo4j": {
                            "status": "healthy",
                            "database": "neo4j",
                            "uri": "bolt://localhost:7687",
                        },
                        "schema_status": {
                            "constraints": {"expected": 10, "found": 10, "missing": []},
                            "indexes": {"expected": 15, "found": 15, "missing": []},
                            "valid": True,
                        },
                        "system_info": {
                            "platform": "Windows-10-10.0.19041-SP0",
                            "python_version": "3.11.0",
                            "cpu_count": 8,
                            "memory_total_gb": 16.0,
                            "disk_usage_gb": 250.5,
                        },
                        "configuration": {
                            "api_host": "0.0.0.0",
                            "api_port": 8001,
                            "log_level": "INFO",
                            "log_format": "json",
                            "neo4j_database": "neo4j",
                            "neo4j_max_pool_size": 50,
                            "pinecone_configured": True,
                        },
                    }
                }
            },
        }
    },
)
async def detailed_health_check(
    schema_initializer=Depends(get_schema_initializer),
    app_state: AppState = Depends(get_app_state),
):
    """Get detailed health information with system info and configuration."""
    time.time()

    # Basic health check
    dependencies = await check_dependencies(schema_initializer=schema_initializer)
    metrics = get_system_metrics()
    if getattr(schema_initializer, "_driver", None) is None:
        neo4j_health = {"status": "unavailable", "message": "Neo4j not initialized"}
        schema_status = {"status": "degraded", "message": "Schema initializer has no Neo4j driver"}
    else:
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
        "disk_usage_gb": psutil.disk_usage("/").used / (1024**3),
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
        configuration=configuration,
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
                        "constraints": {"expected": 10, "found": 10, "missing": []},
                        "indexes": {"expected": 15, "found": 15, "missing": []},
                        "valid": True,
                    }
                }
            },
        }
    },
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
    return init_schemaResult.model_validate({"status": "initialized", "drop_existing": drop_existing})


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
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
):
    """Ingest RDF data from Layer 2 extraction pipeline."""
    # Extract tenant_id from header or request body (header takes precedence)
    # Strip whitespace and fall back to "system" for empty/None values
    tenant_id = (x_tenant_id or request.tenant_id or "system").strip()
    if not tenant_id:
        tenant_id = "system"

    try:
        stats = await sync_manager.sync_extraction_result(
            rdf_data=request.rdf_data,
            source_id=request.source_id,
            extraction_job_id=request.extraction_job_id,
            content_hash=request.content_hash,
            tenant_id=tenant_id,
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
        raise HTTPException(status_code=500, detail="Ingestion failed. Please try again later.")


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
    return delete_sourceResult.model_validate({
        "status": "deleted",
        "source_id": source_id,
        "entities_deleted": stats["entities_deleted"],
        "relationships_deleted": stats["relationships_deleted"],
    })


# Query endpoints
# Canonical route. Legacy `/v1/query` remains for backward compatibility.


async def _execute_graph_rag_query(
    graph_rag,
    query_text: str,
    entity_type: str | None,
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


@app.post("/v1/graphrag", response_model=GraphRAGResponse)
async def graph_rag_legacy_alias(
    query: GraphRAGQuery,
    graph_rag=Depends(get_graph_rag),
):
    """Execute a GraphRAG query - backward-compatible alias for /v1/query/graph.

    This endpoint exists for backward compatibility with existing clients and tests.
    New implementations should use `/v1/query/graph` (preferred) or `/v1/query`.
    """
    try:
        deduplicator = get_request_deduplicator()

        if deduplicator:
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
                ttl=60,
                graph_rag=graph_rag,
                query_text=query.query,
                entity_type=query.entity_type,
                max_hops=query.max_hops,
                max_results=query.max_results,
            )
        else:
            return await _execute_graph_rag_query(
                graph_rag,
                query.query,
                query.entity_type,
                query.max_hops,
                query.max_results,
            )
    except Exception as e:
        logger.error(f"GraphRAG query failed: {e}")
        raise HTTPException(status_code=500, detail="Query processing failed. Please try again later.")


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
    - Backward-compatible alias: `/v1/graphrag`
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
        raise HTTPException(status_code=500, detail="Query processing failed. Please try again later.")


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
    entity_type: str | None,
    search_type: str,
    top_k: int,
    weights: dict | None,
) -> SearchResponse:
    """Execute hybrid search (extracted for caching/deduplication)."""
    if search_type == "vector":
        results = await hybrid_search.semantic_search(query, entity_type, top_k)
    elif search_type == "fulltext":
        results = await hybrid_search.fulltext_search(query, entity_type, top_k)
    else:  # hybrid
        results = await hybrid_search.search(
            query,
            [entity_type] if entity_type else None,
            top_k,
            weights,
        )

    # Convert HybridSearchResult dataclass objects to SearchResult Pydantic models
    search_results = [
        SearchResult(**asdict(result)) for result in results
    ]

    return SearchResponse(
        query=query,
        results=search_results,
        total_results=len(search_results),
        search_type=search_type,
    )


@app.post(
    "/v1/search/hybrid",
    response_model=SearchResponse,
    deprecated=True,
    summary="Deprecated: Use GET /v1/entities for entity listing",
)
@app.post("/v1/search", response_model=SearchResponse, deprecated=True)
async def hybrid_search(
    request: SearchRequest,
    hybrid_search=Depends(get_hybrid_search),
):
    """DEPRECATED: Use GET /v1/entities for entity listing with server-backed filtering.

    This endpoint is deprecated in favor of the canonical entity browser API.
    Sunset date: 2026-05-18 (30 days from deprecation).

    Legacy behavior: Execute hybrid search combining BM25, vector, and graph signals.
    Uses request deduplication to prevent redundant computation.

    Migration guide:
    - For entity listing: Use GET /v1/entities with filter parameters
    - For text search: Use search_text query param on /v1/entities
    - For type filtering: Use entity_types query param on /v1/entities
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
        raise HTTPException(status_code=500, detail="Search failed. Please try again later.")


# Entity endpoints
@app.get("/v1/entity/{entity_id}/context", response_model=EntityContextResponse)
async def get_entity_context(
    entity_id: str,
    hops: int = 2,
    relationship_types: list[str] | None = None,
    fields: str | None = Query(
        None, description="Comma-separated fields to include (e.g., 'id,name,type')"
    ),
    cursor: str | None = Query(None, description="Pagination cursor for neighbors"),
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
            center = {
                k: v
                for k, v in context["center"].items()
                if k in field_list or k == "id"
            }
            neighbors = [
                {k: v for k, v in n.items() if k in field_list or k == "id"}
                for n in context["neighbors"]
            ]
            relationships = [
                {
                    k: v
                    for k, v in r.items()
                    if k in field_list or k in ["source", "target", "type"]
                }
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
            paginated_neighbors = neighbors[offset : offset + limit]
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
        raise HTTPException(status_code=500, detail="Context retrieval failed. Please try again later.")


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
        raise HTTPException(status_code=500, detail="Value tree traversal failed. Please try again later.")


# ═══════════════════════════════════════════════════════════════════════════════
# Canonical Entity Browser Endpoints (High-Quality Contract)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/v1/entities", response_model=EntityListResponse)
async def list_entities(
    request: Request,  # Sprint 5: For tenant context extraction
    search_text: str | None = Query(None, max_length=200, description="Search across name and description"),
    entity_types: list[str] | None = Query(None, description="Filter by entity types"),
    domains: list[str] | None = Query(None, description="Filter by domains"),
    statuses: list[str] | None = Query(None, description="Filter by status: validated, pending, draft, deprecated"),
    min_confidence: float | None = Query(None, ge=0.0, le=1.0, description="Minimum confidence"),
    max_confidence: float | None = Query(None, ge=0.0, le=1.0, description="Maximum confidence"),
    limit: int = Query(25, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Results to skip"),
    sort_by: str = Query("updated_at", description="Field to sort by: name, updated_at, confidence, entity_type, status"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    _ctx: RequestContext = Depends(require_authenticated),
    neo4j_driver=Depends(get_neo4j_driver),
):
    """List entities with server-backed filtering and sorting.

    This endpoint provides a canonical entity summary contract optimized for
    browser table views. It supports filtering by domain, status, type, and
    confidence—eliminating the need for client-side filtering of large datasets.

    **Query Parameters:**
    - `search_text`: Full-text search across entity names and descriptions
    - `entity_types`: Filter by one or more entity types (e.g., Capability, UseCase)
    - `domains`: Filter by business domain (e.g., Finance, Healthcare)
    - `statuses`: Filter by lifecycle status (validated, pending, draft, deprecated)
    - `min_confidence`/`max_confidence`: Filter by confidence score range (0.0-1.0)
    - `sort_by`: Sort field (name, updated_at, confidence, entity_type, status)
    - `sort_order`: Sort direction (asc, desc)
    - `limit`/`offset`: Pagination control

    **Response:** Returns EntityListResponse with canonical EntitySummary objects.
    """
    try:
        # Sprint 5: Extract tenant context for multi-tenant security
        tenant_id = _extract_tenant_id(request)

        # Require tenant_id for multi-tenant security
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="tenant_id is required for entity listing"
            )

        # Build dynamic Cypher query based on filters
        where_clauses = ["e.tenant_id = $tenant_id"]  # Mandatory tenant filter
        params: dict[str, Any] = {"tenant_id": tenant_id}

        if search_text:
            where_clauses.append("(toLower(e.name) CONTAINS toLower($search_text) OR toLower(e.description) CONTAINS toLower($search_text))")
            params["search_text"] = search_text

        if entity_types:
            where_clauses.append("e.entity_type IN $entity_types")
            params["entity_types"] = entity_types

        if domains:
            where_clauses.append("e.domain IN $domains")
            params["domains"] = domains

        if statuses:
            where_clauses.append("e.status IN $statuses")
            params["statuses"] = statuses

        if min_confidence is not None:
            where_clauses.append("e.confidence >= $min_confidence")
            params["min_confidence"] = min_confidence

        if max_confidence is not None:
            where_clauses.append("e.confidence <= $max_confidence")
            params["max_confidence"] = max_confidence

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Validate sort_by to prevent injection
        valid_sort_fields = {"name", "updated_at", "confidence", "entity_type", "status", "created_at"}
        if sort_by not in valid_sort_fields:
            sort_by = "updated_at"
        sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"

        # Build and execute count query
        count_query = f"""
            MATCH (e:Entity)
            {where_clause}
            RETURN count(e) as total
        """

        async with neo4j_driver.session() as session:
            # Get total count
            count_result = await session.run(count_query, params)
            total_count_record = await count_result.single()
            total_count = total_count_record["total"] if total_count_record else 0

            # Build entity query with sorting and pagination
            entity_query = f"""
                MATCH (e:Entity)
                {where_clause}
                RETURN e {{
                    .id, .name, .entity_type, .domain, .status,
                    .confidence, .confidence_label, .description,
                    .updated_at, .source_name, .extraction_job_id,
                    .created_at, .created_by
                }}
                ORDER BY e.{sort_by} {sort_direction}
                SKIP $offset
                LIMIT $limit
            """
            params["offset"] = offset
            params["limit"] = limit

            # Execute entity query
            result = await session.run(entity_query, params)
            records = await result.fetch()

            # Build summary objects
            summaries = []
            for record in records:
                node = record["e"]
                # Derive status and confidence_label if not stored
                confidence = node.get("confidence", 0.0)
                status = node.get("status")
                if status is None:
                    if confidence >= 0.9:
                        status = "validated"
                    elif confidence >= 0.7:
                        status = "pending"
                    else:
                        status = "draft"

                confidence_label = node.get("confidence_label")
                if confidence_label is None:
                    if confidence >= 0.9:
                        confidence_label = "high"
                    elif confidence >= 0.7:
                        confidence_label = "medium"
                    else:
                        confidence_label = "low"

                summary = EntitySummary(
                    id=node.get("id", "unknown"),
                    name=node.get("name", "Unknown"),
                    entity_type=node.get("entity_type", "Capability"),
                    domain=node.get("domain"),
                    status=status,
                    confidence=confidence,
                    confidence_label=confidence_label,
                    description=node.get("description"),
                    updated_at=node.get("updated_at") or datetime.utcnow(),
                    source_name=node.get("source_name"),
                    extraction_job_id=node.get("extraction_job_id"),
                )
                summaries.append(summary)

            # Get available filter values for UI dropdowns
            available_domains = []
            available_sources = []
            if summaries:
                domains_query = """
                    MATCH (e:Entity {tenant_id: $tenant_id})
                    WHERE e.domain IS NOT NULL
                    RETURN collect(DISTINCT e.domain) as domains
                """
                domains_result = await session.run(domains_query, {"tenant_id": tenant_id})
                domains_record = await domains_result.single()
                if domains_record:
                    available_domains = domains_record["domains"]

                sources_query = """
                    MATCH (e:Entity {tenant_id: $tenant_id})
                    WHERE e.source_name IS NOT NULL
                    RETURN collect(DISTINCT e.source_name) as sources
                """
                sources_result = await session.run(sources_query, {"tenant_id": tenant_id})
                sources_record = await sources_result.single()
                if sources_record:
                    available_sources = sources_record["sources"]

        has_more = (offset + len(summaries)) < total_count

        return EntityListResponse(
            results=summaries,
            total_count=total_count,
            filtered_count=total_count,  # Total matching filters
            limit=limit,
            offset=offset,
            has_more=has_more,
            available_domains=available_domains,
            available_sources=available_sources,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity listing failed: {e}")
        raise HTTPException(status_code=500, detail="Entity listing failed. Please try again later.")


@app.get("/v1/entities/{{entity_id}}", response_model=EntityDetail)
async def get_entity_detail(
    entity_id: str,
    request: Request,  # Sprint 5: For tenant context extraction
    include_provenance: bool = Query(True, description="Include provenance chain"),
    include_relationships: bool = Query(True, description="Include related entities"),
    _ctx: RequestContext = Depends(require_authenticated),
    neo4j_driver=Depends(get_neo4j_driver),
):
    """Get full entity detail for inspection/drawer views.

    Returns the canonical EntityDetail shape with all fields from EntitySummary
    plus extended data: relationships, provenance, validation state, and raw properties.

    **Path Parameters:**
    - `entity_id`: Canonical entity identifier

    **Query Parameters:**
    - `include_provenance`: Whether to include audit trail (default: true)
    - `include_relationships`: Whether to include related entities (default: true)

    **Response:** Returns EntityDetail with full canonical contract.
    """
    try:
        # Sprint 5: Extract tenant context for multi-tenant security
        tenant_id = _extract_tenant_id(request)

        # Require tenant_id for multi-tenant security (Task 1: Multi-Tenancy Hardening)
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="tenant_id is required for entity access"
            )
        
        async with neo4j_driver.session() as session:
            # Fetch main entity with mandatory tenant filtering
            entity_query = """
                MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})
                RETURN e {
                    .id, .name, .entity_type, .domain, .status,
                    .confidence, .confidence_label, .description,
                    .updated_at, .source_name, .extraction_job_id,
                    .created_at, .created_by, .properties,
                    .validation_errors, .last_validated_at
                }
            """
            query_params = {"entity_id": entity_id, "tenant_id": tenant_id}
            result = await session.run(entity_query, query_params)
            record = await result.single()

            if not record:
                raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

            node = record["e"]

            # Derive status and confidence_label if not stored
            confidence = node.get("confidence", 0.0)
            status = node.get("status")
            if status is None:
                if confidence >= 0.9:
                    status = "validated"
                elif confidence >= 0.7:
                    status = "pending"
                else:
                    status = "draft"

            confidence_label = node.get("confidence_label")
            if confidence_label is None:
                if confidence >= 0.9:
                    confidence_label = "high"
                elif confidence >= 0.7:
                    confidence_label = "medium"
                else:
                    confidence_label = "low"

            # Build relationships if requested
            relationships = EntityRelationships()
            if include_relationships:
                # Outgoing relationships with mandatory tenant filtering
                outgoing_query = """
                    MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})-[r]->(target:Entity {tenant_id: $tenant_id})
                    RETURN type(r) as rel_type, target.id as target_id,
                           target.name as target_name, target.entity_type as target_type
                    LIMIT 5
                """
                outgoing_params = {"entity_id": entity_id, "tenant_id": tenant_id}
                outgoing_result = await session.run(outgoing_query, outgoing_params)
                outgoing_records = await outgoing_result.fetch()
                outgoing_rels = [
                    RelationshipPreview(
                        relationship_type=r["rel_type"],
                        target_entity_id=r["target_id"],
                        target_entity_name=r["target_name"],
                        target_entity_type=r["target_type"],
                    )
                    for r in outgoing_records
                ]

                # Incoming relationships with mandatory tenant filtering
                incoming_query = """
                    MATCH (source:Entity {tenant_id: $tenant_id})-[r]->(e:Entity {id: $entity_id, tenant_id: $tenant_id})
                    RETURN type(r) as rel_type, source.id as source_id,
                           source.name as source_name, source.entity_type as source_type
                    LIMIT 5
                """
                incoming_params = {"entity_id": entity_id, "tenant_id": tenant_id}
                incoming_result = await session.run(incoming_query, incoming_params)
                incoming_records = await incoming_result.fetch()
                incoming_rels = [
                    RelationshipPreview(
                        relationship_type=r["rel_type"],
                        target_entity_id=r["source_id"],
                        target_entity_name=r["source_name"],
                        target_entity_type=r["source_type"],
                    )
                    for r in incoming_records
                ]

                # Total count with mandatory tenant filtering
                count_query = """
                    MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})
                    OPTIONAL MATCH (e)-[r1]->(:Entity {tenant_id: $tenant_id})
                    OPTIONAL MATCH (e)<-[r2]-(:Entity {tenant_id: $tenant_id})
                    RETURN count(r1) + count(r2) as total
                """
                count_params = {"entity_id": entity_id, "tenant_id": tenant_id}
                count_result = await session.run(count_query, count_params)
                count_record = await count_result.single()
                total_rels = count_record["total"] if count_record else 0

                relationships = EntityRelationships(
                    total_count=total_rels,
                    incoming=incoming_rels,
                    outgoing=outgoing_rels,
                )

            # Build provenance if requested
            provenance: list[Any] = []
            if include_provenance:
                # For now, return basic provenance from entity fields
                # This can be extended to query a separate provenance store
                if node.get("extraction_job_id"):
                    provenance.append({
                        "event_type": "extracted",
                        "timestamp": node.get("created_at") or datetime.utcnow(),
                        "actor": node.get("extraction_job_id"),
                        "details": {"source": node.get("source_name")},
                    })

            # Build detail response
            detail = EntityDetail(
                id=node.get("id", "unknown"),
                name=node.get("name", "Unknown"),
                entity_type=node.get("entity_type", "Capability"),
                domain=node.get("domain"),
                status=status,
                confidence=confidence,
                confidence_label=confidence_label,
                description=node.get("description"),
                updated_at=node.get("updated_at") or datetime.utcnow(),
                source_name=node.get("source_name"),
                extraction_job_id=node.get("extraction_job_id"),
                created_at=node.get("created_at") or datetime.utcnow(),
                created_by=node.get("created_by"),
                provenance=provenance,
                relationships=relationships,
                properties=node.get("properties") or {},
                validation_errors=node.get("validation_errors") or [],
                last_validated_at=node.get("last_validated_at"),
            )

            return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity detail retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Entity detail retrieval failed. Please try again later.")


@app.post("/v1/entities/query", response_model=EntityListResponse)
async def query_entities(
    request: EntityFilterRequest,
    _ctx: RequestContext = Depends(require_authenticated),
    neo4j_driver=Depends(get_neo4j_driver),
):
    """Advanced entity filtering with complex criteria.

    Supports complex filter combinations not easily expressed in query parameters.
    Uses the same underlying logic as GET /v1/entities but with a request body.

    **Request Body:** EntityFilterRequest with full filter specification

    **Response:** Returns EntityListResponse with canonical EntitySummary objects.
    """
    try:
        # Delegate to the same implementation as GET endpoint
        # Convert request body to the same parameters
        return await list_entities(
            search_text=request.search_text,
            entity_types=request.entity_types,
            domains=request.domains,
            statuses=request.statuses,
            min_confidence=request.min_confidence,
            max_confidence=request.max_confidence,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            neo4j_driver=neo4j_driver,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed. Please try again later.")


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
            raise HTTPException(
                status_code=400, detail=f"Unknown algorithm: {request.algorithm}"
            )

        return CommunityDetectionResponse(
            algorithm=result["algorithm"],
            total_communities=result["total_communities"],
            valid_communities=result.get(
                "valid_communities", result["total_communities"]
            ),
            total_nodes=result.get("total_nodes", 0),
            communities=[
                Community(id=c["id"], size=c["size"], members=c["members"])
                for c in result["communities"]
            ],
            modularity=result.get("modularity"),
        )
    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        raise HTTPException(status_code=500, detail="Community detection failed. Please try again later.")


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
            raise HTTPException(
                status_code=400, detail=f"Unknown algorithm: {request.algorithm}"
            )

        return CentralityResponse(
            algorithm=result["algorithm"],
            total_ranked=result["total_ranked"],
            top_entities=result["top_entities"],
            by_layer=result.get("by_layer"),
            key_connectors=result.get("key_connectors"),
        )
    except Exception as e:
        logger.error(f"Centrality calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Centrality calculation failed. Please try again later.")


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
        raise HTTPException(status_code=500, detail="Similarity analysis failed. Please try again later.")


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
        raise HTTPException(status_code=500, detail="Entity comparison failed. Please try again later.")


# Batch Operations Endpoints
@app.post("/v1/batch/entities", response_model=BatchEntityResponse)
async def batch_entity_operations(
    request: BatchEntityRequest,
    fastapi_request: Request,  # Sprint 5: For tenant context
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

    # Sprint 5: Extract tenant context for multi-tenant security
    tenant_id = _extract_tenant_id(fastapi_request)

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
                    results.append(
                        {
                            "index": i,
                            "operation": "create",
                            "entity_id": result.get("entity_id"),
                            "success": result["success"],
                            "error": result.get("error"),
                        }
                    )

                elif operation.operation == "update":
                    # Update entity (Sprint 5: Pass tenant_id for security)
                    result = await _update_entity(neo4j_driver, operation, tenant_id)
                    if result["success"]:
                        successful += 1
                    else:
                        failed += 1
                    results.append(
                        {
                            "index": i,
                            "operation": "update",
                            "entity_id": operation.entity_id,
                            "success": result["success"],
                            "error": result.get("error"),
                        }
                    )

                elif operation.operation == "delete":
                    # Delete entity (Sprint 5: Pass tenant_id for security)
                    result = await _delete_entity(neo4j_driver, operation, tenant_id)
                    if result["success"]:
                        successful += 1
                    else:
                        failed += 1
                    results.append(
                        {
                            "index": i,
                            "operation": "delete",
                            "entity_id": operation.entity_id,
                            "success": result["success"],
                            "error": result.get("error"),
                        }
                    )

            except Exception as e:
                failed += 1
                results.append(
                    {
                        "index": i,
                        "operation": operation.operation,
                        "entity_id": operation.entity_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        # Atomic rollback if requested and any failures occurred
        if request.atomic and failed > 0 and created_entities:
            atomic_rollback = True
            logger.warning(
                f"Atomic rollback: deleting {len(created_entities)} created entities"
            )
            for entity_id in created_entities:
                try:
                    await _delete_entity_by_id(neo4j_driver, entity_id, tenant_id)
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
        raise HTTPException(status_code=500, detail="Batch operations failed. Please try again later.")


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
                    results.append(
                        {
                            "entity_id": entity_id,
                            "success": False,
                            "error": "Entity not found",
                        }
                    )
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

                results.append(
                    {
                        "entity_id": entity_id,
                        "success": True,
                        "metrics": metrics,
                    }
                )
                successful += 1

            except Exception as e:
                logger.warning(f"Batch analytics failed for {entity_id}: {e}")
                results.append(
                    {
                        "entity_id": entity_id,
                        "success": False,
                        "error": str(e),
                    }
                )
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
        raise HTTPException(status_code=500, detail="Batch analytics failed. Please try again later.")


# Helper functions for batch operations
async def _create_entity(driver, operation: BatchEntityOperation) -> dict[str, Any]:
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
                    "entity_type": operation.entity_type.value
                    if operation.entity_type
                    else "Unknown",
                    "properties": operation.properties or {},
                },
            )
            record = await result.single()
            if record:
                return _create_entityResult.model_validate({"success": True, "entity_id": record["entity_id"]})
            return _create_entityResult.model_validate({"success": False, "error": "Failed to create entity"})
    except Exception as e:
        return _create_entityResult.model_validate({"success": False, "error": str(e)})


async def _update_entity(
    driver, operation: BatchEntityOperation, tenant_id: str | None = None
) -> dict[str, Any]:
    """Update a single entity in Neo4j.

    Args:
        driver: Neo4j async driver
        operation: Batch entity operation with entity_id and properties
        tenant_id: Optional tenant ID for multi-tenant scoping

    Returns:
        Dict with success flag or error message
    """
    try:
        # Require tenant_id for multi-tenant security (Task 1: Multi-Tenancy Hardening)
        if not tenant_id:
            return _update_entityResult.model_validate({"success": False, "error": "tenant_id is required for entity updates"})
        
        async with driver.session() as session:
            # Update entity with mandatory tenant filtering
            query = """
            MATCH (n {id: $entity_id, tenant_id: $tenant_id})
            SET n += $properties, n.updated_at = datetime()
            RETURN n.id as entity_id
            """
            params = {
                "entity_id": operation.entity_id,
                "tenant_id": tenant_id,
                "properties": operation.properties or {},
            }
            result = await session.run(query, params)
            record = await result.single()
            if record:
                return _update_entityResult.model_validate({"success": True})
            return _update_entityResult.model_validate({"success": False, "error": "Entity not found"})
    except Exception as e:
        return _update_entityResult.model_validate({"success": False, "error": str(e)})


async def _delete_entity(
    driver, operation: BatchEntityOperation, tenant_id: str | None = None
) -> dict[str, Any]:
    """Delete a single entity from Neo4j.

    Args:
        driver: Neo4j async driver
        operation: Batch entity operation with entity_id
        tenant_id: Optional tenant ID for multi-tenant scoping

    Returns:
        Dict with success flag or error message
    """
    try:
        # Require tenant_id for multi-tenant security (Task 1: Multi-Tenancy Hardening)
        if not tenant_id:
            return _delete_entityResult.model_validate({"success": False, "error": "tenant_id is required for entity deletion"})
        
        async with driver.session() as session:
            # Delete entity with mandatory tenant filtering
            query = """
            MATCH (n {id: $entity_id, tenant_id: $tenant_id})
            DETACH DELETE n
            RETURN count(n) as deleted
            """
            params = {"entity_id": operation.entity_id, "tenant_id": tenant_id}
            result = await session.run(query, params)
            record = await result.single()
            if record and record["deleted"] > 0:
                return _delete_entityResult.model_validate({"success": True})
            return _delete_entityResult.model_validate({"success": False, "error": "Entity not found"})
    except Exception as e:
        return _delete_entityResult.model_validate({"success": False, "error": str(e)})


async def _delete_entity_by_id(
    driver, entity_id: str, tenant_id: str | None = None
) -> None:
    """Delete entity by ID (used for atomic rollback).

    Args:
        driver: Neo4j async driver
        entity_id: Entity ID to delete
        tenant_id: Optional tenant ID for multi-tenant scoping
    """
    # Require tenant_id for multi-tenant security (Task 1: Multi-Tenancy Hardening)
    if not tenant_id:
        raise ValueError("tenant_id is required for entity deletion")
    
    async with driver.session() as session:
        # Delete entity with mandatory tenant filtering
        query = "MATCH (n {id: $entity_id, tenant_id: $tenant_id}) DETACH DELETE n"
        params = {"entity_id": entity_id, "tenant_id": tenant_id}
        await session.run(query, params)


# Agent endpoints (from value_fabric_backend_logic_specifications.md)
@app.post("/v1/agents/value-tree-projection")
async def value_tree_projection(
    request: dict[str, Any],
    agent=Depends(get_value_tree_projection_agent),
):
    """Execute value tree projection agent for traversal and semantic matching."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, "to_dict") else result.__dict__
    except Exception as e:
        logger.error(f"Value tree projection failed: {e}")
        raise HTTPException(status_code=500, detail="Value tree projection failed. Please try again later.")


@app.post("/v1/agents/whitespace-analysis")
async def whitespace_analysis(
    request: dict[str, Any],
    agent=Depends(get_whitespace_analysis_agent),
):
    """Execute whitespace analysis agent for gap identification and account planning."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, "to_dict") else result.__dict__
    except Exception as e:
        logger.error(f"Whitespace analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Whitespace analysis failed. Please try again later.")


@app.post("/v1/agents/roi-calculation")
async def roi_calculation(
    request: dict[str, Any],
    agent=Depends(get_roi_calculation_agent),
):
    """Execute ROI calculation agent for formula execution and sensitivity analysis."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, "to_dict") else result.__dict__
    except Exception as e:
        logger.error(f"ROI calculation failed: {e}")
        raise HTTPException(status_code=500, detail="ROI calculation failed. Please try again later.")


@app.post("/v1/agents/narrative-synthesis")
async def narrative_synthesis(
    request: dict[str, Any],
    agent=Depends(get_narrative_synthesis_agent),
):
    """Execute narrative synthesis agent for report generation."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, "to_dict") else result.__dict__
    except Exception as e:
        logger.error(f"Narrative synthesis failed: {e}")
        raise HTTPException(status_code=500, detail="Narrative synthesis failed. Please try again later.")


@app.post("/v1/agents/provenance-tracking")
async def provenance_tracking(
    request: dict[str, Any],
    agent=Depends(get_provenance_tracking_agent),
):
    """Execute provenance tracking agent for lineage and decision traces."""
    try:
        result = await agent.execute(request)
        return result.to_dict() if hasattr(result, "to_dict") else result.__dict__
    except Exception as e:
        logger.error(f"Provenance tracking failed: {e}")
        raise HTTPException(status_code=500, detail="Provenance tracking failed. Please try again later.")


@app.post("/v1/agents/workflow")
async def agent_workflow(
    workflow_type: str,
    context: dict[str, Any],
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
            gap_result = await whitespace_agent.execute(
                {"operation": "gap_analysis", **context}
            )
            results.append(
                {"step": 1, "agent": "WhitespaceAnalysisAgent", "result": gap_result}
            )

            # Step 2: Account plan synthesis
            plan_result = await whitespace_agent.execute(
                {"operation": "account_plan", **context}
            )
            results.append(
                {"step": 2, "agent": "WhitespaceAnalysisAgent", "result": plan_result}
            )

            # Step 3: Record provenance
            await provenance_agent.execute(
                {
                    "operation": "create_decision_trace",
                    "workflow_id": "whitespace_analysis_v1",
                    "workflow_instance_id": f"ws-{datetime.utcnow().timestamp()}",
                    "output_type": "account_plan",
                    "output_id": plan_result.output.get("plan_id", "unknown"),
                    "steps": results,
                }
            )

        elif workflow_type == "business_case":
            # Step 1: Value tree projection
            vt_result = await value_tree_agent.execute(
                {"operation": "upward_traversal", **context}
            )
            results.append(
                {"step": 1, "agent": "ValueTreeProjectionAgent", "result": vt_result}
            )

            # Step 2: ROI calculation
            roi_result = await roi_agent.execute({"operation": "calculate", **context})
            results.append(
                {"step": 2, "agent": "ROICalculationAgent", "result": roi_result}
            )

            # Step 3: Narrative synthesis
            narrative_result = await narrative_agent.execute(
                {"operation": "generate_executive_summary", **context}
            )
            results.append(
                {
                    "step": 3,
                    "agent": "NarrativeSynthesisAgent",
                    "result": narrative_result,
                }
            )

            # Step 4: Record provenance
            await provenance_agent.execute(
                {
                    "operation": "create_decision_trace",
                    "workflow_id": "business_case_v1",
                    "workflow_instance_id": f"bc-{datetime.utcnow().timestamp()}",
                    "output_type": "business_case",
                    "output_id": narrative_result.output.get("narrative_id", "unknown"),
                    "steps": results,
                }
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown workflow type: {workflow_type}"
            )

        return agent_workflowResult.model_validate({
            "workflow_type": workflow_type,
            "steps_completed": len(results),
            "results": results,
        })


    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent workflow failed: {e}")
        raise HTTPException(status_code=500, detail="Agent workflow failed. Please try again later.")


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
    request: Request | None = None,  # Sprint 5: For tenant context
):
    """Get full provenance trail for an entity."""
    # Validate entity_id
    if not entity_id or not entity_id.strip():
        raise HTTPException(status_code=400, detail="entity_id is required")

    # Sprint 5: Extract tenant context for multi-tenant security
    tenant_id = _extract_tenant_id(request)

    # Sanitize entity_id to prevent injection
    entity_id = entity_id.strip()
    if len(entity_id) > 255:
        raise HTTPException(
            status_code=400, detail="entity_id too long (max 255 chars)"
        )

    try:
        # Query Neo4j for entity and its provenance
        neo4j = app_state.neo4j_manager
        if not neo4j:
            raise HTTPException(status_code=503, detail="Neo4j not available")

        # Require tenant_id for multi-tenant security (Task 1: Multi-Tenancy Hardening)
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="tenant_id is required for provenance access"
            )
        
        # Get entity details with mandatory tenant filtering
        entity_query = """
        MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})
        RETURN e.id as entity_id, e.type as entity_type, e.name as entity_name,
               e.created_at as created_at, e.source as source,
               e.extraction_job_id as extraction_job_id, e.confidence as confidence_score
        LIMIT 1
        """
        query_params = {"entity_id": entity_id, "tenant_id": tenant_id}
        entity_result = await neo4j.execute_query(entity_query, query_params)

        if not entity_result:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        record = entity_result[0]

        # Build provenance steps from related audit events with mandatory tenant filtering
        steps_query = """
        MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})
        OPTIONAL MATCH (e)-[:AUDIT_OF]->(a:AuditEvent)
        WITH a
        WHERE a IS NOT NULL
        RETURN a.step as step, a.label as label, a.detail as detail,
               a.timestamp as timestamp, a.agent as agent, a.entity_id as step_entity_id
        ORDER BY a.step
        """
        steps_params = {"entity_id": entity_id, "tenant_id": tenant_id}
        steps_result = await neo4j.execute_query(steps_query, steps_params)

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
        raise HTTPException(status_code=500, detail="Provenance query failed. Please try again later.")


@app.get(
    "/v1/audit/logs",
    response_model=AuditLogResponse,
    tags=["Audit"],
    summary="List Audit Logs",
    description="Query system audit events from Neo4j provenance or API access logs",
)
async def list_audit_logs(
    source: Literal["all", "provenance", "access"] = Query(
        "all", description="Source: 'provenance', 'access', or 'all'"
    ),
    from_date: datetime | None = Query(None, description="Start date filter"),
    to_date: datetime | None = Query(None, description="End date filter"),
    entity_type: str | None = Query(None, description="Filter by entity type"),
    event_type: str | None = Query(None, description="Filter by event type"),
    agent: str | None = Query(None, description="Filter by agent"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Entries per page"),
    app_state: AppState = Depends(get_app_state),
):
    """List audit log entries with filtering."""
    try:
        entries: list[AuditLogEntry] = []

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
                    logger.warning(
                        f"Neo4j audit query failed (schema may not exist yet): {neo4j_error}"
                    )
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
    description="Generate PDF from business case via L4 DocumentExportTool",
)
async def export_document(
    request: DocumentExportRequest,
    app_state: AppState = Depends(get_app_state),
):
    """Export business case to PDF via L4 DocumentExportTool.

    Calls Layer 4 analysis export endpoint to generate PDF from business case data.
    Returns export status and download URL.
    """
    export_id = f"exp-{uuid.uuid4().hex[:8]}"

    try:
        # Get L4 API URL from environment
        l4_api_url = os.getenv("LAYER4_API_URL", "http://layer4-agents:8004")

        # Call L4 analysis export endpoint
        async with httpx.AsyncClient(timeout=60.0) as client:
            l4_response = await client.get(
                f"{l4_api_url}/v1/analysis/cases/{request.business_case_id}/export",
                params={"format": request.format},
                headers={"Content-Type": "application/json"},
            )

            if l4_response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Business case {request.business_case_id} not found"
                )
            elif l4_response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"L4 export service error: {l4_response.text}"
                )

            l4_data = l4_response.json()

            # Check if export is ready or if we need to trigger generation
            if not l4_data.get("download_ready"):
                # Export not ready - trigger PDF generation via L4
                logger.info(f"Triggering PDF generation for case {request.business_case_id}")

                # Call L4 document generation endpoint
                gen_response = await client.post(
                    f"{l4_api_url}/v1/tools/export-document",
                    json={
                        "document_type": request.document_type,
                        "business_case_id": request.business_case_id,
                        "format": request.format,
                        "include_provenance": request.include_provenance,
                    },
                    timeout=120.0,  # Longer timeout for PDF generation
                )

                if gen_response.status_code != 200:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Document generation failed: {gen_response.text}"
                    )

                gen_data = gen_response.json()

                return DocumentExportResponse(
                    export_id=export_id,
                    status="completed" if gen_data.get("success") else "failed",
                    download_url=gen_data.get("download_url"),
                    format=request.format,
                    expires_at=datetime.utcnow() + timedelta(hours=24) if gen_data.get("success") else None,
                    message="PDF generated successfully" if gen_data.get("success") else gen_data.get("error"),
                )

            # Export already ready
            return DocumentExportResponse(
                export_id=export_id,
                status="completed",
                download_url=l4_data.get("document_url"),
                format=request.format,
                expires_at=datetime.utcnow() + timedelta(hours=24),
                message="Document ready for download",
            )

    except httpx.TimeoutException:
        logger.error(f"Document export timed out for case {request.business_case_id}")
        raise HTTPException(status_code=504, detail="Document generation timed out")
    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to L4 service: {e}")
        raise HTTPException(status_code=503, detail="Document generation service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document export failed: {str(e)}")


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
                            {
                                "id": "cap-1",
                                "label": "CRM Integration",
                                "type": "Capability",
                                "confidence": 0.95,
                            },
                            {
                                "id": "uc-1",
                                "label": "Pipeline Forecast",
                                "type": "UseCase",
                                "confidence": 0.88,
                            },
                        ],
                        "edges": [
                            {
                                "source": "cap-1",
                                "target": "uc-1",
                                "type": "ENABLES",
                                "weight": 1.0,
                            }
                        ],
                        "stats": {
                            "total_nodes": 8532,
                            "total_edges": 24156,
                            "node_types": {"Capability": 2847, "UseCase": 1923},
                            "communities": 47,
                            "density": 0.03,
                        },
                    }
                }
            },
        },
        503: {"description": "Database unavailable"},
    },
)
async def get_full_graph(
    limit: int = 1000,
    app_state: AppState = Depends(get_app_state),
    request: Request | None = None,  # Sprint 5: For tenant context extraction
) -> GraphResponse:
    """Get the full knowledge graph for visualization.

    Returns nodes, edges, and statistics. Results are limited for performance.
    """
    try:
        neo4j = app_state.neo4j_manager
        if not neo4j:
            raise HTTPException(status_code=503, detail="Neo4j not available")

        # Sprint 5: Extract tenant context for multi-tenant security
        tenant_id = _extract_tenant_id(request)

        # Require tenant_id for multi-tenant security
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="tenant_id is required for graph access"
            )

        # Query for nodes with limit and tenant filter
        nodes_query = """
        MATCH (n {tenant_id: $tenant_id})
        WHERE n.id IS NOT NULL
        RETURN n.id as id, n.name as label, n.type as type,
               n.confidence as confidence, n.x as x, n.y as y
        LIMIT $limit
        """
        nodes_result = await neo4j.execute_query(nodes_query, {"tenant_id": tenant_id, "limit": limit})

        nodes = []
        node_ids = set()
        node_types: dict[str, int] = {}

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
                properties={"name": r.get("label")},
            )
            nodes.append(node)
            node_ids.add(r.get("id"))

        # Query for edges between returned nodes with tenant filter
        edges_query = """
        MATCH (a {tenant_id: $tenant_id})-[r]->(b {tenant_id: $tenant_id})
        WHERE a.id IN $node_ids AND b.id IN $node_ids
        RETURN a.id as source, b.id as target, type(r) as rel_type,
               r.weight as weight
        """
        edges_result = await neo4j.execute_query(
            edges_query, {"tenant_id": tenant_id, "node_ids": list(node_ids)}
        )

        edges = []
        for r in edges_result:
            edges.append(
                GraphEdge(
                    source=r.get("source"),
                    target=r.get("target"),
                    type=r.get("rel_type", "RELATED_TO"),
                    weight=r.get("weight") or 1.0,
                )
            )

        # Calculate stats with tenant filter
        total_nodes_query = "MATCH (n {tenant_id: $tenant_id}) RETURN count(n) as total"
        total_edges_query = "MATCH (:Entity {tenant_id: $tenant_id})-[r]->(:Entity {tenant_id: $tenant_id}) RETURN count(r) as total"

        total_nodes_result = await neo4j.execute_query(total_nodes_query, {"tenant_id": tenant_id})
        total_edges_result = await neo4j.execute_query(total_edges_query, {"tenant_id": tenant_id})

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
            density=round(density, 4),
        )

        return GraphResponse(nodes=nodes, edges=edges, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve graph: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve graph: {str(e)}"
        )


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
                            {
                                "id": "cap-1",
                                "label": "CRM Integration",
                                "type": "Capability",
                            },
                            {
                                "id": "uc-1",
                                "label": "Pipeline Forecast",
                                "type": "UseCase",
                            },
                        ],
                        "edges": [
                            {"source": "cap-1", "target": "uc-1", "type": "ENABLES"}
                        ],
                        "depth": 2,
                        "stats": {
                            "total_nodes": 15,
                            "total_edges": 22,
                            "node_types": {"Capability": 1, "UseCase": 3},
                        },
                    }
                }
            },
        },
        404: {"description": "Entity not found"},
        503: {"description": "Database unavailable"},
    },
)
async def get_entity_subgraph(
    entity_id: str,
    depth: int = 2,
    app_state: AppState = Depends(get_app_state),
    request: Request | None = None,  # Sprint 5: For tenant context
) -> SubgraphResponse:
    """Get subgraph centered on a specific entity.

    - **entity_id**: ID of the central entity
    - **depth**: How many hops to traverse (1-5, default 2)
    """
    try:
        neo4j = app_state.neo4j_manager
        if not neo4j:
            raise HTTPException(status_code=503, detail="Neo4j not available")

        # Sprint 5: Extract tenant context for multi-tenant security
        tenant_id = _extract_tenant_id(request)

        # Clamp depth
        depth = max(1, min(depth, 5))

        # Require tenant_id for multi-tenant security (Task 1: Multi-Tenancy Hardening)
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="tenant_id is required for value tree access"
            )
        
        # Query for root entity with mandatory tenant filtering
        root_query = """
        MATCH (n {id: $entity_id, tenant_id: $tenant_id})
        RETURN n.id as id, n.name as label, n.type as type,
               n.confidence as confidence
        """
        root_params = {"entity_id": entity_id, "tenant_id": tenant_id}
        root_result = await neo4j.execute_query(root_query, root_params)

        if not root_result:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        root_record = root_result[0]

        # Query for connected nodes up to depth with mandatory tenant filtering
        subgraph_query = """
        MATCH path = (root {id: $entity_id, tenant_id: $tenant_id})-[*1..$depth]-(connected {tenant_id: $tenant_id})
        WHERE root.id IS NOT NULL AND connected.id IS NOT NULL
        RETURN root, connected, relationships(path) as rels,
               length(path) as path_length
        """
        subgraph_params = {"entity_id": entity_id, "depth": depth, "tenant_id": tenant_id}
        subgraph_result = await neo4j.execute_query(subgraph_query, subgraph_params)

        # Collect unique nodes and edges
        nodes_map: dict[str, GraphNode] = {}
        edges_map: dict[str, GraphEdge] = {}
        node_types: dict[str, int] = {}

        # Add root node
        root_type = root_record.get("type", "Unknown")
        node_types[root_type] = node_types.get(root_type, 0) + 1
        nodes_map[entity_id] = GraphNode(
            id=entity_id,
            label=root_record.get("label") or entity_id,
            type=root_type,
            confidence=root_record.get("confidence") or 0.8,
            properties={"is_root": True},
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
                        properties={},
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
                                weight=rel.get("weight", 1.0),
                            )

        nodes = list(nodes_map.values())
        edges = list(edges_map.values())

        stats = GraphStats(
            total_nodes=len(nodes),
            total_edges=len(edges),
            node_types=node_types,
            communities=0,
            density=0.0
            if len(nodes) <= 1
            else (2 * len(edges)) / (len(nodes) * (len(nodes) - 1)),
        )

        return SubgraphResponse(
            root_entity_id=entity_id, nodes=nodes, edges=edges, depth=depth, stats=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve subgraph for {entity_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve subgraph: {str(e)}"
        )


@app.get(
    "/v1/graph/subgraph",
    response_model=SubgraphResponse,
    tags=["Graph"],
    summary="Get Query-Based Subgraph",
    description="Returns a coherent subgraph based on a search query or centered on a specific entity. Returns both nodes and edges in a single call.",
    responses={
        200: {
            "description": "Subgraph retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "root_entity_id": "",
                        "nodes": [{"id": "cap-1", "label": "AI Processing", "type": "Capability"}],
                        "edges": [{"source": "cap-1", "target": "uc-1", "type": "ENABLES"}],
                        "depth": 2,
                        "stats": {"node_count": 10, "edge_count": 15, "density": 0.33},
                    }
                }
            },
        },
        400: {"description": "Invalid parameters - query or center_entity_id required"},
        500: {"description": "Internal server error"},
    },
)
async def get_query_subgraph(
    query: str | None = Query(None, description="Search query to find matching entities"),
    center_entity_id: str | None = Query(None, description="Center entity ID for expansion mode"),
    depth: int = Query(2, ge=1, le=3, description="Traversal depth (1-3)"),
    limit: int = Query(100, ge=1, le=500, description="Max nodes to return"),
    entity_types: list[str] | None = Query(None, description="Filter by entity types"),
    relationship_types: list[str] | None = Query(None, description="Filter by relationship types"),
    hybrid_search=Depends(get_hybrid_search),
    graph_rag=Depends(get_graph_rag),
    app_state: AppState = Depends(get_app_state),
    request: Request | None = None,  # Sprint 5: For tenant context
) -> SubgraphResponse:
    """
    Get a coherent subgraph based on query or center entity.

    **Query Mode**: Provide `query` parameter to search for entities, returns subgraph
    with matching nodes + 1-hop neighbors.

    **Center Mode**: Provide `center_entity_id` to expand N hops from that node.

    **Parameters:**
    - `query`: Search string to find entities (query mode)
    - `center_entity_id`: Specific entity to expand from (center mode)
    - `depth`: How many hops to traverse (1-3, default 2)
    - `limit`: Maximum nodes to return (default 100)
    - `entity_types`: Optional filter (e.g., ["Capability", "UseCase"])
    - `relationship_types`: Optional filter (e.g., ["ENABLES", "BENEFITS"])

    **Note:** Requires either `query` or `center_entity_id`, not both.
    """
    if not query and not center_entity_id:
        raise HTTPException(
            status_code=400,
            detail="Either 'query' or 'center_entity_id' parameter is required"
        )

    try:
        neo4j = app_state.neo4j
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        root_id = center_entity_id or ""

        # Sprint 5: Extract tenant context for multi-tenant security
        tenant_id = _extract_tenant_id(request)
        
        # Require tenant_id for multi-tenant security (Task 1: Multi-Tenancy Hardening)
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="tenant_id is required for graph explorer access"
            )

        if center_entity_id:
            # Center mode: expand N hops from specific entity with mandatory tenant filtering
            root_result = await neo4j.execute_query(
                "MATCH (root {id: $entity_id, tenant_id: $tenant_id}) RETURN root",
                {"entity_id": center_entity_id, "tenant_id": tenant_id}
            )
            if not root_result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Entity {center_entity_id} not found"
                )

            # Build relationship filter if specified
            rel_filter = ""
            if relationship_types:
                # Validate relationship types - only allow uppercase alphanumeric and underscores
                import re
                valid_rel_pattern = re.compile(r'^[A-Z_][A-Z0-9_]*$')
                validated_types = [r for r in relationship_types if valid_rel_pattern.match(r)]
                if validated_types:
                    rel_filter = f"AND ALL(r IN relationships(path) WHERE type(r IN [{', '.join(repr(r) for r in validated_types)}]))"

            # Query for connected nodes with mandatory tenant filtering
            subgraph_query = f"""
            MATCH path = (root {{id: $entity_id, tenant_id: $tenant_id}})-[*1..{depth}]-(connected {{tenant_id: $tenant_id}})
            WHERE root.id IS NOT NULL AND connected.id IS NOT NULL
            {rel_filter}
            WITH root, connected, relationships(path) as rels, length(path) as hops
            RETURN root, collect(DISTINCT connected) as neighbors,
                   collect(DISTINCT rels) as paths, max(hops) as max_hops
            LIMIT $limit
            """
            query_params = {"entity_id": center_entity_id, "tenant_id": tenant_id, "limit": limit}
            result = await neo4j.execute_query(subgraph_query, query_params)

            if result:
                record = result[0]
                root_data = record.get("root", {})
                neighbors = record.get("neighbors", [])
                paths = record.get("paths", [])

                # Add root node
                if root_data:
                    nodes.append(GraphNode(
                        id=root_data.get("id", center_entity_id),
                        label=root_data.get("name", root_data.get("id", "Unknown")),
                        type=root_data.get("entity_type", "Unknown"),
                        properties={k: v for k, v in root_data.items() if k not in ["id", "name", "entity_type"]},
                    ))

                # Add neighbor nodes
                for neighbor in neighbors:
                    if neighbor and neighbor.get("id"):
                        nodes.append(GraphNode(
                            id=neighbor.get("id"),
                            label=neighbor.get("name", neighbor.get("id", "Unknown")),
                            type=neighbor.get("entity_type", "Unknown"),
                            properties={k: v for k, v in neighbor.items() if k not in ["id", "name", "entity_type"]},
                        ))

                # Extract edges from paths
                edge_keys = set()
                for rel_list in paths:
                    for rel in rel_list:
                        if hasattr(rel, "start_node") and hasattr(rel, "end_node"):
                            src = rel.start_node.get("id")
                            tgt = rel.end_node.get("id")
                            edge_key = f"{src}-{tgt}-{rel.type}"
                            if src and tgt and edge_key not in edge_keys:
                                edge_keys.add(edge_key)
                                edges.append(GraphEdge(
                                    source=src,
                                    target=tgt,
                                    type=rel.type,
                                    properties={},
                                ))

        else:
            # Query mode: search for entities, return subgraph with 1-hop expansion
            search_results = await hybrid_search.search(
                query=query,
                top_k=min(limit, 50),
                entity_type_filter=entity_types[0] if entity_types else None,
            )

            if not search_results:
                # Return empty subgraph
                return SubgraphResponse(
                    root_entity_id="",
                    nodes=[],
                    edges=[],
                    depth=depth,
                    stats=GraphStats(total_nodes=0, total_edges=0, density=0.0),
                )

            # Collect seed entity IDs
            seed_ids = [r.entity_id for r in search_results if r.entity_id]
            if not seed_ids:
                return SubgraphResponse(
                    root_entity_id="",
                    nodes=[],
                    edges=[],
                    depth=depth,
                    stats=GraphStats(total_nodes=0, total_edges=0, density=0.0),
                )

            # Query for 1-hop expansion from all seeds with mandatory tenant filtering
            seed_query = """
            UNWIND $seed_ids as seed_id
            MATCH (seed {id: seed_id, tenant_id: $tenant_id})
            OPTIONAL MATCH (seed)-[r]-(neighbor {tenant_id: $tenant_id})
            WHERE neighbor.id IS NOT NULL
            RETURN seed, collect(DISTINCT neighbor) as neighbors,
                   collect(DISTINCT r) as rels
            """
            result = await neo4j.execute_query(
                seed_query, {"seed_ids": seed_ids[:20], "tenant_id": tenant_id}  # Limit seeds for performance
            )

            node_ids = set()
            for record in result:
                seed = record.get("seed")
                neighbors = record.get("neighbors", [])
                rels = record.get("rels", [])

                # Add seed node
                if seed and seed.get("id") and seed.get("id") not in node_ids:
                    node_ids.add(seed.get("id"))
                    nodes.append(GraphNode(
                        id=seed.get("id"),
                        label=seed.get("name", seed.get("id", "Unknown")),
                        type=seed.get("entity_type", "Unknown"),
                        properties={k: v for k, v in seed.items() if k not in ["id", "name", "entity_type"]},
                    ))

                # Add neighbors and edges
                for neighbor in neighbors:
                    if neighbor and neighbor.get("id") and neighbor.get("id") not in node_ids:
                        node_ids.add(neighbor.get("id"))
                        nodes.append(GraphNode(
                            id=neighbor.get("id"),
                            label=neighbor.get("name", neighbor.get("id", "Unknown")),
                            type=neighbor.get("entity_type", "Unknown"),
                            properties={k: v for k, v in neighbor.items() if k not in ["id", "name", "entity_type"]},
                        ))

                # Add edges
                for rel in rels:
                    if hasattr(rel, "start_node") and hasattr(rel, "end_node"):
                        src = rel.start_node.get("id")
                        tgt = rel.end_node.get("id")
                        if src and tgt and src in node_ids and tgt in node_ids:
                            edges.append(GraphEdge(
                                source=src,
                                target=tgt,
                                type=rel.type,
                                properties={},
                            ))

        # Calculate stats
        node_count = len(nodes)
        edge_count = len(edges)
        density = 0.0 if node_count <= 1 else (2 * edge_count) / (node_count * (node_count - 1))

        return SubgraphResponse(
            root_entity_id=root_id,
            nodes=nodes,
            edges=edges,
            depth=depth,
            stats=GraphStats(
                total_nodes=node_count,
                total_edges=edge_count,
                density=density,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve subgraph: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve subgraph: {str(e)}"
        )


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
