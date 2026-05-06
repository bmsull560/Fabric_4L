# Layer 4 externally reachable route inventory and sensitivity classes

This inventory defines endpoint classes used for layered quota policy.

## Endpoint classes

- `auth`: authentication and key/session endpoints.
- `write`: state-mutating endpoints (`POST`, `PUT`, `PATCH`, `DELETE`).
- `admin`: tenant admin and control-plane endpoints.
- `expensive_compute`: long-running analysis/orchestration endpoints.
- `read`: default read-only endpoints.

## Route groups

- `/health`, `/metrics`: public operational endpoints (read).
- `/v1/workflows*`, `/v1/agent-stream*`, `/v1/analysis*`, `/v1/prospects*`: expensive_compute + write for mutating verbs.
- `/v1/tools*`, `/v1/signals*`, `/v1/checkpoints*`, `/v1/state-inspector*`, `/v1/health*`: read/write mixed, classify by HTTP verb.
- `/v1/tenants*`, `/v1/users*`, `/v1/api-keys*`, `/auth/oidc*`, `/v1/feature-flags*`, `/v1/models*`, `/v1/tenants/{tenant_id}/provisioning*`: auth/admin sensitive.
- `/v1/enrichment*`, `/v1/hypotheses*`, `/v1/narratives*`, `/v1/intelligence*`: expensive_compute.
- `/v1/billing*`, `/v1/accounts*`, `/v1/integrations*`, `/v1/audit*`: admin/read-write (tenant-scoped).
- `/v1/c1*`, `/v1/ground-truth*`, `/v1/webhooks/crm*`: integration/webhook surfaces; write-sensitive.

## Layered quotas (policy intent)

Enforcement order in middleware:
1. Per-tenant baseline.
2. Per-user quota (when user identity exists).
3. Per-API-key quota (for API-key auth).
4. Per-endpoint-class quota (auth/write/admin/expensive_compute/read).

Ingress/gateway policies MUST use the same class mapping and key dimensions to prevent bypass.
