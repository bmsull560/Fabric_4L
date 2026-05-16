# Harness UI — Regression Coverage Complete; Production Signoff

## Classification

**Harness UI regression coverage complete; production signoff pending Node 22 TypeScript verification.**

## Status
Confirmed — ready for implementation

---

## Current State

All harness integration work is complete and committed on `feat/harness-live-l5-validator`. The following was delivered:

- `services/layer4-agents/src/harness/api_models.py` — Pydantic request/response models
- `services/layer4-agents/src/api/routes/harness.py` — 12 FastAPI endpoints
- `services/layer4-agents/src/api/routers.py` — harness router registered at `/v1`
- `apps/web/src/api/harness.ts` — TypeScript types and `harnessApi` client
- `apps/web/src/hooks/useHarness.ts` — TanStack Query hooks with polling
- `apps/web/src/hooks/queryKeys.ts` — `QK.harness.*` key group
- `apps/web/src/components/HarnessRunDetail.tsx` — Sheet with state progress, gates, checkpoints
- `apps/web/src/pages/AgentWorkflows.tsx` — "Harness Runs" tab, updated KPI card
- `services/layer4-agents/config/harness.runtime.yaml` — per-workflow-type runtime config
- `services/layer4-agents/config/harness.service.yaml` — service deployment config
- `docs/architecture/harness-agent-integration.md` — architecture doc with API reference
- `services/layer4-agents/docs/harness-runbook.md` — operator runbook
- `scripts/generate_harness_docs.py` — validation script (`--check` / `--fix` modes)
- `Makefile` — `docs-harness` target wired into `make verify`

Two bugs were found and fixed during regression testing:

1. **`useHarness.ts`**: `POLL_INTERVALS` was imported from `./useApiShared` (does not export it). Fixed to import from `./usePolling`.
2. **`AgentWorkflows.tsx`**: Harness `DataTable` passed `headers={...}` instead of `columns={...}`. Fixed to `columns={...}`.

Two regression test files were added:

- `apps/web/src/hooks/useHarness.test.ts` — 15 tests (import smoke, layer key, path, polling guards, mutation call signatures)
- `apps/web/src/pages/AgentWorkflows.harness.test.tsx` — 8 tests (tab render, empty/loading/error states, View opens sheet, Cancel calls transition mutation)

---

## Problem Statement

TypeScript verification (`pnpm tsc --noEmit`) could not be confirmed in the session environment (Node 20, project requires ≥22). The `tsc` binary was run directly from `node_modules` and produced **zero harness-related errors** — all errors are pre-existing in unrelated files (`useValueSignals.ts`, `TargetsAdmin.*`, `valueSignal.ts`). Production signoff requires confirming this in a proper Node ≥22 environment and fixing any harness-specific errors that surface.

---

## Requirements

### 1. TypeScript Verification

**Accepted approach (confirmed):** TypeScript verification is complete via `node_modules/.bin/tsc --noEmit` run under Node 20. This is accepted because:

1. `node_modules/.bin/tsc --noEmit` ran successfully
2. It produced zero harness-related errors
3. Harness-specific unit and page tests passed
4. The prior blocker was inability to run TypeScript at all — that blocker is resolved
5. Node 20 vs project-required Node ≥22 is an environment caveat, not a harness implementation failure

**Final report must state:**
- TypeScript: passed via `node_modules/.bin/tsc --noEmit`
- Harness-related TypeScript errors: 0
- Environment caveat: run under Node 20; project package policy expects Node ≥22
- Recommended CI confirmation: re-run under Node ≥22 in normal CI/dev environment

**If a Node ≥22 run later reveals harness-specific errors**, the fix scope is:

- Harness files directly changed or added: `harness.ts`, `useHarness.ts`, `HarnessRunDetail.tsx`, `AgentWorkflows.tsx`, harness tests
- Shared types/utilities **only** where harness integration exposed or broke an existing contract: query key types, `DataTable` prop typing, API client layer/path typing, shared polling constants/types, shared test fixtures used by harness tests
- Do not broaden into unrelated app-wide TypeScript cleanup
- Do not revert harness changes unless errors reveal a fundamental integration mistake that cannot be fixed surgically
- If shared types are touched, the final report must explain: which harness usage required the change, why it is backward-compatible, which existing tests confirm no regression

### 2. Bug Fix Preservation

The following fixes must remain intact:

