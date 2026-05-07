# Abuse Emergency Controls Runbook

## Purpose
Define emergency controls for abuse spikes (401/403/429 bursts, token replay signals) and how to safely tighten protections.

## Controls

### 1) Blocklists
- Apply temporary IP/CIDR blocklists at edge/gateway.
- Apply API key / tenant blocklists in auth layer when repeated abusive patterns are confirmed.
- Expire blocklist entries by default (recommended TTL: 1-24h) and require incident ticket linkage.

### 2) Temporary stricter limits
- Reduce route-class limits for:
  - Auth endpoints (`/auth`, `/v1/auth`)
  - Write-heavy endpoints (`/v1/ingest`, `/v1/sync`, `/v1/schema/init`)
  - Export/report endpoints (`/v1/export`, `/v1/report`)
- Increase WAF/gateway anomaly sensitivity only during active incident windows.
- Keep rollback criteria explicit (e.g., deny/error rates normalize for >=30 minutes).

### 3) Replay protection escalation
- Rotate signing keys/session secrets if replay is broad or credential theft suspected.
- Force token re-issue for impacted tenants/users.
- Require nonce/jti replay cache checks in auth stack for elevated mode.

## Activation checklist
1. Confirm alert source and scope (layer, endpoint, tenant, API key, source IP).
2. Declare incident and assign commander.
3. Apply least-disruptive control first (key block > IP/CIDR block > global stricter limits).
4. Monitor 5-minute rolling rates for 401/403/429 and replay signals.
5. Escalate only if abuse persists.

## Rollback checklist
1. Remove temporary blocks in reverse order of application.
2. Restore normal route-class rate limits.
3. Verify error budgets and auth success rates return to baseline.
4. Publish incident summary with retained and removed controls.

## Related monitoring
- `AuthDeniedSpike` alert (401/403 surge)
- `RateLimit429Spike` alert (429 surge)
- `TokenReplaySuspected` alert (replay pattern)
