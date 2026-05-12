# Layer 4 Troubleshooting Runbook

Common production issues and their resolution paths.

---

## Workflow Stuck in RUNNING

**Symptoms:**
- Workflow status remains `RUNNING` for longer than expected.
- No new events in the SSE stream.
- Pod logs show `WorkflowTimeoutError` or the workflow ID simply stops emitting logs.

**Root Causes:**
1. Workflow task timed out (`asyncio.TimeoutError` in `_run_workflow_task`).
2. Pod was killed during workflow execution (OOM, eviction, rolling update).
3. LangGraph checkpoint saver lost connection mid-run.

**Resolution:**

1. Check the workflow status endpoint:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
        -H "X-Tenant-ID: $TENANT" \
        https://layer4.value-fabric.svc.cluster.local/v1/workflows/$WORKFLOW_ID
   ```

2. If status is `RUNNING` but no recent events, check checkpoints:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
        -H "X-Tenant-ID: $TENANT" \
        "https://layer4.value-fabric.svc.cluster.local/v1/workflows/$WORKFLOW_ID/checkpoints?limit=10"
   ```

3. Resume the workflow if checkpoints exist:
   ```bash
   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "X-Tenant-ID: $TENANT" \
        https://layer4.value-fabric.svc.cluster.local/v1/workflows/$WORKFLOW_ID/resume
   ```

4. If no checkpoints and the workflow is genuinely stuck, cancel and recreate:
   ```bash
   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "X-Tenant-ID: $TENANT" \
        https://layer4.value-fabric.svc.cluster.local/v1/workflows/$WORKFLOW_ID/cancel
   ```

**Prevention:**
- Ensure `CHECKPOINT_DATABASE_URL` points to a stable PostgreSQL instance.
- Monitor pod memory usage; LangGraph state can grow large with long conversations.
- Set realistic `workflow_timeout_seconds` in settings.

---

## Tenant Isolation Failure

**Symptoms:**
- Tenant A sees data from Tenant B.
- RLS policy violation errors in PostgreSQL logs.
- `cross-tenant` or `tenant isolation violation` in application logs.

**Root Causes:**
1. `tenant_id` not set in `RequestContext` before repository call.
2. Direct SQL query missing `WHERE tenant_id = ...` filter.
3. `SET LOCAL app.tenant_id = ...` not executed before RLS-guarded query.

**Resolution:**

1. Verify the request carries `X-Tenant-ID` (or JWT claim) all the way to the route handler.
2. Check that `GovernanceMiddleware` is running and populating `request.state.tenant_context`.
3. Inspect the suspect repository method:
   ```python
   # Correct pattern
   tenant_id = ctx.tenant_id
   repo.method(..., tenant_id=tenant_id)
   ```
4. Run the tenant isolation test suite:
   ```bash
   pytest tests/test_tenant_isolation.py -v
   ```

**Prevention:**
- Never trust `tenant_id` from request body over authenticated context.
- Always use `RequestContext` derived from JWT/API key, not raw headers.
- Add hostile cross-tenant tests for every new repository method.

---

## Redis Unavailable

**Symptoms:**
- `ConnectionError` to Redis in logs.
- State manager falls back to in-memory LRU.
- Scheduler task queue appears empty or tasks disappear on pod restart.

**Root Causes:**
1. Redis pod crashed or network partitioned.
2. Redis memory eviction under pressure.

**Resolution:**

1. Check Redis health:
   ```bash
   redis-cli ping
   ```

2. If Redis is down, Layer 4 automatically falls back to in-memory storage. This is safe for transient operations but **not** for checkpoint recovery.

3. Restore Redis and restart Layer 4 pods. The in-memory fallback state will be lost, but PostgreSQL-backed checkpoints survive.

**Prevention:**
- Run Redis in highly available mode (Redis Sentinel or Cluster).
- Monitor Redis memory usage and eviction rates.
- Set alerts on `redis_connection_failed` log patterns.

---

## Checkpoint DB Connection Failed

**Symptoms:**
- `AsyncPostgresSaver` connection errors on startup.
- Workflows cannot be paused or resumed.
- Logs show `cannot import name 'AsyncPostgresSaver'` or `no pq wrapper available` (if psycopg/asyncpg driver is missing).

**Root Causes:**
1. `CHECKPOINT_DATABASE_URL` is invalid or database is down.
2. `asyncpg` / `psycopg` binary driver missing in the container image.
3. Connection pool exhausted.

**Resolution:**

1. Verify the connection string:
   ```bash
   python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('$CHECKPOINT_DATABASE_URL'))"
   ```

