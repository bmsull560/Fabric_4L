"""Suite 6 — Approval, Export, and CRM Governance."""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.backend_integrated, pytest.mark.integration, pytest.mark.e2e]


@pytest.mark.asyncio
async def test_business_case_export_blocked_before_approval(backend, seed_ids):
    draft, _ = await backend.request(
        "l4",
        "POST",
        "/v1/cases",
        json={"account_id": seed_ids.account_id, "approval_status": "draft", "evidence_ids": [seed_ids.evidence_id]},
        expected=(200, 201, 202),
    )
    case_id = draft.get("id") or draft.get("case_id") or seed_ids.account_id
    await backend.request("l4", "GET", f"/v1/cases/{case_id}/export", expected=(401, 403, 409, 423))


@pytest.mark.asyncio
async def test_business_case_export_allowed_after_approval(backend, seed_ids):
    await backend.create_seed_graph()
    case, _ = await backend.request(
        "l4",
        "POST",
        "/v1/cases",
        json={"account_id": seed_ids.account_id, "approval_status": "submitted", "evidence_ids": [seed_ids.evidence_id]},
        expected=(200, 201, 202),
    )
    case_id = case.get("id") or case.get("case_id") or seed_ids.account_id
    await backend.request("l4", "POST", f"/v1/cases/{case_id}/approval", json={"status": "approved", "reviewer_id": seed_ids.user_reviewer}, expected=(200, 201, 202))
    export, _ = await backend.request("l4", "GET", f"/v1/cases/{case_id}/export?include_provenance=true", expected=(200, 202))
    assert any(token in str(export).lower() for token in ("export", "download", "url", "provenance")), export


@pytest.mark.asyncio
async def test_reviewer_can_request_changes(backend, seed_ids):
    hypothesis, _ = await backend.request(
        "l4",
        "POST",
        "/v1/hypotheses",
        json={"account_id": seed_ids.account_id, "text": "Improve conversion", "evidence_ids": [seed_ids.evidence_id]},
        expected=(200, 201, 202),
    )
    hypothesis_id = hypothesis.get("id") or hypothesis.get("hypothesis_id") or seed_ids.evidence_id
    changes, _ = await backend.request(
        "l4",
        "POST",
        f"/v1/hypotheses/{hypothesis_id}/review",
        json={"decision": "changes_requested", "comment": "Attach stronger source lineage", "reviewer_id": seed_ids.user_reviewer},
        expected=(200, 201, 202),
    )
    assert "changes_requested" in str(changes).lower(), changes


@pytest.mark.asyncio
async def test_user_can_resubmit_after_review_changes(backend, seed_ids):
    case, _ = await backend.request("l4", "POST", "/v1/cases", json={"account_id": seed_ids.account_id, "approval_status": "changes_requested"}, expected=(200, 201, 202))
    case_id = case.get("id") or case.get("case_id") or seed_ids.account_id
    resubmitted, _ = await backend.request(
        "l4",
        "POST",
        f"/v1/cases/{case_id}/resubmit",
        json={"submitted_by": seed_ids.user_admin, "changes": "Added source lineage"},
        expected=(200, 201, 202),
    )
    assert any(token in str(resubmitted).lower() for token in ("submitted", "resubmitted", "review")), resubmitted


@pytest.mark.asyncio
async def test_unsupported_claim_blocks_approval(backend, seed_ids):
    case, _ = await backend.request(
        "l4",
        "POST",
        "/v1/cases",
        json={"account_id": seed_ids.account_id, "claims": [{"text": "unsupported metric", "evidence_ids": []}]},
        expected=(200, 201, 202),
    )
    case_id = case.get("id") or case.get("case_id") or seed_ids.account_id
    body, response = await backend.request(
        "l4",
        "POST",
        f"/v1/cases/{case_id}/approval",
        json={"status": "approved", "reviewer_id": seed_ids.user_reviewer},
        expected=(400, 409, 422),
    )
    assert response.status_code in {400, 409, 422}
    assert any(token in str(body).lower() for token in ("unsupported", "evidence", "claim", "validation")), body


@pytest.mark.asyncio
async def test_crm_push_blocked_before_approval(backend, seed_ids):
    case, _ = await backend.request("l4", "POST", "/v1/cases", json={"account_id": seed_ids.account_id, "approval_status": "draft"}, expected=(200, 201, 202))
    case_id = case.get("id") or case.get("case_id") or seed_ids.account_id
    await backend.request(
        "l4",
        "POST",
        f"/v1/integrations/crm/connections/{seed_ids.crm_connection_id}/push",
        json={"case_id": case_id, "account_id": seed_ids.account_id, "artifacts": ["business_case_link"]},
        expected=(401, 403, 409, 423),
    )


@pytest.mark.asyncio
async def test_crm_push_records_sync_log(backend, seed_ids):
    await backend.request("l4", "POST", "/v1/integrations/crm/connections", json={"provider": "salesforce", "connection_id": seed_ids.crm_connection_id, "mode": "mocked_external_provider"}, expected=(200, 201, 202, 409))
    push, _ = await backend.request(
        "l4",
        "POST",
        f"/v1/integrations/crm/connections/{seed_ids.crm_connection_id}/push",
        json={"account_id": seed_ids.account_id, "approval_status": "approved", "artifacts": ["roi_summary", "business_case_link"]},
        expected=(200, 201, 202),
    )
    assert any(token in str(push).lower() for token in ("queued", "synced", "job", "summary")), push
    log, _ = await backend.request("l4", "GET", f"/v1/integrations/crm/connections/{seed_ids.crm_connection_id}/sync-log", expected=(200,))
    assert seed_ids.account_id in str(log) or seed_ids.crm_connection_id in str(log), log


@pytest.mark.asyncio
async def test_crm_sync_failure_is_retryable(backend, seed_ids):
    failure, _ = await backend.request(
        "l4",
        "POST",
        f"/v1/integrations/crm/connections/{seed_ids.crm_connection_id}/push",
        json={"account_id": seed_ids.account_id, "approval_status": "approved", "simulate_provider_failure": True},
        expected=(200, 201, 202, 400, 409, 502, 503),
    )
    assert any(token in str(failure).lower() for token in ("retry", "failed", "job", "sync", "provider")), failure


@pytest.mark.asyncio
async def test_approval_history_is_persisted(backend, seed_ids):
    history, _ = await backend.request("l4", "GET", f"/v1/reviews/history?account_id={seed_ids.account_id}", expected=(200,))
    assert any(token in str(history).lower() for token in ("review", "decision", "history", "audit")), history
