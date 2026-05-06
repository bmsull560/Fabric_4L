from fastapi.testclient import TestClient

from value_fabric.layer4.api.main import app


client = TestClient(app)


def _lineage(correlation_id: str) -> dict:
    return {
        "business_case_id": "bc-1",
        "value_model_id": None,
        "correlation_id": correlation_id,
    }


def test_approval_gated_export_blocks_without_approval() -> None:
    review_payload = {
        "review_id": "rev-blocked",
        "status": "submitted",
        "subject_type": "business_case",
        "submitted_at": "2026-05-06T00:00:00Z",
        "lineage": _lineage("corr-blocked"),
    }
    review_resp = client.post("/v1/governance/reviews", json=review_payload)
    assert review_resp.status_code == 201

    export_resp = client.post(
        "/v1/governance/audit/exports",
        json={"review_id": "rev-blocked", "correlation_id": "corr-blocked"},
    )
    assert export_resp.status_code == 201
    assert export_resp.json()["status"] == "blocked"
    assert export_resp.json()["reason"] == "approval_required"


def test_lineage_retrieval_contains_review_decision_version_and_export() -> None:
    review_id = "rev-lineage"
    correlation_id = "corr-lineage"

    client.post(
        "/v1/governance/reviews",
        json={
            "review_id": review_id,
            "status": "submitted",
            "subject_type": "business_case",
            "submitted_at": "2026-05-06T00:00:00Z",
            "lineage": _lineage(correlation_id),
        },
    )

    decision_resp = client.post(
        f"/v1/governance/reviews/{review_id}/decisions",
        json={
            "decision_id": "dec-1",
            "review_id": review_id,
            "decision": "approved",
            "immutable_audit_hash": "sha256:abc",
            "decided_at": "2026-05-06T00:01:00Z",
            "lineage": _lineage(correlation_id),
        },
    )
    assert decision_resp.status_code == 201

    version_resp = client.post(
        "/v1/governance/versions",
        json={
            "version_id": "ver-1",
            "version_status": "active",
            "created_at": "2026-05-06T00:02:00Z",
            "lineage": _lineage(correlation_id),
        },
    )
    assert version_resp.status_code == 201

    export_resp = client.post(
        "/v1/governance/audit/exports",
        json={"review_id": review_id, "correlation_id": correlation_id},
    )
    assert export_resp.status_code == 201
    assert export_resp.json()["status"] == "pending"

    lineage_resp = client.get(f"/v1/governance/lineage/{correlation_id}")
    assert lineage_resp.status_code == 200
    payload = lineage_resp.json()
    assert len(payload["reviews"]) >= 1
    assert len(payload["decisions"]) >= 1
    assert len(payload["versions"]) >= 1
    assert len(payload["exports"]) >= 1
