# Layer 3 API route ownership

Canonical ownership map during monolith decomposition:

- `value_fabric/layer3/api/routes/system.py` owns `/health`, `/health/detailed`, `/metrics`.
- `value_fabric/layer3/api/routes/query_search.py` owns GraphRAG and hybrid search business logic.
- `value_fabric/layer3/api/routes/compat_aliases.py` owns legacy route aliases (`/v1/graphrag`, `/v1/query`, `/v1/search`) and delegates to canonical implementations.
- `value_fabric/layer3/api/routes/entities.py` owns canonical entity browser endpoints (`/v1/entities*`, `/v1/entity/traverse`).
- `value_fabric/layer3/api/routes/entity_compat.py` owns temporary compatibility logic for legacy entity-context semantics.

`value_fabric/layer3/api/app_monolith.py` is bootstrap/composition only and must not own business endpoint logic.
