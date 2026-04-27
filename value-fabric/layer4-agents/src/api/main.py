"""FastAPI main application for Layer 4 Agentic Workflow Engine.

P1-29: OpenTelemetry tracing integration for observability.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..services.oidc_cleanup import OIDCCleanupTask

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Task 60/61: Shared error handling and request correlation
from shared.error_handling import RequestIDMiddleware, register_exception_handlers
SHARED_ERROR_HANDLING_AVAILABLE = True

# Shared identity imports
from shared.identity.feature_flags import init_feature_flags, register_feature_flag_lookup

# Governance middleware replaces the old TenantMiddleware
# P1-29: OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Hard imports - fail fast if security components unavailable
from shared.identity.middleware import GovernanceMiddleware
from shared.identity.rate_limiter import RedisRateLimiter
from shared.identity.vault_check import is_vault_healthy
from shared.security import add_security_middleware, SecurityConfig

from ..config.checkpoint import CheckpointConfig
from ..config.settings import settings
from ..database import close_db, db_session, init_db
from ..engine.executor import OrchestrationController
from ..engine.state_manager import StateManager
from ..feature_flags.api import feature_flags_router
from ..feature_flags.service import FeatureFlagService
from ..metrics import get_metrics, initialize_metrics
from ..registry.api.routes import router as models_router

# Import metrics access control
try:
    from shared.observability.metrics_access import verify_metrics_access
    METRICS_ACCESS_AVAILABLE = True
except ImportError:
    METRICS_ACCESS_AVAILABLE = False
    verify_metrics_access = None
from ..services.crm_sync_scheduler import CRMSyncScheduler, get_crm_sync_scheduler
from ..services.health_tracker import get_health_tracker
from ..tenants import get_tenant_settings, lookup_api_key_by_hash
from ..tenants.api import (
    admin_router,
    api_keys_router,
    provisioning_router,
    registration_router,
    tenants_router,
    users_router,
)
from ..tenants.api.routes.oidc import router as oidc_router
from ..tools import create_default_registry
from .routes import accounts, agent_stream, analysis, signals, tools, workflows
from .routes.enrichment import router as enrichment_router
from .routes.value_hypotheses import router as value_hypotheses_router
from .routes.narratives import router as narratives_router
from .routes.intelligence import router as intelligence_router
from .routes.billing import router as billing_router
from .routes.c1 import router as c1_router
from .routes.checkpoints import checkpoint_router
from .routes.crm_webhooks import router as crm_webhooks_router
from .routes.health_badges import health_badges_router
from .routes.integrations import router as integrations_router
from .routes.state_inspector import state_inspector_router
from .websocket import get_ws_manager, websocket_router

# App start time for uptime calculation
_app_start_time = time.time()


# Global service instances
workflow_executor: OrchestrationController | None = None
state_manager: StateManager | None = None
checkpoint_saver: AsyncPostgresSaver | None = None
ws_manager = get_ws_manager()
health_tracker = get_health_tracker()
crm_sync_scheduler: CRMSyncScheduler | None = None
oidc_cleanup_task: "OIDCCleanupTask | None" = None  # Task 69 gap fix


# P1-29: OpenTelemetry tracer provider (initialized on startup)
_tracer_provider: TracerProvider | None = None


def init_telemetry() -> TracerProvider | None:
    """Initialize OpenTelemetry tracing if endpoint configured.

    P1-29: OpenTelemetry integration for distributed tracing.
    """
    if not settings.otel_exporter_endpoint:
        return None

    resource = Resource.create({SERVICE_NAME: "layer4-agents"})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=f"{settings.otel_exporter_endpoint}/v1/traces"
    )
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return provider


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global workflow_executor, state_manager, checkpoint_saver, _tracer_provider, crm_sync_scheduler

    # P1-29: Initialize OpenTelemetry
    _tracer_provider = init_telemetry()

    # Initialize Prometheus metrics
    metrics = initialize_metrics()
    app.state.metrics = metrics

    # Metrics middleware is registered at module level; it reads from app.state.metrics

    # Startup
    # Initialize database tables (required for checkpoint and workflow state)
    # P0: Database is a required dependency - fail fast if unavailable
    try:
        await init_db()
        logger.info("L4: Database initialized successfully")
    except Exception as e:
        logger.error(f"L4: Database initialization failed: {e}")
        raise RuntimeError(f"Database initialization failed - cannot start without persistence: {e}") from e

    # Production Vault smoke gate
    if os.getenv("ENVIRONMENT", "development") == "production":
        vault_addr = os.getenv("VAULT_ADDR")
        if vault_addr:
            logger.info("L4: Checking Vault connectivity at %s", vault_addr)
            ok = await is_vault_healthy(vault_addr)
            if not ok:
                logger.error("L4: Vault unreachable — cannot start in production without secrets backend")
                raise RuntimeError("Vault unreachable — cannot start in production without secrets backend")
            logger.info("L4: Vault connectivity verified")

    tool_registry = create_default_registry()
    state_manager = StateManager()  # Add Redis client if configured

    # P0: Verify Redis connectivity (required for rate limiting, feature flags, and WebSocket)
    redis_client = getattr(state_manager, "redis_client", None)
    if redis_client is not None:
        try:
            await redis_client.ping()
            logger.info("L4: Redis connectivity verified")
        except Exception as e:
            logger.error(f"L4: Redis connectivity failed: {e}")
            raise RuntimeError(f"Redis connectivity failed - cannot start without cache: {e}") from e
    else:
        logger.error("L4: Redis client not configured - Redis is required")
        raise RuntimeError("Redis client not configured - Redis is required for operation")

    # Initialize rate limiter and feature flags
    redis_rate_limiter = RedisRateLimiter(state_manager.redis_client)
    app.state.rate_limiter = redis_rate_limiter
    init_feature_flags(state_manager.redis_client)

    # Register DB-backed feature flag lookup
    async def _feature_flag_lookup(flag_key: str, tenant_id):
        async with db_session() as db:
            return await FeatureFlagService.lookup_flag(db, flag_key, tenant_id)

    register_feature_flag_lookup(_feature_flag_lookup)

    # Wire WebSocket manager for real-time state broadcasting
    state_manager.set_ws_manager(ws_manager)

    # Initialize checkpoint saver for workflow resumption (required)
    try:
        checkpoint_saver = await CheckpointConfig.create_saver()
        logger.info("L4: Checkpoint saver initialized successfully")
    except Exception as e:
        logger.error(f"L4: Checkpoint saver initialization failed: {e}")
        raise RuntimeError(f"Checkpoint saver failed - cannot start without workflow resumption: {e}") from e

    workflow_executor = OrchestrationController(
        tool_registry, state_manager, checkpoint_saver=checkpoint_saver
    )

    # Start the orchestration controller
    await workflow_executor.start()

    # Recover orphaned workflows from previous pod (P0-26)
    # This is critical for correctness - fail if we can't establish workflow state
    try:
        recovered = await workflow_executor.recover_workflows()
        if recovered:
            logger.info(f"L4: Recovery complete - {len(recovered)} workflows marked as INTERRUPTED")
        else:
            logger.info("L4: No orphaned workflows to recover")
    except Exception as e:
        logger.error(f"L4: Workflow recovery failed: {e}")
        raise RuntimeError(f"Workflow recovery failed - cannot start with unknown workflow state: {e}") from e

    # Start WebSocket manager for real-time streaming
    await ws_manager.start()

    # Start health tracker for graceful degradation badges
    await health_tracker.start()

    # Start CRM sync scheduler for periodic account synchronization
    crm_sync_scheduler = await get_crm_sync_scheduler()
    await crm_sync_scheduler.start()

    # Start OIDC session cleanup task (Task 69 gap fix)
    from ..services.oidc_cleanup import create_oidc_cleanup_task
    from ..database import db_session

    global oidc_cleanup_task
    oidc_cleanup_task = await create_oidc_cleanup_task(
        db_session_factory=db_session,
        interval_seconds=300.0,  # Run every 5 minutes
    )

    yield

    # Shutdown
    if workflow_executor:
        await workflow_executor.stop()

    # Stop WebSocket manager
    await ws_manager.stop()

    # Stop health tracker
    await health_tracker.stop()

    # Stop CRM sync scheduler
    if crm_sync_scheduler:
        await crm_sync_scheduler.stop()

    # Stop OIDC cleanup task
    if oidc_cleanup_task:
        await oidc_cleanup_task.stop()

    # Close checkpoint saver connection
    if checkpoint_saver:
        await CheckpointConfig.close_saver(checkpoint_saver)

    # Close database connection pool
    await close_db()

    # P1-29: Shutdown OpenTelemetry tracer
    if _tracer_provider:
        _tracer_provider.shutdown()
        _tracer_provider = None

    workflow_executor = None
    state_manager = None
    checkpoint_saver = None
    oidc_cleanup_task = None


app = FastAPI(
    title="Layer 4: Agentic Workflow Engine",
    description="LangGraph-powered workflow orchestration for Value Fabric with multi-agent support",
    version="0.2.0",
    lifespan=lifespan,
)

# P1-29: Instrument FastAPI with OpenTelemetry (after app creation)
if settings.otel_exporter_endpoint:
    FastAPIInstrumentor.instrument_app(app)


# Dev auth bypass — when DEV_AUTH_BYPASS=true, injects a synthetic tenant
# context so the UI can be explored without a real JWT.
# MUST be added before GovernanceMiddleware so the context is already set
# when GovernanceMiddleware.dispatch() runs.
try:
    from shared.identity.dev_bypass import maybe_install_dev_bypass
    maybe_install_dev_bypass(app)
except Exception:
    pass  # Module not available or DEV_AUTH_BYPASS not set — production path

# GovernanceMiddleware — replaces TenantMiddleware; verifies JWTs, resolves
# tenant/user/role context from Bearer JWT or X-API-Key.
# api_key_resolver is wired to the DB-backed lookup so keys are verified
# against the persistent api_keys table.
# Task 84: Per-tenant rate limiting with settings from JSONB
def on_rate_limit_hit(tenant_id: str, scope: str):
    metrics = get_metrics()
    if metrics:
        metrics.increment_rate_limit_hit(tenant_id, scope)


async def _tenant_settings_lookup(tenant_id) -> dict | None:
    """Fetch tenant settings for rate limiting (Task 84)."""
    async with db_session() as db:
        return await get_tenant_settings(db, tenant_id)


app.add_middleware(
    GovernanceMiddleware,
    api_key_resolver=lookup_api_key_by_hash,
    rate_limiter=getattr(app.state, "rate_limiter", None),
    on_rate_limit_hit=on_rate_limit_hit,
    tenant_settings_resolver=_tenant_settings_lookup,
)

# CORS middleware — restrict origins in production via the CORS_ORIGINS env var
# Note: allow_origins=["*"] cannot be used with allow_credentials=True per browser security spec
# F-9 FIX: Fail-closed in production — require explicit CORS_ORIGINS

_cors_raw = os.getenv("CORS_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()] if _cors_raw else ["*"]
_cors_credentials = "*" not in _cors_origins  # Must be False when using wildcard origins

if "*" in _cors_origins:
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        raise RuntimeError(
            "CORS_ORIGINS must be set to specific origins in production. "
            "Wildcard origins are not permitted."
        )
    logging.getLogger(__name__).warning(
        "CORS_ORIGINS not set — using wildcard origins. "
        "Set CORS_ORIGINS to specific origins in production."
    )

# SecurityMiddleware — input validation and security headers (mandatory)
_security_config_l4 = SecurityConfig(
    skip_validation_paths=frozenset({
        "/agents/v1/workflows",
        "/agents/v1/skills",
        "/agents/v1/analyze",
    }),
    strict_mode=True,
)
add_security_middleware(app, config=_security_config_l4)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Task 61: Request ID middleware for trace correlation (after CORS)
if SHARED_ERROR_HANDLING_AVAILABLE:
    app.add_middleware(RequestIDMiddleware)

# Task 60: Register shared exception handlers for standardized error responses
if SHARED_ERROR_HANDLING_AVAILABLE:
    register_exception_handlers(app)

# Include routers
app.include_router(workflows.router, prefix="/v1", tags=["workflows"])
app.include_router(tools.router, prefix="/v1", tags=["tools"])
app.include_router(analysis.router, prefix="/v1", tags=["analysis"])
app.include_router(accounts.router, prefix="/v1", tags=["Accounts"])
app.include_router(signals.router, prefix="/v1", tags=["signals"])
app.include_router(agent_stream.router, prefix="/v1", tags=["agent-stream"])
app.include_router(crm_webhooks_router, prefix="/v1")
app.include_router(checkpoint_router, prefix="/v1", tags=["checkpoints"])
app.include_router(state_inspector_router, prefix="/v1", tags=["state-inspector"])
app.include_router(health_badges_router, prefix="/v1", tags=["health"])
app.include_router(integrations_router, prefix="/v1")
app.include_router(websocket_router, prefix="/v1")

# Governance routes
app.include_router(tenants_router, prefix="/v1")
app.include_router(users_router, prefix="/v1")
app.include_router(api_keys_router, prefix="/v1")
app.include_router(oidc_router)

# Phase 2: Provisioning routes
app.include_router(provisioning_router, prefix="/v1")

# Phase 3: Self-service control plane routes
app.include_router(registration_router, prefix="/v1")
app.include_router(admin_router, prefix="/v1")
app.include_router(models_router, prefix="/v1")
app.include_router(feature_flags_router, prefix="/v1")

# Data Intelligence Layer: Enrichment routes
app.include_router(enrichment_router, prefix="/v1")
app.include_router(value_hypotheses_router, prefix="/v1")  # DIL Phase 2 — Value Hypotheses
app.include_router(narratives_router, prefix="/v1")  # DIL Phase 3 — Narrative Builder
app.include_router(intelligence_router, prefix="/v1")  # DIL Phase 3 — Intelligence Orchestrator

# Billing routes (conditional on feature flag)
if settings.is_billing_configured:
    app.include_router(billing_router, prefix="/v1")
    logger.info("Billing routes enabled (Stripe configured)")
else:
    logger.info("Billing routes disabled (set BILLING_ENABLED=true and STRIPE_SECRET_KEY to enable)")

# Thesys C1 streaming proxy
app.include_router(c1_router, prefix="/v1", tags=["c1"])


@app.get("/health")
async def health_check():
    """Health check endpoint with real metrics and dependency status."""
    from datetime import UTC, datetime

    import psutil

    uptime = time.time() - _app_start_time
    memory_info = psutil.virtual_memory()

    metrics = get_metrics()
    total_requests = 0
    active_connections = 0

    if metrics and metrics.config.enabled:
        try:
            requests_counter = metrics._metrics.get("requests_total", {})
            total_requests = (
                sum(
                    v._value.get() if hasattr(v._value, "get") else v._value
                    for method_dict in requests_counter._metrics.values()
                    for endpoint_dict in method_dict.values()
                    for v in endpoint_dict.values()
                )
                if hasattr(requests_counter, "_metrics")
                else 0
            )
        except (AttributeError, TypeError):
            total_requests = 0

        try:
            active_connections = int(
                metrics._metrics.get("active_connections", {}).get("total", {}).get("_value", 0)
            )
        except (AttributeError, TypeError):
            active_connections = 0

    # Check dependencies
    dependencies = []
    overall_status = "healthy"

    # Check PostgreSQL (via checkpoint_saver)
    try:
        start_time = time.time()
        if checkpoint_saver is not None:
            # Try to access the connection to verify it's alive
            if hasattr(checkpoint_saver, "conn") and checkpoint_saver.conn:
                await checkpoint_saver.conn.execute("SELECT 1")
                response_time = (time.time() - start_time) * 1000
                dependencies.append(
                    {
                        "name": "postgres",
                        "status": "healthy",
                        "response_time_ms": round(response_time, 2),
                        "error": None,
                    }
                )
            else:
                dependencies.append(
                    {
                        "name": "postgres",
                        "status": "degraded",
                        "response_time_ms": None,
                        "error": "Checkpoint saver not fully initialized",
                    }
                )
                overall_status = "degraded"
        else:
            dependencies.append(
                {
                    "name": "postgres",
                    "status": "degraded",
                    "response_time_ms": None,
                    "error": "Checkpointing not configured",
                }
            )
            overall_status = "degraded"
    except Exception as e:
        dependencies.append(
            {"name": "postgres", "status": "unhealthy", "response_time_ms": None, "error": str(e)}
        )
        overall_status = "degraded"

    # Check Redis (via state_manager)
    try:
        start_time = time.time()
        if (
            state_manager is not None
            and hasattr(state_manager, "redis_client")
            and state_manager.redis_client
        ):
            await state_manager.redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            dependencies.append(
                {
                    "name": "redis",
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "error": None,
                }
            )
        else:
            dependencies.append(
                {
                    "name": "redis",
                    "status": "degraded",
                    "response_time_ms": None,
                    "error": "Redis not configured",
                }
            )
    except Exception as e:
        dependencies.append(
            {"name": "redis", "status": "unhealthy", "response_time_ms": None, "error": str(e)}
        )

    # Update health status metric for alerting
    if metrics:
        metrics.set_health_status(overall_status == "healthy", component="api")
        if checkpoint_saver is not None:
            postgres_healthy = any(
                d["name"] == "postgres" and d["status"] == "healthy" for d in dependencies
            )
            metrics.set_health_status(postgres_healthy, component="postgres")
        if state_manager is not None and hasattr(state_manager, "redis_client"):
            redis_healthy = any(
                d["name"] == "redis" and d["status"] == "healthy" for d in dependencies
            )
            metrics.set_health_status(redis_healthy, component="redis")

    return {
        "status": overall_status,
        "service": "layer4-agents",
        "version": "0.2.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "executor_ready": workflow_executor is not None,
        "uptime_seconds": uptime,
        "dependencies": dependencies,
        "metrics": {
            "memory_usage_mb": memory_info.used / (1024 * 1024),
            "cpu_percent": psutil.cpu_percent(),
            "active_connections": active_connections,
            "total_requests": total_requests,
        },
    }


@app.get("/metrics")
async def metrics_endpoint(request: Request):
    """Prometheus metrics endpoint.

    SECURITY: Requires valid Bearer token, scrape token header, or internal IP.
    Dev bypass via ALLOW_INSECURE_DEV_AUTH_BYPASS env var (never enable in production).
    """
    # Verify access control
    if METRICS_ACCESS_AVAILABLE and verify_metrics_access:
        is_authorized, error_message = verify_metrics_access(request)
        if not is_authorized:
            return Response(
                content=error_message or "Unauthorized",
                status_code=401,
                media_type="text/plain",
            )

    metrics = getattr(request.app.state, "metrics", None)

    if not metrics:
        return Response(
            content="Metrics collection is disabled", status_code=503, media_type="text/plain"
        )

    try:
        metrics_data = metrics.get_metrics()
        return Response(content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8")
    except Exception as e:
        return Response(
            content=f"Error generating metrics: {e}", status_code=500, media_type="text/plain"
        )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Layer 4: Agentic Workflow Engine",
        "version": "0.2.0",
        "documentation": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }
