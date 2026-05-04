# Salesforce CRM Integration — Operator Runbook

## Overview

This runbook covers the operation of the Salesforce CRM integration in the Value Fabric platform.

## Prerequisites

- Access to the Salesforce Connected App configured for Value Fabric
- Access to Infisical or the deployment secret manager
- `kubectl` access to the production cluster (if applicable)
- Database access for troubleshooting (read-only recommended)

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SALESFORCE_CLIENT_ID` | Yes | Salesforce Connected App Consumer Key |
| `SALESFORCE_CLIENT_SECRET` | Yes | Salesforce Connected App Consumer Secret |
| `SALESFORCE_REDIRECT_URI` | Yes | Must match Connected App callback URL |
| `CREDENTIALS_MASTER_KEY` | Yes | Fernet key for credential encryption (43 chars) |
| `CRM_SYNC_BATCH_SIZE` | No | Records per sync batch (default: 100) |
| `CRM_SYNC_INTERVAL_MINUTES` | No | Minutes between sync sweeps (default: 60) |
| `CRM_SYNC_MAX_TENANTS_PER_BATCH` | No | Max tenants per sweep (default: 100) |

**NEVER set `ALLOW_ENV_CRM_FALLBACK=true` in production.**

---

## How to Configure Salesforce Connected App

1. Log in to Salesforce as an admin.
2. Go to **Setup > App Manager > New Connected App**.
3. Enable **OAuth Settings**.
4. Set **Callback URL** to the value of `SALESFORCE_REDIRECT_URI`.
5. Select OAuth scopes: `api`, `refresh_token`.
6. Save and copy **Consumer Key** → `SALESFORCE_CLIENT_ID`.
7. Copy **Consumer Secret** → `SALESFORCE_CLIENT_SECRET`.
8. Wait 2–10 minutes for Salesforce to propagate the app.

---

## How to Rotate Client Secret

1. In Salesforce, go to the Connected App > **Manage** > **Edit Policies**.
2. Click **Regenerate Consumer Secret**.
3. Update `SALESFORCE_CLIENT_SECRET` in Infisical.
4. Roll the Layer 4 deployment to pick up the new secret.
5. Monitor `crm_salesforce_token_refresh_failed_total` for spikes.

---

## How to Reconnect a Tenant

1. Ask the tenant admin to visit **Settings > Integrations > Salesforce**.
2. Click **Disconnect** (this deletes the integration row and clears tokens).
3. Click **Connect Salesforce** and complete OAuth.
4. Verify connection with **Test Connection**.

---

## How to Manually Trigger Sync

### Via API

```bash
curl -X POST "https://api.valuefabric.io/v1/integrations/salesforce/sync" \
  -H "Authorization: Bearer <admin_token>" \
  -H "X-Tenant-ID: <tenant_id>"
```

### Via Database (emergency only)

Update the integration row to set `sync_status = 'pending'`. The scheduler will pick it up on the next sweep.

---

## How to Inspect Failed Syncs

### Check Logs

Filter logs for:
```
crm_sync_event:{"event":"sync_failed", "tenant_id":"<tenant_id>"}
```

### Check Database

```sql
SELECT tenant_id, sync_status, last_error_message, last_sync_at
FROM integrations
WHERE provider = 'salesforce' AND sync_status = 'failed';
```

### Common Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `Token refresh failed: HTTP 401` | Refresh token revoked | Tenant must reconnect OAuth |
| `CRM configuration missing` | Integration disabled or missing | Verify integration row exists and `enabled = true` |
| `Rate limit exceeded` | Salesforce API limit hit | Wait and retry; increase `CRM_SYNC_INTERVAL_MINUTES` |
| `Invalid prospect_id format` | Bad Salesforce ID in webhook | Check webhook payload for malformed IDs |

---

## How to Handle Revoked Tokens

1. Check logs for `Token refresh failed`.
2. If the refresh token is invalid, the integration status becomes `degraded`.
3. Notify the tenant admin to reconnect.
4. If the tenant cannot reconnect, delete the integration row:
   ```sql
   DELETE FROM integrations
   WHERE tenant_id = '<tenant_id>' AND provider = 'salesforce';
   ```

---

## How to Disable Integration

### Per-Tenant

1. Set `enabled = false` on the integration row.
2. The scheduler skips disabled integrations.

### Globally

1. Unset `SALESFORCE_CLIENT_ID` and `SALESFORCE_CLIENT_SECRET`.
2. Token refresh will fail; integrations will enter `degraded` status.
3. Frontend will show reconnection prompt.

---

## Rollback Plan

If a sync job causes data corruption:

1. Stop the scheduler: set `CRM_SYNC_INTERVAL_MINUTES=999999` and restart Layer 4.
2. Identify affected tenant_ids from logs.
3. Restore accounts from backup if available.
4. Fix the bug and redeploy.
5. Re-enable scheduler.

## Metrics to Watch

| Metric | Alert Threshold | Meaning |
|--------|-----------------|---------|
| `crm_salesforce_sync_failed_total` | > 5 in 10 min | Multiple sync failures |
| `crm_salesforce_token_refresh_failed_total` | > 3 in 1 hour | OAuth refresh issues |
| `crm_salesforce_rate_limit_total` | > 1 in 1 hour | Hitting Salesforce API limits |
