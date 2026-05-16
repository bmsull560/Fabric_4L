# Spec: Harness L5 Integration — LiveL5Validator

## Status
Draft — pending user confirmation

## Problem Statement

The harness `ValidationHook` currently uses `UnavailableValidator` as its primary validator, which always returns `INSUFFICIENT_EVIDENCE`. This means no claim can ever reach `PASSED` state through the harness without a human override. The ADR requires that customer-facing outputs be validated by L5 Ground Truth or explicitly overridden.

`LiveL5Validator` must implement the `ClaimValidator` interface and call the existing `Layer5GroundTruthClient` to:
1. Look up an existing TruthObject for the claim (idempotent — avoid duplicates).
2. Create one if none exists.
3. Map the L5 `TruthStatus` to a harness `ValidationState`.
4. Return a `ClaimValidationResult` that the `ValidationHook` can use.

### Key constraints from codebase exploration

- **No `external_claim_id` on `TruthObject`** — L5 has no native idempotency key. Lookup must use `list_truths` filtered by `claim_type` + `applies_to_opportunity` (account_id), then match by normalized claim text. A deterministic `claim_key` (SHA-256) is computed harness-side for deduplication.
- **`ClaimValidator.validate()` is synchronous** — the interface must become async, or `LiveL5Validator` must use `asyncio.get_event_loop().run_until_complete()`. The cleaner fix is to make `ClaimValidator.validate()` async.
- **`Layer5GroundTruthClient` already exists** with retry/resilience — `LiveL5Validator` wraps it, does not reimplement HTTP.
- **`ValidationHook.validate_claims()` is synchronous** — must become async to support `LiveL5Validator`.

---

## TruthStatus → ValidationState mapping

| L5 TruthStatus | Harness ValidationState | Rationale |
|---|---|---|
| `extracted` | `needs_review` | AI-identified, not yet validated |
| `supported` | `needs_review` | Has sources but not human-approved |
| `corroborated` | `needs_review` | Multiple sources, still needs human sign-off |
| `approved` | `passed` | Human-validated — safe to publish |
| `disputed` | `failed` | Flagged as conflicting/unreliable |
| L5 unavailable / timeout | `insufficient_evidence` | Graceful fallback — never silently approves |
| HTTP error / unexpected | `insufficient_evidence` | Same fallback |

---

## Requirements

### R1 — Make `ClaimValidator` interface async (`src/harness/validation_hooks.py`)

Change `ClaimValidator.validate()` from sync to async:

```python
@abc.abstractmethod
async def validate(self, request: ClaimValidationRequest) -> ClaimValidationResult: ...

@abc.abstractmethod
async def health(self) -> bool: ...
```

Update all implementations:
- `UnavailableValidator.validate()` → `async def validate(...)` (body unchanged)
- `UnavailableValidator.health()` → `async def health(...)` (returns `False`)
- `MockValidator.validate()` → `async def validate(...)` (body unchanged)
- `MockValidator.health()` → `async def health(...)` (returns `True`)

Update `ValidationHook`:
- `validate_claims()` → `async def validate_claims(...)`
- `validate_single()` → `async def validate_single(...)`
- `is_available` property → `async def is_available() -> bool`

### R2 — `LiveL5Validator` (`src/harness/live_l5_validator.py`)

New file implementing `ClaimValidator` using `Layer5GroundTruthClient`.

#### Constructor
```python
class LiveL5Validator(ClaimValidator):
    def __init__(
        self,
        client: Layer5GroundTruthClient,
        stale_threshold_hours: int = 24,
    ) -> None:
```

#### `async def health(self) -> bool`
Calls `client.get_freshness_summary(organization_id=None, allow_system_call=True)` — returns `True` if no error, `False` otherwise. Catches all exceptions.

#### `async def validate(self, request: ClaimValidationRequest) -> ClaimValidationResult`

Full idempotent flow:

1. **Compute `claim_key`**: `SHA-256(tenant_id + ":" + normalized_claim_text + ":" + sorted_evidence_refs)` — hex digest, first 32 chars used as a stable lookup key.

2. **Query L5** via `client.list_truths(organization_id=request.tenant_id, claim_type=_infer_claim_type(request), applies_to_opportunity=request.account_id, limit=50)`.

