# Production Launch Sprint Plan

**Date:** 2026-04-13
**Assessed by:** Architecture review of full repository
**Baseline:** LAUNCH_READINESS_REPORT.md (2026-04-11, claimed ~75%)

---

## Launch Readiness Assessment

**Current readiness: ~68%** (revised down from 75% after stricter production criteria)

### Top 5 Risks Blocking Launch

| # | Risk | Severity | Location |
|---|------|----------|----------|
| 1 | **No database-level tenant isolation** — app-only filtering via `TenantScopedMixin.scoped_query()`. One missed filter = full data leak | P0 | `shared/identity/isolation.py`, all L4 route handlers |
| 2 | **Unbounded in-memory state** — `StateManager._memory_store` and `TaskScheduler._task_history` grow without bound → OOM under load | P0 | `layer4-agents/src/engine/state_manager.py:39`, `scheduler.py:120` |
| 3 | **Zero security scanning in CI** — No SAST, no dependency audit, no container scan | P0 | `.github/workflows/pr-checks.yml`, `build-deploy.yml` |
| 4 | **No startup env validation on L4** — Missing/weak `JWT_SECRET` or `API_KEY_HMAC_SECRET` → silent auth failure | P1 | `layer4-agents/src/` (no settings.py) |
| 5 | **No production alerting** — Alertmanager config is a stub, no routes, no webhook integration | P1 | `monitoring/alertmanager/alertmanager.yml` |

### Critical Missing Capabilities

- PostgreSQL RLS policies (defense-in-depth)
- Request correlation IDs / distributed tracing (OpenTelemetry)
- Idempotency keys for workflow creation
- Circuit breaker for cross-layer HTTP calls
- Dead letter queue for failed tasks
- Container image scanning (Trivy/Grype)
- K8s NetworkPolicy, Pod Security Standards, HPA
- Rate limit response headers (`X-RateLimit-*`)
- Production error sanitization (stack traces leak to clients)
- Secrets rotation mechanism

---

## What Works Well

These are solid and require no rework:

- **Architecture**: Clean 6-layer separation, independent deployability, unified `GovernanceMiddleware`
- **Auth/RBAC**: JWT + API key + RBAC with 6 roles / 24 permissions, HMAC-SHA256 key hashing
- **Audit trail**: Append-only `audit_events` with DB trigger enforcing immutability
- **Database schema**: UUID PKs, timezone-aware timestamps, JSONB metadata, proper FKs/indexes
- **CI/CD**: Matrix builds, 80% coverage gate, K8s manifest validation, OIDC auth (no long-lived creds)
- **Monitoring foundations**: Prometheus scrape configs for all 6 layers, Grafana dashboard provisioned
- **Testing**: 52 backend test files, 326 frontend tests, testcontainers/respx/factory-boy

---

## Sprint 1 — Tenant Isolation & Data Safety (Weeks 1–2)

### Goal
Zero possibility of cross-tenant data leakage. Defense-in-depth at database level. Fix memory safety. Fail-fast on misconfiguration.

### Tasks

- [ ] **Alembic migration 007**: Add PostgreSQL RLS to `accounts`, `users`, `api_keys`, `audit_events`
  ```sql
  ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
  CREATE POLICY tenant_isolation ON accounts
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
  ```
- [ ] Hook `SET LOCAL app.tenant_id` into `get_db()` session dependency from `RequestContext`
- [ ] Audit all L4 route handlers — verify every query uses `scoped_query(ctx.tenant_id)` or is explicitly a system route
- [ ] Bound `StateManager._memory_store`: add LRU eviction, default 10K entries
- [ ] Bound `NotificationService._event_queue`: add `maxsize` to `asyncio.Queue`
- [ ] Create `layer4-agents/src/config/settings.py` with `pydantic-settings.BaseSettings`:
  - `JWT_SECRET` (min 32 chars), `API_KEY_HMAC_SECRET` (min 32 chars), `DATABASE_URL`, `REDIS_URL`
- [ ] Verify L1/L3/L5 startup validation (already use pydantic-settings — add min-strength checks)
- [ ] Integration test: two-tenant data isolation via API
- [ ] Integration test: RLS blocks raw SQL without session var

