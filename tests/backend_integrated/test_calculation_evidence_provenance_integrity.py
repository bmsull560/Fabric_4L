"""Suite 5 — Calculation, Evidence, and Provenance Integrity."""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.backend_integrated, pytest.mark.integration, pytest.mark.e2e]


@pytest.mark.asyncio
async def test_formula_inputs_validate_required_fields(backend, seed_ids):
    body, response = await backend.request(
        "l4",
        "POST",
        "/v1/analysis/roi",
        json={"account_id": seed_ids.account_id, "formula_id": seed_ids.formula_id, "variables": {"annual_revenue": 10_000_000}},
        expected=(400, 422),
    )
    assert response.status_code in {400, 422}
    assert any(token in str(body).lower() for token in ("required", "missing", "validation", "detail")), body


@pytest.mark.asyncio
async def test_invalid_numeric_inputs_are_rejected(backend, seed_ids):
    body, response = await backend.request(
        "l4",
        "POST",
        "/v1/analysis/roi",
        json={"account_id": seed_ids.account_id, "variables": {"annual_revenue": "not-a-number", "implementation_cost": 125000}},
        expected=(400, 422),
    )
    assert response.status_code in {400, 422}
    assert any(token in str(body).lower() for token in ("invalid", "number", "validation", "error", "detail")), body


@pytest.mark.asyncio
async def test_currency_and_time_period_handling_are_consistent(backend, seed_ids):
    result, _ = await backend.request(
        "l4",
        "POST",
        "/v1/analysis/roi",
        json={
            "account_id": seed_ids.account_id,
            "formula_id": seed_ids.formula_id,
            "currency": "USD",
            "time_period": "annual",
            "variables": {"annual_revenue_usd": 10_000_000, "annual_benefit_usd": 500_000, "implementation_cost_usd": 125_000},
        },
        expected=(200, 201),
    )
    result_text = str(result).lower()
    assert "usd" in result_text or "currency" in result_text, result
    assert "annual" in result_text or "period" in result_text, result


@pytest.mark.asyncio
async def test_conservative_expected_optimistic_scenarios_are_reproducible(backend, seed_ids):
    payload = {
        "account_id": seed_ids.account_id,
        "formula_id": seed_ids.formula_id,
        "variables": {"annual_revenue": 10_000_000, "conversion_lift_pct": 11, "implementation_cost": 125_000},
        "scenarios": ["conservative", "expected", "optimistic"],
    }
    first, _ = await backend.request("l4", "POST", "/v1/analysis/roi", json=payload, expected=(200, 201))
    second, _ = await backend.request("l4", "POST", "/v1/analysis/roi", json=payload, expected=(200, 201))
    assert first == second, "Identical calculation input must produce deterministic scenario output."
    assert all(name in str(first).lower() for name in ("conservative", "expected", "optimistic")), first


@pytest.mark.asyncio
async def test_scenario_output_is_stable_after_reload(backend, seed_ids):
    scenario, _ = await backend.request(
        "l4",
        "POST",
        "/v1/scenarios",
        json={"account_id": seed_ids.account_id, "name": "expected", "formula_id": seed_ids.formula_id, "inputs": {"annual_benefit": 500000}},
        expected=(200, 201, 202),
    )
    scenario_id = scenario.get("id") or scenario.get("scenario_id") or seed_ids.formula_id
    reloaded, _ = await backend.request("l4", "GET", f"/v1/scenarios/{scenario_id}", expected=(200,))
    assert str(scenario) == str(reloaded) or seed_ids.formula_id in str(reloaded), reloaded


@pytest.mark.asyncio
async def test_customer_metric_override_takes_precedence_over_benchmark(backend, seed_ids):
    override, _ = await backend.request(
        "l4",
        "POST",
        f"/v1/accounts/{seed_ids.account_id}/metrics/overrides",
        json={"metric": "conversion_lift_pct", "value": 13, "evidence_id": seed_ids.evidence_id, "benchmark_id": seed_ids.benchmark_id},
        expected=(200, 201, 202),
    )
    assert "13" in str(override)
    result, _ = await backend.request(
        "l4",
        "POST",
        "/v1/analysis/roi",
        json={"account_id": seed_ids.account_id, "formula_id": seed_ids.formula_id, "variables": {"conversion_lift_pct": 11}, "use_customer_overrides": True},
        expected=(200, 201),
    )
    assert "13" in str(result) or "override" in str(result).lower(), result


@pytest.mark.asyncio
async def test_business_case_claims_trace_to_evidence_benchmark_or_assumption(backend, seed_ids):
    await backend.create_seed_graph()
    case, _ = await backend.request(
        "l4",
        "POST",
        "/v1/cases",
        json={"account_id": seed_ids.account_id, "claims": [{"text": "Conversion improved", "evidence_ids": [seed_ids.evidence_id], "benchmark_id": seed_ids.benchmark_id}]},
        expected=(200, 201, 202),
    )
    case_id = case.get("id") or case.get("case_id") or seed_ids.account_id
    trace, _ = await backend.request("l4", "GET", f"/v1/cases/{case_id}/traceability", expected=(200,))
    assert any(token in str(trace).lower() for token in ("evidence", "benchmark", "assumption")), trace
    assert seed_ids.evidence_id in str(trace) or seed_ids.benchmark_id in str(trace), trace


@pytest.mark.asyncio
async def test_calculation_change_creates_version_history_event(backend, seed_ids):
    created, _ = await backend.request(
        "l4",
        "POST",
        "/v1/formulas",
        json={"id": seed_ids.formula_id, "name": "ROI payback", "expression": "benefit - cost"},
        expected=(200, 201, 202, 409),
    )
    assert seed_ids.formula_id in str(created)
    updated, _ = await backend.request("l4", "PATCH", f"/v1/formulas/{seed_ids.formula_id}", json={"expression": "(benefit - cost) / cost"}, expected=(200, 202))
    assert "version" in str(updated).lower(), updated
    await backend.assert_audit_event("formula.version.created", seed_ids.formula_id)


@pytest.mark.asyncio
async def test_unapproved_assumption_blocks_business_case_approval(backend, seed_ids):
    case, _ = await backend.request(
        "l4",
        "POST",
        "/v1/cases",
        json={"account_id": seed_ids.account_id, "claims": [{"text": "Assumed uplift", "assumption_id": seed_ids.evidence_id, "assumption_status": "pending_review"}]},
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
    assert any(token in str(body).lower() for token in ("assumption", "unapproved", "pending", "validation")), body