3. **Match existing TruthObject** by normalized claim text similarity (exact match on lowercased, stripped text). If found:
   - If `status == "approved"` and not stale → return `PASSED`.
   - If `status == "disputed"` → return `FAILED`.
   - If stale (updated_at older than `stale_threshold_hours`) → trigger revalidation via `validate_truth(action="advance_supported")` if eligible, then return current mapped state.
   - Otherwise → return mapped state from table above.

4. **If not found** → call `client.submit_truth(claim=request.claim_text, claim_type=_infer_claim_type(request), confidence=0.5, organization_id=request.tenant_id, applies_to={"account_id": request.account_id}, sources=[{"url": ref, "source_type": "internal"} for ref in request.evidence_refs])`.
   - On success → return `NEEDS_REVIEW` (newly created, not yet validated).
   - On error → return `INSUFFICIENT_EVIDENCE`.

5. **On any exception** → log warning, return `INSUFFICIENT_EVIDENCE`. Never raise.

#### `_infer_claim_type(request: ClaimValidationRequest) -> str`
Private helper. Returns `"outcome"` by default. If `value_pack_id` contains `"roi"` → `"roi_assumption"`. If `value_pack_id` contains `"benchmark"` → `"benchmark"`. Extensible.

#### `_map_status(l5_status: str) -> ValidationState`
Private helper implementing the mapping table above.

### R3 — Update `ValidationHook` callers in `HarnessRegistry` and `SqlHarnessRegistry`

`HarnessRegistry.validate_claims()` and `SqlHarnessRegistry.validate_claims()` call `self._validation.validate_claims(requests)` — must become `await self._validation.validate_claims(requests)`.

### R4 — Update `StateMachine` publish guard

`StateMachine._enforce_publish_policy()` calls `can_publish_output()` which checks `validation_state`. This is pure/sync — no change needed. The async boundary is at the registry level.

### R5 — Factory update (`src/harness/factory.py`)

Add `make_live_l5_registry()`:

```python
async def make_live_l5_registry(
    session: AsyncSession,
    l5_base_url: str,
    l5_service_token: str | None = None,
    l5_tenant_id: str | None = None,
    stale_threshold_hours: int = 24,
) -> SqlHarnessRegistry:
    """Returns a SqlHarnessRegistry with LiveL5Validator as primary validator."""
```

### R6 — Tests (`src/harness/tests/test_live_l5_validator.py`)

New test file. Uses `respx` (already in dev deps) to mock HTTP calls to L5.

#### `TestLiveL5ValidatorHealth`
- `test_health_returns_true_when_l5_responds`
- `test_health_returns_false_when_l5_unreachable`

#### `TestLiveL5ValidatorValidate`
- `test_existing_approved_truth_returns_passed`
- `test_existing_disputed_truth_returns_failed`
- `test_existing_extracted_truth_returns_needs_review`
- `test_existing_corroborated_truth_returns_needs_review`
- `test_no_existing_truth_submits_and_returns_needs_review`
- `test_l5_error_on_list_returns_insufficient_evidence`
- `test_l5_error_on_submit_returns_insufficient_evidence`
- `test_cross_tenant_truths_not_reused` — two requests with different `tenant_id` but same claim text each get their own L5 query scoped to their tenant
- `test_duplicate_call_is_idempotent` — same request twice hits list_truths both times, does not call submit_truth twice

#### `TestValidationHookAsync`
- `test_validate_claims_async_with_mock_validator`
- `test_validate_claims_falls_back_to_unavailable_when_primary_unhealthy`
- `test_unavailable_validator_never_approves`

### R7 — Update `__init__.py` exports

Add `LiveL5Validator` and `make_live_l5_registry` to `src/harness/__init__.py` lazy exports.

### R8 — Update ADR

Update `docs/architecture/adr-001-harness.md`:
- Remove "SQL persistence" from Non-Decisions (now implemented).
- Add note: "L5 integration: LiveL5Validator implemented in `src/harness/live_l5_validator.py`."
- Mark FastAPI routes and Frontend as "Deferred" rather than "Non-Decisions".

---

## Acceptance Criteria

