# Layer 5 — Ground Truth
> Routing/versioning reference: see the canonical [Service Routing and API Version Matrix](../../docs/reference/service-routing-and-api-version-matrix.md).

> Runtime path governance: net-new Layer 5 logic must go to `services/layer5-ground-truth/src/layer5_ground_truth`. See [`docs/reference/layer-runtime-path-governance.md`](../../docs/reference/layer-runtime-path-governance.md).

> **Evidence-backed, CFO-defensible facts for the Value Fabric platform.**

Layer 5 is the epistemic foundation of the Value Fabric stack. It stores, validates, and governs factual claims extracted from customer conversations, documents, and web content. Every claim in the system has a traceable provenance, a confidence score, and a maturity level that reflects how thoroughly it has been validated.

---

## Architecture Position

```
L1 Ingestion → L2 Extraction → L3 Knowledge Graph → L4 Agents
                                         ↑
                              L5 Ground Truth (this service)
```

Layer 5 sits alongside Layer 3. Approved TruthObjects are synced to the Knowledge Graph as `:GroundTruth` nodes, where they ground the claims made by Layer 4 agents in the ROI models and executive narratives they produce.

---

## Core Concepts

### TruthObject

A `TruthObject` is a structured, evidence-backed factual claim. Each object has:

| Field | Description |
|-------|-------------|
| `claim` | The plain-language factual statement |
| `claim_type` | Semantic category (e.g., `efficiency_gain`, `cost_savings_baseline`) |
| `value` | Structured value payload (amount, unit, period) |
| `confidence` | 0.0–1.0 score from the extraction model |
| `status` | Current validation state (see state machine below) |
| `maturity_level` | 0–5 maturity ladder position |
| `sources` | List of evidence sources (call transcripts, documents, web pages) |
| `applies_to` | Scoping context (opportunity_id, account_id, persona_id) |
| `approved_by` | Identity of the human approver (required for APPROVED status) |
| `freshness` | Timestamp of the most recent supporting evidence |

### Validation State Machine

```
EXTRACTED ──► SUPPORTED ──► CORROBORATED ──► APPROVED ──► (OPERATIONALIZED)
                │                │                │
                └────────────────┴────────────────┴──► DISPUTED ──► CORROBORATED
```

| Transition | Action | Preconditions |
|------------|--------|---------------|
| `extracted → supported` | `advance_supported` | ≥ 1 source, confidence ≥ threshold |
| `supported → corroborated` | `advance_corroborated` | ≥ 2 independent sources |
| `corroborated → approved` | `approve` | Human actor, `approved_by` required |
| `any → disputed` | `dispute` | `dispute_reason` required |
| `disputed → corroborated` | `resolve_dispute` | Human actor |
| `approved → operationalized` | `operationalize` | Referenced in downstream artefact |

### Maturity Ladder

| Level | Name | Description |
|-------|------|-------------|
| 0 | Raw | Captured but not processed |
| 1 | Extracted | AI-structured from source content |
| 2 | Supported | ≥ 1 linked evidence source |
| 3 | Corroborated | ≥ 2 independent sources |
| 4 | Approved | Human-validated |
| 5 | Operationalized | Used in board-level decision |

---

## API

The service runs on **port 8005** and exposes a fully documented OpenAPI interface.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/truths` | Create a TruthObject |
| `GET` | `/api/v1/truths` | List with filters (status, claim_type, maturity, confidence) |
| `GET` | `/api/v1/truths/{id}` | Get full detail with sources and audit trail |
| `POST` | `/api/v1/truths/{id}/validate` | Apply a state transition |
| `POST` | `/api/v1/truths/{id}/sources` | Add an evidence source |
| `GET` | `/api/v1/truths/{id}/audit` | Full immutable audit log |
| `DELETE` | `/api/v1/truths/{id}` | Soft delete |
| `POST` | `/api/v1/truths/sync-kg` | Bulk sync approved objects to Layer 3 KG |
| `GET` | `/api/v1/maturity-ladder` | Reference: full ladder definition |
| `GET` | `/api/v1/health` | Health check |

Interactive docs: `http://localhost:8005/docs`

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or SQLite for development/testing)
- Layer 3 Knowledge Graph service (optional — sync is best-effort)

### Local Development

```bash
cd services/layer5-ground-truth

# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export DATABASE_URL="sqlite+aiosqlite:///./ground_truth.db"
export DATABASE_URL_SYNC="sqlite:///./ground_truth.db"
export LAYER3_BASE_URL="http://localhost:8001"

# Run database migrations
alembic upgrade head

# Start the service
uvicorn layer5_ground_truth.api.main:app --host 0.0.0.0 --port 8005 --reload
```

### Docker Compose

Add to the root `docker-compose.yml`:

```yaml
layer5-ground-truth:
  build: ./services/layer5-ground-truth
  ports:
    - "8005:8005"
  environment:
    DATABASE_URL: ${DATABASE_URL}
    DATABASE_URL_SYNC: ${DATABASE_URL_SYNC}
    LAYER3_BASE_URL: http://layer3-knowledge:8001
    LAYER3_SYNC_ENABLED: "true"
  depends_on:
    - postgres
    - layer3-knowledge
```


