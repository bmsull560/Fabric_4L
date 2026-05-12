"""Audit logging middleware for state-changing actions.

Logs every POST, PUT, PATCH, DELETE with:
- timestamp
- actor_id (sub from JWT)
- tenant_id
- impersonator_id (if applicable)
- ip_address
- method, path, status_code
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from value_fabric.shared.identity.context import get_request_context

logger = logging.getLogger("fabric.audit")

# State-changing HTTP methods
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths to skip audit logging
AUDIT_SKIP_PATHS = {
    "/health",
    "/health/detailed",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Log every state-changing request with identity and tenant context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        if request.url.path in AUDIT_SKIP_PATHS or request.url.path.startswith(("/docs", "/redoc")):
            return response

        method = request.method.upper()
        is_mutating = method in MUTATING_METHODS

        # Always log mutating requests; optionally log reads for high-sensitivity paths
        if not is_mutating:
            return response

        ctx = get_request_context()

        actor_id = str(ctx.user_id) if ctx and ctx.user_id else None
        tenant_id = str(ctx.tenant_id) if ctx and ctx.tenant_id else None
        impersonator_id = ctx.impersonator_id if ctx else None

        # Extract client IP with proxy awareness
        forwarded = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")
        client_ip = (
            forwarded.split(",")[0].strip() if forwarded
            else real_ip if real_ip
            else request.client.host if request.client
            else None
        )

        audit_entry: dict[str, Any] = {
            "event": "state_change",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "actor_id": actor_id,
            "tenant_id": tenant_id,
            "impersonator_id": impersonator_id,
            "ip_address": client_ip,
            "method": method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        # Security events: always log at WARNING
        if response.status_code in (401, 403):
            audit_entry["event"] = "access_denied"
            logger.warning(
                "access_denied",
                extra=audit_entry,
            )
        elif response.status_code >= 500:
            audit_entry["event"] = "server_error"
            logger.error(
                "server_error",
                extra=audit_entry,
            )
        else:
            logger.info(
                "state_change",
                extra=audit_entry,
            )

        return response