1. `ClaimValidator.validate()` and `health()` are async — all three implementations updated.
2. `ValidationHook.validate_claims()` and `validate_single()` are async.
3. `LiveL5Validator` implements the full idempotent flow: query → match → submit if missing → map status.
4. `LiveL5Validator` never raises — all exceptions produce `INSUFFICIENT_EVIDENCE`.
5. Cross-tenant isolation: `list_truths` is always called with `organization_id=request.tenant_id`.
6. All new tests pass with mocked HTTP (no live L5 required).
7. All 156 existing harness tests continue to pass.
8. `ruff check src/harness/` reports zero errors.
9. `make_live_l5_registry()` is exported from `factory.py` and `__init__.py`.

---

## Implementation Order

1. **Make `ClaimValidator` interface async** — `validation_hooks.py`
2. **Update `ValidationHook`** — `validate_claims`, `validate_single`, `is_available` async
3. **Update `HarnessRegistry` and `SqlHarnessRegistry`** — `await` the validation calls
4. **Create `src/harness/live_l5_validator.py`** — `LiveL5Validator` full implementation
5. **Update `src/harness/factory.py`** — add `make_live_l5_registry`
6. **Update `src/harness/__init__.py`** — add lazy exports
7. **Create `src/harness/tests/test_live_l5_validator.py`** — full test suite
8. **Update `docs/architecture/adr-001-harness.md`** — reflect completed items
9. **Validate** — `uv run pytest src/harness/tests/ tests/migrations/ -v` + `ruff check src/harness/`

---

## Out of Scope

- FastAPI harness routes (next spec)
- Frontend `/governance/harness` UI (after API routes)
- Revalidation scheduling / background jobs
- L5 webhook callbacks for async validation completion
- `claim_key` stored on TruthObject (L5 schema change — out of scope)

---

## Previous specs preserved below

---

# Spec: Harness Persistence — Residual Risk Fixes

## Previous spec
`spec-oidc-audit.md` — OIDC audit (separate)
Previous implementation: Harness persistence upgrade (in-memory → PostgreSQL) — complete.

---

# Spec: Harness Persistence — Residual Risk Fixes

## Status
Draft — pending user confirmation

## Problem Statement

Three residual risks were identified after the harness persistence upgrade:

1. **Migration 031 unverified** — the SQL DDL for the five harness tables has never been
   generated and inspected offline. There is no CI artifact or test that catches schema
   drift between the migration file and the ORM models.

2. **`SqlTelemetryEmitter.get_events()` returns `[]` silently** — callers that call
   `get_events()` on a SQL-backed emitter receive an empty list instead of an error,
   making it impossible to distinguish "no events" from "wrong method called". This
   produces false-negative telemetry assertions in any code that migrates from the
   in-memory emitter.

3. **`SqlHarnessRegistry.decide_gate()` does a full-tenant scan** — to enrich the
   telemetry event with `trace_id` and `workflow_type`, the method calls
   `self._run_repo.list(tenant_id=tenant_id)` and then scans the result for
   `gate.run_id`. This is an O(n) scan over all tenant runs when a direct point
   lookup by `run_id` is available.

---

## Conventions (from codebase)

- Migration numbering: `031` is the last; next is `032` if needed (not needed here).
- `alembic upgrade <prev>:<rev> --sql` generates offline DDL — requires env vars:
  `PYTHONPATH`, `LAYER4_DATABASE_URL`, `LAYER1/2/3/5_API_URL`,
  `ALLOW_INSECURE_SERVICE_HTTP_IN_DEVELOPMENT=true`.
- `get_events()` is called in two places in `test_harness.py` (lines 930, 1282) —
  both use the in-memory `TelemetryEmitter`, not `SqlTelemetryEmitter`. No production
  code outside `harness/` calls `get_events()`.
- `decide_gate()` already holds `gate.run_id` after fetching the gate — the run can
  be fetched directly with `self._run_repo.get(gate.run_id, tenant_id)`.

---

## Requirements

### R1 — Migration SQL artifact (`migrations/sql/031_harness_tables.sql`)

Generate the offline SQL for migration 031 and commit it as a static artifact.

- File: `services/layer4-agents/migrations/sql/031_harness_tables.sql`
- Content: output of `alembic upgrade 030:031 --sql`, stripped of INFO log lines and
  warnings, containing only the SQL statements from `BEGIN` to `COMMIT`.
- This file is the canonical human-readable record of what migration 031 does.
- It must be regenerated whenever migration 031 is modified.