| File | Fix |
|---|---|
| `apps/web/src/hooks/useHarness.ts` | `POLL_INTERVALS` imported from `./usePolling`, not `./useApiShared` |
| `apps/web/src/pages/AgentWorkflows.tsx` | Harness `DataTable` uses `columns={...}`, not `headers={...}` |

### 3. Test Preservation

The following test files must remain and continue to pass:

| File | Tests |
|---|---|
| `apps/web/src/hooks/useHarness.test.ts` | 15 tests |
| `apps/web/src/pages/AgentWorkflows.harness.test.tsx` | 8 tests |

### 4. No Mock State (confirm unchanged)

- All harness data flows through `harnessApi` → `apiClient` → real `/v1/harness/*` endpoints
- Gate approve/reject calls `useDecideGate` → `harnessApi.decideGate`
- Polling stops when `isTerminalState(run.current_state)` returns true
- Pending gates poll at `POLL_INTERVALS.workflows` (5 s) and stop when no pending gates remain

---

## Acceptance Criteria

- [ ] `pnpm tsc --noEmit` run in Node ≥22 environment
- [ ] Zero TypeScript errors attributable to harness files
- [ ] Pre-existing TypeScript errors documented and left untouched
- [ ] `useHarness.test.ts`: 15/15 passing
- [ ] `AgentWorkflows.harness.test.tsx`: 8/8 passing
- [ ] `make docs-harness` exits 0
- [ ] Both bug fixes confirmed present in final state

---

## Implementation Steps

1. Run `pnpm tsc --noEmit` in a Node ≥22 environment
2. Triage errors: separate harness-introduced from pre-existing
3. Fix harness-introduced errors only (if any)
4. Re-run harness tests to confirm fixes did not break coverage
5. Re-run `make docs-harness` to confirm doc validation still passes
6. Produce final verification report

---

## Final Verification Report Template

```
## Harness UI — Final Verification Report

### Bug Fixes (preserved)
- useHarness.ts: POLL_INTERVALS from ./usePolling ✅
- AgentWorkflows.tsx: DataTable columns= prop ✅

### Harness-specific tests
- useHarness.test.ts: 15/15 ✅
- AgentWorkflows.harness.test.tsx: 8/8 ✅

### Broader suite baseline (pre-existing, not caused by harness work)
- Baseline before harness work: 19 test files failing / 122 tests failing
- After harness work: 16 test files failing / 100 tests failing (net improvement from DataTable bug fix)
- Harness-introduced regressions: 0

### TypeScript verification
- Command: node_modules/.bin/tsc --noEmit
- Harness-related errors: 0
- Pre-existing errors (not touched): useValueSignals.ts, TargetsAdmin.*, valueSignal.ts
- Environment: Node 20 (project requires ≥22 — environment caveat, not a harness failure)
- Result: PASSED
- Recommended CI confirmation: re-run under Node ≥22

### make docs-harness
- Result: all checks passed ✅

### Production signoff
- Frontend Harness UI verification: COMPLETE
- Classification: Harness UI regression coverage complete; production signoff pending Node ≥22 CI confirmation
```

---

## Out of Scope

- Fixing pre-existing TypeScript errors in `useValueSignals.ts`, `TargetsAdmin.*`, `valueSignal.ts`
- Cleaning the broader test suite baseline (100 pre-existing failures)
- Any new harness features or UI changes

---

## [ARCHIVED] Original Implementation Spec

The sections below are the original implementation spec, preserved for reference. All items were completed.

### 1. Backend — FastAPI Harness Routes

Create `services/layer4-agents/src/api/routes/harness.py` and register it in `src/api/routers.py` under prefix `/v1`.

**Run management:**
- `POST   /v1/harness/runs` — create a new `HarnessRun`
- `GET    /v1/harness/runs` — list runs for authenticated tenant (filterable by `status`, `workflow_type`)
- `GET    /v1/harness/runs/{run_id}` — get a single run
- `POST   /v1/harness/runs/{run_id}/transition` — advance state machine (`to_state`, optional `validation_results`, `human_override`, `state_payload`)
- `DELETE /v1/harness/runs/{run_id}` — cancel/archive a run

**Checkpoints:**
- `GET    /v1/harness/runs/{run_id}/checkpoints` — list checkpoints for a run
- `GET    /v1/harness/runs/{run_id}/checkpoints/latest` — get latest checkpoint

**Human gates:**
- `GET    /v1/harness/runs/{run_id}/gates` — list gates for a run
- `POST   /v1/harness/runs/{run_id}/gates` — create a gate (`gate_type`)
- `POST   /v1/harness/gates/{gate_id}/decide` — approve / reject / modify / expire a gate

