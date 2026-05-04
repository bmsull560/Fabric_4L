from fastapi.testclient import TestClient
from .conftest import auth_headers, TENANT_ALPHA
from app.main import app

HEADERS = auth_headers(TENANT_ALPHA)


def test_roi_calculation():
    with TestClient(app) as client:
        payload = {
            "scenario_id": "sc-test",
            "revenue_uplift": 1_000_000,
            "cost_savings": 200_000,
            "risk_reduction": 100_000,
            "solution_cost": 400_000,
        }
        response = client.post("/v1/accounts/acc-allego/roi/calculate", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["total_benefit"] == 1_300_000
        assert data["net_benefit"] == 900_000
        assert data["roi_percent"] == 225.0
        assert data["payback_months"] == 3.69


def test_roi_divide_by_zero():
    with TestClient(app) as client:
        payload = {
            "scenario_id": "sc-zero",
            "revenue_uplift": 0,
            "cost_savings": 0,
            "risk_reduction": 0,
            "solution_cost": 0,
        }
        response = client.post("/v1/accounts/acc-allego/roi/calculate", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["roi_percent"] == 0.0
        assert data["payback_months"] == 0.0