### R2 — Migration SQL validation test (`tests/migrations/test_031_harness_tables_sql.py`)

A pytest test that parses `031_harness_tables.sql` and asserts structural correctness
**without requiring a live database**.

The test must verify:

#### Tables present
All five harness tables appear in the SQL:
- `harness_runs`
- `harness_human_gates`
- `harness_checkpoints`
- `harness_tool_contracts`
- `harness_trace_events`

#### Tenant columns
Each table has a `tenant_id` column definition in the SQL.

#### Required indexes
The following indexes appear:
- `ix_harness_runs_tenant_status`
- `ix_harness_runs_tenant_state`
- `ix_harness_runs_trace_id`
- `ix_harness_human_gates_run_tenant`
- `ix_harness_human_gates_tenant_status`
- `ix_harness_checkpoints_run_tenant`
- `ix_harness_checkpoints_tenant_state`
- `ix_harness_checkpoints_input_hash`
- `ix_harness_tool_contracts_tenant_layer`
- `ix_harness_tool_contracts_tenant_risk`
- `ix_harness_trace_events_run_tenant`
- `ix_harness_trace_events_tenant_type`
- `ix_harness_trace_events_trace_id`

#### FK relationships
The SQL contains `FOREIGN KEY` or `REFERENCES harness_runs` for the three child tables
(`harness_human_gates`, `harness_checkpoints`, `harness_trace_events`).

#### RLS policies
The SQL contains `ENABLE ROW LEVEL SECURITY` and `tenant_isolation_policy` for each
of the five tables.

#### Unique constraint
`uq_harness_tool_contracts_tenant_tool` appears in the SQL.

#### Offline generatability (meta-test)
The test reads the SQL file from disk — it does not invoke `alembic` at test time.
The SQL file is the pre-generated artifact; the test validates its content.

### R3 — `SqlTelemetryEmitter.get_events()` raises `NotImplementedError`

Replace the current silent `return []` with an explicit error:

```python
def get_events(
    self,
    run_id: str | None = None,
    tenant_id: str | None = None,
) -> list[HarnessTraceEvent]:
    raise NotImplementedError(
        "SqlTelemetryEmitter.get_events() is not supported in synchronous mode. "
        "Use 'await emitter.get_events_async(run_id=..., tenant_id=...)' instead."
    )
```

The `get_events_async()` method is unchanged.

### R4 — `SqlHarnessRegistry.decide_gate()` uses point lookup

Replace the full-tenant scan with a direct `get_run()` call:

**Before (O(n) scan):**
```python
run_result = await self._run_repo.list(tenant_id=tenant_id)
run = next((r for r in run_result if r.id == gate.run_id), None)
```

**After (O(1) point lookup):**
```python
try:
    run = await self._run_repo.get(gate.run_id, tenant_id)
except HarnessRegistryError:
    run = None
```

The rest of the method (telemetry enrichment, `_dispatch`) is unchanged.

---

## Acceptance Criteria

1. `migrations/sql/031_harness_tables.sql` exists and contains valid SQL from `BEGIN`
   to `COMMIT` covering all five harness tables.
2. `tests/migrations/test_031_harness_tables_sql.py` passes with all structural
   assertions (tables, tenant columns, indexes, FKs, RLS, unique constraint).
3. `SqlTelemetryEmitter.get_events()` raises `NotImplementedError` with a message
   that names `get_events_async()`.
4. A test in `test_harness_persistence.py` asserts that calling `get_events()` on a
   `SqlTelemetryEmitter` raises `NotImplementedError`.
5. `SqlHarnessRegistry.decide_gate()` no longer calls `self._run_repo.list()`.
6. A test in `test_harness_persistence.py` asserts that `decide_gate()` correctly
   enriches the telemetry event with `trace_id` from the parent run (proving the
   point lookup works).
7. All 117 existing harness tests continue to pass.
8. `ruff check src/harness/ tests/migrations/` reports zero errors.

---

## Implementation Order

1. **Generate `migrations/sql/031_harness_tables.sql`** — run offline SQL generation,
   strip log lines, write file.
2. **Create `tests/migrations/__init__.py`** — empty, makes directory a package.
3. **Create `tests/migrations/test_031_harness_tables_sql.py`** — structural SQL
   validation tests (file-based, no DB).
