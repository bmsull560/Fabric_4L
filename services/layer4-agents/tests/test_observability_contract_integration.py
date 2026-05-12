from fastapi.testclient import TestClient

from value_fabric.layer4.api.app_factory import create_app


def test_standard_observability_probes_and_correlation_header() -> None:
    app = create_app()
    client = TestClient(app)

    for path in ("/health", "/ready", "/metrics"):
        response = client.get(path)
        assert response.status_code in {200, 401, 503}

    trace_id = "trace-l4-123"
    health = client.get("/health", headers={"X-Trace-ID": trace_id})
    assert health.headers.get("X-Request-ID") == trace_id
    assert health.headers.get("X-Correlation-ID") == trace_id
    assert health.headers.get("X-Trace-ID") == trace_id
