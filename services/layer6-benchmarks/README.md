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
| GET | `/health` | Health check |
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

Canonical runtime package: `value_fabric/layer6`.

`services/layer6-benchmarks/src/` contains service wiring plus compatibility shims for legacy imports.
Use canonical imports (`value_fabric.layer6.*`) for all new code.


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
