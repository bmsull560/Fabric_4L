"""FastAPI main application for Layer 4 Agentic Workflow Engine."""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from shared.identity.feature_flags import init_feature_flags, register_feature_flag_lookup

# Governance middleware replaces the old TenantMiddleware
from shared.identity.middleware import GovernanceMiddleware
from shared.identity.rate_limiter import RedisRateLimiter
from shared.identity.vault_check import check_vault_health

from ..config.checkpoint import CheckpointConfig
from ..database import close_db, db_session, init_db
from ..engine.executor import OrchestrationController
from ..engine.state_manager import StateManager
from ..feature_flags.api import feature_flags_router
from ..feature_flags.service import FeatureFlagService
from ..metrics import MetricsMiddleware, get_metrics, initialize_metrics
from ..registry.api.routes import router as models_router
from ..services.health_tracker import get_health_tracker
from ..tenants import lookup_api_key_by_hash
from ..tenants.api import api_keys_router, tenants_router, users_router
from ..tenants.api.routes.oidc import router as oidc_router
from ..tools import create_default_registry
from .routes import accounts, analysis, tools, workflows
from .routes.c1 import router as c1_router
from .routes.checkpoints import checkpoint_router
from .routes.crm_webhooks import router as crm_webhooks_router
from .routes.health_badges import health_badges_router
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global workflow_executor, state_manager, checkpoint_saver

    # Initialize Prometheus metrics
    metrics = initialize_metrics()
    app.state.metrics = metrics

    # Add metrics middleware if available
    if metrics:
        metrics_middleware = MetricsMiddleware(metrics)
        app.middleware("http")(metrics_middleware)

    # Startup
    # Initialize database tables (dev/test convenience)
    import logging
    import os

    try:
        await init_db()
    except Exception as e:
        # In production, database failures are fatal. In dev/test, log warning.
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            raise RuntimeError(f"Database initialization failed in production: {e}") from e
        logging.getLogger(__name__).warning(f"Database initialization skipped: {e}")

    # Production Vault smoke gate
    if os.getenv("ENVIRONMENT", "development") == "production":
        vault_addr = os.getenv("VAULT_ADDR")
        if vault_addr:
            ok = await check_vault_health(vault_addr)
            if not ok:
                raise RuntimeError(
                    "Vault unreachable — cannot start in production without secrets backend"
                )

    tool_registry = create_default_registry()
    state_manager = StateManager()  # Add Redis client if configured

    # Initialize rate limiter and feature flags
    redis_rate_limiter = None
    if state_manager is not None and getattr(state_manager, "redis_client", None) is not None:
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

    # Initialize checkpoint saver if database is configured
    checkpoint_saver = None
    try:
        checkpoint_saver = await CheckpointConfig.create_saver()
    except Exception:
        # Checkpointing is optional - log warning but continue
        import logging

        logging.getLogger(__name__).warning(
            "Checkpointing not available - workflows will not be resumable"
        )

    workflow_executor = OrchestrationController(
        tool_registry, state_manager, checkpoint_saver=checkpoint_saver
    )

    # Start the orchestration controller
    await workflow_executor.start()

    # Start WebSocket manager for real-time streaming
    await ws_manager.start()

    # Start health tracker for graceful degradation badges
    await health_tracker.start()

    yield

    # Shutdown
    if workflow_executor:
        await workflow_executor.stop()

    # Stop WebSocket manager
    await ws_manager.stop()

    # Stop health tracker
    await health_tracker.stop()

    # Close checkpoint saver connection
    if checkpoint_saver:
        await CheckpointConfig.close_saver(checkpoint_saver)

    # Close database connection pool
    await close_db()

    workflow_executor = None
    state_manager = None
    checkpoint_saver = None


app = FastAPI(
    title="Layer 4: Agentic Workflow Engine",
    description="LangGraph-powered workflow orchestration for Value Fabric with multi-agent support",
    version="0.2.0",
    lifespan=lifespan,
)


# GovernanceMiddleware — replaces TenantMiddleware; verifies JWTs, resolves
# tenant/user/role context from Bearer JWT or X-API-Key.
# api_key_resolver is wired to the DB-backed lookup so keys are verified
# against the persistent api_keys table.
def on_rate_limit_hit(tenant_id: str, scope: str):
    metrics = get_metrics()
    if metrics:
        metrics.increment_rate_limit_hit(tenant_id, scope)


app.add_middleware(
    GovernanceMiddleware,
    api_key_resolver=lookup_api_key_by_hash,
    rate_limiter=getattr(app.state, "rate_limiter", None),
    on_rate_limit_hit=on_rate_limit_hit,
)

# CORS middleware — restrict origins in production via the CORS_ORIGINS env var

_cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workflows.router, prefix="/v1", tags=["workflows"])
app.include_router(tools.router, prefix="/v1", tags=["tools"])
app.include_router(analysis.router, prefix="/v1", tags=["analysis"])
app.include_router(accounts.router, prefix="/v1", tags=["Accounts"])
app.include_router(crm_webhooks_router, prefix="/v1")
app.include_router(checkpoint_router, prefix="/v1", tags=["checkpoints"])
app.include_router(state_inspector_router, prefix="/v1", tags=["state-inspector"])
app.include_router(health_badges_router, prefix="/v1", tags=["health"])
app.include_router(websocket_router, prefix="/v1")

# Governance routes
app.include_router(tenants_router, prefix="/v1")
app.include_router(users_router, prefix="/v1")
app.include_router(api_keys_router, prefix="/v1")
app.include_router(oidc_router)
app.include_router(models_router, prefix="/v1")
app.include_router(feature_flags_router, prefix="/v1")

# Thesys C1 streaming proxy
app.include_router(c1_router, prefix="/v1", tags=["c1"])


@app.get("/health")
async def health_check():
    """Health check endpoint with real metrics and dependency status."""
    from datetime import datetime

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
        "timestamp": datetime.utcnow().isoformat(),
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
    """Prometheus metrics endpoint."""
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