### Exit Criteria
- All existing tests pass
- Cross-tenant isolation proven at DB level by new integration tests
- L4 fails fast on missing/weak secrets

---

## Sprint 2 — Security Scanning & Error Hardening (Weeks 3–4)

### Goal
Close security scanning gaps. Prevent information leakage. Add request traceability.

### Tasks

- [ ] Add `bandit -r src/` to `pr-checks.yml` for all Python layers
- [ ] Add `pip-audit` to `pr-checks.yml`
- [ ] Add `trivy image --exit-code 1 --severity HIGH,CRITICAL` to `build-deploy.yml`
- [ ] Add `pnpm audit` to frontend CI
- [ ] Global FastAPI exception handler: return `{"error": "Internal server error", "request_id": "..."}` — no stack traces when `ENVIRONMENT=production`
- [ ] Fix `ErrorBoundary.tsx`: hide stack in prod (`import.meta.env.PROD`)
- [ ] Fix `workflows.py:250`: generic error message, log full error server-side
- [ ] `X-Request-ID` middleware in `GovernanceMiddleware`: generate UUID, propagate via `RequestContext`, include in all responses
- [ ] Add `request_id` to `AuditEvent` model
- [ ] Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- [ ] Fix `client.ts:51-53`: toast "Session expired" before 401 redirect

### Exit Criteria
- Every PR runs SAST + dependency audit; every build runs container scan
- No stack traces in production API responses
- Every request/response has a correlation ID

---

## Sprint 3 — Agent Reliability & Resilience (Weeks 5–6)

### Goal
Production-resilient agent workflows: circuit breakers, dead letter handling, idempotency, timeouts.

### Tasks

- [ ] `CircuitBreaker` class in `shared/`: closed/open/half-open states, configurable thresholds
- [ ] Wrap all cross-layer `httpx` calls (L4 → L2, L3, L5) with circuit breaker
- [ ] Alembic migration 008: `dead_letter_queue` table (`id`, `tenant_id`, `task_type`, `payload` JSONB, `error`, `failed_at`, `retry_count`)
- [ ] `TaskScheduler._handle_retry()`: after max retries → insert into DLQ (not silent drop)
- [ ] Admin endpoints: `GET /v1/admin/dlq`, `POST /v1/admin/dlq/{id}/retry`
- [ ] `Idempotency-Key` header on `POST /v1/workflows`: Redis `SET NX` with 24h TTL
- [ ] Global workflow timeout: configurable `max_execution_time` (default 30min), cancel + audit
- [ ] Add jitter to retry backoff: `delay * 2^retry + random(0, delay)`
- [ ] Explicit timeouts on all `httpx` calls (30s connect, 60s read)
- [ ] Default to `RedisMessageBus` in production (not `InMemoryMessageBus`)

### Exit Criteria
- Circuit breakers open after N failures (tested)
- Failed tasks visible in DLQ (not dropped)
- Duplicate workflow creation returns cached response
- Workflows exceeding timeout are cancelled with audit event

---

## Sprint 4 — Observability & Alerting (Weeks 7–8)

### Goal
Production-grade observability: distributed tracing, actionable alerts, SLI dashboards, incident runbooks.

### Tasks

- [ ] OpenTelemetry instrumentation on L4: `opentelemetry-instrumentation-fastapi`, `-httpx`, OTLP exporter
- [ ] Propagate `traceparent` header in cross-layer calls
- [ ] Jaeger service in `docker-compose.yml`
- [ ] Prometheus alert rules (`monitoring/alerting/rules.yml`):
  - `HighErrorRate` (>5% 5xx / 5min)
  - `HighLatency` (p99 >2s / 5min)
  - `ServiceDown` (health fail >1min)
  - `DLQBacklog` (>10 items)
  - `RateLimitExhausted` (>100 rejections/min/tenant)
- [ ] Alertmanager routing: critical → PagerDuty, warning → Slack
- [ ] Grafana SLI dashboard: request rate, error rate, p50/p95/p99 latency, availability — per layer
- [ ] Standardize `structlog` JSON logging with `trace_id`, `span_id`, `tenant_id`, `request_id`
- [ ] `LOG_LEVEL` env var on all layers
- [ ] `docs/runbooks/`: incident response playbook (triage, escalation, rollback, common failures)

### Exit Criteria
- Cross-layer requests traceable by single trace ID
- 5+ alert rules firing correctly
- Grafana SLI dashboard showing live data
- All services emit structured JSON logs with trace context

---

## Sprint 5 — Kubernetes Production Hardening (Weeks 9–10)

### Goal
Production-safe K8s deployment: network segmentation, pod security, autoscaling, secrets management.

### Tasks

- [ ] NetworkPolicy per layer (deny-all default, explicit allow):
  - L4 → {Postgres, Redis, Neo4j, L2, L3, L5}
  - Frontend → {L4 only}
- [ ] `securityContext` on all deployments: `runAsNonRoot`, `readOnlyRootFilesystem`, `drop: [ALL]`
- [ ] `USER` directive in all Dockerfiles (non-root)
- [ ] HPA: L4 (CPU >70% → 2–8 replicas), frontend (2–4 replicas)
- [ ] Resource limits (not just requests) on all deployments
- [ ] PodDisruptionBudget: L4 `minAvailable: 1`
- [ ] External-secrets operator manifests → Vault for `JWT_SECRET`, `API_KEY_HMAC_SECRET`, `DATABASE_URL`, `OPENAI_API_KEY`
- [ ] `preStop` lifecycle hooks (sleep 5s for LB drain), `terminationGracePeriodSeconds: 30`
- [ ] Ingress with TLS (cert-manager / Let's Encrypt)
- [ ] Pin image tags to SHA in prod overlay
- [ ] Liveness/readiness probes on all deployments

### Exit Criteria
- NetworkPolicy enforced for all pods
- No pod runs as root
- HPA scales under load
- All secrets from Vault via external-secrets
- Zero-downtime rolling updates verified

---

## Sprint 6 — Launch Validation (Weeks 11–12)

### Goal
Full E2E validation, load test, security review, launch sign-off.

### Tasks

- [ ] E2E tests for critical flows:
  - Tenant signup → API key → first workflow → results
  - Two-tenant concurrent workflows (no data leakage)
  - OIDC login → session → logout
  - Workflow create → run → checkpoint → resume → complete
  - Formula create → approve → publish → use in workflow
- [ ] Load test (k6/Locust): 100 concurrent users, 50 req/s, 10 min sustained
  - Target: <200ms p95 reads, <2s p95 workflow creation
- [ ] Security checklist:
  - OWASP Top 10 against all endpoints
  - No sensitive data in error responses
  - CORS correctly scoped
  - Rate limiting prevents abuse
  - Audit log captures all admin actions
  - API key rotation works E2E
- [ ] `.dockerignore` for all layers
- [ ] Switch `pip install -e "."` → `pip install "."` in prod Dockerfiles
- [ ] Production launch checklist: alerts working, dashboards live, backups tested, secrets rotated, DNS/TLS configured, on-call rotation set, rollback tested
- [ ] `make verify && make evals` on release candidate
- [ ] Tag `v1.0.0-rc1`

### Exit Criteria
- All E2E tests pass in staging
- Load test meets latency targets
- Security checklist fully passed
- 24h soak test with zero errors
- Sign-off from engineering, security, product

---

## Timeline Summary

| Sprint | Weeks | Focus | Key Outcome |
|--------|-------|-------|-------------|
| 1 | 1–2 | Tenant Isolation & Data Safety | DB-level RLS, memory bounds, env validation |
| 2 | 3–4 | Security Scanning & Error Hardening | SAST/container scan in CI, no info leakage |
| 3 | 5–6 | Agent Reliability & Resilience | Circuit breakers, DLQ, idempotency, timeouts |
| 4 | 7–8 | Observability & Alerting | OTel tracing, alert rules, SLI dashboards |
| 5 | 9–10 | K8s Production Hardening | NetworkPolicy, pod security, HPA, secrets |
| 6 | 11–12 | Launch Validation | E2E, load test, security review, sign-off |

**Critical path:** 1 → 2 → 3 → 4 → 5 → 6 (sequential)
**Parallelism opportunity:** Sprints 4 + 5 can run concurrently with separate teams (observability + infra)