**Validation:**
- `POST   /v1/harness/runs/{run_id}/validate` — validate claims for a run (delegates to `ValidationHook`)

**Health:**
- `GET    /v1/harness/health` — returns `validation_available`, `l5_healthy`, `db_healthy`

**Constraints:**
- All routes must extract `tenant_id` from authenticated context (never from request body).
- All routes must use `make_live_l5_registry` (or `make_sql_registry` when L5 is not configured) injected via FastAPI dependency.
- Error responses must follow the existing error shape used by `/v1/workflows/*`.
- All Pydantic request/response models must live in `src/harness/api_models.py` (new file).

### 2. OpenAPI Contract Update

After routes are registered, regenerate `contracts/openapi/layer4-agents.json` via `make contracts`. The harness paths must appear in the contract. The frontend generated client (`apps/web/src/api/generated/l4/`) must be regenerated via `make contract-freshness`.

### 3. Frontend — TypeScript API Client

Create `apps/web/src/api/harness.ts`:
- TypeScript types mirroring `HarnessRun`, `HarnessCheckpoint`, `HumanGate`, `ClaimValidationResult`, `HarnessState`, `HarnessRunStatus`, `GateStatus`, `GateType`, `ValidationState`
- `harnessApi` object with typed functions for each route group (runs, checkpoints, gates, validate, health)
- Follows the existing pattern in `apps/web/src/api/workflows.ts`

### 4. Frontend — React Query Hooks

Create `apps/web/src/hooks/useHarness.ts`:
- `useHarnessRuns({ status?, workflow_type?, limit, offset })` — paginated list
- `useHarnessRun(runId)` — single run with polling when status is non-terminal
- `useHarnessCheckpoints(runId)` — checkpoint list
- `useHarnessGates(runId)` — gate list
- `useCreateHarnessRun()` — mutation
- `useTransitionHarnessRun()` — mutation (advance state)
- `useDecideGate()` — mutation (approve/reject/modify/expire)
- `useValidateHarnessClaims()` — mutation
- Follows the existing patterns in `apps/web/src/hooks/useWorkflows.ts` (TanStack Query, `QK` query keys, `STALE_TIME`, `POLL_INTERVALS`)

### 5. Frontend — AgentWorkflows.tsx Extension

Extend `apps/web/src/pages/AgentWorkflows.tsx` to add a **"Harness Runs"** tab alongside the existing "Workflow Dashboard", "Whitespace Analysis", and "Business Cases" tabs.

The Harness Runs tab must display:
- A paginated list of harness runs (run ID, workflow type, current state, status badge, created at)
- Per-run inline actions: **Resume** (transition to next state), **Retry** (re-enter failed state), **Cancel** (transition to CANCELLED)
- A **View** button that opens a `HarnessRunDetail` sheet showing:
  - Run metadata (ID, tenant, workflow type, initiated by, trace ID)
  - Current state and status with visual state machine progress
  - Checkpoint list (state name, created at, input hash)
  - Human gate list (gate type, status, decision by, decision reason) with **Approve** / **Reject** actions for `PENDING` gates
  - Validation outcomes (claim ID, state, confidence, validator, reason)
  - Available control actions based on current state

**Constraints:**
- Preserve existing page structure, `PageHeader`, `Tabs`, `SectionCard`, `DataTable`, `StatusBadge`, `QueryState` primitives from `WfPrimitives`
- Do not introduce new UI libraries
- Add loading, empty, and error states consistent with existing patterns
- The "Human-in-Loop Pending" KPI card on the dashboard tab should count pending harness gates in addition to workflow pending count

### 6. YAML Configuration Files

#### `services/layer4-agents/config/harness.runtime.yaml`

Agent/workflow runtime configuration. Must include:
- `schema_version`
- Per-workflow-type sections (`roi_calculator`, `whitespace_analysis`, `business_case`, `orchestrator`) each with:
  - `allowed_tools` list
  - `denied_tools` list
  - `budget`: `max_steps`, `max_retries`, `timeout_seconds`, `max_cost_usd`
  - `invariants`: `require_human_approval` (list of states), `max_tool_calls_per_run`
  - `validation`: `require_l5_validation` (bool), `stale_threshold_hours`
  - `checkpointing`: `enabled` (bool), `checkpoint_on_states` (list)
  - `failure_policy`: `on_l5_unavailable` (`degrade` | `block`), `on_gate_timeout` (`expire` | `block`)
  - `audit`: `emit_trace_events` (bool), `log_level`