4. **Fix `SqlTelemetryEmitter.get_events()`** in `src/harness/sql_stores.py` — replace
   `return []` with `raise NotImplementedError(...)`.
5. **Fix `SqlHarnessRegistry.decide_gate()`** in `src/harness/sql_stores.py` — replace
   `list()` scan with `get()` point lookup.
6. **Add two new tests** to `src/harness/tests/test_harness_persistence.py`:
   - `test_get_events_sync_raises_not_implemented`
   - `test_decide_gate_enriches_telemetry_with_run_trace_id`
7. **Validate** — run `uv run pytest src/harness/tests/ tests/migrations/ -v` and
   `ruff check src/harness/ tests/migrations/`.

---

## Out of Scope

- Migration 032 (no new columns needed on `HumanGateRow`).
- Changes to `TelemetryEmitter` (in-memory) — `get_events()` stays synchronous there.
- Changes to `test_harness.py` — existing tests use in-memory emitter, unaffected.
- Alembic added to `pyproject.toml` as a permanent dev dep (already added in previous
  session; verify it persists in `uv.lock`).

---

## Previous spec content (harness persistence upgrade) preserved below

---

| Store | Class | In-memory field |
|---|---|---|
| Runs | `HarnessRegistry` | `self._runs: dict[str, HarnessRun]` |
| Gates | `HumanGateManager` | `self._gates / self._run_gates` |
| Checkpoints | `CheckpointManager` | `self._checkpoints / self._run_checkpoints` |
| Tool contracts | `ToolContractRegistry` | `self._tools` |
| Telemetry events | `TelemetryEmitter` | `self._events` |

All five stores are lost on process restart. This blocks production use: harness
runs cannot survive deploys, gate decisions cannot be audited across sessions,
and checkpoints cannot be replayed.

The upgrade replaces each in-memory store with a PostgreSQL-backed repository
using the Layer 4 SQLAlchemy/Alembic conventions already established in the
service. The harness public API (`HarnessRegistry`, `CheckpointManager`,
`HumanGateManager`, `ToolContractRegistry`, `TelemetryEmitter`) must remain
unchanged so all 86 existing tests continue to pass.

---

## Conventions to Follow (from codebase exploration)

- **ORM base**: `from src.database import Base` (SQLAlchemy `DeclarativeBase`)
- **Async session**: `get_session_factory()` → `async_sessionmaker[TenantEnforcedAsyncSession]`
- **Tenant isolation**: `tenant_id: Mapped[str]` column + RLS policy via `current_setting('app.tenant_id', true)`
- **JSONB for dicts**: `from sqlalchemy.dialects.postgresql import JSONB` (see `WorkspaceTabData.data`)
- **Migration numbering**: sequential `031_`, `032_`, … with `revision / down_revision` chain
- **RLS pattern**: strict `tenant_id::text = current_setting('app.tenant_id', true)` + `admin_bypass_policy` for `admin_role, system_role`
- **Timestamps**: `DateTime(timezone=True)`, UTC, `default=lambda: datetime.now(UTC)`
- **Primary keys**: `String` IDs (matching harness `run_id`, `gate_id`, etc.) — not UUID, not int
- **Indexes**: composite `(tenant_id, <status/state>)` for list queries; single-column for FK lookups

---

## Requirements

### R1 — SQLAlchemy ORM Models (new file: `src/harness/db_models.py`)

Five ORM models, all inheriting from `Base`:

#### `HarnessRunRow`
```
__tablename__ = "harness_runs"
id            String(64)  PK
tenant_id     String(255) NOT NULL  ← RLS column
account_id    String(255) nullable
workflow_type String(64)  NOT NULL
initiated_by  String(32)  NOT NULL
status        String(32)  NOT NULL
current_state String(32)  NOT NULL
value_pack_id String(255) nullable
trace_id      String(64)  NOT NULL
created_at    DateTime(tz)
updated_at    DateTime(tz)
```
Indexes: `(tenant_id, status)`, `(tenant_id, current_state)`, `trace_id`

