# Test Inventory - Autonomous Test Assurance Agent

## Backend Tests
| Layer | Unit Tests | Integration Tests | Security Tests | E2E Tests |
|-------|-----------|-------------------|----------------|-----------|
| Layer 1 (Ingestion) | ~15 | ~5 | 3 | 0 |
| Layer 2 (Extraction) | ~20 | ~8 | 5 | 0 |
| Layer 3 (Knowledge) | ~25 | ~10 | 8 | 2 |
| Layer 4 (Agents) | ~45 | ~15 | 12 | 3 |
| Layer 5 (Ground Truth) | ~20 | ~8 | 4 | 1 |
| Layer 6 (Benchmarks) | ~10 | ~3 | 2 | 0 |
| Shared | ~15 | ~10 | 18 | 0 |

## Frontend Tests
| Category | Count | Framework |
|----------|-------|-----------|
| Unit/Component | ~25 | Vitest |
| Integration | ~15 | Vitest + MSW |
| E2E | ~8 | Playwright |

## CI Gates
| Gate | Status | Command |
|------|--------|---------|
| Unit | ✅ | `make test` |
| Integration | ✅ | `make test-integration` |
| Security Smoke | ✅ | `make security-smoke` |
| Contract | ✅ | `make contract-tests` |

## Existing Security Test Coverage
- `test_adversarial_auth.py` - 18 negative auth tests
- `test_tenant_isolation.py` - 14 tenant boundary tests
- `test_rls_enforcement.py` - 12 RLS policy tests
- `test_rbac.py` - 9 role-based access tests
- `test_owasp_top10.py` - 35 OWASP coverage tests
