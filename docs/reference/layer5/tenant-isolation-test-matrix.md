# Layer 5 Tenant-Isolation Hostile Test Matrix (Phase 1 Gate)

This matrix defines the **minimum hostile tenant-isolation coverage** for Layer 5 endpoint families and the **Phase 1 exit gate**.

## Scope

Layer 5 endpoint families covered:
- Truth CRUD/list
- Validation
- Governance summaries
- Transitions
- Sync endpoints
- Future bulk endpoints

Each family must include automated tests for:
1. Cross-tenant read denial.
2. Cross-tenant write denial.
3. Request-body tenant override rejection (authenticated tenant context wins).
4. Missing-tenant-context fail-closed behavior.

## Matrix

| Endpoint family | Representative endpoints | Cross-tenant read denial | Cross-tenant write denial | Request-body tenant override rejection | Missing-tenant-context fail-closed | Automated test file references | Phase 1 gate status |
|---|---|---|---|---|---|---|---|
| Truth CRUD/list | `GET/POST /api/v1/truths`, `GET/DELETE /api/v1/truths/{truth_id}`, `GET /api/v1/truths/stale` | Required | Required | Required | Required | `services/layer5-ground-truth/tests/test_cross_tenant_hostile.py`; `services/layer5-ground-truth/tests/test_api_tenant_propagation.py`; `tests/security/test_tenant_boundary_fails_closed.py`; `tests/security/test_cross_tenant_api.py`; `tests/security/test_cross_tenant_write.py` | Pass only when all four hostile classes are asserted in automated tests |
| Validation | `POST /api/v1/truths/{truth_id}/validate`, `POST /api/v1/truths/{truth_id}/sources`, `GET /api/v1/truths/{truth_id}/audit` | Required | Required | Required | Required | `services/layer5-ground-truth/tests/test_cross_tenant_hostile.py`; `services/layer5-ground-truth/tests/test_api.py`; `services/layer5-ground-truth/tests/test_api_tenant_propagation.py`; `tests/security/test_tenant_context_contract.py` | Pass only when all four hostile classes are asserted in automated tests |
| Governance summaries | `GET /api/v1/maturity-ladder`, `GET /api/v1/truths/freshness-summary` | Required (for tenant-scoped summaries) | Required (N/A for read-only endpoints; assert no state mutation path) | Required (reject/ignore tenant hints in query/body where applicable) | Required | `services/layer5-ground-truth/tests/test_freshness_monitor.py`; `services/layer5-ground-truth/tests/test_api_tenant_propagation.py`; `tests/security/test_tenant_boundary_fails_closed.py`; `tests/security/test_tenant_context_contract.py` | Pass only when read-path fail-closed and tenant-context integrity are automated |
| Transitions | `POST /api/v1/truths/{truth_id}/validate` transition actions | Required | Required | Required | Required | `services/layer5-ground-truth/tests/test_state_machine.py`; `services/layer5-ground-truth/tests/test_cross_tenant_hostile.py`; `services/layer5-ground-truth/tests/test_api_tenant_propagation.py`; `tests/security/test_cross_layer_tenant.py` | Pass only when transition calls cannot cross tenant boundaries and cannot honor body tenant overrides |
| Sync endpoints | `POST /api/v1/truths/sync-kg`, `POST /api/v1/truths/check-stale` | Required | Required | Required | Required | `services/layer5-ground-truth/tests/test_api.py`; `services/layer5-ground-truth/tests/test_api_tenant_propagation.py`; `services/layer5-ground-truth/tests/test_cross_tenant_hostile.py`; `tests/security/test_tenant_boundary_fails_closed.py` | Pass only when sync actions are strictly tenant-scoped and fail closed without tenant context |
| Future bulk endpoints | `POST /api/v1/truths/bulk-*` (reserved family) | Required | Required | Required | Required | `tests/security/test_tenant_boundary_fails_closed.py` (baseline fail-closed pattern); **plus** family-specific bulk tests to be added under `services/layer5-ground-truth/tests/` before endpoint launch | **Blocked** until each concrete bulk route has at least one explicit automated test file reference |

## Phase 1 Exit Rule (Mandatory)

Phase 1 is complete **only when every matrix row maps to at least one automated test file under**:
- `services/layer5-ground-truth/tests/`, or
- `tests/security/`

with explicit file references in this matrix.

If any row lacks explicit file mapping, Phase 1 exit is **denied**.

## CI/Review Enforcement Guidance

- Treat this matrix as a required review artifact for Layer 5 tenant-isolation changes.
- For new Layer 5 endpoint families, add a matrix row and test-file references in the same change set.
- For future bulk endpoints, merge is blocked until endpoint-specific hostile tests exist and this matrix is updated with exact files.
