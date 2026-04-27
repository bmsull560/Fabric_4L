# RFC-001: Add Formula Scenario Endpoint to L3 Knowledge API

**Status:** Approved  
**Author:** Frontend Engineering  
**Date:** 2026-04-27  
**Layer:** L3 Knowledge  
**Council Reviewers:** Backend Engineering, Platform/Security  

---

## 1. Summary

Add a new `POST /formulas/scenario` endpoint to the L3 Knowledge API that accepts a formula ID and a set of variable adjustments, and returns the recalculated ROI metrics alongside the original values for comparison.

## 2. Motivation

The FormulaBuilder page requires a "what-if" scenario analysis feature that lets users adjust input variables and see the impact on ROI, payback period, and NPV in real time. Currently, the only way to evaluate a formula is via the existing `POST /formulas/evaluate` endpoint, which does not support side-by-side comparison of original vs. adjusted values and does not return delta percentages.

Without this endpoint, the frontend would need to make two separate API calls (one for original, one for adjusted) and compute deltas client-side, which duplicates business logic and creates inconsistency risk.

## 3. Proposed Changes

### New Endpoint

- **Method:** `POST`
- **Path:** `/api/v1/formulas/scenario`
- **Authentication:** Bearer token (tenant-scoped)

### Request Schema: `ScenarioRequest`

```json
{
  "formula_id": "string (required)",
  "adjustments": [
    {
      "variable_id": "string (required)",
      "new_value": "number (required)"
    }
  ]
}
```

### Response Schema: `ScenarioResponse`

```json
{
  "formula_id": "string",
  "original_value": "number",
  "adjusted_value": "number",
  "delta_percentage": "number",
  "new_roi": "number",
  "new_payback_months": "number",
  "warnings": ["string"]
}
```

### OpenAPI Spec Change

File: `contracts/openapi/layer3-knowledge.json`

A new path `/formulas/scenario` will be added with the `POST` method, referencing the `ScenarioRequest` and `ScenarioResponse` schemas defined in the `components/schemas` section.

## 4. Breaking Change Assessment

- [x] **Non-breaking:** This is a new endpoint. No existing endpoints are modified. Safe to deploy independently.

## 5. Security & Governance Impact

- [ ] Exposes new data fields — No. The response contains the same ROI metrics already available via `/formulas/evaluate`.
- [ ] Changes authentication/authorization requirements — No. Same tenant-scoped Bearer token.
- [x] Modifies tenant scoping — No change. The formula is resolved within the tenant's scope via the existing `GovernanceMiddleware`.

The `formula_id` is validated against the tenant's owned formulas. A user cannot run scenarios against formulas belonging to another tenant.

## 6. Alternatives Considered

**Alternative A: Client-side delta computation.** The frontend calls `/formulas/evaluate` twice (once with original variables, once with adjusted) and computes deltas in JavaScript. Rejected because it duplicates business logic, increases latency (two round trips), and risks inconsistency if the formula's underlying data changes between calls.

**Alternative B: Extend the existing `/formulas/evaluate` endpoint with an optional `compare_to` parameter.** Rejected because it overloads the evaluate endpoint's semantics and complicates its response schema for all consumers.

---

## Council Decision

**Approved** on 2026-04-27. The new endpoint is additive, non-breaking, and follows existing naming conventions. The `useFormulaScenario` frontend hook was implemented in Sprint 4 (commit `4978c58`).
