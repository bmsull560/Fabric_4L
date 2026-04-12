"""FastAPI main application for Layer 4 Agentic Workflow Engine."""

from contextlib import asynccontextmanager
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .routes import workflows, tools, analysis, accounts
from ..database import init_db, close_db
from ..engine.executor import OrchestrationController
from ..engine.state_manager import StateManager
from ..tools import create_default_registry
from ..tenant.middleware import TenantMiddleware
from ..config.checkpoint import CheckpointConfig
from ..metrics import initialize_metrics, MetricsMiddleware, get_metrics
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# App start time for uptime calculation
_app_start_time = time.time()


# Global service instances
workflow_executor: OrchestrationController | None = None
state_manager: StateManager | None = None
checkpoint_saver: AsyncPostgresSaver | None = None


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

    tool_registry = create_default_registry()
    state_manager = StateManager()  # Add Redis client if configured

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
        tool_registry,
        state_manager,
        checkpoint_saver=checkpoint_saver
    )

    # Start the orchestration controller
    await workflow_executor.start()

    yield

    # Shutdown
    if workflow_executor:
        await workflow_executor.stop()

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
    lifespan=lifespan
)

# Tenant middleware (must be before CORS to extract from JWT)
app.add_middleware(TenantMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workflows.router, prefix="/v1", tags=["workflows"])
app.include_router(tools.router, prefix="/v1", tags=["tools"])
app.include_router(analysis.router, prefix="/v1", tags=["analysis"])
app.include_router(accounts.router, prefix="/v1", tags=["Accounts"])


@app.get("/health")
async def health_check():
    """Health check endpoint with real metrics and dependency status."""
    import psutil
    from datetime import datetime
    uptime = time.time() - _app_start_time
    memory_info = psutil.virtual_memory()

    metrics = get_metrics()
    total_requests = 0
    active_connections = 0

    if metrics and metrics.config.enabled:
        try:
            requests_counter = metrics._metrics.get("requests_total", {})
            total_requests = sum(
                v._value.get() if hasattr(v._value, 'get') else v._value
                for method_dict in requests_counter._metrics.values()
                for endpoint_dict in method_dict.values()
                for v in endpoint_dict.values()
            ) if hasattr(requests_counter, '_metrics') else 0
        except (AttributeError, TypeError):
            total_requests = 0

        try:
            active_connections = int(
                metrics._metrics.get("active_connections", {})
                .get("total", {})
                .get("_value", 0)
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
            if hasattr(checkpoint_saver, 'conn') and checkpoint_saver.conn:
                await checkpoint_saver.conn.execute("SELECT 1")
                response_time = (time.time() - start_time) * 1000
                dependencies.append({
                    "name": "postgres",
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "error": None
                })
            else:
                dependencies.append({
                    "name": "postgres",
                    "status": "degraded",
                    "response_time_ms": None,
                    "error": "Checkpoint saver not fully initialized"
                })
                overall_status = "degraded"
        else:
            dependencies.append({
                "name": "postgres",
                "status": "degraded",
                "response_time_ms": None,
                "error": "Checkpointing not configured"
            })
            overall_status = "degraded"
    except Exception as e:
        dependencies.append({
            "name": "postgres",
            "status": "unhealthy",
            "response_time_ms": None,
            "error": str(e)
        })
        overall_status = "degraded"

    # Check Redis (via state_manager)
    try:
        start_time = time.time()
        if state_manager is not None and hasattr(state_manager, 'redis_client') and state_manager.redis_client:
            await state_manager.redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            dependencies.append({
                "name": "redis",
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "error": None
            })
        else:
            dependencies.append({
                "name": "redis",
                "status": "degraded",
                "response_time_ms": None,
                "error": "Redis not configured"
            })
    except Exception as e:
        dependencies.append({
            "name": "redis",
            "status": "unhealthy",
            "response_time_ms": None,
            "error": str(e)
        })

    # Update health status metric for alerting
    if metrics:
        metrics.set_health_status(overall_status == "healthy", component="api")
        if checkpoint_saver is not None:
            postgres_healthy = any(d["name"] == "postgres" and d["status"] == "healthy" for d in dependencies)
            metrics.set_health_status(postgres_healthy, component="postgres")
        if state_manager is not None and hasattr(state_manager, 'redis_client'):
            redis_healthy = any(d["name"] == "redis" and d["status"] == "healthy" for d in dependencies)
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
            "total_requests": total_requests
        }
    }


@app.get("/metrics")
async def metrics_endpoint(request: Request):
    """Prometheus metrics endpoint."""
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
        return Response(
            content=f"Error generating metrics: {e}",
            status_code=500,
            media_type="text/plain"
        )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Layer 4: Agentic Workflow Engine",
        "version": "0.2.0",
        "documentation": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }
