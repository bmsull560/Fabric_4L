# Harness Service Runbook

Operational reference for the Fabric Harness — the governed execution spine of Layer 4.

**Service:** `layer4-agents` · **Port:** 8004 · **Base path:** `/v1/harness`

---

## Table of Contents

1. [Service Overview](#1-service-overview)
2. [Environment Variables](#2-environment-variables)
3. [Deployment](#3-deployment)
4. [Health Checks](#4-health-checks)
5. [Monitoring and Alerts](#5-monitoring-and-alerts)
6. [Common Operations](#6-common-operations)
7. [Troubleshooting](#7-troubleshooting)
8. [Incident Response](#8-incident-response)
9. [Database Maintenance](#9-database-maintenance)
10. [Security Checklist](#10-security-checklist)

---

## 1. Service Overview

The Harness governs every agentic workflow run in Layer 4. It enforces:

- **State machine** — deterministic transitions through `INIT → RESOLVE_CONTEXT → … → DONE`
- **Checkpoints** — durable snapshots at each state boundary for resume-on-failure
- **Human gates** — approval/rejection barriers before `PUBLISH_OUTPUT`
- **Tool contracts** — per-workflow-type allow/deny lists with budget enforcement
- **Claim validation** — async validation via Layer 5 Ground Truth (`LiveL5Validator`)
- **Tenant isolation** — every read and write is scoped by `tenant_id`

The harness does **not** replace LangGraph workflows. It wraps them, providing governance, auditability, and recovery.

### State Machine (happy path)

```
INIT → RESOLVE_CONTEXT → LOAD_VALUE_PACK → RETRIEVE_KNOWLEDGE
     → GENERATE_HYPOTHESES → MATCH_EVIDENCE → QUANTIFY_IMPACT
     → VALIDATE_CLAIMS → HUMAN_REVIEW → PUBLISH_OUTPUT → DONE
```

Terminal states: `DONE`, `FAILED`, `CANCELLED`

---

## 2. Environment Variables

### Required

| Variable | Description |
|---|---|
| `LAYER4_DATABASE_URL` | PostgreSQL connection (asyncpg). Harness tables live here. |
| `JWT_SECRET` | HS256 secret for JWT validation |
| `API_KEY_HMAC_SECRET` | HMAC key for API key hashing |

### Harness-specific

| Variable | Default | Description |
|---|---|---|
| `HARNESS_REGISTRY_BACKEND` | `sql` | `sql` for production, `memory` for tests |
| `HARNESS_L5_VALIDATION_ENABLED` | `true` | Enable `LiveL5Validator`. Set `false` to use `NoOpValidator`. |
| `LAYER5_API_URL` | — | Required when `HARNESS_L5_VALIDATION_ENABLED=true` |
| `HARNESS_MAX_CONCURRENT_RUNS` | `50` | Per-tenant concurrent run cap |
| `HARNESS_RUN_TIMEOUT_SECONDS` | `3600` | Hard timeout per run (1 hour) |
| `HARNESS_GATE_EXPIRY_HOURS` | `72` | Hours before a pending gate auto-expires |
| `HARNESS_CHECKPOINT_RETENTION_DAYS` | `30` | Days to retain checkpoint data |
| `HARNESS_METRICS_PREFIX` | `harness` | Prometheus metric name prefix |
| `HARNESS_TRACE_SAMPLING_RATE` | `0.1` | Fraction of runs included in distributed traces |

### Inherited from Layer 4

| Variable | Default | Description |
|---|---|---|
| `CHECKPOINT_DATABASE_URL` | `LAYER4_DATABASE_URL` | Dedicated checkpoint DB (recommended at scale) |
| `REDIS_URL` | `redis://localhost:6379` | Queue backend |
| `SERVICE_MESH_MTLS_ENABLED` | — | Set `true` when mesh mTLS terminates HTTPS |

---

## 3. Deployment

### Kubernetes

The harness runs inside the `layer4-agents` pod. No separate deployment is required.

```bash
# Verify the pod is running
kubectl get pods -n value-fabric -l app=layer4-agents

# Check harness-specific logs
kubectl logs -n value-fabric -l app=layer4-agents --tail=100 | grep '"component":"harness"'
```

### Database migrations

Harness tables are managed by the Layer 4 Alembic setup. Run migrations before deploying a new image:

```bash
cd services/layer4-agents
alembic upgrade head
```

Harness tables:
- `harness_runs`
- `harness_checkpoints`
- `harness_gates`
- `harness_tool_contracts`
- `harness_trace_events`

### Configuration files

| File | Purpose |
|---|---|
| `config/harness.runtime.yaml` | Per-workflow-type tool budgets, invariants, validation, checkpointing |
| `config/harness.service.yaml` | Service-level env vars, feature flags, observability, security |

Both files are mounted as ConfigMaps. Changes require a pod restart.

---

## 4. Health Checks

### Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /v1/harness/health` | Harness component health (database + L5 reachability) |
| `GET /healthz` | Layer 4 liveness probe |
| `GET /ready` | Layer 4 readiness probe (includes harness database check) |

### Interpreting `/v1/harness/health`

```json
{
  "status": "healthy",
  "registry_backend": "sql",
  "l5_validation_enabled": true,
  "l5_reachable": true,
  "active_runs": 12,
  "pending_gates": 3
}
```

| Field | Healthy | Degraded | Action |
|---|---|---|---|
| `status` | `healthy` | `degraded` | See component fields |
| `l5_reachable` | `true` | `false` | L5 is down; validation falls back to `NEEDS_REVIEW` |
| `active_runs` | < 80% of `HARNESS_MAX_CONCURRENT_RUNS` | ≥ 80% | Check for stuck runs |
| `pending_gates` | < 20 | ≥ 20 | Alert human reviewers |

**L5 unavailability is non-fatal.** The harness degrades gracefully: claims that cannot be validated are marked `NEEDS_REVIEW` and routed to `HUMAN_REVIEW` rather than failing the run.

---

## 5. Monitoring and Alerts

### Key Prometheus metrics

All metrics use the prefix defined by `HARNESS_METRICS_PREFIX` (default: `harness`).

| Metric | Type | Description |
|---|---|---|
| `harness_runs_total` | Counter | Runs created, labeled by `workflow_type`, `tenant_id` |
| `harness_runs_completed_total` | Counter | Runs reaching `DONE` |
| `harness_runs_failed_total` | Counter | Runs reaching `FAILED` |
| `harness_run_duration_seconds` | Histogram | Wall time from `INIT` to terminal state |
| `harness_gate_decisions_total` | Counter | Gate decisions, labeled by `decision` (`approved`/`rejected`) |
| `harness_gate_pending_count` | Gauge | Current pending gates across all tenants |
| `harness_validation_outcomes_total` | Counter | Validation results, labeled by `outcome` |
| `harness_l5_request_duration_seconds` | Histogram | L5 validation call latency |
| `harness_checkpoint_writes_total` | Counter | Checkpoint writes |
| `harness_tool_budget_exceeded_total` | Counter | Runs stopped by budget enforcement |

### Recommended alerts

```yaml
# Run failure rate > 10% over 5 minutes
- alert: HarnessHighFailureRate
  expr: rate(harness_runs_failed_total[5m]) / rate(harness_runs_total[5m]) > 0.10
  severity: warning

# Pending gates older than 48 hours
- alert: HarnessStaleGates
  expr: harness_gate_pending_count > 0
  for: 48h
  severity: warning

# L5 validation latency p99 > 10s
- alert: HarnessL5SlowValidation
  expr: histogram_quantile(0.99, harness_l5_request_duration_seconds_bucket) > 10
  severity: warning

# Active runs near concurrency cap
- alert: HarnessNearConcurrencyLimit
  expr: harness_active_runs_count / harness_max_concurrent_runs > 0.85
  severity: warning
```

### Log fields

Harness logs are structured JSON. Key fields:

| Field | Description |
|---|---|
| `component` | Always `harness` |
| `run_id` | UUID of the affected run |
| `tenant_id` | Tenant scope |
| `workflow_type` | e.g. `roi_calculator_generation` |
| `from_state` / `to_state` | State transition |
| `gate_id` | Present on gate events |
| `validation_outcome` | Present on validation events |
| `error` | Error message on failures |

---

## 6. Common Operations

### List active runs for a tenant

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.valuefabric.io/v1/harness/runs?status=running&limit=50"
```

### Cancel a stuck run

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "cancel", "reason": "Operator: run stuck in VALIDATE_CLAIMS for >2h"}' \
  "https://api.valuefabric.io/v1/harness/runs/{run_id}/transition"
```

### Approve a pending human gate

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved", "decided_by": "ops@example.com", "notes": "Reviewed and approved"}' \
  "https://api.valuefabric.io/v1/harness/runs/{run_id}/gates/{gate_id}/decide"
```

### Retry a failed run

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "retry", "reason": "Operator: retrying after L5 outage resolved"}' \
  "https://api.valuefabric.io/v1/harness/runs/{run_id}/transition"
```

### Inspect checkpoints for a run

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.valuefabric.io/v1/harness/runs/{run_id}/checkpoints"
```

### Force-validate claims (re-trigger L5)

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"run_id": "{run_id}", "claim_ids": ["claim-1", "claim-2"]}' \
  "https://api.valuefabric.io/v1/harness/runs/{run_id}/validate"
```

---

## 7. Troubleshooting

### Run stuck in a non-terminal state

**Symptoms:** Run has been in `VALIDATE_CLAIMS` or `HUMAN_REVIEW` for an unexpected duration.

**Steps:**
1. Check the run's trace events for the last recorded transition:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     "https://api.valuefabric.io/v1/harness/runs/{run_id}"
   ```
2. Check Layer 4 logs for errors associated with `run_id`.
3. If stuck in `VALIDATE_CLAIMS`: check L5 health (`GET /v1/harness/health`). If L5 is down, the run will remain until L5 recovers or the gate is manually decided.
4. If stuck in `HUMAN_REVIEW`: check for pending gates and notify the responsible reviewer.
5. If the run cannot recover, cancel it and create a new one from the last valid checkpoint state.

### Run fails immediately at INIT

**Symptoms:** Run transitions `INIT → FAILED` within seconds.

**Likely causes:**
- Missing required context fields (`account_id`, `workflow_type`)
- Tenant concurrency cap reached (`HARNESS_MAX_CONCURRENT_RUNS`)
- Database connectivity issue

**Steps:**
1. Check the `error` field in the run response.
2. Check `harness_tool_budget_exceeded_total` metric.
3. Check `LAYER4_DATABASE_URL` connectivity.

### Validation always returns NEEDS_REVIEW

**Symptoms:** All claims land in `NEEDS_REVIEW` regardless of content.

**Likely causes:**
- `HARNESS_L5_VALIDATION_ENABLED=false`
- `LAYER5_API_URL` not set or unreachable
- L5 service returning 5xx

**Steps:**
1. Check `GET /v1/harness/health` → `l5_reachable` field.
2. Verify `LAYER5_API_URL` is set and resolves.
3. Check L5 service logs at port 8005.
4. If L5 is intentionally disabled, this is expected behavior — claims route to `HUMAN_REVIEW`.

### Gate decisions not advancing the run

**Symptoms:** Gate is marked `approved` but run stays in `HUMAN_REVIEW`.

**Likely causes:**
- Multiple gates exist; not all are resolved
- State machine requires all gates to be decided before advancing

**Steps:**
1. List all gates for the run:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     "https://api.valuefabric.io/v1/harness/runs/{run_id}/gates"
   ```
2. Identify any gates still in `pending` status.
3. Decide all pending gates.

### High `harness_runs_failed_total` rate

**Steps:**
1. Check logs for `"component":"harness"` + `"level":"error"` entries.
2. Group failures by `workflow_type` to isolate the affected workflow.
3. Check if a recent deployment changed tool contracts or validation thresholds.
4. Check `harness_tool_budget_exceeded_total` — budget misconfiguration causes immediate failures.
5. Roll back `config/harness.runtime.yaml` if a config change is suspected.

### Checkpoint writes failing

**Symptoms:** `harness_checkpoint_writes_total` stops incrementing; runs cannot resume after failure.

**Steps:**
1. Check `CHECKPOINT_DATABASE_URL` (or `LAYER4_DATABASE_URL` if not separately configured).
2. Check disk space on the PostgreSQL host.
3. Check for long-running transactions blocking writes.

---

## 8. Incident Response

### Severity definitions

| Severity | Condition |
|---|---|
| P1 | All harness runs failing; no new runs can start |
| P2 | Failure rate > 25% sustained for > 10 minutes |
| P3 | L5 validation unavailable (degraded mode active) |
| P4 | Pending gates > 20 or stale > 48 hours |

### P1 — All runs failing

1. Check `GET /healthz` and `GET /ready` on the Layer 4 pod.
2. Check database connectivity (`LAYER4_DATABASE_URL`).
3. Check for a recent deployment — roll back if correlated.
4. Check Kubernetes events: `kubectl describe pod -n value-fabric -l app=layer4-agents`.
5. If database is unreachable, escalate to infrastructure on-call.
6. Communicate impact to affected tenants via status page.

### P2 — Elevated failure rate

1. Identify the failing `workflow_type` from `harness_runs_failed_total` labels.
2. Check recent config changes to `harness.runtime.yaml` for that workflow type.
3. Check L5 health — validation failures can cascade to run failures.
4. If a config change is the cause, revert and redeploy.
5. If L5 is the cause, see P3 procedure.

### P3 — L5 validation unavailable

The harness degrades gracefully: validation results become `NEEDS_REVIEW` and runs enter `HUMAN_REVIEW` rather than failing. This is expected behavior.

1. Confirm L5 is down: `curl https://api.valuefabric.io/v1/harness/health`.
2. Notify the L5 on-call team.
3. Alert human reviewers that gate volume will increase until L5 recovers.
4. Monitor `harness_gate_pending_count` — if it grows beyond capacity, consider temporarily pausing new run creation.
5. Once L5 recovers, runs in `HUMAN_REVIEW` due to L5 unavailability can be re-validated via `POST /v1/harness/runs/{run_id}/validate`.

### P4 — Stale pending gates

1. Query all pending gates older than 48 hours (use the UI "Harness Runs" tab or API).
2. Notify the responsible tenant's reviewer contacts.
3. If a gate is blocking a time-sensitive run and the reviewer is unavailable, escalate to the tenant account owner.
4. Do not auto-approve gates — human review is a governance requirement.

---

## 9. Database Maintenance

### Checkpoint retention

Checkpoints older than `HARNESS_CHECKPOINT_RETENTION_DAYS` (default: 30) should be pruned. This is not yet automated — run manually during low-traffic windows:

```sql
DELETE FROM harness_checkpoints
WHERE created_at < NOW() - INTERVAL '30 days'
  AND run_id IN (
    SELECT id FROM harness_runs
    WHERE status IN ('completed', 'failed', 'cancelled')
  );
```

### Trace event retention

Trace events for terminal runs can be archived after 90 days:

```sql
-- Archive to cold storage before deleting
DELETE FROM harness_trace_events
WHERE run_id IN (
    SELECT id FROM harness_runs
    WHERE status IN ('completed', 'failed', 'cancelled')
      AND updated_at < NOW() - INTERVAL '90 days'
);
```

### Index health

Key indexes to monitor:

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE tablename LIKE 'harness_%'
ORDER BY idx_scan ASC;
```

Low `idx_scan` on `harness_runs(tenant_id, status)` or `harness_gates(run_id, status)` indicates a missing or unused index — investigate query plans.

---

## 10. Security Checklist

Before each production deployment, verify:

- [ ] `JWT_SECRET` and `API_KEY_HMAC_SECRET` are rotated per policy and not committed to source control
- [ ] `LAYER5_API_URL` uses HTTPS (or `SERVICE_MESH_MTLS_ENABLED=true`)
- [ ] `ALLOW_INSECURE_SERVICE_HTTP_IN_DEVELOPMENT` is **not** set in production
- [ ] All harness API endpoints require authenticated tenant context (no anonymous access)
- [ ] `harness_runs`, `harness_gates`, `harness_checkpoints` tables have row-level tenant filters in all queries
- [ ] Gate decisions are logged with `decided_by` and timestamp for audit trail
- [ ] `harness.runtime.yaml` `denied_tools` lists are reviewed for each workflow type
- [ ] Budget limits (`max_llm_calls`, `max_tool_calls`, `max_tokens`) are set for all workflow types
- [ ] Prometheus metrics endpoint is not publicly exposed (internal only)

---

*For architecture context, see [`docs/architecture/harness-agent-integration.md`](../../docs/architecture/harness-agent-integration.md).*
*For Layer 4 general operations, see [`OPERATIONS.md`](OPERATIONS.md).*
