# Migration Reproducibility Invariants (All Maintained Layer Services)

This reference defines mandatory migration reproducibility invariants for all maintained layer services:

- `services/layer1-ingestion`
- `services/layer2-extraction`
- `services/layer3-knowledge`
- `services/layer4-agents`
- `services/layer5-ground-truth`
- `services/layer6-benchmarks`

Use this document during incident response, schema rollback/forward operations, and post-incident reconstruction.

## 1. Mandatory migration metadata invariants

All schema/data migrations MUST satisfy the following invariants.

### 1.1 Revision ID format

- Layer 1/2/4/5 (Alembic-backed): migration filenames MUST start with either:
  - `NNN_<slug>.py` (example: `014_add_tenant_id_to_billing.py`), or
  - `YYYYMMDD_NNNN_<slug>.py` (example: `20260101_0000_a1b2c3d4e5f6_initial_layer4_schema.py`).
- Layer 3 (scripted migrations): migration scripts MUST be numerically prefixed and sortable (example: `028_l3_tenant_standardization.py`, `029_backfill_sync_metadata_tenant.py`).
- Layer 6 (Cypher migrations): migration files MUST be numerically prefixed and sortable (example: `001_initial_schema.cypher`).

### 1.2 Forward/backward compatibility expectations

- **Forward compatibility (required):** each migration must be additive-first whenever feasible (new tables/columns/indexes/constraints), with guarded rollout for code that depends on new fields.
- **Backward compatibility window (required):** during rollout, the previously deployed service version must continue to operate until all replicas are updated.
- **Destructive operations:** destructive schema changes (drop/rename without compatibility bridge) require explicit incident/release annotation and a staged migration plan.
- **Tenant invariants:** tenant scoping columns, RLS policies, and ownership semantics must remain valid before and after migration steps.

### 1.3 Downgrade policy

- Downgrades are **best-effort and explicit**:
  - If a downgrade is safe, implement it and document any lossy behavior.
  - If not safely reversible, downgrade code path must fail closed with a clear rationale and recovery guidance.
- Layer-specific policy:
  - Layer 1/2/4/5: use Alembic `downgrade` implementation where safe.
  - Layer 3/6: provide an explicit rollback script/procedure in release docs or runbook entry for each non-trivial migration.

### 1.4 Data backfill rules

- Every migration that introduces non-nullable fields, tenant/ownership metadata, derived indexes, or policy-critical columns MUST include a deterministic backfill step.
- Backfill must be:
  - idempotent,
  - tenant-safe,
  - resumable,
  - auditable (log command, input scope, completion marker).
- Backfill completion criteria must be measurable (row counts, missing-field count, policy validation query).

## 2. Time travel procedures by service

The objective is to restore schema state to revision `X` and rehydrate required baseline data.

> Always snapshot database/graph store state before rollback/forward remediation in production.

### 2.1 Layer 1 (`services/layer1-ingestion`)

**Schema to revision X**

```bash
cd services/layer1-ingestion
alembic current
alembic history --verbose
alembic downgrade <REVISION_X>   # or alembic upgrade <REVISION_X>
```

**Baseline rehydration**

- Re-run seed/bootstrap steps used by ingestion state tables (sources, compliance defaults, robots cache prerequisites).
- Validate tenant and RLS coverage for ingestion tables before reopening traffic.

### 2.2 Layer 2 (`services/layer2-extraction`)

**Schema to revision X**

```bash
cd services/layer2-extraction
alembic current
alembic history --verbose
alembic downgrade <REVISION_X>   # or alembic upgrade <REVISION_X>
```

**Baseline rehydration**

- Rehydrate ontology/extraction baseline tables required by the active packs and runtime extraction flow.
- Re-run any pending-ingestions consistency backfill expected by current extraction workers.

### 2.3 Layer 3 (`services/layer3-knowledge`)

Layer 3 uses scripted migrations under `services/layer3-knowledge/src/migrations/`.

**Schema/data to revision X (scripted)**

1. Identify ordered migration script set up to `X`.
2. Execute rollback or forward scripts in controlled order using service runbook orchestration.
3. Record executed script names and timestamps in incident log.

**Baseline rehydration**

- Rebuild required tenant metadata alignment and index backfills expected by retrieval and graph APIs.
- Re-run tenant-scoped data integrity checks before enabling query traffic.

### 2.4 Layer 4 (`services/layer4-agents`)

