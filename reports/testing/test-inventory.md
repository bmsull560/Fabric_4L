# Test Inventory

Generated: 2026-05-04 (Autonomous Test Assurance Agent)

## Backend Tests
| Layer | Unit Tests | Integration Tests | Security Tests | E2E Tests |
|-------|-----------|-------------------|----------------|-----------|
| layer1-ingestion | TBD | TBD | TBD | TBD |
| layer2-extraction | TBD | TBD | TBD | TBD |
| layer3-knowledge | TBD | TBD | TBD | TBD |
| layer4-agents | TBD | TBD | TBD | TBD |
| layer5-ground-truth | 3 test files | TBD | TBD | TBD |
| layer6-benchmarks | 2 test files | TBD | TBD | TBD |
| tests/ (shared) | 52 test_*.py files | Multiple categories | Security suite | Backend-integrated |
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
- Repository uses 6-layer architecture (layer1-ingestion through layer6-benchmarks)
- Frontend uses React + Vite + Playwright for E2E
- Backend uses pytest with extensive marker system (mandatory, unit, integration, e2e, contract, security, tenant_boundary, auth_boundaries, cross_tenant_write, etc.)
- Auth pattern: Depends(get_current_user) with TokenClaims in layer5
- Database: AsyncSession with RLS enforcement via get_db_from_context and SET LOCAL app.tenant_id
- OpenAPI specs available in contracts/openapi/ for layer1, layer2, layer3
- Migrations found in all 6 services (layer1-ingestion, layer2-extraction, layer3-knowledge, layer4-agents, layer5-ground-truth, layer6-benchmarks)
- RLS policies enforced via SET LOCAL app.tenant_id in layer4-agents and layer5-ground-truth
- Phase 2 E2E validation milestone complete: 78 interaction-level tests across P0 production-gate suites
- Deep test infrastructure: e2e/helpers/validation-program.ts, e2e/fixtures/deep-test-data.ts
