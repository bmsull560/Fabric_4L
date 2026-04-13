# Phase 3: Enterprise Hardening — Implementation Plan (Tasks 40–48)

> Generated from a full codebase audit on 2026-04-13.
> Covers nine tasks spanning SSO, model registry, Vault, alerting,
> feature flags, rate limiting, LLM cost metrics, and SDK/CLI.

---

## Table of Contents

- [Architecture Context](#architecture-context)
- [Task 40 — SSO / OIDC](#task-40--sso--oidc)
- [Task 41 — Model Registry](#task-41--model-registry)
- [Task 42 — Vault Wiring](#task-42--vault-wiring)
- [Task 43 — Incident Runbooks](#task-43--incident-runbooks)
- [Task 44 — Alertmanager Config + Slack Notifications](#task-44--alertmanager-config--slack-notifications)
- [Task 45 — Feature Flags](#task-45--feature-flags)
- [Task 46 — Per-Tenant Rate Limiting](#task-46--per-tenant-rate-limiting)
- [Task 47 — LLM Cost Prometheus Metrics](#task-47--llm-cost-prometheus-metrics)
- [Task 48 — SDK / CLI](#task-48--sdk--cli)
- [Execution Order & Dependencies](#execution-order--dependencies)
- [Migration Numbering Plan](#migration-numbering-plan)
- [New Permissions Summary](#new-permissions-summary)

---

## Architecture Context

### What Already Exists

| Component | Location | Status |
|---|---|---|
| `GovernanceMiddleware` (unified auth) | `shared/identity/middleware.py` | ✅ Production-ready — JWT + API-key + X-Tenant-ID |
| Roles & Permissions (6 roles, 17 permissions) | `shared/identity/permissions.py` | ✅ `ROLE_PERMISSIONS` single source of truth |
| Pydantic models (Tenant, User, APIKey) | `shared/identity/models.py` | ✅ `TenantModel.settings` is JSONB (extensible) |
| RequestContext (async-safe ContextVar) | `shared/identity/context.py` | ✅ Available from any await point |
| FastAPI dependency factories | `shared/identity/dependencies.py` | ✅ `require_role()`, `require_permission()`, etc. |
| JWT encode/decode (HS256) | `shared/identity/jwt.py` | ✅ Issuer-agnostic — accepts any HS256 token with correct claims |
| API-key hashing (HMAC-SHA256) | `shared/identity/hashing.py` | ✅ `generate_api_key()`, `hash_api_key()`, `verify_api_key()` |
| Tenant isolation (SQL + Neo4j + Redis) | `shared/identity/isolation.py` | ✅ `TenantScopedMixin`, `TenantScopedCypher`, `tenant_cache_key()` |
| Audit trail (append-only) | `shared/audit/` | ✅ `AuditEmitter`, 21 `AuditAction` enum values, structured JSON log + optional DB write |
| Prometheus metrics (14 types) | `layer4-agents/src/metrics/prometheus_metrics.py` | ✅ HTTP, workflow, agent, health, build info metrics |
| Alert rules (11 rules) | `monitoring/alerting/rules.yml` | ⚠️ No `runbook_url` annotations |
| Prometheus scrape config | `monitoring/prometheus/prometheus.yml` | ✅ All 6 layers + Alertmanager target |
| Vault integration (External Secrets Operator) | `k8s/external-secrets/vault-integration.yml` | ⚠️ Template with `vault.example.com` placeholder |
| K8s manifests | `k8s/` | ✅ All layers + databases + namespace + secrets |
| Tenant ORM model | `layer4-agents/src/tenants/models/tenant.py` | ✅ `settings` JSONB column for config |
| User ORM model | `layer4-agents/src/tenants/models/user.py` | ✅ Invitation flow, bcrypt passwords |
| APIKey ORM model | `layer4-agents/src/tenants/models/api_key.py` | ✅ `rate_limit_per_minute` field exists (not enforced) |
| Alembic migrations (001–003) | `layer4-agents/migrations/versions/` | ✅ accounts → governance → audit |
| OpenAPI export script | `scripts/export_openapi.py` | ✅ Generates L3/L5/L6 specs |
| Contract tests | `tests/contract/test_tool_manifests.py` | ✅ Schema validation for tool manifests |
| GovernanceMiddleware in L1 | `layer1-ingestion/src/api/main.py` | ✅ Wired (api_key_resolver=None) |

### Key Design Constraints

1. **`shared/identity/`** is the cross-layer auth package — all layers import from it. Changes here affect L1–L4.
2. **`Tenant.settings`** (JSONB) is the extensible config blob — use it for OIDC, rate limits, feature flags, model registry thresholds (no schema migration needed for config).
3. **Alembic in L4 manages all governance schema** — all new tables go here.
4. **Audit events are append-only** — DB trigger prevents UPDATE/DELETE on `audit_events`. All new audit actions add to the `AuditAction` enum.
5. **`APIKey.rate_limit_per_minute`** field already exists but has no enforcement logic.
6. **Prometheus metrics use `layer4_` prefix** — new LLM cost metrics should use `vf_` prefix (cross-layer).

---

## Task 40 — SSO / OIDC

**Priority:** P0 | **Effort:** 3 weeks | **Component:** authlib OIDC client, per-tenant IdP config, claim→Role mapping

### Current State

- `GovernanceMiddleware` supports Bearer JWT and API keys — no OIDC flow.
- `jwt.py` uses HS256 (symmetric); no asymmetric key support for verifying external IdP tokens.
- `Tenant.settings` JSONB can store per-tenant IdP config without a migration.
- The middleware is issuer-agnostic: any JWT with `tenant_id`, `sub`, `roles` claims works if signed with `JWT_SECRET`.

### Design Decision: OIDC → Internal JWT Pattern

External IdP tokens are exchanged for VF-signed HS256 JWTs at the callback endpoint. This keeps `GovernanceMiddleware` unchanged on the hot path and avoids asymmetric key verification per request.

```
User → IdP login → authorization code → VF callback → verify id_token (RS256 against IdP JWKS)
                                                     → map claims → Role
                                                     → issue internal VF JWT (HS256)
                                                     → return JWT to client
```

### Files to Create

| File | Purpose |
|---|---|
| `shared/identity/oidc_config.py` | Pydantic model `OIDCProviderConfig` (issuer_url, client_id, client_secret_ref, claim_mapping, default_role, auto_provision_users) |
| `shared/identity/oidc.py` | `OIDCClient` class: discover IdP, verify id_token against JWKS (RS256/ES256), map claims→Role. In-memory JWKS cache (1h TTL per issuer) |
| `layer4-agents/migrations/versions/004_add_oidc_sessions.py` | Table `oidc_sessions`: id (UUID), tenant_id (FK), state (str, unique), nonce, redirect_uri, created_at, expires_at. For CSRF protection during auth code flow |
| `layer4-agents/src/tenants/api/routes/oidc.py` | Endpoints: `GET /v1/auth/oidc/{tenant_slug}/login` (redirect to IdP), `GET /v1/auth/oidc/callback` (exchange code, verify, issue JWT), `GET /v1/auth/oidc/{tenant_slug}/metadata` (non-sensitive IdP info for frontend) |
| `layer4-agents/tests/test_oidc.py` | Unit tests for OIDCClient, claim mapping, auto-provisioning, callback flow with mocked IdP |

### Files to Modify

| File | Change |
|---|---|
| `layer4-agents/pyproject.toml` | Add `authlib>=1.3,<2.0` and `httpx>=0.27` |
| `layer4-agents/src/api/main.py` | Register `oidc_router` under `/v1` |
| `shared/identity/__init__.py` | Export `OIDCClient`, `OIDCProviderConfig` |
| `shared/audit/models.py` | Add `AuditAction.OIDC_LOGIN = "oidc.login"` |
| `value-fabric/.env.example` | Add `OIDC_DEFAULT_REDIRECT_URI` placeholder |
| `docs/secrets-management.md` | Document OIDC client_secret handling via Vault |

### Per-Tenant IdP Configuration (stored in `tenants.settings.oidc`)

```json
{
  "oidc": {
    "provider_name": "Okta",
    "issuer_url": "https://acme.okta.com",
    "client_id": "0oa1234567abcdef",
    "client_secret_ref": "vault:secret/value-fabric/oidc/acme-corp",
    "scopes": ["openid", "profile", "email", "groups"],
    "claim_mapping": {
      "groups.vf_admin": "tenant_admin",
      "groups.vf_analyst": "analyst",
      "groups.vf_viewer": "read_only"
    },
    "default_role": "analyst",
    "auto_provision_users": true,
    "enabled": true
  }
}
```

### Claim→Role Mapping Engine

1. Read `claim_mapping` from tenant's OIDC settings
2. Extract claims from id_token (support nested paths like `groups.value`)
3. Match claims against mapping keys (exact match, array membership, regex)
4. Pick the highest-privilege matching role
5. Fallback to `default_role` if no match
6. Log mapping decision to audit trail

### Acceptance Criteria

- [ ] Tenant admin can configure OIDC IdP via `PATCH /v1/tenants/{id}` (settings.oidc)
- [ ] Users initiate SSO via `GET /v1/auth/oidc/{slug}/login` → IdP redirect → callback → VF JWT
- [ ] IdP claims are mapped to VF roles per configurable claim_mapping
- [ ] Users auto-provisioned on first OIDC login (when enabled)
- [ ] OIDC client secrets stored as Vault references, not plaintext in DB
- [ ] Audit log entry (`oidc.login`) for every OIDC login
- [ ] All OIDC endpoints tested with mocked IdP (no external calls in CI)

---

## Task 41 — Model Registry

**Priority:** P0 | **Effort:** 2 weeks | **Component:** promotion gates, audit trail, CI eval gate

### Current State

- `LLM_MODEL=gpt-4o` in `.env.example` — single env var, no versioning.
- No model registry, promotion workflow, or eval gate.
- L5 (`layer5-ground-truth`) has evaluation infrastructure.
- `audit_events` table is ready for model lifecycle events.

### Files to Create

| File | Purpose |
|---|---|
| `layer4-agents/migrations/versions/005_add_model_registry.py` | Tables: `model_versions` (id, tenant_id, provider, model_name, model_version, stage, promoted_by, eval_score, eval_run_id, config JSONB, created_at) + `model_promotion_log` (id, model_version_id, from_stage, to_stage, promoted_by, reason, eval_score, eval_gate_passed, created_at) |
| `layer4-agents/src/registry/` | Package: `__init__.py`, `models.py` (ORM), `service.py` (CRUD + promotion logic), `eval_gate.py` (call L5 eval API, check threshold) |
| `layer4-agents/src/registry/api/routes.py` | `POST /v1/models` (register), `GET /v1/models` (list), `GET /v1/models/{id}` (detail), `POST /v1/models/{id}/promote` (promote), `GET /v1/models/{id}/history` (audit), `GET /v1/models/active` (resolve active production model) |
| `scripts/ci_eval_gate.py` | CLI script: `python scripts/ci_eval_gate.py --model-version-id <uuid> --min-score 0.85` → exit 0 (pass) or 1 (fail) |
| `layer4-agents/tests/test_model_registry.py` | Registration CRUD, promotion gate enforcement, audit trail, active model resolution |

### Files to Modify

| File | Change |
|---|---|
| `shared/identity/permissions.py` | Add `READ_MODELS`, `WRITE_MODELS`, `ADMIN_MODELS` permissions |
| `shared/identity/permissions.py` | Update `ROLE_PERMISSIONS` (analyst→read, content_admin→write, tenant_admin→admin) |
| `shared/audit/models.py` | Add `MODEL_REGISTERED`, `MODEL_PROMOTED`, `MODEL_DEPRECATED` audit actions |
| `layer4-agents/src/api/main.py` | Register model registry router |
| `layer4-agents/src/engine/executor.py` | Look up active production model from registry (fallback to `LLM_MODEL` env var) |

### Promotion Gates

| Transition | Gate |
|---|---|
| `dev → staging` | Always allowed (reason required) |
| `staging → production` | **Eval gate:** score ≥ configurable threshold (default 0.85 in `tenants.settings.model_registry.promotion_threshold`) |
| `production → deprecated` | Always allowed (audit trail) |

### Acceptance Criteria

- [ ] Model versions registered with provider, name, version, config
- [ ] Promotion workflow: `staging → production` requires eval score ≥ threshold
- [ ] Audit trail in both `audit_events` and `model_promotion_log`
- [ ] CI script exits non-zero when eval score below threshold
- [ ] Active production model resolvable per tenant per provider
- [ ] Backward compatible: falls back to `LLM_MODEL` env var when registry is empty

---

## Task 42 — Vault Wiring

**Priority:** P0 | **Effort:** 1 week | **Component:** replace placeholder, PostgreSQL dynamic secrets, smoke-gate check

### Current State

- `k8s/external-secrets/vault-integration.yml` has `https://vault.example.com:8200` placeholder.
- ExternalSecrets defined for: `openai-api-key`, `neo4j-credentials`, `jwt-signing-secret`, `postgres-password`.
- Missing: `API_KEY_HMAC_SECRET`, `ANTHROPIC_API_KEY`.
- No dynamic secret support (PostgreSQL creds are static).
- No startup Vault connectivity check.

### Files to Create

| File | Purpose |
|---|---|
| `k8s/external-secrets/vault-database-dynamic.yml` | Vault Database Secrets Engine config for PostgreSQL dynamic creds (1h TTL, auto-renew) |
| `shared/identity/vault_check.py` | `check_vault_health(vault_addr)`, `verify_secret_access(vault_addr, paths)` — async HTTP calls to Vault API |
| `scripts/smoke/vault_smoke.py` | Standalone smoke test: Vault reachable? All required secrets accessible? PostgreSQL dynamic cred generation works? |
| `scripts/vault-dev-init.sh` | Pre-seed Vault dev container with test secrets for local development |

### Files to Modify

| File | Change |
|---|---|
| `k8s/external-secrets/vault-integration.yml` | Replace `vault.example.com` with ConfigMap reference `$(VAULT_ADDR)`. Add `API_KEY_HMAC_SECRET` ExternalSecret. Add `ANTHROPIC_API_KEY` ExternalSecret |
| `k8s/configmap-global.yml` | Add `VAULT_ADDR` entry (defaults to `https://vault.value-fabric.svc:8200`) |
| `layer4-agents/src/api/main.py` | In `lifespan()`: call `check_vault_health()` in production mode; hard-fail if unreachable |
| `value-fabric/docker-compose.yml` | Add optional Vault dev container (`vault:latest -dev`), mount init script |
| `k8s/secrets.yml` | Add warning labels clarifying dev-only status |
| `docs/secrets-management.md` | Add dynamic secrets section, smoke gate instructions |
| `value-fabric/.env.example` | Add `VAULT_ADDR`, `API_KEY_HMAC_SECRET` placeholders |

### Dynamic PostgreSQL Credentials

```yaml
# vault-database-dynamic.yml (ExternalSecret with GeneratorRef)
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: postgres-dynamic-secret
  data:
    - secretKey: username
      remoteRef:
        key: database/creds/value-fabric-role
        property: username
    - secretKey: password
      remoteRef:
        key: database/creds/value-fabric-role
        property: password
```

### Startup Smoke Gate

```python
# In layer4-agents/src/api/main.py lifespan():
if os.getenv("ENVIRONMENT", "development") == "production":
    vault_addr = os.getenv("VAULT_ADDR")
    if vault_addr:
        ok = await check_vault_health(vault_addr)
        if not ok:
            raise RuntimeError("Vault unreachable — cannot start in production without secrets backend")
```

### Acceptance Criteria

- [ ] All `vault.example.com` placeholders replaced with configurable `VAULT_ADDR`
- [ ] `API_KEY_HMAC_SECRET` has corresponding ExternalSecret manifest
- [ ] PostgreSQL dynamic credentials via Vault Database Secrets Engine (1h TTL)
- [ ] Startup smoke gate hard-fails in production if Vault is unreachable
- [ ] `scripts/smoke/vault_smoke.py` validates secret access (exit 0/1 for CI)
- [ ] Docker Compose includes optional Vault dev container for local testing

---

## Task 43 — Incident Runbooks

**Priority:** P0 | **Effort:** 3 days | **Component:** runbook_url annotations on every alert rule

### Current State

- 11 alert rules in `monitoring/alerting/rules.yml` — none have `runbook_url` annotations.
- No runbook documents in `docs/`.
- Annotations only contain `summary` and `description`.

### Files to Create

Each runbook follows a consistent template:

```markdown
# {Alert Name} Runbook
## Severity: {critical|warning}
## Alert Condition
{PromQL expression and plain-English explanation}
## Impact
{What breaks when this fires}
## Triage Steps
1. {Check X}
2. {Check Y}
## Resolution
### Quick Fix
### Root Cause Analysis
## Escalation
{When to page on-call, who to contact}
## Prevention
{Long-term fixes}
```

| File | Alert |
|---|---|
| `docs/runbooks/README.md` | Index page linking all runbooks |
| `docs/runbooks/high-error-rate.md` | HighErrorRate — triage 5xx errors, check logs, rollback |
| `docs/runbooks/disk-space-low.md` | DiskSpaceLow — identify large files, clean logs/temp, expand PVC |
| `docs/runbooks/disk-space-critical.md` | DiskSpaceCritical — emergency cleanup, PVC resize, node eviction |
| `docs/runbooks/disk-inode-exhaustion.md` | DiskInodeExhaustion — find inode hogs, clean small files |
| `docs/runbooks/slow-queries.md` | SlowQueries — identify slow queries, check indexes, connection pool |
| `docs/runbooks/neo4j-down.md` | Neo4jDown — check pod, restart, data recovery |
| `docs/runbooks/postgres-down.md` | PostgresDown — check pod, connection limits, failover |
| `docs/runbooks/redis-down.md` | RedisDown — check pod, memory limits, sentinel |
| `docs/runbooks/workflow-stalled.md` | WorkflowStalled — identify stuck workflow, check agent logs, force cancel |
| `docs/runbooks/high-memory-usage.md` | HighMemoryUsage — identify leaks, restart pods, adjust limits |
| `docs/runbooks/high-cpu-usage.md` | HighCPUUsage — identify CPU hogs, check event loops, scale |

### Files to Modify

| File | Change |
|---|---|
| `monitoring/alerting/rules.yml` | Add `runbook_url` annotation to all 11 rules: `runbook_url: "https://github.com/bmsull560/Fabric_4L/blob/main/docs/runbooks/{name}.md"` |

### Acceptance Criteria

- [ ] Every alert rule in `rules.yml` has a `runbook_url` annotation
- [ ] Every referenced runbook file exists in `docs/runbooks/`
- [ ] Runbooks follow consistent template (Severity, Triage, Resolution, Escalation, Prevention)
- [ ] `docs/runbooks/README.md` index page exists

---

## Task 44 — Alertmanager Config + Slack Notifications

**Priority:** P1 | **Effort:** 1 week | **Component:** Alertmanager config, formula-approval Slack channel

### Current State

- `prometheus.yml` references `alertmanager:9093` but no Alertmanager config exists.
- No Alertmanager container in docker-compose.
- `layer4-agents/src/services/formula_governance_service.py` has formula approval logic — no notification hooks.

### Files to Create

| File | Purpose |
|---|---|
| `monitoring/alertmanager/alertmanager.yml` | Alertmanager config: global settings, route tree, Slack receivers, inhibition rules |
| `monitoring/alertmanager/templates/slack.tmpl` | Rich Slack message templates with severity badges, runbook links, silence links |
| `k8s/alertmanager.yml` | Kubernetes Deployment + Service + ConfigMap |
| `docs/runbooks/formula-approval.md` | How to review and approve/reject formulas |

### Files to Modify

| File | Change |
|---|---|
| `monitoring/alerting/rules.yml` | Add `FormulaApprovalRequired` alert rule (new gauge from L4) |
| `layer4-agents/src/metrics/prometheus_metrics.py` | Add `layer4_formula_approval_pending` gauge with `tenant_id` label |
| `layer4-agents/src/services/formula_governance_service.py` | Increment/decrement pending gauge on approval queue changes |
| `value-fabric/docker-compose.yml` | Add Alertmanager service |
| `monitoring/prometheus/prometheus.yml` | Verify Alertmanager target (already present) |

### Alertmanager Route Tree

```yaml
route:
  receiver: 'slack-default'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'slack-critical'
      repeat_interval: 1h
    - match:
        alertname: FormulaApprovalRequired
      receiver: 'slack-formula-approval'
      repeat_interval: 30m

receivers:
  - name: 'slack-default'
    slack_configs:
      - channel: '#vf-alerts'
        send_resolved: true
  - name: 'slack-critical'
    slack_configs:
      - channel: '#vf-alerts-critical'
        send_resolved: true
  - name: 'slack-formula-approval'
    slack_configs:
      - channel: '#vf-formula-approvals'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
```

### Acceptance Criteria

- [ ] `monitoring/alertmanager/alertmanager.yml` exists with Slack routing
- [ ] Critical alerts route to `#vf-alerts-critical`
- [ ] Formula-approval events generate Slack notification in `#vf-formula-approvals`
- [ ] Rich Slack templates with severity badges, descriptions, runbook links
- [ ] Alertmanager deployed via Docker Compose and K8s manifests
- [ ] Config passes `amtool check-config` validation

---

## Task 45 — Feature Flags

**Priority:** P1 | **Effort:** 1 week | **Component:** per-tenant, rollout %, is_enabled() helper, audited

### Current State

- `Tenant.settings` JSONB exists — could store flags informally, but no formal system.
- No `is_enabled()` helper, no rollout percentages, no flag management API.
- `AuditEmitter` infrastructure is ready for flag change auditing.

### Files to Create

| File | Purpose |
|---|---|
| `layer4-agents/migrations/versions/006_add_feature_flags.py` | Table `feature_flags`: id (UUID), tenant_id (FK nullable — NULL = platform-wide), flag_key (str), enabled (bool), rollout_percentage (int 0–100), description (text), metadata (JSONB), created_at, updated_at, updated_by (FK→users). Unique constraint: `(tenant_id, flag_key)` |
| `shared/identity/feature_flags.py` | `is_enabled(flag_key, tenant_id, user_id=None)` — lookup order: tenant-specific → platform-wide → False. Deterministic rollout bucketing via `hash(tenant_id:user_id:flag_key) % 100`. Redis-cached (30s TTL via `tenant_cache_key()`) |
| `layer4-agents/src/feature_flags/` | Package: `__init__.py`, `models.py` (ORM), `service.py` (CRUD + audit) |
| `layer4-agents/src/feature_flags/api/routes.py` | `GET /v1/feature-flags` (list), `GET /v1/feature-flags/{key}` (check), `PUT /v1/feature-flags/{key}` (create/update), `DELETE /v1/feature-flags/{key}` (remove), `GET /v1/feature-flags/{key}/evaluate` (evaluate for current user) |
| `layer4-agents/tests/test_feature_flags.py` | CRUD, rollout bucketing, tenant isolation, cache invalidation, audit logging |

### Files to Modify

| File | Change |
|---|---|
| `shared/identity/__init__.py` | Export `is_enabled` |
| `shared/audit/models.py` | Add `FEATURE_FLAG_CREATED`, `FEATURE_FLAG_UPDATED`, `FEATURE_FLAG_DELETED` |
| `layer4-agents/src/api/main.py` | Register feature flags router |

### Rollout Bucketing

```python
import hashlib

def _in_rollout(flag_key: str, tenant_id: UUID, user_id: str | None, pct: int) -> bool:
    """Deterministic: same user always gets same result for same flag."""
    seed = f"{tenant_id}:{user_id or 'anon'}:{flag_key}"
    bucket = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % 100
    return bucket < pct
```

### Acceptance Criteria

- [ ] Feature flags stored per-tenant in PostgreSQL with rollout percentage
- [ ] `is_enabled(flag_key, tenant_id)` helper available from `shared.identity`
- [ ] Deterministic rollout bucketing (same user → same result)
- [ ] CRUD API for managing flags (tenant_admin+)
- [ ] Every flag change audited via `AuditEmitter`
- [ ] Redis-cached with 30s TTL for read performance
- [ ] Platform-wide flags (tenant_id=NULL) supported

---

## Task 46 — Per-Tenant Rate Limiting

**Priority:** P1 | **Effort:** 1 week | **Component:** TENANT scope, wired into GovernanceMiddleware, L1/L4

### Current State

- `APIKey.rate_limit_per_minute` field exists in DB model — **not enforced**.
- `GovernanceMiddleware` resolves identity but does not enforce rate limits.
- `Tenant.settings` JSONB can store rate limit config.
- Redis available in both L1 and L4 for token bucket state.

### Files to Create

| File | Purpose |
|---|---|
| `shared/identity/rate_limiting.py` | Pydantic `RateLimitConfig` model (requests_per_minute, requests_per_hour, burst_size, scope=TENANT\|USER\|API_KEY). Default configs per role |
| `shared/identity/rate_limiter.py` | `RedisRateLimiter` class: Redis sorted-set sliding window (ZADD+ZREMRANGEBYSCORE+ZCARD via Lua script). Returns `RateLimitResult(allowed, remaining, reset_at, retry_after)`. Graceful degradation if Redis unavailable |

### Files to Modify

| File | Change |
|---|---|
| `shared/identity/middleware.py` | After identity resolution, before `call_next`: resolve rate limit config (per-key → tenant settings → role defaults) → `rate_limiter.check_rate_limit()` → if denied, return HTTP 429 with `Retry-After` header. Always add `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` response headers. Constructor accepts optional `rate_limiter: RedisRateLimiter` |
| `layer4-agents/src/api/main.py` | Create `RedisRateLimiter` in `lifespan()`, pass to `GovernanceMiddleware` |
| `layer1-ingestion/src/api/main.py` | Same: create and pass `RedisRateLimiter` to `GovernanceMiddleware` |
| `shared/identity/__init__.py` | Export `RedisRateLimiter`, `RateLimitConfig` |
| `layer4-agents/src/metrics/prometheus_metrics.py` | Add `layer4_rate_limit_hits_total{tenant_id, scope}` counter |

### Rate Limit Resolution Order

```
1. Per-key override (APIKey.rate_limit_per_minute)    — if set
2. Tenant settings (tenants.settings.rate_limits)      — if configured
3. Role defaults:
     read_only:     30 rpm
     analyst:       60 rpm
     content_admin: 120 rpm
     tenant_admin:  300 rpm
     super_admin:   unlimited
     system:        unlimited
```

### Redis Sliding Window (Lua Script)

```lua
-- Atomic: remove expired, add current, count
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)

if count < limit then
    redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))
    redis.call('EXPIRE', key, window)
    return {1, limit - count - 1}  -- allowed, remaining
else
    return {0, 0}  -- denied
end
```

### Acceptance Criteria

- [ ] Per-tenant rate limiting enforced in `GovernanceMiddleware` (TENANT scope)
- [ ] Redis sliding window via Lua script (atomic)
- [ ] Per-key `rate_limit_per_minute` override respected
- [ ] Tenant-level config via `tenants.settings.rate_limits`
- [ ] HTTP 429 with `Retry-After` header on exceeded limit
- [ ] `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` on every response
- [ ] Graceful degradation when Redis unavailable (allow + log warning)
- [ ] Wired into both L1 and L4
- [ ] `super_admin` and `system` roles exempt

---

## Task 47 — LLM Cost Prometheus Metrics

**Priority:** P1 | **Effort:** 2 days | **Component:** `vf_llm_cost_usd_total{provider,model,tenant_id}`

### Current State

- L4 has `layer4_agent_calls_total{agent_type, status}` — no cost or token tracking.
- No token counting or cost calculation exists anywhere.
- L2 also makes LLM calls for extraction (separate integration point).

### Files to Create

| File | Purpose |
|---|---|
| `layer4-agents/src/metrics/llm_cost_calculator.py` | `LLMCostCalculator` class with configurable cost-per-1K-tokens table. Default pricing for gpt-4o, gpt-4o-mini, claude-3-opus, claude-3-sonnet, etc. Override via `LLM_COST_TABLE_PATH` env var pointing to JSON |
| `monitoring/grafana/dashboards/llm-costs.json` | Grafana dashboard: total cost over time, cost by provider, cost by model, cost by tenant, token usage, cost rate ($/hr) |
| `docs/runbooks/high-llm-cost.md` | Runbook for HighLLMCostRate alert |
| `layer4-agents/tests/test_llm_cost_metrics.py` | Cost calculation correctness, metric emission, unknown model fallback |

### Files to Modify

| File | Change |
|---|---|
| `layer4-agents/src/metrics/prometheus_metrics.py` | Add: `vf_llm_cost_usd_total` (Counter, labels: provider, model, tenant_id), `vf_llm_tokens_total` (Counter, labels: provider, model, tenant_id, token_type=prompt\|completion), `vf_llm_requests_total` (Counter, labels: provider, model, tenant_id, status). Add `record_llm_cost()` helper method |
| `layer4-agents/src/engine/executor.py` | After LLM API response: extract token usage from response, call `metrics.record_llm_cost(provider, model, tenant_id, cost, prompt_tokens, completion_tokens)` |
| `monitoring/alerting/rules.yml` | Add `HighLLMCostRate` alert: `sum(rate(vf_llm_cost_usd_total[1h])) > 50` for 15m (warning). Add `runbook_url` annotation |

### Cost Table (Default Pricing)

```python
COST_PER_1K_TOKENS = {
    ("openai", "gpt-4o"):           {"prompt": 0.005,   "completion": 0.015},
    ("openai", "gpt-4o-mini"):      {"prompt": 0.00015, "completion": 0.0006},
    ("anthropic", "claude-3-opus"):  {"prompt": 0.015,   "completion": 0.075},
    ("anthropic", "claude-3-sonnet"):{"prompt": 0.003,   "completion": 0.015},
    ("anthropic", "claude-3-haiku"): {"prompt": 0.00025, "completion": 0.00125},
}
```

### Acceptance Criteria

- [ ] `vf_llm_cost_usd_total{provider, model, tenant_id}` counter emitted on every LLM call
- [ ] `vf_llm_tokens_total{provider, model, tenant_id, token_type}` tracks prompt/completion tokens
- [ ] Cost calculator with configurable per-model pricing
- [ ] Grafana dashboard for LLM cost visualization
- [ ] `HighLLMCostRate` alert rule with runbook
- [ ] Tests verify cost calculation and metric emission

---

## Task 48 — SDK / CLI

**Priority:** P1 | **Effort:** 2 weeks | **Component:** generated from OpenAPI spec, `vf` CLI via typer, published to GitHub Packages

### Current State

- `scripts/export_openapi.py` generates L3/L5/L6 OpenAPI specs.
- `contracts/` has tool manifests and JSON schemas.
- No SDK, no CLI, no package publishing.

### Files to Create

| File | Purpose |
|---|---|
| **SDK Package** | |
| `sdk/python/pyproject.toml` | Package: `valuefabric-sdk`, deps: httpx, pydantic, typer, rich |
| `sdk/python/src/valuefabric/__init__.py` | Package root |
| `sdk/python/src/valuefabric/client.py` | `ValueFabricClient(base_url, api_key=None)` — sync + async methods for all endpoints |
| `sdk/python/src/valuefabric/auth.py` | API key auth, JWT token management |
| `sdk/python/src/valuefabric/models.py` | Generated Pydantic models from OpenAPI spec |
| **CLI** | |
| `sdk/python/src/valuefabric/cli/__init__.py` | Package root |
| `sdk/python/src/valuefabric/cli/main.py` | Typer app entry: `vf --help` |
| `sdk/python/src/valuefabric/cli/config.py` | Config management: `~/.config/valuefabric/config.toml` (base_url, api_key, profiles) |
| `sdk/python/src/valuefabric/cli/tenants.py` | `vf tenants list`, `vf tenants get <id>` |
| `sdk/python/src/valuefabric/cli/users.py` | `vf users list`, `vf users invite` |
| `sdk/python/src/valuefabric/cli/api_keys.py` | `vf api-keys create`, `vf api-keys list` |
| `sdk/python/src/valuefabric/cli/workflows.py` | `vf workflows list`, `vf workflows execute` |
| `sdk/python/src/valuefabric/cli/models.py` | `vf models list`, `vf models promote` |
| `sdk/python/src/valuefabric/cli/flags.py` | `vf feature-flags list`, `vf feature-flags set` |
| `sdk/python/src/valuefabric/cli/health.py` | `vf health` |
| **Tests** | |
| `sdk/python/tests/test_client.py` | HTTP client tests with mocked responses |
| `sdk/python/tests/test_cli.py` | Typer CliRunner tests |
| **Publishing** | |
| `.github/workflows/publish-sdk.yml` | Build + publish to GitHub Packages on `sdk/v*` tag |
| **Generation** | |
| `scripts/generate_sdk.py` | Export OpenAPI → generate client → apply patches |
| **Docs** | |
| `sdk/python/README.md` | Installation, quick start, authentication, examples |

### Files to Modify

| File | Change |
|---|---|
| `scripts/export_openapi.py` | Add L4 OpenAPI export (currently missing) → `contracts/openapi/layer4-agents.json` |
| `Makefile` | Add `sdk` target (depends on `contracts`) |
| `README.md` | Add SDK installation section |

### CLI Commands

```
vf config set-url https://api.valuefabric.example.com
vf config set-api-key vf_abc123...
vf config use-profile staging

vf tenants list [--status active]
vf tenants get <id>
vf users list [--tenant <id>]
vf users invite --email user@example.com --role analyst
vf api-keys create --name "Script Key" --role analyst
vf workflows list
vf workflows execute <workflow_id> --input '{"query": "..."}'
vf models list [--stage production]
vf models promote <id> --to production --reason "Passed eval"
vf feature-flags list
vf feature-flags set enable_oidc --enabled --rollout 50
vf health [--json]
```

### Acceptance Criteria

- [ ] Python SDK generated from OpenAPI spec with typed client
- [ ] `vf` CLI via typer with commands for all major resources
- [ ] Config management (`~/.config/valuefabric/config.toml`) with profile support
- [ ] Rich table output + `--json` flag
- [ ] GitHub Actions workflow publishes to GitHub Packages on tag push
- [ ] SDK installable via `pip install valuefabric-sdk --index-url https://pypi.pkg.github.com/...`
- [ ] Tests with mocked backends

---

## Execution Order & Dependencies

```
                    ┌── Task 42 (Vault) ──────────────────────────┐
                    │                                              │
Track A (Ops):      │   Task 43 (Runbooks) ──→ Task 44 (AM)      │
                    │                                              │
                    ├── Task 40 (OIDC) ──┐                        │
Track B (Auth):     │                     ├──→ Task 48 (SDK)     │
                    │   Task 41 (Registry)┘                       │
                    │                                              │
Track C (Govern):   │   Task 45 (Flags) ──→ Task 46 (Rate Lim)  │
                    │                    ──→ Task 47 (LLM Cost)  │
                    └──────────────────────────────────────────────┘
```

**Recommended parallel tracks:**

| Track | Tasks | Duration | Notes |
|---|---|---|---|
| **A (Ops)** | 42 → 43 → 44 | ~2.5 weeks | 42 is standalone; 43 provides runbook URLs for 44 |
| **B (Auth/API)** | 40 → 41 → 48 | ~7 weeks | 48 must be last (generates from final API surface) |
| **C (Governance)** | 45 → 46 → 47 | ~2.5 weeks | 45 and 46 both touch middleware, sequence them |

**Key dependency:** Task 48 (SDK) should run last since it generates from the complete API surface including endpoints from Tasks 40, 41, 45, and 46.

---

## Migration Numbering Plan

| Migration | Task | Tables |
|---|---|---|
| 004 | Task 40 (OIDC) | `oidc_sessions` |
| 005 | Task 41 (Model Registry) | `model_versions`, `model_promotion_log` |
| 006 | Task 45 (Feature Flags) | `feature_flags` |

Alternative: batch 004/005/006 into a single migration if tasks are implemented simultaneously.

---

## New Permissions Summary

All new permissions should be added in a single commit to `shared/identity/permissions.py`:

```python
# Task 41 — Model Registry
READ_MODELS = "read:models"
WRITE_MODELS = "write:models"
ADMIN_MODELS = "admin:models"

# Task 45 — Feature Flags (uses existing ADMIN_SYSTEM for management)
# No new permissions — tenant_admin can manage flags via ADMIN_TENANTS
```

**ROLE_PERMISSIONS updates:**

| Role | New Permissions |
|---|---|
| `analyst` | `read:models` |
| `content_admin` | `read:models`, `write:models` |
| `tenant_admin` | `read:models`, `write:models`, `admin:models` |
| `super_admin` | All (automatic via `frozenset(p for p in Permission)`) |
| `system` | All (automatic) |

---

## New Audit Actions Summary

Add to `shared/audit/models.py`:

```python
# Task 40 — OIDC
OIDC_LOGIN = "oidc.login"
OIDC_LOGIN_FAILED = "oidc.login_failed"

# Task 41 — Model Registry
MODEL_REGISTERED = "model.registered"
MODEL_PROMOTED = "model.promoted"
MODEL_DEPRECATED = "model.deprecated"

# Task 45 — Feature Flags
FEATURE_FLAG_CREATED = "feature_flag.created"
FEATURE_FLAG_UPDATED = "feature_flag.updated"
FEATURE_FLAG_DELETED = "feature_flag.deleted"
```
