# Spec: Layer 2 — Improve Test Coverage and Pass Rate

## Status
Draft — pending user confirmation

---

## Problem Statement

Layer 2 (`services/layer2-extraction`) has 31 failing tests and 61.1% coverage against an 80% project target. Failures fall into four distinct root causes, all fixable without touching production business logic:

1. **SSE endpoint missing** (24 failures) — `test_sse_streaming.py` tests a `/v1/extract/jobs/{id}/events` SSE endpoint that does not exist in `api/main.py`. The tests also reference `job_store.set()` / `get()` / `delete()` methods (vs actual `set_job()` / `get_job()`), a `_SSE_TERMINAL_STATUSES` constant, and a `PipelineJob` constructor that accepts `created_at` without requiring `source_url`.
2. **Auth missing in test fixtures** (5 failures) — `test_extract_and_ingest_pipeline.py` creates an `async_client` with no auth headers; `GovernanceMiddleware` returns 401 for all unauthenticated requests.
3. **`build_job_store()` missing fail-closed logic** (1 failure) — test expects `RuntimeError("REDIS_URL is required")` in production when no Redis URL is set; current implementation silently falls back to `InMemoryJobStore`.
4. **`asyncpg` stub breaks `find_spec()`** (1 failure) — `conftest.py` stubs `asyncpg` as `MagicMock`, setting `__spec__ = None`; `importlib.util.find_spec('asyncpg')` then raises `ValueError`.

Coverage gaps (modules at 0% or <50%): `validation/__init__.py`, `alignment/semantic_aligner.py`, `api/service.py` (0%); `integration/layer3_client.py` (25%), `extraction/cache.py` (30%), `api/main.py` (35%), `extraction/llm_extractor.py` (39%), `integration/job_store.py` (44%).

---

## Requirements

### R1 — Fix existing test failures (31 → 0)

