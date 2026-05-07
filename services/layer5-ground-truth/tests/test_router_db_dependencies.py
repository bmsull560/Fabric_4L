from __future__ import annotations

from fastapi.routing import APIRoute

from layer5_ground_truth.api.main import create_app
from layer5_ground_truth.database import get_db


TENANT_ROUTE_EXCEPTIONS = {
    "/api/v1/health",
}


def test_tenant_routes_do_not_use_raw_get_db_dependency() -> None:
    """Tenant-owned routes must use context-aware DB dependency wiring."""
    app = create_app()

    unsafe_routes: list[str] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith("/api/v1"):
            continue
        if route.path in TENANT_ROUTE_EXCEPTIONS:
            continue

        for dependency in route.dependant.dependencies:
            if dependency.call is get_db:
                unsafe_routes.append(f"{route.path} ({','.join(sorted(route.methods or []))})")
                break

    assert not unsafe_routes, (
        "Tenant routes cannot depend on get_db(); use get_db_from_context instead. "
        f"Unsafe routes: {unsafe_routes}"
    )