**Schema to revision X**

```bash
cd services/layer4-agents
alembic current
alembic history --verbose
alembic downgrade <REVISION_X>   # or alembic upgrade <REVISION_X>
```

**Baseline rehydration**

- Rehydrate governance, feature flag, billing, and tenant-lifecycle baseline state required by agent orchestration.
- Re-validate RLS and tenant coverage for agent-side persistence tables.

### 2.5 Layer 5 (`services/layer5-ground-truth`)

**Schema to revision X**

```bash
cd services/layer5-ground-truth
alembic current
alembic history --verbose
alembic downgrade <REVISION_X>   # or alembic upgrade <REVISION_X>
```

**Baseline rehydration**

- Rehydrate truth-object validation and model-registry baseline records needed for claims validation.
- Re-run migration/schema alignment test gate before reopening write paths.

### 2.6 Layer 6 (`services/layer6-benchmarks`)

Layer 6 migration artifacts are Cypher-based under `services/layer6-benchmarks/migrations/versions/`.

**Schema/data to revision X (Cypher)**

1. Identify ordered Cypher migrations up to `X`.
2. Apply rollback/forward Cypher plan using benchmark service operational procedure.
3. Persist applied migration revision markers in service operations log.

**Baseline rehydration**

- Rehydrate benchmark catalog baseline nodes/relationships required for compare/validate APIs.
- Validate dataset lineage references before enabling benchmark read/write flows.

## 3. Canonical incident-state reconstruction checklist

Use this checklist during schema incidents, failed deploy rollback, or historical replay:

1. Capture incident metadata (service, environment, commit SHA, UTC timestamps, operator).
2. Freeze schema-changing deploys for impacted service.
3. Capture pre-change snapshot/backup and current revision markers.
4. Identify migration root for affected service:
   - `services/layer1-ingestion/migrations/versions/`
   - `services/layer2-extraction/migrations/versions/`
   - `services/layer3-knowledge/src/migrations/`
   - `services/layer4-agents/migrations/versions/`
   - `services/layer5-ground-truth/src/layer5_ground_truth/migrations/versions/`
   - `services/layer6-benchmarks/migrations/versions/`
5. Execute revision-history command for service (Alembic `history`/`heads` or scripted inventory command).
6. Determine target revision `X` and document rationale.
7. Execute rollback/forward to `X` using service migration entrypoint.
8. Run mandatory baseline rehydration/backfill for affected tables/entities.
9. Validate tenant isolation and policy invariants (RLS, tenant IDs, access boundaries).
10. Run service-level smoke/contract checks.
11. Record all commands and outputs in incident log.
12. Re-enable deploys/traffic only after validation sign-off.

## 4. CI enforcement

Migration reproducibility entrypoints are enforced by:

```bash
python scripts/ci/check_migration_entrypoints.py
```

This check verifies each maintained layer service exposes:

- migration directory contract,
- executable migration entrypoint commands,
- revision-history command coverage.

Integrate this check in local verification and CI gates where reproducibility assurance is required.

## 5. Service migration entrypoint and history command matrix

Use these canonical commands for reproducibility checks and incident prep:

| Service | Entrypoint check | Revision history check |
|---|---|---|
| Layer 1 (`services/layer1-ingestion`) | `alembic -c alembic.ini current --help` | `alembic -c alembic.ini history` and `alembic -c alembic.ini heads` |
| Layer 2 (`services/layer2-extraction`) | `alembic -c alembic.ini current --help` | `alembic -c alembic.ini history` and `alembic -c alembic.ini heads` |
| Layer 3 (`services/layer3-knowledge`) | migration scripts directory exists at `src/migrations/` | `python -c "from pathlib import Path; p=Path('src/migrations'); print(len([x for x in p.iterdir() if x.is_file()]))"` |
| Layer 4 (`services/layer4-agents`) | `alembic -c alembic.ini current --help` | `alembic -c alembic.ini history` and `alembic -c alembic.ini heads` |
| Layer 5 (`services/layer5-ground-truth`) | `alembic -c alembic.ini current --help` | `alembic -c alembic.ini history` and `alembic -c alembic.ini heads` |
| Layer 6 (`services/layer6-benchmarks`) | migration scripts directory exists at `migrations/versions/` | `python -c "from pathlib import Path; p=Path('migrations/versions'); print(len([x for x in p.iterdir() if x.is_file()]))"` |

