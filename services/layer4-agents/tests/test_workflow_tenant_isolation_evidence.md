# Workflow Tenant Isolation — Test Assurance Evidence

**Generated**: 2026-05-05
**Agent**: Autonomous Test Assurance Agent (Level 4)
**Scope**: Layer 4 Agents — Workflow API routes

## 1. Gap Discovered

The `src/api/routes/workflows.py` endpoint had **inconsistent tenant isolation enforcement**:

| Endpoint | Had Tenant Check? |
|----------|-------------------|
| `GET /workflows` | Yes (via `_ctx.tenant_id` in `_filter_and_paginate_workflows`) |
| `GET /workflows/active` | Yes (via `_ctx.tenant_id` in `_filter_and_paginate_workflows`) |
| `POST /workflows/{id}/archive` | Yes |
| `POST /workflows` | **No** — `tenant_id` in body was not validated against auth context |
| `GET /workflows/{id}` | **No** |
| `GET /workflows/{id}/result` | **No** |
| `DELETE /workflows/{id}` | **No** |
| `POST /workflows/{id}/resume` | **No** |
| `POST /workflows/{id}/pause` | **No** |
| `GET /workflows/{id}/events` | **No** |

This allowed an authenticated user from **Tenant A** to:
- Read status, results, and events of workflows owned by **Tenant B**
- Cancel, resume, or pause workflows owned by **Tenant B**
- Create workflows attributed to **Tenant B** via body parameter

## 2. Tests Engineered

File: `tests/test_workflow_tenant_isolation.py`

### Positive Tests (same-tenant access works)
- `test_get_status_same_tenant`
- `test_get_result_same_tenant`
- `test_cancel_same_tenant`
- `test_resume_same_tenant`
- `test_pause_same_tenant`
- `test_archive_same_tenant`
- `test_create_workflow_valid_tenant`

### Negative Tests (cross-tenant access blocked with 403)
- `test_get_status_cross_tenant_returns_403`
- `test_get_result_cross_tenant_returns_403`
- `test_cancel_cross_tenant_returns_403`
- `test_resume_cross_tenant_returns_403`
- `test_pause_cross_tenant_returns_403`
- `test_archive_cross_tenant_returns_403`
- `test_create_workflow_cross_tenant_returns_403`

### Adversarial Tests (edge cases)
- `test_get_status_missing_workflow_returns_404`
- `test_get_result_not_terminal_returns_400`
- `test_resume_terminal_workflow_returns_400`
- `test_pause_already_paused_returns_400`

**Result**: 18/18 tests pass

## 3. Production Fixes Applied

File: `src/api/routes/workflows.py`

Added tenant isolation checks to:
1. `create_workflow` — validates `request.tenant_id == _ctx.tenant_id` before execution
2. `get_workflow_status` — checks `status["tenant_id"]` against `_ctx.tenant_id`
3. `get_workflow_result` — checks `status["tenant_id"]` against `_ctx.tenant_id`
4. `cancel_workflow` — checks `status["tenant_id"]` against `_ctx.tenant_id`
5. `resume_workflow` — checks `status["tenant_id"]` against `_ctx.tenant_id`
6. `pause_workflow` — checks `status["tenant_id"]` against `_ctx.tenant_id`
7. `get_workflow_events` — checks `status["tenant_id"]` before starting SSE stream

Pattern used (consistent with existing `archive_workflow` endpoint):
```python
workflow_tenant = status.get("tenant_id")
if workflow_tenant and str(workflow_tenant) != str(_ctx.tenant_id):
    raise HTTPException(
        status_code=403,
        detail=f"Workflow {workflow_id} does not belong to the current tenant",
    )
```

## 4. Supporting Fix

File: `tests/conftest.py`

Added `openai` module stub to the heavy-dependency stub block (lines 54-60), matching the pattern used for `jinja2`, `botocore`, and `langgraph.checkpoint.postgres`. This unblocks test collection in environments where `openai` is not installed.

## 5. Verification

```bash
cd services/layer4-agents
python -m pytest tests/test_workflow_tenant_isolation.py -v
# 18 passed, 6 warnings in 0.98s

python -m py_compile src/api/routes/workflows.py
# Syntax OK
```

## 6. Regression Risk Assessment

- **Low risk**: The tenant check pattern is already used in `archive_workflow` (line 711-717) and is well-established in the codebase.
- **Backward compatible**: Workflows without a `tenant_id` (legacy data) are allowed through (`if workflow_tenant and ...`).
- **No breaking changes**: All changes are additive guards; no existing behavior is modified except cross-tenant access, which was never intended to work.
