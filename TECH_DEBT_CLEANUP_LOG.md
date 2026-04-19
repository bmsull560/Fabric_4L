# Technical Debt Cleanup Report
## Fabric_4L Repository

### BASELINE METRICS (Pre-Cleanup)
| Metric | Count |
|--------|-------|
| Python files (all source) | ~400 |
| Layer 1 (ingestion) | 32 files |
| Layer 2 (extraction) | 50 files |
| Layer 3 (knowledge) | 75 files |
| Layer 4 (agents) | 119 files |
| Layer 5 (ground-truth) | 26 files |
| Layer 6 (benchmarks) | 12 files |
| Shared | 21 files |
| Tests | 45 files |
| Frontend TS | 86 files |
| Frontend TSX | 142 files |

---

## PHASE 1: UNUSED IMPORTS & VARIABLES

### Layer 2 Extraction Issues Found:
1. `typing.Optional` imported but unused in `layer2_extraction/db/connection.py`
2. `.config.get_db_config` imported but unused in `layer2_extraction/db/connection.py`

### Layer 3 Knowledge Issues Found:
1. `filtered_count` unused variable in `api/main.py:2029`
2. `rel_types` unused variable in `api/main.py:3585`
3. `FORMULA_REGISTRY` imported but unused in `api/routes/value_packs.py:17`

### Layer 4 Agents Issues Found:
1. `MetricsMiddleware` imported but unused in `api/main.py:60`
2. `IntegrationStatus` imported but unused in `api/routes/integrations.py:18`

### Layer 5 Ground-Truth Issues Found:
1. `ModelDeploymentCreate` imported but unused in `model_registry_routes.py:38`
2. `PG_UUID` imported but unused in `models/model_registry.py:32`

### Layer 6 Benchmarks Issues Found:
1. `typing.List` imported but unused in `api/main.py:10`
2. `pydantic.BaseModel` imported but unused in `api/main.py:21`

---

## ACTIONS LOG

### Phase 1: Unused Imports & Variables - COMPLETED

| File | Item | Action | Status |
|------|------|--------|--------|
| layer2/db/connection.py | typing.Optional | Removed | ✅ |
| layer2/db/connection.py | get_db_config | Removed | ✅ |
| layer3/api/main.py | filtered_count | Removed | ✅ |
| layer3/api/main.py | rel_types | Removed | ✅ |
| layer3/api/routes/value_packs.py | FORMULA_REGISTRY | Removed | ✅ |
| layer4/api/main.py | MetricsMiddleware | Removed | ✅ |
| layer4/api/routes/integrations.py | IntegrationStatus | Removed | ✅ |
| layer5/api/model_registry_routes.py | ModelDeploymentCreate | Removed | ✅ |
| layer5/models/model_registry.py | PG_UUID | Removed | ✅ |
| layer6/api/main.py | typing.List | Removed | ✅ |
| layer6/api/main.py | pydantic.BaseModel | Removed | ✅ |
| layer1/crawler/decision_store.py | uuid.uuid4 | Removed | ✅ |
| layer2/extraction/llm_extractor.py | BenefitType | Removed | ✅ |
| layer4/contracts/artifacts.py | covered variable | Removed | ✅ |
| layer5/models/model_registry.py | TypeDecorator | Removed | ✅ |
| layer6/api/main.py | pydantic.Field | Removed | ✅ |

**Total Phase 1 Issues Fixed: 16**

### Bug Fixes During Cleanup
| File | Issue | Severity | Fix |
|------|-------|----------|-----|
| layer2/shared/llm_client.py | `_resolve_model_from_registry` attr name inconsistent with `_resolve_from_registry_enabled` | P0 | Fixed attribute reference in `chat_completion()` method |

### Remaining Issues to Fix (30 found)
| Layer | Count | Categories |
|-------|-------|------------|
| Layer 2 | 4 | Unused variables in extraction engine |
| Layer 4 | 13 | Unused imports in services, tools, contracts |
| Layer 6 | 1 | Unused import in benchmark routes |
| Shared | 5 | Identity, audit modules |
| Tests | 4 | Import patterns, test utilities |

**Next Phase Recommendations:**
- Phase 2: Run `ruff check --select=F401,F841` on remaining files
- Phase 3: Address dead code in shared modules (requires cross-layer impact analysis)
- Phase 4: Add linting to CI to prevent regression