- References to corresponding `.abom.json` manifests in `services/layer4-agents/manifests/`

#### `services/layer4-agents/config/harness.service.yaml`

Service deployment configuration. Must include:
- `schema_version`
- `service`: name, version, port
- `database`: pool size, timeout, migration auto-run
- `l5_integration`: base_url env var, service_token env var, stale_threshold_hours, health_check_interval_seconds
- `queue`: concurrency, max_retries, retry_backoff_seconds
- `timeouts`: default_run_timeout_seconds, gate_decision_timeout_seconds
- `feature_flags`: `harness_enabled`, `live_l5_validation_enabled`, `sql_registry_enabled`
- `observability`: log_level, trace_sampling_rate, emit_metrics
- `security`: require_tenant_context, validate_claim_tenant_on_submit
- `health`: readiness_checks list

### 7. Documentation

#### `docs/architecture/harness-agent-integration.md` (new file)

Architecture-level document covering:
- Harness purpose and role in the six-layer pipeline
- Relationship to LangGraph workflows and existing `/v1/workflows/*` surface
- Key concepts: runs, state machine, transitions, checkpoints, human gates, validation hook, LiveL5Validator
- Data flow diagram (text/ASCII): UI → API → SqlHarnessRegistry → L5 → UI
- Tenant isolation model
- Security and RBAC notes
- Extension points (custom validators, new workflow types, pack integration)

#### `services/layer4-agents/docs/harness-runbook.md` (new file)

Operator/developer runbook covering:
- Setup and environment variables (`L5_BASE_URL`, `L5_SERVICE_TOKEN`, `DATABASE_URL`)
- Factory selection: `make_in_memory_registry` vs `make_sql_registry` vs `make_live_l5_registry`
- API reference: all `/v1/harness/*` endpoints with method, path, request schema, response schema, status codes, and example payloads
- Common workflows: create run → transition → validate → gate → complete
- Human gate lifecycle: create → pending → approve/reject → effect on run
- Validation outcomes: state mapping table, staleness behavior, fallback behavior
- Checkpoint usage: deterministic hashing, replay, verify_payload_unchanged
- Failure modes: L5 unavailable, gate timeout, state machine violation, tenant mismatch
- Recovery procedures: how to resume a stuck run, how to expire a stale gate
- Observability: trace events, structured logs, metrics emitted
- Testing guidance: unit (MockValidator), integration (SQLite), contract, E2E expectations
- Known limitations and future extension points

### 8. Generation and Validation Script

#### `scripts/generate_harness_docs.py`

A Python script that:
1. **Validates** required documentation files exist and are non-empty:
   - `docs/architecture/harness-agent-integration.md`
   - `services/layer4-agents/docs/harness-runbook.md`
2. **Validates** required YAML config files exist, are syntactically valid YAML, and contain required top-level keys:
   - `services/layer4-agents/config/harness.runtime.yaml` — required keys: `schema_version`, `workflows`
   - `services/layer4-agents/config/harness.service.yaml` — required keys: `schema_version`, `service`, `l5_integration`, `feature_flags`
3. **Generates** a Markdown table of all harness API endpoints (method, path, summary) by introspecting the FastAPI router from `src/api/routes/harness.py` and writes it to `services/layer4-agents/docs/harness-api-table.md`
4. **In `--check` mode** (default for CI): compares the generated endpoint table against the committed file and fails with a diff if stale
5. **In `--fix` mode**: overwrites the committed file with the freshly generated output
6. Exits non-zero with clear, actionable error messages on any failure

#### Makefile target

```makefile
.PHONY: docs-harness
docs-harness: ## Validate harness docs and config; regenerate API table
	python scripts/generate_harness_docs.py --check
```

Wire `docs-harness` into the existing `verify` target by appending it to the `verify` recipe dependencies.

---

## Acceptance Criteria

### Backend
- [ ] `GET /v1/harness/runs` returns 200 with paginated run list scoped to authenticated tenant
- [ ] `POST /v1/harness/runs/{run_id}/transition` advances state and returns updated run + trace event
- [ ] `POST /v1/harness/gates/{gate_id}/decide` with `approved` transitions gate and is reflected in run
- [ ] `POST /v1/harness/runs/{run_id}/validate` returns `ClaimValidationResult` list
- [ ] All routes return 403/404 (not 500) on tenant mismatch or missing resource
- [ ] Harness paths appear in `contracts/openapi/layer4-agents.json` after `make contracts`

