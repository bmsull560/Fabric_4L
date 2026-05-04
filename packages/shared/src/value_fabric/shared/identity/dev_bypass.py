"""Development auth bypass middleware.

When ``DEV_AUTH_BYPASS=true`` is set in the environment, this middleware
replaces the production ``GovernanceMiddleware`` and injects a synthetic
tenant/user context on every request — no JWT or API key required.

**NEVER enable in production.** The env var is checked at import time;
if it is not explicitly ``"true"`` (case-insensitive), this module
exports a no-op passthrough so the production middleware runs normally.

Usage in Layer 4 ``main.py``::

    from value_fabric.shared.identity.dev_bypass import maybe_install_dev_bypass
    maybe_install_dev_bypass(app)   # no-op unless DEV_AUTH_BYPASS=true
"""

from __future__ import annotations

import logging
import os
from uuid import UUID, uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dev tenant/user constants — deterministic UUIDs for reproducibility
# ---------------------------------------------------------------------------
DEV_TENANT_ID = UUID("00000000-0000-4000-a000-000000000001")
DEV_USER_ID = UUID("00000000-0000-4000-a000-000000000002")
DEV_ORG_ID = UUID("00000000-0000-4000-a000-000000000003")

_DEV_BYPASS_ENABLED = os.getenv("DEV_AUTH_BYPASS", "").strip().lower() == "true"

# SECURITY: Hard-block dev bypass in production environments
# This prevents accidental exposure if DEV_AUTH_BYPASS is set in production
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production").strip().lower()
if _DEV_BYPASS_ENABLED and _ENVIRONMENT == "production":
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: DEV_AUTH_BYPASS cannot be enabled in production.\n"
        "This is a development-only feature that bypasses all authentication.\n"
        "Unset DEV_AUTH_BYPASS or change ENVIRONMENT to 'development' to proceed."
    )


class DevAuthBypassMiddleware(BaseHTTPMiddleware):
    """Injects a fully-populated RequestContext without authentication."""

    async def dispatch(self, request: Request, call_next):
        from value_fabric.shared.identity.context import RequestContext

        request_id = request.headers.get("X-Request-ID") or f"dev_{uuid4().hex[:12]}"
        tenant_id = UUID(request.headers.get("X-Tenant-ID", str(DEV_TENANT_ID)))
        user_id = UUID(request.headers.get("X-User-ID", str(DEV_USER_ID)))
        org_id = UUID(request.headers.get("X-Org-ID", str(DEV_ORG_ID)))
        header_role = request.headers.get("X-Role") or request.headers.get("X-Roles")
        roles = [role.strip() for role in header_role.split(",") if role.strip()] if header_role else []
        for required_role in ("super_admin", "admin", "tenant_admin"):
            if required_role not in roles:
                roles.append(required_role)
        ctx = RequestContext(
            tenant_id=tenant_id,
            user_id=user_id,
            org_id=org_id,
            roles=roles,
            permissions=[
                "read:accounts",
                "write:accounts",
                "read:intelligence",
                "write:intelligence",
                "read:value_models",
                "write:value_models",
                "read:narratives",
                "write:narratives",
                "read:workflows",
                "write:workflows",
                "read:tools",
                "write:tools",
                "read:exports",
                "write:exports",
                "read:agents",
                "write:agents",
                "admin:tenant",
            ],
            auth_source="jwt_claim",
            tenant_role="admin",
            isolation_tier="shared",
            request_id=request_id,
        )

        # Store on request.state so downstream dependencies work unchanged
        request.state.governance_context = ctx

        # Also set the trace_id for RequestIDMiddleware compatibility
        request.state.trace_id = ctx.request_id

        response: Response = await call_next(request)

        # Surface dev mode in response headers for easy identification
        response.headers["X-Dev-Auth-Bypass"] = "true"
        response.headers["X-Dev-Tenant-ID"] = str(tenant_id)
        response.headers["X-Request-ID"] = ctx.request_id

        return response


def maybe_install_dev_bypass(app: ASGIApp) -> bool:
    """Install dev bypass middleware if DEV_AUTH_BYPASS=true.

    Call this **before** adding GovernanceMiddleware in main.py.
    When active, GovernanceMiddleware will see a pre-populated
    ``request.state.governance_context`` and skip authentication.

    Returns:
        True if dev bypass was installed, False otherwise.
    """
    if not _DEV_BYPASS_ENABLED:
        return False

    # CRITICAL: Log at error level to ensure visibility in all logging configs
    logger.error(
        "SECURITY: Dev auth bypass is ACTIVE. All requests will be auto-authenticated "
        "as tenant %s with admin privileges. This should NEVER be enabled in production.",
        DEV_TENANT_ID,
    )
    logger.warning(
        "╔══════════════════════════════════════════════════════════╗\n"
        "║  DEV AUTH BYPASS ENABLED — ALL REQUESTS AUTO-AUTHED    ║\n"
        "║  Tenant: %s                     ║\n"
        "║  DO NOT USE IN PRODUCTION                              ║\n"
        "╚══════════════════════════════════════════════════════════╝",
        DEV_TENANT_ID,
    )

    app.add_middleware(DevAuthBypassMiddleware)
    return True
