# Layer 1 Failure Inventory (Wave 0)

## Service-Local Tests (`services/layer1-ingestion/tests/`)

### Collection Errors (2)
| File | Error | Classification |
|------|-------|---------------|
| `tests/unit/test_quality_gate.py` | Collection error when run with full suite; passes individually | import/path conflict |
| `tests/unit/test_smart_router.py` | Collection error when run with full suite; passes individually | import/path conflict |

### Failed Tests (~143)
| Test File | Failure | Count | Classification |
|-----------|---------|-------|---------------|
| `tests/unit/test_celery_tasks.py` | `ModuleNotFoundError: No module named 'celery'` | ~20 | missing dependency |
| `tests/unit/test_h03_security_config.py` | `ModuleNotFoundError: No module named 'shared.config'; 'shared' is not a package` | ~6 | import/path drift |
| `tests/crawler/test_smart_router.py` | `AssertionError: /page.html should route to RouteType.FAST` | 1 | ingestion pipeline bug |
| `tests/crawler/test_smart_router.py` | `test_detect_spa_react_marker - assert False is True` | 1 | ingestion pipeline bug |

### Runtime Errors (~16)
| Test File | Error | Count | Classification |
|-----------|-------|-------|---------------|
| `tests/crawler/test_httpx_crawler.py` | `ImportError: Using http2=True, but the 'h2' package is not installed` | ~6 | missing dependency |
| `tests/unit/test_batch_operations.py` | Various runtime errors | ~8 | ingestion pipeline bug / schema drift |

## Repo-Wide Tests Touching Layer 1

From previous `pytest tests/` run (repo root):
- `tests/ci/test_check_no_nul_bytes.py` - `ImportError: cannot import name 'files_with_nul'` (unrelated to Layer 1)
- `tests/contract/test_layer1_compatibility_deprecation_contract.py` - contract drift (ADR-required)
- Many other repo-wide failures are unrelated to Layer 1

## Proposed Wave Ordering

1. **Wave 1: Import/Path Stabilization** - Fix collection errors, shared.config import, namespace package conflicts
2. **Wave 4: Pipeline Correctness** - Fix smart_router assertions, batch_operations errors
3. **Wave 9: Environment/Deps** - Fix missing celery, h2 dependencies
4. **Wave 2: API Contract** - Address deprecation date drift (ADR-required)
