# Layer 3 service source inventory (`services/layer3-knowledge/src`)

Source-of-truth policy references:

- `docs/reference/layer-runtime-path-governance.md`
- `docs/governance/compatibility-debt-registry.md`

## Classification rules

- **shim-only required**: mirrored compatibility path that must thinly delegate to `value_fabric.layer3...`.
- **allowed service-local exception**: explicitly allowed service wrapper locations (`api/`, `agents/`, `cache/`, `docs/`, `metrics/`, top-level `config.py`, and service-local migrations).
- **canonical implementation required in `value_fabric/layer3`**: any runtime module under `services/layer3-knowledge/src` that is neither a sanctioned exception nor a compatibility shim (none currently).

## Per-path inventory

### shim-only required

- `services/layer3-knowledge/src/__init__.py`
- `services/layer3-knowledge/src/analytics/*.py`
- `services/layer3-knowledge/src/auth/*.py`
- `services/layer3-knowledge/src/backup/*.py`
- `services/layer3-knowledge/src/config/*.py`
- `services/layer3-knowledge/src/db/*.py`
- `services/layer3-knowledge/src/gateway/*.py`
- `services/layer3-knowledge/src/ingestion/*.py`
- `services/layer3-knowledge/src/load_balancing/*.py`
- `services/layer3-knowledge/src/logging_config.py`
- `services/layer3-knowledge/src/models/*.py`
- `services/layer3-knowledge/src/performance/*.py`
- `services/layer3-knowledge/src/rate_limiting/*.py`
- `services/layer3-knowledge/src/retrieval/*.py`
- `services/layer3-knowledge/src/schema/*.py`
- `services/layer3-knowledge/src/security/*.py`
- `services/layer3-knowledge/src/services/*.py`
- `services/layer3-knowledge/src/tracing/*.py`

### allowed service-local exception

- `services/layer3-knowledge/src/api/**/*.py`
- `services/layer3-knowledge/src/agents/**/*.py`
- `services/layer3-knowledge/src/cache/**/*.py`
- `services/layer3-knowledge/src/docs/**/*.py`
- `services/layer3-knowledge/src/metrics/**/*.py`
- `services/layer3-knowledge/src/config.py`
- `services/layer3-knowledge/src/migrations/**/*.py`

All allowed service-local exception modules must retain an explicit module docstring with owner (`layer3-knowledge`) and migration target date (`2026-09-30`) while exceptions remain.

### canonical implementation required in `value_fabric/layer3`

- None currently.
