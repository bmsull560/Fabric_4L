# Test Inventory

Generated: 2026-05-04 (Autonomous Test Assurance Agent — Phase 1 Complete)
Collection Status: **4623 tests collected, 0 collection errors**

## Backend Tests
| Layer | Unit Tests | Integration Tests | Security Tests | E2E Tests |
|-------|-----------|-------------------|----------------|-----------|
| layer1-ingestion | 12 test files | 3 test files | 2 test files | N/A |
| layer2-extraction | 4 test files | 2 test files | 1 test file | N/A |
| layer3-knowledge | 14 test files | 4 test files | 3 test files | N/A |
| layer4-agents | 25+ test files | 5 test files | 8 test files | N/A |
| layer5-ground-truth | 3 test files | 1 test file | 1 test file | N/A |
| layer6-benchmarks | 2 test files | N/A | N/A | N/A |
| tests/ (shared) | ~40 test files | 10 test files | 52 test files | 3 test files |
| packages/shared | 16 test files | Contract tests | Security tests | MCP gateway tests |
| packs (7 packs) | 21 test files | Formula/ontology tests | Pack integrity | N/A |
| sdk/python | 7 test files | Integration tests | N/A | N/A |
| services/api | 10 test files | Auth/governance tests | Production safety | N/A |

## Frontend Tests
| Category | Count | Framework |
|----------|-------|-----------|
| Unit/Component | 51 .test.ts files | Vitest |
| Integration | Contract tests (12 files) | Vitest |
| E2E | 57 .spec.ts files | Playwright |
| Deep Validation | 7 -deep.spec.ts files | Playwright (Phase 2 complete) |

## CI Gates
| Gate | Status | Command |
|------|--------|---------|
| pytest mandatory | Configured | pytest -m mandatory |
| playwright e2e | Configured | pnpm run test:e2e |
| playwright deep validation | Configured | pnpm run test:e2e:validation:deep |
| security gates | Configured | .github/workflows/security-gates.yml |
| contract compliance | Configured | .github/workflows/contract-compliance.yml |
| test-mandatory | Configured | .github/workflows/test-mandatory.yml |

## Discovery Notes
- **Repository uses 6-layer architecture** (layer1-ingestion through layer6-benchmarks)
- **Frontend uses React + Vite + Playwright** for E2E
- **Backend uses pytest** with extensive marker system (mandatory, unit, integration, e2e, contract, security, tenant_boundary, auth_boundaries, cross_tenant_write, etc.)
- **Auth pattern**: GovernanceMiddleware with JWT/API-key/X-Service-Auth resolution; FastAPI Depends with role/permission checks
- **Database**: AsyncSession with RLS enforcement via `SET LOCAL app.tenant_id`
- **OpenAPI specs** available in contracts/openapi/ for layer1, layer2, layer3
- **Migrations found** in all 6 services
- **RLS policies** enforced via SET LOCAL app.tenant_id in layer4-agents and layer5-ground-truth
- **Phase 2 E2E validation milestone complete**: 78 interaction-level tests across P0 production-gate suites
- **Collection errors fixed in this session**:
  1. `pytest_plugins` in non-top-level conftest (tests/layer1, tests/layer4)
  2. `pdf2image` missing in test_pdf_adapter.py
  3. `protego` missing in test_pii_scanner.py
  4. `playwright` missing in test_playwright_crawler.py
  5. `global_exception_handler` import path in test_exception_handlers.py
  6. `_extract_tenant_id` import path in test_tenant_context_extraction.py
  7. `_extract_tenant_id` import path in test_tenant_isolation.py
  8. `pytest_plugins` double-registration conflict in tests/conftest.py
  9. `redis` / `psutil` missing in services/layer3-knowledge/tests/conftest.py
  10. `MagicMock(spec=Request)` falsy issue in test_tenant_isolation.py
  11. `async with` mock fix for mock_neo4j_driver in test_tenant_isolation.py
  12. `opentelemetry` / `psycopg2` / `asyncpg` / `jinja2` / `botocore` / `langgraph.checkpoint.postgres` missing across layer1/2/4 conftests
  13. Import file mismatch across services fixed with `--import-mode=importlib`
  14. Idempotent opentelemetry stub strategy across conftests to prevent partial-stub conflicts
