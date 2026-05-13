# Layer 6: Benchmark Service
> Routing/versioning reference: see the canonical [Service Routing and API Version Matrix](../../docs/reference/service-routing-and-api-version-matrix.md).

> Runtime path governance: net-new layer logic must go to canonical runtime packages in `value_fabric/layer*/`. See [`docs/reference/layer-runtime-path-governance.md`](../../docs/reference/layer-runtime-path-governance.md).

Standalone service for comparative intelligence and peer benchmarking.

## Overview

The Benchmark Service provides curated datasets for peer comparison and statistical validation. Unlike Ground Truth (validated claims), benchmarks are reference datasets for comparative analysis.

## Features

- **Benchmark Dataset Management**: By industry and segment
- **Peer Comparison APIs**: Percentile ranking against peers
- **Range Validation**: Sanity checks against benchmark ranges
- **Manufacturing Reference Dataset**: Included as seed data

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Process liveness only (no dependency checks) |
| GET | `/ready` | Dependency readiness (DB/connectivity/config checks) |
| GET | `/v1/benchmarks/datasets` | List datasets |
| GET | `/v1/benchmarks/datasets/{id}` | Get dataset details |
| POST | `/v1/benchmarks/compare` | Peer comparison |
| POST | `/v1/benchmarks/validate` | Range validation |
| GET | `/v1/benchmarks/industries` | List industries |

## Quick Start

```bash
# Run with Docker
docker build -t layer6-benchmarks .
docker run -p 8006:8006 layer6-benchmarks

# Or run locally
cd services/layer6-benchmarks
python -m uvicorn src.api.main:app --port 8006
```

## Integration

Layer 6 integrates with Layer 4 Agents via the `IBenchmarkClient` interface (see `layer4-agents/src/interfaces/benchmark_client.py`).

## Source ownership

Canonical runtime location for Layer 6 implementation logic: `value_fabric/layer6/`.

`services/layer6-benchmarks/` remains the deployable service root (Docker, migrations, tests, packaging).
If compatibility wrappers exist under `services/layer6-benchmarks/src/`, they must stay thin re-exports only
and be enforced by:

- `scripts/mirrored_files.json`
- `scripts/check_mirrored_files.py`
- `scripts/ci/check_layer6_wrapper_drift.py`

Use canonical imports (`value_fabric.layer6.*`) for all new Layer 6 runtime code.


## Dependency locking

- Canonical Python lock artifact for this service: `uv.lock` (source of truth).
- Regenerate lock state after dependency edits in `pyproject.toml`:

```bash
cd services/layer6-benchmarks
uv lock
uv export --locked --no-dev --format requirements-txt -o requirements.lock
```

- CI and Docker builds must consume `uv.lock` deterministically (`uv sync --locked` or equivalent).


## Migration reproducibility reference

- `docs/reference/migration-reproducibility-invariants.md` (mandatory migration invariants and incident-state reconstruction)

## Operational observability

See `docs/operations/layer6/observability.md` for Layer 6 metrics, SLO indicators, and troubleshooting.

## Health and readiness semantics

- `/health` is a **lightweight liveness probe**: it reports whether the process is up and able to serve HTTP. It must not perform expensive or flaky downstream checks.
- `/ready` is a **readiness probe**: it validates critical dependencies and startup invariants such as database connectivity, graph connectivity, and required runtime configuration.
- Deterministic failure behavior: if any critical readiness dependency fails, `/ready` returns HTTP `503` with a stable not-ready payload; `/health` remains `200` unless the process itself is unhealthy.
- Alerting expectations:
  - Page on sustained `/ready` failures because the service should be removed from traffic until dependencies recover.
  - Treat `/health` failures as process-level incidents; investigate restart loops or repeated liveness failures immediately.

## Environment variables (Layer 6)

The Layer 6 service uses a centralized Pydantic settings module at `value_fabric/layer6/settings.py` with a compatibility shim at `services/layer6-benchmarks/src/settings.py`. Startup should call `validate_layer6_startup_settings()` to fail fast on missing or invalid critical configuration.

| Variable | Required | Default | Example | Security notes |
|---|---|---|---|---|
| `ENVIRONMENT` | Optional | `development` | `production` | In `staging`/`production`, strict TLS validation is enforced for DB/Neo4j URLs. |
| `TESTING` | Optional | `false` | `true` | Test-only toggle; do not enable in production deployments. |
| `AUTH_REQUIRED` | Optional | `true` | `true` | Keep enabled in production to prevent unauthenticated access paths. |
| `DATABASE_URL` | Required | none | `postgresql://app:***@postgres:5432/benchmarks?sslmode=verify-full` | Must be PostgreSQL. In `staging`/`production`, `sslmode` is required and must be `require`, `verify-ca`, or `verify-full`. Treat as sensitive credential material. |
| `NEO4J_URI` | Required | none | `neo4j+s://neo4j.example.com:7687` | In `staging`/`production`, only TLS schemes (`neo4j+s://` or `bolt+s://`) are accepted. |
| `NEO4J_USER` | Optional | `neo4j` | `app_reader` | Non-secret identifier; use least privilege accounts. |
| `NEO4J_PASSWORD` | Required | none | `<vault-managed-secret>` | Secret; minimum 12 characters enforced. Never commit to source control. |
| `JWT_SECRET` | Required | none | `<openssl rand -hex 32>` | Secret; minimum 32 characters enforced. Rotation invalidates existing JWTs. |
| `API_KEY_HMAC_SECRET` | Required | none | `<openssl rand -hex 32>` | Secret; minimum 32 characters enforced. Required for API key verification. |
| `SERVICE_AUTH_SECRET` | Required | none | `<openssl rand -hex 32>` | Secret; minimum 32 characters enforced. Required for service-to-service authentication. |
| `ALLOW_INSECURE_DEV_AUTH_BYPASS` | Optional | `false` | `true` | Local-dev only. Layer 6 startup rejects this flag in `staging` or `production`. |
| `DEV_AUTH_BYPASS` | Optional | `false` | `true` | Test-only. Keep isolated to test harnesses; startup rejects it in production-like environments. |
| `AUTH_BYPASS_ENABLED` | Optional | `false` | `true` | Local-dev only compatibility flag. Never ship it in shared deployment config. |
| `JWT_FALLBACK_TO_QUERY_PARAM` | Optional | `false` | `true` | Test-only fallback. Startup rejects it in production-like environments. |
| `ALLOW_EPHEMERAL_ENCRYPTION` | Optional | `false` | `true` | Local-dev only. Production-like startup rejects it and Layer 4 runtime no longer permits it there. |
| `ALLOW_DEV_AUTH_BYPASS` | Optional | none | `I_UNDERSTAND_RISK` | Legacy explicit opt-in token for test harnesses only. Production-like startup rejects it. |
