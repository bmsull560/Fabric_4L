"""Helpers for tenant source-of-truth enforcement in request payloads."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status


def enforce_authenticated_tenant(
    *,
    body_tenant_id: str | None,
    authenticated_tenant_id: str,
    route: str,
    operation: str,
) -> None:
    """Reject body/header tenant mismatch against authenticated context.

    IMPORTANT — explicit call required:
    This helper is NOT applied by middleware. Each router that accepts a
    body or header tenant_id must call this function explicitly before
    processing the request. There is no automatic enforcement layer.

    Failure to call this on a route that accepts tenant_id in the request
    body or headers leaves that route vulnerable to X-Tenant-ID header
    spoofing (TEST_AUDIT.md P0 gap #1). See services/api/app/routers/ for
    the expected call pattern.
    """
    if body_tenant_id is None:
        return
    if str(body_tenant_id) == str(authenticated_tenant_id):
        return

    logging.getLogger(__name__).warning(
        "tenant_context_mismatch",
        extra={
            "event_type": "tenant_context_mismatch",
            "route": route,
            "operation": operation,
            "authenticated_tenant_id": str(authenticated_tenant_id),
            "request_tenant_id": str(body_tenant_id),
        },
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "TENANT_CONTEXT_MISMATCH",
            "message": "Body tenant_id does not match authenticated tenant context.",
        },
    )