#### `HumanGateRow`
```
__tablename__ = "harness_human_gates"
id              String(64)  PK
run_id          String(64)  NOT NULL  FK → harness_runs.id CASCADE
tenant_id       String(255) NOT NULL
gate_type       String(64)  NOT NULL
status          String(32)  NOT NULL  default "pending"
decision_by     String(255) nullable
decision_reason Text        nullable
created_at      DateTime(tz)
decided_at      DateTime(tz) nullable
```
Indexes: `(run_id, tenant_id)`, `(tenant_id, status)`

#### `HarnessCheckpointRow`
```
__tablename__ = "harness_checkpoints"
id             String(64)  PK
run_id         String(64)  NOT NULL  FK → harness_runs.id CASCADE
tenant_id      String(255) NOT NULL
state_name     String(32)  NOT NULL
state_payload  JSONB       NOT NULL  default {}
input_hash     String(64)  NOT NULL
output_hash    String(64)  nullable
tool_calls     JSONB       NOT NULL  default []
created_at     DateTime(tz)
```
Indexes: `(run_id, tenant_id)`, `(tenant_id, state_name)`, `input_hash`

#### `ToolContractRow`
```
__tablename__ = "harness_tool_contracts"
id                       String(64)  PK
tool_id                  String(255) NOT NULL
tenant_id                String(255) NOT NULL
layer                    String(32)  NOT NULL
version                  String(32)  NOT NULL  default "v1"
input_schema_ref         String(255) NOT NULL
output_schema_ref        String(255) NOT NULL
side_effect_class        String(64)  NOT NULL
risk_level               String(32)  NOT NULL
requires_tenant_context  Boolean     NOT NULL  default True
requires_account_context Boolean     NOT NULL  default False
approval_policy_id       String(255) nullable
created_at               DateTime(tz)
```
Unique constraint: `(tenant_id, tool_id)` — enforces no-duplicate registration
Indexes: `(tenant_id, layer)`, `(tenant_id, risk_level)`

#### `HarnessTraceEventRow`
```
__tablename__ = "harness_trace_events"
id               String(64)  PK  (generated: `evt_{uuid4().hex[:16]}`)
trace_id         String(64)  NOT NULL
run_id           String(64)  NOT NULL  FK → harness_runs.id CASCADE
tenant_id        String(255) NOT NULL
account_id       String(255) nullable
workflow_type    String(64)  NOT NULL
from_state       String(32)  nullable
to_state         String(32)  nullable
status           String(32)  nullable
value_pack_id    String(255) nullable
validation_state String(32)  nullable
human_gate_id    String(64)  nullable
tool_contract_id String(64)  nullable
event_type       String(64)  NOT NULL  default "transition"
metadata         JSONB       NOT NULL  default {}
timestamp        DateTime(tz)
```
Indexes: `(run_id, tenant_id)`, `(tenant_id, event_type)`, `trace_id`

---

### R2 — Alembic Migration (`migrations/versions/031_add_harness_tables.py`)

- Revision: `031`, `down_revision: "030"`
- Creates all five tables in dependency order:
  1. `harness_runs` (no FK dependencies)
  2. `harness_human_gates` (FK → harness_runs)
  3. `harness_checkpoints` (FK → harness_runs)
  4. `harness_tool_contracts` (no FK dependencies)
  5. `harness_trace_events` (FK → harness_runs)
- Enables RLS on all five tables
- Creates `tenant_isolation_policy` (strict: `tenant_id::text = current_setting('app.tenant_id', true)`)
- Creates `admin_bypass_policy` for `admin_role, system_role`
- `downgrade()` drops tables in reverse order (events → checkpoints → gates → tool_contracts → runs)

---

### R3 — SQL Repository Layer (new file: `src/harness/repositories.py`)

Five async repository classes. Each takes an `AsyncSession` as constructor arg.
All methods are `async`. All queries filter by `tenant_id`.

#### `HarnessRunRepository`
```python
async def create(run: HarnessRun) -> HarnessRun
async def get(run_id: str, tenant_id: str) -> HarnessRun          # raises HarnessRegistryError if not found / wrong tenant
async def update(run: HarnessRun) -> HarnessRun                   # upsert by id
async def list(tenant_id: str, status: HarnessRunStatus | None) -> list[HarnessRun]
```

#### `HumanGateRepository`
```python
async def create(gate: HumanGate) -> HumanGate
async def get(gate_id: str, tenant_id: str) -> HumanGate          # raises GateNotFoundError if not found / wrong tenant
async def update(gate: HumanGate) -> HumanGate
async def list_for_run(run_id: str, tenant_id: str) -> list[HumanGate]
```