### CI Runtime / Test Matrix (required before merge)

Layer 5 now includes dedicated required CI jobs in `PR Checks`:

| Job name | Scope | Command(s) | Typical runtime |
|---|---|---|---|
| `Layer 5 - Source Contract` | Prevent Layer 5 source-of-truth and shim drift | `python scripts/check_no_duplicate_modules.py` | ~1 minute |
| `Layer 5 - Tenant Isolation Regression` | Tenant invariants and hostile cross-tenant access regression | `uv run pytest -v --tb=short tests/test_tenant_id_consistency.py tests/test_api.py::TestGetTruth::test_org_isolation` | ~2-4 minutes |
| `Layer 5 - Contract Shape Regression` | OpenAPI drift check + Layer 5 contract suite + endpoint response-shape snapshots | `uv run python scripts/check_openapi_contract.py`<br>`uv run pytest -v --tb=short ../../tests/contract/test_layer5_contract.py`<br>`uv run pytest -v --tb=short tests/test_endpoint_response_shape_snapshots.py` | ~4-7 minutes |

These checks should be configured as required branch-protection status checks on `main` so merges are blocked if any Layer 5 regression appears.

### Running Tests

```bash
# All tests (uses SQLite in-memory — no external services needed)
pytest

# With coverage
pytest --cov=layer5_ground_truth --cov-report=html

# Unit tests only
pytest -m unit

# Integration tests (requires running services)
pytest -m integration
```


## Source Contract Guardrail (CI Required)

Layer 5 enforces a CI guard that blocks source-of-truth drift between:

- `services/layer5-ground-truth/src/layer5_ground_truth` (canonical runtime source-of-truth)
- `value_fabric/layer5` (compatibility shim package)

Run locally before tests:

```bash
python scripts/check_no_duplicate_modules.py
```

If the check fails, keep the canonical implementation in `services/layer5-ground-truth/src/layer5_ground_truth` and update `value_fabric/layer5` to thin compatibility shims.

---

## OpenAPI Contract Drift Guardrail (Canonical Command Path)

Layer 5 uses one canonical command path to validate OpenAPI contract drift so local and CI behavior stay identical:

```bash
python services/layer5-ground-truth/scripts/check_openapi_contract.py
```

What this command does:

1. Generates OpenAPI from canonical runtime module `services/layer5-ground-truth/src/layer5_ground_truth/api/main.py` (`layer5_ground_truth.api.main:app`).
2. Normalizes generated and committed JSON with deterministic ordering/format.
3. Diffs normalized output against `contracts/openapi/layer5-ground-truth.json`.
4. Exits non-zero on mismatch.

CI runs this same command in `.github/workflows/contract-compliance.yml` as part of Layer 5 OpenAPI drift detection.

---

## Contract and Snapshot Remediation Playbook

When `Layer 5 - Contract Shape Regression` fails, use this sequence:

1. **Regenerate and inspect OpenAPI locally**
   ```bash
   uv run python scripts/check_openapi_contract.py
   ```
   - If drift is valid and intentional, regenerate `contracts/openapi/layer5-ground-truth.json` from
     `services/layer5-ground-truth/src/layer5_ground_truth/api/main.py` and commit the contract update with the implementation change.
2. **Re-run Layer 5 contract tests**
   ```bash
   uv run pytest -v --tb=short ../../tests/contract/test_layer5_contract.py
   ```
3. **Re-run endpoint response-shape snapshots**
   ```bash
   uv run pytest -v --tb=short tests/test_endpoint_response_shape_snapshots.py
   ```
   - Update `tests/snapshots/layer5_response_shapes.json` only when the response-shape change is intentional and contract-reviewed.

### Required reviewers for contract/snapshot changes

Any PR that changes either:
- `contracts/openapi/layer5-ground-truth.json`, or
- `services/layer5-ground-truth/tests/snapshots/layer5_response_shapes.json`

must include **all** of the following reviewers before merge:
- **Layer 5 service owner/maintainer**
- **Platform contracts owner**
- **QA or release governance reviewer**

This keeps API contract evolution explicit, auditable, and aligned with downstream consumers.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./ground_truth.db` | Async DB URL |
| `DATABASE_URL_SYNC` | `sqlite:///./ground_truth.db` | Sync DB URL (Alembic) |
| `LAYER3_BASE_URL` | `http://localhost:8001` | Layer 3 API base URL |
| `LAYER3_SYNC_ENABLED` | `true` | Enable KG sync on approval |
| `LAYER3_API_KEY` | — | Bearer token for Layer 3 |
| `LAYER3_TIMEOUT_SECONDS` | `10` | HTTP timeout for Layer 3 calls |
| `MIN_CONFIDENCE_FOR_SUPPORTED` | `0.5` | Confidence threshold for SUPPORTED |
| `MIN_SOURCES_FOR_CORROBORATED` | `2` | Source count for CORROBORATED |
| `AUTO_ADVANCE_TO_SUPPORTED` | `true` | Auto-advance on source add |
| `DEBUG` | `false` | Enable debug mode + auto table creation |
| `API_PORT` | `8005` | Service port |

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Generate a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Downgrade one step
alembic downgrade -1