#### R1.1 — Implement SSE endpoint in `api/main.py`
- Add `GET /v1/extract/jobs/{job_id}/events` returning `text/event-stream`.
- Emit SSE events: `status`, `progress`, `log`, `entity`, `complete`, `error`.
- Expose `_SSE_TERMINAL_STATUSES: frozenset` constant (e.g. `{"completed", "failed"}`).
- Stream terminates when `overall_status` is in `_SSE_TERMINAL_STATUSES`.
- Returns 404 with `job_id` in detail when job not found.
- Sets response headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`.

#### R1.2 — Align `job_store` API surface
- Add `set()`, `get()`, `delete()` as aliases on `InMemoryJobStore` and `RedisJobStore` to match what tests call.
- Make `source_url` optional (default `""`) on `PipelineJob` — tests create jobs without it.
- Add `created_at` field to `PipelineJob` (optional, `datetime | None = None`) — tests pass it.

#### R1.3 — Fix `_compute_overall_status` logic
- `('pending', 'queued')` should return `'running'` not `'pending'` (test matrix expects this).

#### R1.4 — Add JWT auth to pipeline test fixtures
- In `tests/test_extract_and_ingest_pipeline.py`, update the `async_client` fixture to include a valid `Authorization: Bearer <token>` header.
- Generate the token using `pyjwt.encode` with `JWT_SECRET` env var, `tenant_id` claim, and `sub` claim — matching the pattern in the root `tests/conftest.py`.
- Add a local `jwt_token` fixture inline in the test file — do not modify the service's `conftest.py`.

#### R1.5 — Fix `build_job_store()` fail-closed logic
- In `integration/job_store.py`, update `build_job_store()` to raise `RuntimeError("REDIS_URL is required in production")` when `ENVIRONMENT` is `production` or `staging` and `REDIS_URL` is not set.

#### R1.6 — Fix `asyncpg` stub in `conftest.py`
- Replace `sys.modules["asyncpg"] = MagicMock()` with a proper `types.ModuleType` stub that sets `__spec__` correctly, so `importlib.util.find_spec('asyncpg')` does not raise `ValueError`.

---

### R2 — New tests to reach 80% coverage

#### R2.1 — `validation/__init__.py` (0% → ≥80%)
`EntailmentValidator` is pure logic with no I/O. Add `tests/test_validation.py` covering:
- `validate()` returns `VAL-000` pass result when no violations.
- `VAL-001`: `ValueDriver` missing `unit` produces ERROR result.
- `VAL-006`: confidence out of `[0, 1]` produces ERROR result.
- `VAL-002`: `ENABLES` predicate with non-`Capability` source produces ERROR.
- `VAL-002`: `ENABLES` predicate with non-`UseCase` target produces ERROR.
- `_all_entities()` collects from all entity lists.
- `_find_entity_by_id()` returns correct entity or `None`.

#### R2.2 — `alignment/semantic_aligner.py` (0% → ≥80%)
`SemanticAligner` is pure logic. Add `tests/test_semantic_aligner.py` covering:
- `_normalize_name()` lowercases, removes punctuation, strips stop words.
- `_normalize_name()` replaces hyphens with spaces.
- `_compute_cache_key()` is deterministic for same entity name/description.
- `_compute_cache_key()` differs for different entity types.

#### R2.3 — `integration/job_store.py` (44% → ≥80%)
Add `tests/test_job_store.py` covering:
- `InMemoryJobStore.set_job()` / `get_job()` round-trip.
- `InMemoryJobStore.get_job()` raises `KeyError` for unknown job.
- `InMemoryJobStore.get_job()` raises `KeyError` for cross-tenant access.
- `InMemoryJobStore.list_jobs()` filters by `tenant_id`.
- `InMemoryJobStore.set_artifacts()` / `get_artifacts()` round-trip.
- `build_job_store()` returns `InMemoryJobStore` in development.
- `build_job_store()` raises `RuntimeError` in production without `REDIS_URL`.
- `RedisJobStore` methods tested with a mocked `redis.asyncio.Redis` client.

#### R2.4 — `extraction/cache.py` (30% → ≥80%)
Add `tests/test_extraction_cache.py` covering:
- Cache hit returns stored value without calling the underlying function.
- Cache miss calls the underlying function and stores result.
- TTL expiry causes cache miss (mock `time.time`).
- Cache key is deterministic for same inputs.

#### R2.5 — `integration/pending_ingestion_store.py` (68% → ≥80%)
Extend existing tests or add new tests covering:
- `SqlitePendingIngestionStore.enqueue()` persists a record.
- `SqlitePendingIngestionStore.dequeue_ready()` returns records past `next_retry_at`.
- `SqlitePendingIngestionStore.mark_completed()` removes the record.
- `build_pending_ingestion_store()` returns `SqlitePendingIngestionStore` in development.

---

## Acceptance Criteria

- [ ] `pytest tests/ --cov=src --cov-report=term-missing` in `services/layer2-extraction/` passes with **0 failures**.
- [ ] Overall coverage for `src/` is **≥80%**.
- [ ] `validation/__init__.py` coverage ≥80%.
- [ ] `alignment/semantic_aligner.py` coverage ≥80%.
- [ ] `integration/job_store.py` coverage ≥80%.
- [ ] `extraction/cache.py` coverage ≥80%.
- [ ] `integration/pending_ingestion_store.py` coverage ≥80%.
- [ ] No files outside `services/layer2-extraction/` are modified.
- [ ] No new production dependencies are added.
- [ ] All new tests are deterministic (no network I/O, no filesystem side effects outside `tmp_path`).
- [ ] Existing passing tests remain passing.

---

## Implementation Steps

1. **Fix `PipelineJob` model** (`integration/job_store.py`) — make `source_url` optional (default `""`), add optional `created_at: datetime | None = None`.

2. **Add `set()` / `get()` / `delete()` aliases** on `InMemoryJobStore` and `RedisJobStore` — thin wrappers around `set_job()` / `get_job()`.

3. **Fix `build_job_store()` fail-closed** — raise `RuntimeError("REDIS_URL is required in production")` when env is production/staging and `REDIS_URL` is unset.

4. **Fix `_compute_overall_status()`** (`api/main.py`) — add `'queued'` to the running-state branch so `('pending', 'queued')` → `'running'`.

5. **Implement SSE endpoint** (`api/main.py`) — add `GET /v1/extract/jobs/{job_id}/events` with correct headers, event format, and `_SSE_TERMINAL_STATUSES` constant.

6. **Fix `asyncpg` stub** (`tests/conftest.py`) — replace `MagicMock()` with a `types.ModuleType` stub that has a valid `__spec__`.

7. **Fix auth in `test_extract_and_ingest_pipeline.py`** — add a `jwt_token` fixture generating a signed JWT and update `async_client` to include `Authorization: Bearer <token>`.

8. **Add `tests/test_validation.py`** — unit tests for `EntailmentValidator` (R2.1).

9. **Add `tests/test_semantic_aligner.py`** — unit tests for `SemanticAligner` (R2.2).

10. **Add `tests/test_job_store.py`** — unit tests for `InMemoryJobStore`, `RedisJobStore` (mocked), and `build_job_store()` (R2.3).

11. **Add `tests/test_extraction_cache.py`** — unit tests for extraction cache (R2.4).

12. **Extend pending ingestion store tests** — add missing coverage for `SqlitePendingIngestionStore` (R2.5).

13. **Run full suite and verify** — `pytest tests/ --cov=src --cov-report=term-missing` must show ≥80% and 0 failures.

---

## Constraints

- Do not modify any file outside `services/layer2-extraction/`.
- Do not add new production dependencies.
- `PipelineJob` model changes must be backward-compatible (additive only).
- The SSE endpoint must not break existing `/v1/extract-and-ingest` or `/v1/extract/status/{job_id}` contracts.
