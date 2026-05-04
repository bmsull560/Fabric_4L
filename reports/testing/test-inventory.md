# Test Inventory

Generated: 2026-05-04

## Backend Tests
| Layer | Unit Tests | Integration Tests | Security Tests | E2E Tests |
|-------|-----------|-------------------|----------------|-----------|
| layer1-ingestion | TBD | TBD | TBD | TBD |
| layer2-extraction | TBD | TBD | TBD | TBD |
| layer3-knowledge | TBD | TBD | TBD | TBD |
| layer4-agents | TBD | TBD | TBD | TBD |
| layer5-ground-truth | 3 test files | TBD | TBD | TBD |
| layer6-benchmarks | 1 test file | TBD | TBD | TBD |
| tests/ (shared) | 60+ test files | Multiple categories | Security suite | Backend-integrated |

## Frontend Tests
| Category | Count | Framework |
|----------|-------|-----------|
| Unit/Component | 1 file (utils.test.ts) | Vitest |
| Integration | TBD | Vitest |
| E2E | 19 spec files | Playwright |

## CI Gates
| Gate | Status | Command |
|------|--------|---------|
| pytest mandatory | Configured | pytest -m mandatory |
| playwright e2e | Configured | pnpm run test:e2e |
| security gates | Configured | .github/workflows/security-gates.yml |
| contract compliance | Configured | .github/workflows/contract-compliance.yml |

## Discovery Notes
- Repository uses 6-layer architecture (layer1-ingestion through layer6-benchmarks)
- Frontend uses React + Vite + Playwright for E2E
- Backend uses pytest with extensive marker system (mandatory, unit, integration, e2e, contract, security, tenant_boundary, etc.)
- Auth pattern: Depends(get_current_user) with TokenClaims in layer5
- Database: AsyncSession with RLS enforcement via get_db_from_context
- OpenAPI specs available for all 6 layers in contracts/openapi/
- No SQL migration files discovered (may use Alembic or other migration tool)
- 60+ Python test files in tests/ directory covering agents, arch, backend_integrated, cache, chaos, ci, config, contract, contracts, e2e, evals, gitops, integration, k8s, performance, quarantine, release, scripts, security, shared, state, tools