#### `CheckpointRepository`
```python
async def create(checkpoint: HarnessCheckpoint) -> HarnessCheckpoint
async def get(checkpoint_id: str, run_id: str, tenant_id: str) -> HarnessCheckpoint
async def list_for_run(run_id: str, tenant_id: str) -> list[HarnessCheckpoint]  # ordered by created_at ASC
async def get_latest(run_id: str, tenant_id: str) -> HarnessCheckpoint | None
```

#### `ToolContractRepository`
```python
async def register(tool: ToolContract, tenant_id: str) -> ToolContract   # raises ToolRegistrationError on duplicate
async def get(tool_id: str, tenant_id: str) -> ToolContract              # raises ToolNotFoundError
async def list(tenant_id: str, layer: str | None, risk_level: ToolRiskLevel | None) -> list[ToolContract]
async def delete(tool_id: str, tenant_id: str) -> None
```

#### `TraceEventRepository`
```python
async def append(event: HarnessTraceEvent) -> HarnessTraceEvent
async def list(run_id: str | None, tenant_id: str | None) -> list[HarnessTraceEvent]
```

**Mapping helpers** (private, in `repositories.py`):
- `_run_to_row(run: HarnessRun) -> HarnessRunRow`
- `_row_to_run(row: HarnessRunRow) -> HarnessRun`
- (same pattern for each entity)

All domain models remain Pydantic v2 frozen models. Repositories translate
between ORM rows and domain models — no ORM objects leak out of the repository
layer.

---

### R4 — SQL-backed Manager/Registry Variants (new file: `src/harness/sql_stores.py`)

Five classes that wrap the repositories and satisfy the same interface as the
in-memory classes. These are **drop-in replacements** — same method signatures,
same error types.

#### `SqlHarnessRegistry`
- Constructor: `__init__(session: AsyncSession, state_machine, tool_registry, gate_manager, checkpoint_manager, telemetry, validation_hook)`
- Delegates to `HarnessRunRepository` for run storage
- All other delegation unchanged from `HarnessRegistry`

#### `SqlHumanGateManager`
- Constructor: `__init__(session: AsyncSession)`
- Delegates to `HumanGateRepository`

#### `SqlCheckpointManager`
- Constructor: `__init__(session: AsyncSession)`
- Delegates to `CheckpointRepository`

#### `SqlToolContractRegistry`
- Constructor: `__init__(session: AsyncSession)`
- Delegates to `ToolContractRepository`

#### `SqlTelemetryEmitter`
- Constructor: `__init__(session: AsyncSession)`
- `_dispatch()` appends to DB via `TraceEventRepository` AND calls in-memory handlers
- `get_events()` queries DB (filtered by `run_id` / `tenant_id`)
- `clear()` is a no-op in production (kept for test compatibility)
- DB write failure in `_dispatch()` is caught and logged — must not raise (same invariant as in-memory emitter)

---

### R5 — Factory Function (new file: `src/harness/factory.py`)

```python
def make_in_memory_registry(...) -> HarnessRegistry:
    """Returns the original in-memory registry. Used in tests."""

async def make_sql_registry(session: AsyncSession, ...) -> HarnessRegistry:
    """Returns a HarnessRegistry wired to SQL stores. Used in production."""
```

The factory is the only place that decides which store implementation to use.
Existing tests continue to use `make_in_memory_registry()` (or construct
components directly as they do today).

---

### R6 — `__init__.py` Exports

Add to `src/harness/__init__.py`:
```python
from harness.sql_stores import (
    SqlHarnessRegistry,
    SqlHumanGateManager,
    SqlCheckpointManager,
    SqlToolContractRegistry,
    SqlTelemetryEmitter,
)
from harness.factory import make_in_memory_registry, make_sql_registry
```

---

### R7 — Tests (`src/harness/tests/test_harness_persistence.py`)

New test file covering SQL-backed stores. Uses `pytest` with an in-process
SQLite database (via `aiosqlite`) so no external Postgres is required in CI.

**SQLite fixture** (inline in test file):
```python
@pytest.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", ...)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def session(async_engine):
    async with AsyncSession(async_engine) as s:
        yield s
```

