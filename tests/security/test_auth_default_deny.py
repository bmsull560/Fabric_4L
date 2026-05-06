from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from value_fabric.shared.fastapi_framework.middleware import add_governance_middleware
from value_fabric.shared.identity.dependencies import require_authenticated
from value_fabric.shared.identity.middleware import audit_protected_routes


def test_non_public_routes_default_to_auth_enforcement() -> None:
    app = FastAPI()
    add_governance_middleware(app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/private")
    async def private() -> dict[str, str]:
        return {"status": "private"}

    client = TestClient(app)

    public_response = client.get("/health")
    assert public_response.status_code == 200

    private_response = client.get("/private")
    assert private_response.status_code in {401, 403}


def test_route_audit_fails_for_unprotected_non_public_routes() -> None:
    app = FastAPI()

    @app.get("/oops")
    async def oops() -> dict[str, str]:
        return {"status": "oops"}

    with pytest.raises(RuntimeError, match="Auth route audit failed"):
        audit_protected_routes(app)


def test_route_audit_allows_explicitly_protected_routes() -> None:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(require_authenticated)])
    async def protected() -> dict[str, str]:
        return {"status": "protected"}

    audit_protected_routes(app)
