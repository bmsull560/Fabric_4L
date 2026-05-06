"""Router registration for Layer 4 API."""

import logging

from fastapi import FastAPI

from ..config.settings import settings
from ..feature_flags.api import feature_flags_router
from ..registry.api.routes import router as models_router
from ..tenants.api import admin_router, api_keys_router, provisioning_router, registration_router, tenants_router, users_router
from ..tenants.api.routes.oidc import router as oidc_router
from .routes import accounts, agent_stream, analysis, prospects, signals, tools, workflows
from .routes import audit as audit_router
from .routes.billing import router as billing_router
from .routes.c1 import router as c1_router
from .routes.checkpoints import checkpoint_router
from .routes.crm_webhooks import router as crm_webhooks_router
from .routes.enrichment import router as enrichment_router
from .routes.frontend_compat import router as frontend_compat_router
from .routes.ground_truth_proxy import router as ground_truth_proxy_router
from .routes.health_badges import health_badges_router
from .routes.integrations import router as integrations_router
from .routes.intelligence import router as intelligence_router
from .routes.narratives import router as narratives_router
from .routes.state_inspector import state_inspector_router
from .routes.value_hypotheses import router as value_hypotheses_router
from .websocket import websocket_router

logger = logging.getLogger(__name__)


def register_routers(app: FastAPI) -> None:
    app.include_router(workflows.router, prefix="/v1", tags=["workflows"])
    app.include_router(tools.router, prefix="/v1", tags=["tools"])
    app.include_router(audit_router.router, prefix="/v1", tags=["audit"])
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
    app.include_router(tenants_router, prefix="/v1")
    app.include_router(users_router, prefix="/v1")
    app.include_router(api_keys_router, prefix="/v1")
    app.include_router(oidc_router)
    app.include_router(provisioning_router, prefix="/v1")
    app.include_router(registration_router, prefix="/v1")
    app.include_router(admin_router, prefix="/v1")
    app.include_router(models_router, prefix="/v1")
    app.include_router(feature_flags_router, prefix="/v1")
    app.include_router(enrichment_router, prefix="/v1")
    app.include_router(value_hypotheses_router, prefix="/v1")
    app.include_router(narratives_router, prefix="/v1")
    app.include_router(intelligence_router, prefix="/v1")
    app.include_router(ground_truth_proxy_router)

    if settings.is_billing_configured:
        app.include_router(billing_router, prefix="/v1")
        logger.info("Billing routes enabled (Stripe configured)")
    else:
        logger.info("Billing routes disabled (set BILLING_ENABLED=true and STRIPE_SECRET_KEY to enable)")

    app.include_router(c1_router, prefix="/v1", tags=["c1"])
    app.include_router(frontend_compat_router, prefix="/v1")
    app.include_router(prospects.router, prefix="/v1")
