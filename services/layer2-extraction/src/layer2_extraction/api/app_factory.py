"""FastAPI app construction for Layer 2 API."""

import structlog

from value_fabric.shared.identity.api_key_stub import reject_api_key_unsupported
from value_fabric.shared.identity.middleware import GovernanceMiddleware

from ..shared_bootstrap import (
    SecurityConfig,
    add_security_middleware,
    create_fabric_app,
    install_metrics_middleware,
    resolve_cors_policy,
)
from ..metrics import MetricsMiddleware, initialize_metrics
from . import routes
from .websocket import websocket_router

logger = structlog.get_logger()


def create_app(*, lifespan):
    app = create_fabric_app(
        service_name="layer2-extraction",
        title="Value Fabric - Extraction Pipeline",
        description="Ontology-guided extraction of entities from unstructured text to RDF/OWL",
        version="1.0.0",
        lifespan=lifespan,
        cors_policy=resolve_cors_policy(),
        telemetry_service_name="layer2-extraction",
        instrument_telemetry=True,
    )

    security_config = SecurityConfig.from_env(skip_validation_paths=frozenset({"/health", "/metrics"}), strict_mode=True)
    add_security_middleware(app, config=security_config)

    class _AppStateRateLimiterProxy:
        def __init__(self, application):
            self._application = application

        async def check(self, rate_key, config):
            limiter = getattr(self._application.state, "redis_rate_limiter", None)
            if limiter is None:
                return None
            return await limiter.check(rate_key, config)

    app.add_middleware(GovernanceMiddleware, api_key_resolver=reject_api_key_unsupported, rate_limiter=_AppStateRateLimiterProxy(app))
    install_metrics_middleware(app, metrics=initialize_metrics(), middleware_factory=MetricsMiddleware, logger=logger)

    app.include_router(websocket_router, prefix="/v1")
    app.include_router(routes.system.router)
    app.include_router(routes.extraction.router)
    app.include_router(routes.jobs.router)
    app.include_router(routes.health.router)
    app.include_router(routes.ontology.router)
    app.include_router(routes.audit.router)
    return app
