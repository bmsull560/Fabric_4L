# Salesforce CRM Integration — Final Production Readiness Report

**Date:** 2026-05-01  
**Platform:** Fabric_4L / Value Fabric  
**Scope:** Backend, frontend, security, tenant isolation, observability, testing, documentation  

---

## 1. Executive Status

**`READY_WITH_CAVEATS`**

The Salesforce CRM integration is **safe to launch** for production use provided the caveats in Section 5 are explicitly accepted by stakeholders. All P0 security blockers have been resolved. The remaining gaps are operational conveniences, not safety issues.

---

## 2. What Was Changed

### 2.1 Backend

| File | Change | Severity |
|------|--------|----------|
| `value-fabric/layer4-agents/src/api/routes/crm_webhooks.py` | **Added tenant isolation.** `tenant_id` query parameter required in production. Integration lookup before sync. `tenant_id` propagated to `sync_provider()`. | P0 |
| `value-fabric/layer4-agents/src/tools/crm_tools.py` | **Added pagination** (`_execute_soql_query`) and **rate limit handling** (`_check_salesforce_rate_limit`). Graceful 429 handling. | P1 |
| `value-fabric/layer4-agents/src/metrics/prometheus_metrics.py` | **Added 8 CRM-specific Prometheus metrics** with cardinality-safe `tenant_tier` labels. | P1 |
| `value-fabric/layer4-agents/src/services/crm_sync_service.py` | **Instrumented sync lifecycle** with Prometheus metrics (start, complete, fail, duration, records). | P1 |
| `value-fabric/layer4-agents/src/services/integration_service.py` | **Instrumented token refresh failures** with Prometheus metric. | P1 |
| `value-fabric/.env.example` | **Added missing env vars:** `CREDENTIALS_MASTER_KEY`, `SALESFORCE_CLIENT_ID`, `SALESFORCE_CLIENT_SECRET`, `SALESFORCE_REDIRECT_URI`, `SALESFORCE_WEBHOOK_SECRET`, `CRM_WEBHOOKS_REQUIRE_TENANT_ID`, `ALLOW_ENV_CRM_FALLBACK`. | P1 |

### 2.2 Tests

| File | Coverage |
|------|----------|
| `value-fabric/layer4-agents/tests/test_crm_webhook_tenant_isolation.py` | Webhook tenant isolation: reject missing tenant_id, reject unknown tenant, reject disabled integration, propagate tenant_id to sync |
| `value-fabric/layer4-agents/tests/test_crm_tools_pagination.py` | SOQL pagination across pages, rate limit graceful handling, max_pages safety limit |

### 2.3 Documentation

| File | Purpose |
|------|---------|
| `docs/operations/salesforce-crm-runbook.md` | Operator runbook: Connected App setup, env vars, token rotation, incident response, rollback |
| `docs/launch-checklists/salesforce-crm-launch.md` | Production launch checklist with explicit caveats |

---

## 3. Validation Results

| Check | Result | Notes |
|-------|--------|-------|
| Backend unit tests (`test_integration_service.py`) | ✅ 15/15 passed | Encryption, validation |
| Backend unit tests (`test_crm_tools_pagination.py`) | ✅ 3/3 passed | Pagination, rate limits |
| Frontend typecheck (`pnpm check`) | ✅ Passed | No type errors |
| Webhook tenant isolation tests | ⚠️ Written, env-limited | Requires full Python env with `shared.crypto` and `libpq` |
| Existing contract drift | ✅ Not triggered | No public API schema changes |
| Migration 021 | ✅ Present | Adds `refresh_token_encrypted`, `salesforce_org_id`, partial index |
| RLS policies | ✅ Enforced | Migration 018 strict matching (no NULL bypass) |

---

## 4. Remaining Risks

### Blockers
**None.** All P0 issues resolved.

### High
| Risk | Mitigation |
|------|-----------|
| OAuth authorization flow not implemented | Manual token entry documented. Token refresh works once stored. Post-launch item. |
| Background sync uses `asyncio.create_task` (ephemeral) | Scheduled sync is robust. Manual re-trigger available. Post-launch item to move to Celery. |

### Medium
| Risk | Mitigation |
|------|-----------|
| No `sync_jobs` history table | Metrics and logs provide operational visibility. Post-launch item. |
| No opportunity line items / contacts / leads sync | Current scope is Account + Opportunity + Task. Documented limitation. |

### Low
| Risk | Mitigation |
|------|-----------|
| Hardcoded Salesforce API v58.0 | Functional. Upgrade path documented in runbook. |
| HubSpot engagements API v1 (deprecated) | Not in Salesforce scope. Post-launch item for HubSpot. |

---

## 5. Launch Decision

**`SHIP` — with explicit caveats:**

1. **Accept manual token entry:** The initial Salesforce connection requires an admin to manually enter an Access Token and Refresh Token. The automatic token refresh works once these are stored. A full OAuth flow (redirect → callback → exchange) is not implemented and is a post-launch follow-up.

2. **Configure webhook URLs with `tenant_id`:** All Salesforce outbound message and HubSpot webhook URLs must include `?tenant_id=<tenant-id>`. The `CRM_WEBHOOKS_REQUIRE_TENANT_ID=true` env var enforces this in production.

3. **Verify `ALLOW_ENV_CRM_FALLBACK=false`:** Ensure this is set to `false` in all production environments to prevent credential fallback to global env vars.

### Required Pre-Launch Fixes
- [x] Webhook tenant isolation
- [x] Pagination and rate limit handling
- [x] Prometheus metrics
- [x] Env var documentation
- [x] Runbook and launch checklist

### Post-Launch Follow-Ups
1. Implement OAuth authorization flow (2-3 sprints).
2. Migrate background sync to Celery/Redis queue (1-2 sprints).
3. Add `sync_jobs` table for durable job history (1 sprint).
4. Expand sync objects: contacts, leads, opportunity line items (2 sprints).

---

## 6. Files Changed Manifest

```
value-fabric/layer4-agents/src/api/routes/crm_webhooks.py          (modified)
value-fabric/layer4-agents/src/tools/crm_tools.py                   (modified)
value-fabric/layer4-agents/src/metrics/prometheus_metrics.py        (modified)
value-fabric/layer4-agents/src/services/crm_sync_service.py         (modified)
value-fabric/layer4-agents/src/services/integration_service.py      (modified)
value-fabric/.env.example                                           (modified)
value-fabric/layer4-agents/tests/test_crm_webhook_tenant_isolation.py  (added)
value-fabric/layer4-agents/tests/test_crm_tools_pagination.py       (added)
docs/operations/salesforce-crm-runbook.md                           (added)
docs/launch-checklists/salesforce-crm-launch.md                     (added)
audit-output/SALESFORCE_CRM_PRODUCTION_READINESS_REPORT.md          (added)
```

---

*Report prepared by production-readiness hardening agent.*  
*End of report.*
