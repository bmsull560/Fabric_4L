# Layer 5 Tenant Isolation Matrix

This matrix tracks tenant-scoped Layer 5 API routes, backing methods, and hostile cross-tenant test coverage.

## Scope

- API modules:
  - `services/layer5-ground-truth/src/layer5_ground_truth/api/router.py`
  - `services/layer5-ground-truth/src/layer5_ground_truth/api/model_registry_routes.py`
- Hostile tests:
  - `services/layer5-ground-truth/tests/test_cross_tenant_hostile.py`

## Matrix

| Method | Route | Backing repository/service methods | Hostile read/write tests | Coverage status |
|---|---|---|---|---|
| POST | `/api/v1/truths` | `create_truth_object`, `get_truth_object` | `test_truth_object_cross_tenant_read_write_denied` | covered |
| GET | `/api/v1/truths` | `list_truth_objects` | `test_truth_list_filter_cross_tenant_enumeration_blocked` | covered |
| GET | `/api/v1/truths/{truth_id}` | `get_truth_object` | `test_truth_object_cross_tenant_read_write_denied` | covered |
| POST | `/api/v1/truths/{truth_id}/validate` | `validate_truth_object` | `test_truth_state_transition_cross_tenant_denied` | covered |
| POST | `/api/v1/truths/{truth_id}/sources` | `add_source` | `test_truth_object_cross_tenant_read_write_denied` | covered |
| GET | `/api/v1/truths/{truth_id}/audit` | `get_truth_object` | `test_truth_audit_cross_tenant_denied` | covered |
| DELETE | `/api/v1/truths/{truth_id}` | `soft_delete_truth_object` | `test_truth_delete_cross_tenant_denied` | covered |
| POST | `/api/v1/truths/sync-kg` | `list_truth_objects`, `layer3_client.sync_truth_object` | `test_truth_sync_cross_tenant_does_not_process_other_tenant_data` | covered |
| POST | `/api/v1/truths/check-stale` | `truth_repo.mark_stale` via stale check flow | `test_truth_check_stale_cross_tenant_does_not_process_other_tenant_data` | covered |
| GET | `/api/v1/truths/stale` | `list_truth_objects` (stale filter path) | `test_truth_stale_list_cross_tenant_enumeration_blocked` | covered |
| GET | `/api/v1/truths/freshness-summary` | freshness aggregation query path | `test_truth_freshness_summary_cross_tenant_scoped` | covered |
| POST | `/api/v1/models` | `ModelVersion` insert | `test_model_registry_cross_tenant_read_write_denied` | covered |
| GET | `/api/v1/models` | `ModelVersion` list query | `test_model_list_cross_tenant_enumeration_blocked` | covered |
| GET | `/api/v1/models/{model_id}` | `ModelVersion` lookup query | `test_model_registry_cross_tenant_read_write_denied` | covered |
| POST | `/api/v1/models/{model_id}/deprecate` | `ModelVersion` update | `test_model_registry_cross_tenant_read_write_denied` | covered |
| POST | `/api/v1/models/{model_id}/set-default` | `ModelVersion` update(s) | `test_model_set_default_cross_tenant_denied` | covered |
| POST | `/api/v1/models/{model_id}/promote` | `ModelDeployment` insert, `ModelVersion` lookup | `test_model_promote_cross_tenant_denied` | covered |
| GET | `/api/v1/models/{model_id}/deployments` | `ModelDeployment` list query | `test_model_deployments_cross_tenant_denied` | covered |
| GET | `/api/v1/deployments` | `ModelDeployment` list query | `test_deployments_list_cross_tenant_enumeration_blocked` | covered |
| POST | `/api/v1/deployments/{deployment_id}/rollback` | `ModelDeployment` lookup + insert | `test_deployment_rollback_cross_tenant_denied` | covered |
| POST | `/api/v1/evaluations` | `ModelEvaluation` insert + `ModelVersion` lookup | `test_evaluation_create_cross_tenant_denied` | covered |
| GET | `/api/v1/evaluations` | `ModelEvaluation` list query | `test_evaluations_list_cross_tenant_enumeration_blocked` | covered |
| GET | `/api/v1/models/{model_id}/evaluations` | `ModelEvaluation` list query | `test_model_evaluations_cross_tenant_denied` | covered |

## Phase 3 Focus Areas

- Bulk operations introduced in Phase 3 must be added to this matrix immediately, with hostile tests that prove no cross-tenant read/write side effects.
- Any new list/filter endpoint must include enumeration-hostile tests.
- Any new transition/sync operation must include cross-tenant denial tests.


## Cross-Layer Route-to-Test Matrix (Layers 1–6, highest-traffic routes first)

This section extends the Layer 5 matrix pattern across the platform and maps each high-traffic route group to hostile test coverage (`Tenant A cannot read/mutate Tenant B`; missing tenant context fails closed).

| Layer | Route group (highest traffic first) | Representative routes | Hostile tests (read/mutate + fail-closed) | Repo/query tenant-filter assertion |
|---|---|---|---|---|
| L1 | Ingestion sources + jobs | `/api/v1/ingestion/sources`, `/api/v1/ingestion/jobs` | `test_l1_read_cross_tenant_denied`, `test_l1_write_cross_tenant_denied`, `test_l1_fail_closed_without_context` | `test_l1_query_filters_present` |
| L2 | Extraction ingest + status/list | `/extract-and-ingest`, `/pipeline/status/{job_id}`, `/pipeline/jobs` | `test_l2_read_cross_tenant_denied`, `test_l2_write_cross_tenant_denied`, `test_l2_fail_closed_without_context` | `test_l2_query_filters_present` |
| L3 | Product/entity read + search/list | `/api/v1/products/{id}`, `/api/v1/products`, graph search/list routes | `test_l3_read_cross_tenant_denied`, `test_l3_write_cross_tenant_denied`, `test_l3_fail_closed_without_context` | `test_l3_query_filters_present` |
| L4 | Workflow create/read/mutate/list | `/api/v1/workflows`, `/api/v1/workflows/{id}`, `/api/v1/workflows/{id}/cancel` | `test_l4_read_cross_tenant_denied`, `test_l4_write_cross_tenant_denied`, `test_l4_fail_closed_without_context` | `test_l4_query_filters_present` |
| L5 | Truth + model registry CRUD | `/api/v1/truths*`, `/api/v1/models*`, `/api/v1/evaluations*` | `services/layer5-ground-truth/tests/test_cross_tenant_hostile.py` (suite), `test_l5_fail_closed_without_context` | `test_l5_query_filters_present` |
| L6 | Benchmarks datasets/list/delete | `/api/v1/datasets`, `/api/v1/datasets/{dataset_id}` | `test_l6_read_cross_tenant_denied`, `test_l6_write_cross_tenant_denied`, `test_l6_fail_closed_without_context` | `test_l6_query_filters_present` |

Primary executable matrix: `tests/security/test_cross_layer_tenant_isolation_matrix.py`.
