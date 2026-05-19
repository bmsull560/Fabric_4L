# Deprecation & Legacy Inventory

This document inventories currently known legacy/deprecated paths across:

- `value-fabric/layer1-ingestion`
- `value-fabric/layer3-knowledge`
- `docs/`

The machine-readable source of truth is `docs/deprecation_register.json`.

## Inventory (human-readable)

| Feature | Code/Doc Path | Notes |
|---|---|---|
| `l1.api.health_legacy_route` | `value-fabric/layer1-ingestion/src/api/main.py` (`GET /health`) | Backward-compatible health route; prefer `/api/v1/ingestion/health`. |
| `l1.api.x_organization_id_header_fallback` | `value-fabric/layer1-ingestion/src/api/main.py` (`get_organization_id`) | `X-Organization-ID` fallback; prefer governance context/JWT tenant resolution. |
| `l3.api.query_legacy_route` | `value-fabric/layer3-knowledge/src/api/main.py` (`POST /v1/query`) | Backward-compatible route; prefer `/v1/query/graph`. |
| `l3.api.search_legacy_route` | `value-fabric/layer3-knowledge/src/api/main.py` (`POST /v1/search`) | Backward-compatible route; prefer `/v1/search/hybrid`. |
| `l3.retrieval.hybrid_search_legacy_dict_format` | `value-fabric/layer3-knowledge/src/retrieval/hybrid_search.py` | Supports old dict result format for compatibility. |
| `docs.semantic_contract.legacy_value_category_aliases` | `docs/semantic_contract.md` | Legacy category aliases retained temporarily. |
| `l3.api.dependencies_tenant_legacy_shim` | `services/layer3-knowledge/src/api/dependencies_tenant.py` | Compatibility shim only; prefer `dependencies_tenant_secured.py`; hard removal target 2026-09-30. |

## Enforcement

- CI check: `python3 scripts/ci/check_deprecations.py`
- Make target: `make check-deprecations` (included in `make verify`)
- Override (explicit only): `DEPRECATION_ALLOW_OVERDUE=true`
