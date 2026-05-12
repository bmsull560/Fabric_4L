# Layer 5 — Ground Truth
> Routing/versioning reference: see the canonical [Service Routing and API Version Matrix](../../docs/reference/service-routing-and-api-version-matrix.md).

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
| `Layer 5 - Duplicate Module Detection` | Prevent duplicate runtime module drift in Layer 5 trees | `python scripts/check_no_duplicate_modules.py` | ~1 minute |
| `Layer 5 - Tenant Isolation Regression` | Tenant invariants and hostile cross-tenant access regression | `uv run pytest -v --tb=short tests/test_tenant_id_consistency.py tests/test_api.py::TestGetTruth::test_org_isolation` | ~2-4 minutes |
| `Layer 5 - Contract Shape Regression` | Model registry and state transition contract-shape coverage | `uv run pytest -v --tb=short tests/test_model_registry.py tests/test_state_machine.py` | ~2-4 minutes |

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


## Duplicate Module Guardrail (CI Required)

Layer 5 enforces a CI guard that blocks duplicate package roots or same-named modules between:

- `value_fabric/layer5` (canonical runtime source-of-truth)
- `services/layer5-ground-truth/src/layer5_ground_truth` (service wrapper package)

Run locally before tests:

```bash
python scripts/check_no_duplicate_modules.py
```

If the check fails, remove or rename the duplicate under `services/layer5-ground-truth/src/layer5_ground_truth` and keep the canonical implementation in `value_fabric/layer5`.

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

Canonical runtime package: `value_fabric/layer5`.

`services/layer5-ground-truth/` owns deployment and operational wrapper concerns. Prefer canonical imports (`value_fabric.layer5.*`) for runtime modules.
