"""
Layer 5 Ground Truth — FastAPI application entry point.

Run with:
  uvicorn layer5_ground_truth.api.main:app --host 0.0.0.0 --port 8005 --reload

Or via Docker:
  docker compose up layer5-ground-truth

"""

import logging
import os
import re
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:
    from value_fabric.shared.security import SecurityConfig, add_security_middleware
except ImportError:
    add_security_middleware = None
    SecurityConfig = None

if not SecurityConfig and os.getenv("ENVIRONMENT") in ("production", "staging"):
    raise RuntimeError("SecurityMiddleware required in production")

try:
    from value_fabric.shared.identity.vault_check import is_vault_healthy
except ImportError:
    is_vault_healthy = None

try:
    from value_fabric.shared.observability import verify_metrics_access
except ImportError:  # pragma: no cover
    verify_metrics_access = None  # type: ignore[assignment]

from metrics import MetricsMiddleware, get_metrics, initialize_metrics

from ..config import get_settings
from ..database import close_db, init_db
from .router import router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_tracer_provider: TracerProvider | None = None


def init_telemetry() -> TracerProvider | None:
    """Initialize OpenTelemetry tracing if OTLP endpoint is configured."""
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otel_endpoint:
        return None

    resource = Resource.create({SERVICE_NAME: "layer5-ground-truth"})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=f"{otel_endpoint}/v1/traces"
    )
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return provider


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle — database init and teardown."""
    global _tracer_provider

    # Initialize OpenTelemetry tracing
    _tracer_provider = init_telemetry()
    if _tracer_provider:
        logger.info("L5: OpenTelemetry tracing initialized")

    settings = get_settings()
    logger.info("Starting Layer 5 Ground Truth service on port %d", settings.api_port)

    # Security: fail fast if weak JWT secret is used in production
    if not settings.debug:
        _validate_jwt_secret(settings.jwt_secret)

    # Initialize DB tables (no-op if already exist; Alembic handles migrations)
    if settings.debug:
        logger.info("DEBUG mode: running init_db() to create tables if missing")
        await init_db()

    # Production Vault smoke gate
    if os.getenv("ENVIRONMENT", "development") == "production":
        vault_addr = os.getenv("VAULT_ADDR")
        if vault_addr and is_vault_healthy:
            logger.info("L5: Checking Vault connectivity at %s", vault_addr)
            ok = await is_vault_healthy(vault_addr)
            if not ok:
                logger.error("L5: Vault unreachable — cannot start in production without secrets backend")
                raise RuntimeError("Vault unreachable — cannot start in production without secrets backend")
            logger.info("L5: Vault connectivity verified")

    # Initialize Prometheus metrics and install the metrics middleware here —
    # NOT in create_app() — because app.state is only writable after the
    # lifespan begins. Installing the middleware in create_app() previously
    # raised AttributeError on `app.state.metrics`.
    metrics = initialize_metrics()
    if metrics:
        logger.info("L5: Prometheus metrics initialized")
        app.state.metrics = metrics
        metrics_middleware = MetricsMiddleware(metrics)
        app.middleware("http")(metrics_middleware)
        logger.info("L5: Metrics middleware installed")
    else:
        app.state.metrics = None

    # Initialize Redis client for rate limiting (async context)
    app.state.redis_rate_limiter = None
    try:
        import redis.asyncio as redis
        from value_fabric.shared.identity.rate_limiter import RedisRateLimiter

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        # Validate connection before using for rate limiting
        await redis_client.ping()
        app.state.redis_rate_limiter = RedisRateLimiter(redis_client)
        logger.info("L5: Redis rate limiter initialized")
    except Exception as e:
        env = os.getenv("ENVIRONMENT", "development")
        redis_required = os.getenv("REDIS_RATE_LIMITING_REQUIRED", "false").lower() == "true"
        
        if redis_required or env in ("production", "staging"):
            logger.error(f"L5: Redis rate limiting required but unavailable: {e}")
            raise RuntimeError(f"Redis rate limiting required in {env} but unavailable: {e}")
        
        logger.warning(f"L5: Redis rate limiter disabled - {e}")
        app.state.redis_rate_limiter = None

    yield

    logger.info("Shutting down Layer 5 Ground Truth service")
    await close_db()
    
    # Close Redis connection if initialized
    if app.state.redis_rate_limiter:
        try:
            await app.state.redis_rate_limiter.close()
            logger.info("L5: Redis connection closed")
        except Exception as e:
            logger.warning(f"L5: Error closing Redis connection: {e}")

    # Shutdown OpenTelemetry tracer provider to flush pending spans
    if _tracer_provider:
        logger.info("L5: Shutting down OpenTelemetry tracer provider")
        _tracer_provider.shutdown()
        _tracer_provider = None


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Value Fabric — Ground Truth Layer (L5)",
        description=(
            "Evidence-backed, CFO-defensible facts for the Value Fabric platform. "
            "Provides a validation state machine (extracted → supported → corroborated → approved), "
            "a 0–5 maturity ladder, and bidirectional integration with the Layer 3 Knowledge Graph."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "Value Fabric Engineering",
            "url": "https://github.com/bmsull560/Fabric_4L",
        },
        license_info={
            "name": "Proprietary",
        },
        openapi_tags=[
            {
                "name": "ground-truth",
                "description": (
                    "CRUD and validation operations for TruthObject records. "
                    "All endpoints are scoped to an tenant_id for multi-tenancy."
                ),
            },
            {
                "name": "model-registry",
                "description": (
                    "LLM model versioning, deployment, and evaluation tracking. "
                    "Manages model lifecycles with cost attribution and canary releases."
                ),
            },
            {
                "name": "system",
                "description": "Health check and operational endpoints.",
            },
        ],
    )

    # SecurityMiddleware — input validation and security headers (before CORS)
    # L5 has no skip paths — all endpoints require strict validation
    if SecurityConfig and add_security_middleware:
        _security_config_l5 = SecurityConfig.from_env(
            skip_validation_paths=frozenset(),
            strict_mode=True,
        )
        add_security_middleware(app, config=_security_config_l5)

    # GovernanceMiddleware — provides auth and tenant context with rate limiting
    # Production/staging: fail closed if auth middleware is missing
    allow_bypass = os.getenv("ALLOW_INSECURE_DEV_AUTH_BYPASS", "").lower() == "true"
    env = os.getenv("ENVIRONMENT", "development")

    # Get Redis rate limiter from app state (initialized in lifespan)
    redis_rate_limiter = getattr(app.state, 'redis_rate_limiter', None)

    # Public paths that skip auth (metrics has its own token/IP-based access control)
    public_paths = frozenset({
        "/metrics",
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/",
    })

    try:
        from value_fabric.shared.identity.middleware import GovernanceMiddleware

        app.add_middleware(
            GovernanceMiddleware,
            api_key_resolver=None,
            rate_limiter=redis_rate_limiter,
            skip_paths=public_paths,
        )
        logger.info("L5: GovernanceMiddleware with rate limiting initialized (public paths: %s)", public_paths)
    except ImportError:
        if env in ("production", "staging") and not allow_bypass:
            logger.error(
                "CRITICAL: GovernanceMiddleware not importable in production/staging. "
                "Authentication is required. Set ALLOW_INSECURE_DEV_AUTH_BYPASS=true ONLY for local dev."
            )
            raise RuntimeError(
                "GovernanceMiddleware is required in production/staging. "
                "shared.identity.middleware is not importable."
            )
        
        logger.warning(
            "SECURITY WARNING: GovernanceMiddleware not imported. "
            "API endpoints are UNPROTECTED. This is only allowed in development with ALLOW_INSECURE_DEV_AUTH_BYPASS=true."
        )

    # CORS — restrict in production via environment variable
    # Note: allow_origins=["*"] cannot be used with allow_credentials=True per browser security spec
    _cors_raw = os.getenv("CORS_ORIGINS", "")
    _cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()] if _cors_raw else (["*"] if settings.debug else [])
    _cors_credentials = "*" not in _cors_origins  # Must be False when using wildcard origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=_cors_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount the API routers
    app.include_router(router)

    # Note: metrics middleware is installed inside `lifespan()` because
    # `app.state.metrics` is only initialized there.

    # Instrument FastAPI with OpenTelemetry after all other middleware
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        FastAPIInstrumentor.instrument_app(app)
        logger.info("L5: FastAPI instrumented with OpenTelemetry")

    # Mount the Model Registry router
    try:
        from .model_registry_routes import router as model_registry_router
        app.include_router(model_registry_router)
    except ImportError:
        logging.getLogger(__name__).warning("Model Registry router not available")

    # Prometheus metrics endpoint — internal only, protected by network/auth
    @app.get("/metrics", tags=["Monitoring"], include_in_schema=False)
    async def metrics_endpoint(request: Request):
        """Prometheus metrics endpoint — requires internal access token."""
        # Verify internal access for metrics (blocks public ingress access).
        # Delegated to shared.observability so all layers stay aligned.
        if verify_metrics_access is None or not verify_metrics_access(request):
            raise HTTPException(status_code=403, detail="Metrics endpoint requires internal access")
        
        metrics = get_metrics()
        if not metrics:
            return Response(
                content="Metrics collection is disabled", status_code=503, media_type="text/plain"
            )
        try:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=metrics.get_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8")
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return Response(
                content=f"Error generating metrics: {e}", status_code=500, media_type="text/plain"
            )

    # Root redirect to docs
    @app.get("/", include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "service": "Value Fabric Ground Truth Layer (L5)",
                "version": "0.1.0",
                "docs": "/docs",
                "health": "/api/v1/health",
                "metrics": "/metrics",
            }
        )

    return app


# ---------------------------------------------------------------------------
# Module-level app instance (used by uvicorn)
# ---------------------------------------------------------------------------

# JWT Secret validation denylist - known weak secrets
JWT_SECRET_DENYLIST = {
    "changeme-in-production",
    "changeme",
    "password",
    "password123",
    "admin",
    "secret",
    "jwt-secret",
    "default",
    "test",
    "",
    "null",
    "none",
    "123456",
    "12345678",
    "qwerty",
    "abc123",
}


def _validate_jwt_secret(secret: str) -> None:
    """
    Validate JWT secret meets security requirements for production.
    
    Requirements:
    - Minimum 32 characters (256 bits equivalent for base64)
    - Not in denylist of known weak secrets
    - Not empty or null
    """
    if not secret:
        raise RuntimeError("JWT_SECRET is empty or not set. Set a secure JWT_SECRET environment variable.")
    
    if len(secret) < 32:
        raise RuntimeError(
            f"JWT_SECRET is too short ({len(secret)} chars). "
            f"Minimum 32 characters required for security. "
            f"Generate a secure secret: openssl rand -base64 32"
        )
    
    # Check denylist (case-insensitive)
    secret_lower = secret.lower()
    if secret_lower in JWT_SECRET_DENYLIST:
        raise RuntimeError(
            f"JWT_SECRET '{secret}' is a known weak/placeholder value. "
            f"Generate a secure secret: openssl rand -base64 32"
        )
    
    # Check for common patterns that indicate weak secrets
    if re.match(r'^(changeme|password|secret|admin|test|default)[0-9]*$', secret_lower):
        raise RuntimeError(
            f"JWT_SECRET '{secret}' matches a weak secret pattern. "
            f"Generate a secure secret: openssl rand -base64 32"
        )


app = create_app()
