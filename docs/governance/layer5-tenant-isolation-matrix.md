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