# Show current revision
alembic current
```

---

## Layer 3 Integration

When a TruthObject reaches **APPROVED** status, Layer 5 automatically syncs it to the Layer 3 Knowledge Graph as a `:GroundTruth` node with the relationship:

```cypher
(GroundTruth)-[:GROUNDS]->(Capability | Outcome | ValueDriver | Persona)
```

Sync is **best-effort** — Layer 5 remains fully operational if Layer 3 is unavailable. Failed syncs can be retried via `POST /api/v1/truths/sync-kg`.

---

## Observability Contract (Logs + Metrics)

Layer 5 validation and Layer 3 sync paths must emit audit-safe, structured observability events even on failure paths (for example: invalid state transitions, retry exhaustion, and partial sync failures).

### Required structured log fields

When context applies, structured log events include:

- `request_id`: request correlation identifier (nullable for background/internal flows).
- `tenant_id`: tenant UUID from authenticated context.
- `truth_object_id`: Layer 5 TruthObject UUID.
- `transition`: transition context (for example `supported->corroborated`, `approved->kg_sync`).
- `sync_status`: sync lifecycle status (`pending`, `success`, `failed`, `not_attempted`, etc.).

### Governed metric names and labels

- `validation_latency_seconds{transition=...}`  
  Histogram for claim validation transition latency.
- `validation_transition_failures_total{transition=...,reason=...}`  
  Counter for rejected or failed validation transitions.
- `kg_sync_total{status=...}`  
  Counter for Layer 3 sync attempts/outcomes at transport/application level.
- `kg_sync_outcomes_total{sync_status=...,transition=...}`  
  Counter for transition-aware sync outcomes including retries/failures.

Authoritative schema reference (must remain aligned with tests and dashboards):

- `docs/reference/layer5-observability-schema.md`

Operational runbooks:

- `docs/runbooks/operational/alerting-source-of-truth.md`
- `docs/troubleshooting/runbooks/application/stale-ground-truth.md`

---

## File Structure

```
layer5-ground-truth/
├── src/
│   ├── api/
│   │   ├── main.py          # FastAPI app factory + lifespan
│   │   ├── router.py        # All API endpoints
│   │   └── schemas.py       # Pydantic request/response models
│   ├── models/
│   │   └── truth_object.py  # SQLAlchemy models + enums
│   ├── services/
│   │   ├── state_machine.py # ValidationStateMachine
│   │   └── truth_service.py # CRUD service layer
│   ├── integration/
│   │   └── layer3_client.py # Layer 3 KG HTTP client
│   ├── migrations/
│   │   ├── env.py           # Alembic environment
│   │   └── versions/        # Migration scripts
│   ├── config.py            # Pydantic Settings
│   └── database.py          # Async SQLAlchemy engine + session
├── tests/
│   ├── conftest.py          # Fixtures (SQLite in-memory)
│   ├── test_state_machine.py
│   └── test_api.py
├── Dockerfile
├── alembic.ini
├── pyproject.toml
├── pytest.ini
└── README.md
```

## Source ownership

Canonical runtime package: `services/layer5-ground-truth/src/layer5_ground_truth`.

`value_fabric/layer5` is compatibility-only. Prefer canonical imports (`layer5_ground_truth.*`) for Layer 5 runtime modules.

`services/layer5-ground-truth/` owns deployment and operational wrapper concerns.

## TruthObject transition concurrency behavior

Validation transitions are handled by `ValidationStateMachine` and routed through `validate_truth_object`.

- Transition handlers/services:
  - `src/layer5_ground_truth/services/truth_service.py::validate_truth_object`
  - `src/layer5_ground_truth/services/state_machine.py` transition methods (`advance_to_supported`, `advance_to_corroborated`, `approve`, `dispute`, `resolve_dispute`, `mark_operationalized`) and `_apply_transition`.
- Allowed concurrent behavior for the same TruthObject:
  - **Optimistic status check:** `_apply_transition` performs a conditional `UPDATE ... WHERE id + tenant_id + expected_status + deleted_at IS NULL`.
  - **Last-write rejection:** if another request has already transitioned the object, rowcount is 0 and `TransitionConflictError` is raised.
  - **Deterministic conflict response:** API returns HTTP 409 with stable error shape:
    - `{"detail": {"code": "TRANSITION_CONFLICT", "message": "..."}}`
  - **No partial audit writes on conflict:** validation event/history are written only after the guarded status update succeeds.
  - **Idempotent retry guidance:** callers may safely retry after conflict by re-fetching the TruthObject and re-evaluating allowed actions against current status.
- Tenant isolation:
  - All transition reads and writes are tenant-scoped (`get_truth_object` filter + guarded update includes `tenant_id`).


## Migration reproducibility reference

- `docs/reference/migration-reproducibility-invariants.md` (mandatory migration invariants and incident-state reconstruction)
