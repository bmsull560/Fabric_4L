from fastapi.testclient import TestClient

from value_fabric.layer3.api.app_monolith import app


def test_standard_observability_probes_and_correlation_header() -> None:
    client = TestClient(app)

    for path in ("/health", "/ready", "/metrics"):
        response = client.get(path)
        assert response.status_code in {200, 401, 503}

    correlation_id = "corr-l3-123"
    health = client.get("/health", headers={"X-Correlation-ID": correlation_id})
    assert health.headers.get("X-Correlation-ID") == correlation_id
