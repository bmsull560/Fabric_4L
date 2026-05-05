from fastapi import HTTPException
from fastapi.testclient import TestClient

from ..app import create_fabric_app, register_health_endpoint


def test_create_fabric_app_applies_shared_defaults() -> None:
    app = create_fabric_app(
        service_name="test-service",
        title="Test Service",
        version="1.0.0",
        description="test app",
        cors_policy={
            "allow_origins": ["https://example.com"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        },
    )

    @app.get("/ok")
    async def ok() -> dict[str, str]:
        return {"service": app.state.service_name}

    @app.get("/boom")
    async def boom() -> None:
        raise HTTPException(status_code=400, detail="bad request")

    client = TestClient(app)

    ok_response = client.get("/ok", headers={"Origin": "https://example.com"})
    assert ok_response.status_code == 200
    assert ok_response.json() == {"service": "test-service"}
    assert ok_response.headers["access-control-allow-credentials"] == "true"
    assert ok_response.headers["access-control-allow-origin"] == "https://example.com"
    assert "x-request-id" in ok_response.headers

    error_response = client.get("/boom")
    assert error_response.status_code == 400
    assert error_response.json()["message"] == "bad request"
    assert "x-request-id" in error_response.headers


def test_register_health_endpoint_uses_service_defaults() -> None:
    app = create_fabric_app(
        service_name="test-health-service",
        title="Test Health Service",
        version="1.0.0",
        description="test app",
    )
    register_health_endpoint(app, service_name="test-health-service")

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "test-health-service"
    assert payload["status"] == "ok"
    assert "timestamp" in payload