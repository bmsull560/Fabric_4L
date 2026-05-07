from fastapi.testclient import TestClient

from src.api.app_factory import create_app


def test_standard_observability_probes_and_correlation_header() -> None:
    app = create_app()
    client = TestClient(app)

    for path in ("/health", "/ready", "/metrics"):
        response = client.get(path)
        assert response.status_code in {200, 401, 503}

    correlation_id = "corr-l4-123"
    health = client.get("/health", headers={"X-Correlation-ID": correlation_id})
    assert health.headers.get("X-Correlation-ID") == correlation_id