Test classes:

#### `TestSqlRunRepository`
- `test_create_and_get_run` — round-trip create → get
- `test_get_wrong_tenant_raises` — cross-tenant access raises `HarnessRegistryError`
- `test_list_filters_by_tenant` — runs from other tenants not returned
- `test_list_filters_by_status` — status filter works
- `test_update_run_state` — state transition persisted

#### `TestSqlGateRepository`
- `test_create_and_get_gate`
- `test_approve_gate_persisted`
- `test_reject_gate_persisted`
- `test_cross_tenant_gate_not_found`
- `test_list_gates_for_run`

#### `TestSqlCheckpointRepository`
- `test_create_checkpoint_deterministic_hash`
- `test_same_payload_same_hash_after_roundtrip`
- `test_cross_tenant_checkpoint_rejected`
- `test_list_ordered_by_created_at`
- `test_get_latest_checkpoint`

#### `TestSqlToolContractRepository`
- `test_register_and_get_tool`
- `test_duplicate_registration_raises`
- `test_cross_tenant_tool_not_found`
- `test_list_by_layer`
- `test_list_by_risk_level`
- `test_delete_tool`

#### `TestSqlTraceEventRepository`
- `test_append_event`
- `test_list_by_run_id`
- `test_list_by_tenant_id`
- `test_event_includes_trace_id_and_tenant_id`

#### `TestSqlHarnessRegistryIntegration`
- `test_full_workflow_persisted_across_registry_instances` — create run in one registry instance, read it back from a second instance sharing the same session
- `test_tenant_isolation_across_registry_instances`
- `test_checkpoint_survives_registry_restart`

---

### R8 — `pyproject.toml` Dependency Check

Verify `aiosqlite` is present in `[dependency-groups.dev]` for SQLite-based
tests. If absent, add it. Do not add it to production dependencies.

---

### R9 — `.env.example` Update

Add a comment block to `.env.example`:
```
# Harness persistence uses the same DATABASE_URL as the rest of Layer 4.
# No additional configuration required.
```

---

## Acceptance Criteria

1. All 86 existing harness tests (`test_harness.py`) pass unchanged.
2. All new SQL persistence tests (`test_harness_persistence.py`) pass with SQLite.
3. `ruff check src/harness/` reports zero errors.
4. Migration `031_add_harness_tables.py` is syntactically valid and chains correctly from `030`.
5. Migration `downgrade()` drops all five tables without error.
6. Cross-tenant access in all five SQL repositories raises the correct domain error (not a raw SQLAlchemy exception).
7. `HarnessRun`, `HumanGate`, `HarnessCheckpoint`, `ToolContract`, `HarnessTraceEvent` domain models remain Pydantic v2 frozen — no ORM objects leak outside repositories.
8. `make_in_memory_registry()` and `make_sql_registry()` both return a `HarnessRegistry`-compatible object.
9. `SqlTelemetryEmitter._dispatch()` does not raise even if the DB write fails.
10. No changes to `src/harness/models.py`, `state_machine.py`, `policies.py`, or `validation_hooks.py`.

---

## Implementation Order

1. **`src/harness/db_models.py`** — five ORM models, no logic
2. **`migrations/versions/031_add_harness_tables.py`** — schema + RLS
3. **`src/harness/repositories.py`** — five async repository classes + mapping helpers
4. **`src/harness/sql_stores.py`** — five SQL-backed manager/registry variants
5. **`src/harness/factory.py`** — `make_in_memory_registry` + `make_sql_registry`
6. **`src/harness/__init__.py`** — add new exports
7. **`src/harness/tests/test_harness_persistence.py`** — full SQL test suite
8. **`pyproject.toml`** — add `aiosqlite` to dev deps if missing
9. **`.env.example`** — add harness persistence comment
10. **Validation** — run `uv run pytest src/harness/tests/ -v` and `ruff check src/harness/`

---

## Out of Scope (this spec)

- L5 `LiveL5Validator` integration (next spec)
- FastAPI harness routes (next spec after L5)
- Frontend `/governance/harness` UI (after API routes)
- Async support for `StateMachine` / `policies.py` (pure functions, no I/O)
- Prometheus/StatsD wiring for `SqlTelemetryEmitter`
- Multi-zone / sharded persistence
