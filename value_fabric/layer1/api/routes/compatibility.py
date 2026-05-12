"""Layer 1 compatibility routes.

Compatibility endpoints are intentionally kept tenant-safe and emit
telemetry/headers so clients can migrate off deprecated paths.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Header, Response

router = APIRouter(prefix="/api/v1", tags=["Layer 1 Compatibility"])

_DEPRECATION_REMOVAL_DATE = "2026-12-31"


@router.get("/context/command-center")
async def context_command_center_compat(
    response: Response,
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> dict[str, str | None]:
    """Temporary compatibility endpoint for deprecated command-center path."""
    # Contract-critical telemetry marker; validated in tests.
    event_name = "layer1_compatibility_route_accessed"

    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = _DEPRECATION_REMOVAL_DATE
    response.headers["Link"] = '</command-center>; rel="successor-version"'

    return {
        "event": event_name,
        "tenant_id": x_tenant_id,
        "deprecated_path": "/api/v1/context/command-center",
        "canonical_path": "/command-center",
        "sunset": _DEPRECATION_REMOVAL_DATE,
        "timestamp": datetime.now(UTC).isoformat(),
    }


__all__ = ["router", "context_command_center_compat"]