2. If the driver is missing, ensure the Docker image includes `asyncpg` and `psycopg-binary`.

3. If the pool is exhausted, increase PostgreSQL `max_connections` or reduce `CHECKPOINT_DATABASE_URL` pool size.

**Graceful Degradation:**
- If the checkpoint DB is unavailable at startup, Layer 4 **hard fails** in production. This is intentional: checkpointing is a safety-critical feature.
- In development, you can set `CHECKPOINT_DATABASE_URL` to the same SQLite or local Postgres instance, but SQLite is **not** supported for LangGraph checkpoints (requires `asyncpg`).

---

## Pydantic v2 Validation Errors

**Symptoms:**
- `AttributeError: 'dict' object has no attribute 'dict'` or similar.
- API responses return 500 instead of the expected shape.
- Logs show `PydanticSerializationError`.

**Root Causes:**
1. Code still uses Pydantic v1 API (`.dict()`, `.json()`) instead of v2 (`.model_dump()`, `.model_dump_json()`).

**Resolution:**

1. Search for v1 patterns:
   ```bash
   grep -rn "\.dict()" services/layer4-agents/src/
   grep -rn "\.json()" services/layer4-agents/src/  # filter out stdlib json usage
   ```

2. Replace with v2 equivalents:
   | v1 | v2 |
   |----|----|
   | `.dict()` | `.model_dump()` |
   | `.json()` | `.model_dump_json()` |
   | `BaseModel.__fields__` | `BaseModel.model_fields` |
   | `@validator` | `@field_validator` |
   | `@root_validator` | `@model_validator` |

**Prevention:**
- The production readiness pass fixed all known v1 calls in Layer 4. Add a CI lint rule or `grep` check to prevent regressions.

---

## Rate Limiting 429 Errors

**Symptoms:**
- Clients receive `429 Too Many Requests`.
- `rate_limit_hits_total` metric spikes.

**Root Causes:**
1. Legitimate burst traffic exceeds `RATE_LIMIT_BURST_SIZE`.
2. Misconfigured upstream proxy retries causing duplicate requests.
3. Tenant sharing API keys across many clients.

**Resolution:**

1. Check the `Retry-After` header value.
2. Review the tenant's recent request volume in logs.
3. If legitimate, temporarily raise `RATE_LIMIT_REQUESTS_PER_MINUTE` for the tenant via `tenant_settings_resolver` (requires code change or admin override).

**Prevention:**
- Set burst sizes based on observed peak traffic + 20% headroom.
- Use client-side request coalescing for identical queries.

---

## Docker Health Check Failing

**Symptoms:**
- Kubernetes marks Layer 4 pods as `Unhealthy`.
- `kubectl describe pod` shows `Liveness probe failed`.

**Root Causes:**
1. Old Dockerfile used `curl` which is not present in `python:3.11-slim-bookworm`.

**Resolution:**

The Dockerfile was updated to use a Python-based health check (`src/health_check.py`). If you see this issue on an older image:

1. Rebuild the image from the current Dockerfile.
2. Verify the health check manually:
   ```bash
   docker exec <container> python -m src.health_check
   ```

---

## Import-Time Side Effects in Tests or Scripts

**Symptoms:**
- `pytest --collect-only` fails with `InfisicalMissingRequiredSecretsError`.
- Scripts that import Layer 4 modules crash before running any code.

**Root Causes:**
1. `settings.py` used to call `verify_layer4_startup_dependencies()` and `load_infisical_secrets()` at module import time.

**Resolution:**

This was fixed in the production readiness pass. All side effects were moved into `configure_settings()`, which is called during FastAPI lifespan startup.

If you encounter this in a fork or older branch:
1. Move initialization into an explicit startup function.
2. Call it from `api/startup.py` inside `lifespan`.
3. Ensure `conftest.py` and one-off scripts can import modules without triggering Infisical.

---

## Agent Not Found for Capability

**Symptoms:**
- `No agent available for capability: <capability>` in logs.
- `distribute_task` returns `None`.

**Root Causes:**
1. No agent registered for the requested capability.
2. `_registered_agents` stored `BaseAgent` instances but code tried dict access (fixed in production readiness pass).

**Resolution:**

1. Verify the agent is registered:
   ```python
   controller.register_agent(agent)
   ```
2. Check `agent.get_capabilities()` includes the requested capability string.
3. Ensure the agent's `agent_type` attribute is accessible (not a dict key).

---

## Contact

For issues not covered here, escalate to the platform engineering team with:
- Workflow ID / Trace ID
- Tenant ID
- Pod logs (structured JSON if available)
- Timestamp of first observed failure