### Frontend
- [ ] "Harness Runs" tab is visible on `AgentWorkflows.tsx` and renders paginated run list
- [ ] Run detail sheet shows checkpoints, gates, and validation outcomes
- [ ] Approve/Reject gate actions call the API and optimistically update the UI
- [ ] Resume/Retry/Cancel actions call the correct transition endpoint
- [ ] Loading, empty, and error states are present and consistent with existing page patterns
- [ ] No new UI libraries introduced

### YAML Config
- [ ] `harness.runtime.yaml` is syntactically valid and contains all required sections
- [ ] `harness.service.yaml` is syntactically valid and contains all required sections
- [ ] Both files are committed to `services/layer4-agents/config/`

### Documentation
- [ ] `docs/architecture/harness-agent-integration.md` covers all required sections
- [ ] `services/layer4-agents/docs/harness-runbook.md` covers all required sections including full API reference
- [ ] `services/layer4-agents/docs/harness-api-table.md` is generated and committed

### Automation
- [ ] `python scripts/generate_harness_docs.py --check` exits 0 when all files are present and current
- [ ] `python scripts/generate_harness_docs.py --check` exits non-zero with actionable message when a file is missing or stale
- [ ] `make docs-harness` invokes the script successfully
- [ ] `make verify` includes `docs-harness` and fails if harness docs/config are missing or stale

---

## Implementation Order

1. **`src/harness/api_models.py`** — Pydantic request/response models for all harness routes
2. **`src/api/routes/harness.py`** — FastAPI router with all 12 endpoints; inject `SqlHarnessRegistry` via dependency
3. **`src/api/routers.py`** — register harness router at `/v1`
4. **`make contracts`** — regenerate `contracts/openapi/layer4-agents.json`
5. **`make contract-freshness`** — regenerate `apps/web/src/api/generated/l4/`
6. **`apps/web/src/api/harness.ts`** — TypeScript types and `harnessApi` client
7. **`apps/web/src/hooks/useHarness.ts`** — TanStack Query hooks
8. **`apps/web/src/components/HarnessRunDetail.tsx`** — detail sheet component (checkpoints, gates, validation)
9. **`apps/web/src/pages/AgentWorkflows.tsx`** — add "Harness Runs" tab; update KPI card
10. **`services/layer4-agents/config/harness.runtime.yaml`** — agent runtime config
11. **`services/layer4-agents/config/harness.service.yaml`** — service deployment config
12. **`docs/architecture/harness-agent-integration.md`** — architecture doc
13. **`services/layer4-agents/docs/harness-runbook.md`** — operator runbook
14. **`scripts/generate_harness_docs.py`** — validation + generation script
15. **`Makefile`** — add `docs-harness` target; wire into `verify`
16. **Run `make docs-harness`** — confirm script passes against committed files

---

## Files Created / Modified

| File | Action |
|---|---|
| `services/layer4-agents/src/harness/api_models.py` | Create |
| `services/layer4-agents/src/api/routes/harness.py` | Create |
| `services/layer4-agents/src/api/routers.py` | Modify (register router) |
| `contracts/openapi/layer4-agents.json` | Regenerated |
| `apps/web/src/api/generated/l4/index.ts` | Regenerated |
| `apps/web/src/api/harness.ts` | Create |
| `apps/web/src/hooks/useHarness.ts` | Create |
| `apps/web/src/components/HarnessRunDetail.tsx` | Create |
| `apps/web/src/pages/AgentWorkflows.tsx` | Modify (add tab + KPI update) |
| `services/layer4-agents/config/harness.runtime.yaml` | Create |
| `services/layer4-agents/config/harness.service.yaml` | Create |
| `docs/architecture/harness-agent-integration.md` | Create |
| `services/layer4-agents/docs/harness-runbook.md` | Create |
| `services/layer4-agents/docs/harness-api-table.md` | Generated |
| `scripts/generate_harness_docs.py` | Create |
| `Makefile` | Modify (add `docs-harness`, wire into `verify`) |

---

## Out of Scope

- New top-level navigation page for harness (deferred)
- CommandCenter right-rail harness panel (deferred — noted as future extension)
- Real-time SSE streaming for harness state transitions (deferred — polling sufficient for MVP)
- Harness-to-LangGraph bridge (harness and LangGraph workflows remain separate surfaces)
- Frontend tests beyond existing `AgentWorkflows.tsx` patterns
