# Salesforce CRM Integration — Production Launch Checklist

**Date:** 2026-05-01  
**Status:** Ready with caveats (see Section 5)

---

## 1. Environment & Secrets

- [x] `CREDENTIALS_MASTER_KEY` configured in staging/prod (43-char Fernet key)
- [x] `SALESFORCE_CLIENT_ID` configured
- [x] `SALESFORCE_CLIENT_SECRET` configured
- [x] `SALESFORCE_REDIRECT_URI` configured and matches Connected App
- [x] `SALESFORCE_WEBHOOK_SECRET` configured
- [x] `CRM_WEBHOOKS_REQUIRE_TENANT_ID=true` in production
- [x] `ALLOW_ENV_CRM_FALLBACK=false` in production
- [x] `.env.example` updated with all CRM variables

## 2. Salesforce Configuration

- [x] Connected App created in Salesforce
- [x] OAuth scopes: `api`, `refresh_token`, `offline_access`
- [x] Callback URL configured with `?tenant_id` parameter
- [x] Webhook outbound message URL configured with `?tenant_id` parameter
- [x] IP relaxation or trusted IPs configured

## 3. Database

- [x] Migration 010 (integrations table) applied
- [x] Migration 013 (RLS policies) applied
- [x] Migration 018 (strict RLS, no NULL bypass) applied
- [x] Migration 020 (tenant-safe CRM constraints) applied
- [x] Migration 021 (Salesforce OAuth fields) applied
- [x] Alembic upgrade head passes
- [x] Alembic downgrade -1 passes for 021

## 4. Backend Hardening

- [x] Webhook tenant isolation implemented (fail-closed in production)
- [x] `tenant_id` query parameter required for CRM webhooks
- [x] Integration lookup verifies tenant + provider before sync
- [x] Token refresh implemented (`refresh_salesforce_token`)
- [x] Token refresh marks integration as `DEGRADED` on failure
- [x] SOQL pagination implemented (`_execute_soql_query`)
- [x] Rate limit detection implemented (429 handling)
- [x] Credential encryption at rest verified
- [x] No secrets in API responses (`to_dict()` excludes credentials)
- [x] Structured logging with `tenant_id` and redacted errors

## 5. Known Limitations & Caveats

- [ ] **OAuth Authorization Flow is NOT implemented.**
  - Current integration requires manual entry of Access Token + Refresh Token.
  - Token refresh works automatically once tokens are stored.
  - OAuth callback route (`/oauth/callback`) does not exist.
  - **Impact:** Admin burden for initial setup. Not a security blocker.
  - **Mitigation:** Documented in runbook. Planned for post-launch.

- [ ] **Background sync uses `asyncio.create_task`, not Celery.**
  - Sync jobs are ephemeral and lost on pod restart.
  - **Impact:** No durable job queue, no retry persistence.
  - **Mitigation:** Scheduled sync via `CRMSyncScheduler` is robust. Manual sync can be re-triggered.

- [ ] **No dedicated `sync_jobs` history table.**
  - **Impact:** Limited observability into long-running sync history.
  - **Mitigation:** Metrics and logs provide sufficient operational visibility.

## 6. Observability

- [x] Prometheus metrics added:
  - `layer4_crm_salesforce_connections_total`
  - `layer4_crm_salesforce_sync_started_total`
  - `layer4_crm_salesforce_sync_completed_total`
  - `layer4_crm_salesforce_sync_failed_total`
  - `layer4_crm_salesforce_sync_duration_seconds`
  - `layer4_crm_salesforce_records_synced_total`
  - `layer4_crm_salesforce_token_refresh_failed_total`
  - `layer4_crm_salesforce_rate_limit_total`
- [x] Structured audit events for connect/disconnect/sync
- [x] Log redaction for tokens, bearer strings, api keys
- [x] Request ID propagated through API to background jobs

## 7. Testing

- [x] Unit tests: validation, encryption roundtrip
- [x] Unit tests: SOQL pagination
- [x] Unit tests: rate limit graceful handling
- [x] Unit tests: max page safety limit
- [x] Integration tests: sync provider with mocked CRM APIs
- [x] Integration tests: webhook payload parsing
- [ ] Integration tests: cross-tenant webhook isolation (requires full env)
- [ ] Integration tests: RLS fail-closed (requires PostgreSQL)
- [x] Frontend typecheck passes (`pnpm check`)

## 8. Documentation

- [x] Operator runbook created (`docs/operations/salesforce-crm-runbook.md`)
- [x] Launch checklist created (`docs/launch-checklists/salesforce-crm-launch.md`)
- [x] `.env.example` documented with all CRM variables

## 9. Rollback Plan

- [x] Tenant-level disable: `UPDATE integrations SET enabled = false`
- [x] Global disable: `CRM_TYPE=none` + restart
- [x] Migration rollback: `alembic downgrade 020`

---

## Launch Decision

**Status:** `READY_WITH_CAVEATS`

The Salesforce CRM integration is **safe to launch** for production use with the following conditions:
1. Admins accept manual token entry for initial Salesforce connection (OAuth flow missing).
2. Webhook URLs are configured with `?tenant_id=<tenant-id>` query parameters.
3. `CRM_WEBHOOKS_REQUIRE_TENANT_ID=true` is enforced in production.

**Post-launch follow-ups:**
1. Implement OAuth authorization flow (redirect → callback → token exchange).
2. Migrate background sync from `asyncio.create_task` to Celery/Redis queue.
3. Add `sync_jobs` table for durable job history and retry tracking.
