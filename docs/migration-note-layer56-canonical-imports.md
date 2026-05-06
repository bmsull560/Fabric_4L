# Migration note: Layer 5/6 canonical imports

Date: 2026-05-06

## Moved/canonicalized modules

Layer 6 service-local modules are now compatibility shims, with canonical sources in `value_fabric/layer6/*`:

- `services/layer6-benchmarks/src/config.py` -> `value_fabric/layer6/config.py`
- `services/layer6-benchmarks/src/database.py` -> `value_fabric/layer6/database.py`
- `services/layer6-benchmarks/src/shared_bootstrap.py` -> `value_fabric/layer6/shared_bootstrap.py`
- `services/layer6-benchmarks/src/metrics/prometheus_metrics.py` -> `value_fabric/layer6/metrics/prometheus_metrics.py`

## Compatibility period

- Legacy imports from `services/layer6-benchmarks/src/*` remain supported through **2026-09-30**.
- After that date, shim modules may be removed and direct canonical imports will be required.

## Required import pattern

Prefer:

- `from value_fabric.layer6.config import ...`
- `from value_fabric.layer6.database import ...`
- `from value_fabric.layer6.shared_bootstrap import ...`
- `from value_fabric.layer6.metrics.prometheus_metrics import ...`
