from fastapi import HTTPException
from fastapi.testclient import TestClient

from value_fabric.shared.fastapi_framework import create_fabric_app


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