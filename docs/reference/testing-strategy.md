# Value Fabric Test Strategy
## Silicon Valley Production Testing Standard

**Version:** 1.0
**Date:** April 19, 2026
**Scope:** Fabric_4L Platform (Layers 1-6 + Frontend)

---

## Executive Summary

This document defines the comprehensive testing strategy for the Value Fabric platform, bringing it to Silicon Valley production standards (Google/Netflix/Meta caliber). The strategy enforces a strict test pyramid with 70% unit tests, 20% integration tests, and 10% E2E tests, with ≥80% line coverage across all backend layers.

---

## Test Pyramid

```
       /\
      /  \      E2E Tests (10%)
     /    \     Critical User Journeys
    /------\
   /        \   Integration Tests (20%)
  /          \  Service Boundaries, APIs
 /------------\
/              \ Unit Tests (70%)
/                \ Fast, Isolated, No I/O
------------------
```

### Pyramid Discipline Rules

1. **Unit Tests: 70%** - Target 100ms execution, no external dependencies
2. **Integration Tests: 20%** - Test service boundaries with real dependencies
3. **E2E Tests: 10%** - Critical user journeys only, never invert the pyramid
4. **Coverage: ≥80%** - Enforced in CI for all backend layers
5. **Flaky Rate: <1%** - Flaky tests are P0 to fix

---

## Test Categories

### 1. Unit Tests (70%)

| Layer | Location | Focus | Coverage Target |
|-------|----------|-------|-----------------|
| L1 Ingestion | `services/layer1-ingestion/tests/unit/` | Crawler, adapters, models | 80% |
| L2 Extraction | `services/layer2-extraction/tests/` | Chunker, LLM extractor | 80% |
| L3 Knowledge | `services/layer3-knowledge/tests/` | Entity CRUD, search, graph | 80% |
| L4 Agents | `services/layer4-agents/tests/unit/` | Workflow state machine | 80% |
| L5 Ground Truth | `services/layer5-ground-truth/tests/unit/` | Evidence, audit log | 80% |
| L6 Benchmarks | `services/layer6-benchmarks/tests/` | Calculations, metrics | 80% |
| Frontend | `frontend/client/src/**/*.test.tsx` | Components, hooks, utils | 70% |

### 2. Integration Tests (20%)

| Category | Location | Dependencies | Markers |
|----------|----------|--------------|---------|
| API Integration | `tests/integration/` | PostgreSQL, Neo4j, Redis | `integration` |
| Cross-Layer Flow | `tests/integration/` | Full stack | `integration` |
| Database Tests | `services/layer*/tests/` | PostgreSQL | `requires_postgres` |
| Graph DB Tests | `services/layer3-knowledge/tests/` | Neo4j | `requires_neo4j` |
| Cache Tests | `services/layer*/tests/` | Redis | `requires_redis` |

### 3. Contract Tests (10% of Integration)

| Type | Location | Tool | Coverage |
|------|----------|------|----------|
| OpenAPI Schema | `tests/contract/` | schemathesis | All endpoints |
| Response Models | `tests/contract/` | pydantic | All responses |
| Tool Manifests | `tests/contract/` | JSON Schema | All skills |

### 4. E2E Tests (10%)

| Journey | Location | Tool | Browsers |
|---------|----------|------|----------|
| Authentication | `frontend/e2e/` | Playwright | Chrome, Firefox, Safari |
| Value Pack Workflow | `frontend/e2e/` | Playwright | Chrome, Firefox, Safari |
| Agent Workflow | `frontend/e2e/` | Playwright | Chrome, Firefox, Safari |
| Knowledge Graph | `frontend/e2e/` | Playwright | Chrome, Firefox, Safari |
| Evidence Export | `frontend/e2e/` | Playwright | Chrome, Firefox, Safari |

### 5. Performance Tests

| Test | Location | SLOs | Markers |
|------|----------|------|---------|
| API Latency | `tests/performance/` | p95 < 200ms | `performance` |
| Search Latency | `tests/performance/` | p95 < 2s | `performance` |
| Load Tests | `tests/performance/` | 50 concurrent | `performance` |
| Frontend LCP | `frontend/e2e/performance/` | < 2.5s | `performance` |

### 6. Security Tests

| OWASP Category | Location | Coverage |
|----------------|----------|----------|
| A01: Broken Access Control | `tests/security/` | ✓ IDOR, authz |
| A02: Cryptographic Failures | `tests/security/` | ✓ TLS, password policy |
| A03: Injection | `tests/security/` | ✓ SQL, NoSQL, command |
| A04: Insecure Design | `tests/security/` | ✓ Rate limiting |
| A05: Security Misconfiguration | `tests/security/` | ✓ Headers, debug mode |
| A06: Vulnerable Components | `tests/security/` | ✓ Dependency scanning |
| A07: Auth Failures | `tests/security/` | ✓ Brute force, MFA |
| A08: Integrity Failures | `tests/security/` | ✓ CSRF, webhooks |
| A09: Logging Failures | `tests/security/` | ✓ Audit, alerts |
| A10: SSRF | `tests/security/` | ✓ URL validation |

### 7. Accessibility Tests

| Test | Location | Standard | Tool |
|------|----------|----------|------|
| WCAG 2.1 AA Audit | `frontend/e2e/accessibility/` | WCAG 2.1 AA | axe-core |
| Keyboard Navigation | `frontend/e2e/accessibility/` | WCAG 2.1.1 | Playwright |
| Screen Reader | `frontend/e2e/accessibility/` | WCAG 4.1.2 | Playwright |
| Mobile A11y | `frontend/e2e/accessibility/` | WCAG 2.1 | axe-core |

---

## Test Infrastructure

### Python Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-xdist>=3.6.0",        # Parallel execution
    "pytest-timeout>=2.3.0",       # Prevent hanging
    "pytest-randomly>=3.16.0",     # Randomize order
    "factory-boy>=3.3.0",          # Test data factories
    "faker>=33.0.0",               # Fake data
    "testcontainers>=4.8.0",       # Docker for tests
    "schemathesis>=3.38.0",        # API contract testing
    "hypothesis>=6.122.0",         # Property-based testing
    "httpx>=0.27.0",               # Async HTTP client
    "respx>=0.21.0",               # HTTPX mocking
]
```

### Frontend Dependencies

```json
{
  "devDependencies": {
    "vitest": "^2.0.0",
    "@vitest/coverage-v8": "^2.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "jsdom": "^24.0.0",
    "msw": "^2.0.0",              # Mock Service Worker
    "@playwright/test": "^1.49.0",
    "@axe-core/playwright": "^4.10.0"  # Accessibility testing
  }
}
```

### Test Data Factories

All test data created via Factory Boy patterns in `tests/factories.py`:

- `EntityFactory` - Capabilities, use cases, personas, value drivers
- `ValuePackFactory` - Value packs with formulas
- `UserFactory` - Users with roles and tiers
- `FormulaFactory` - Formulas with expressions
- `BusinessCaseFactory` - Business cases with financials
- `ExtractionJobFactory` - Ingestion jobs
- `AgentWorkflowStateFactory` - Workflow states
- `AuditLogEntryFactory` - Audit log entries

### Test Markers

```ini
markers =
    unit: Fast unit tests (no I/O, <100ms)
    integration: Integration tests with real dependencies
    e2e: End-to-end tests
    contract: API contract tests (OpenAPI schema validation)
    performance: Performance benchmarks and SLO validation
    security: Security tests (OWASP Top 10)
    accessibility: WCAG 2.1 AA compliance tests
    slow: Tests that take > 1 second
    flaky: Known flaky tests being fixed - skip in CI
    requires_postgres: Tests requiring PostgreSQL
    requires_redis: Tests requiring Redis
    requires_neo4j: Tests requiring Neo4j
```

---

## CI/CD Integration

### GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

**Jobs:**
1. **backend-tests** - Unit, integration, contract, security tests
2. **frontend-tests** - Unit tests, lint, type check
3. **e2e-tests** - Playwright E2E tests (depends on backend/frontend)
4. **performance-tests** - Benchmarks (main branch only)

**Services:**
- PostgreSQL 16
- Redis 7
- Neo4j 5 (Enterprise)

**Coverage Gates:**
- Backend: ≥80% line coverage
- Frontend: ≥70% line coverage
- Security: All OWASP tests pass
- Accessibility: WCAG 2.1 AA compliance

### Parallel Execution

All tests run in parallel:
- Python: `pytest -n auto` (pytest-xdist)
- Frontend: `vitest --pool=threads`
- E2E: Playwright workers = 3 in CI

---

## Test Execution Commands

### Run All Tests

```bash
# Backend (all layers)
pytest -m unit -n auto --timeout=60
pytest -m integration --timeout=120
pytest -m contract --timeout=60
pytest -m security --timeout=60

# Frontend
pnpm test -- --coverage

# E2E
pnpm exec playwright test

# Accessibility
pnpm exec playwright test e2e/accessibility/

# Performance
pytest -m performance --timeout=300 -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit -n auto

# Integration tests with services
pytest -m integration --timeout=120

# Security tests
pytest -m security

# Contract tests
pytest -m contract

# Single layer
pytest services/layer3-knowledge/tests/ -m unit

# Single test file
pytest services/layer4-agents/tests/unit/test_workflow_state_machine.py -v
```

---

## Quality Gates

### Pre-Commit

```bash
# Run via pre-commit hook
make verify  # Runs: lint → type-check → unit tests → contract tests
```

### Pre-PR

```bash
# Full verification
make verify && make evals

# Or individual layers
make test-layer1
make test-layer2
make test-layer3
make test-layer4
make test-frontend
```

### CI Gates

| Gate | Requirement | Blocking |
|------|-------------|----------|
| Unit Tests | ≥80% coverage | Yes |
| Integration Tests | All pass | Yes |
| Contract Tests | All pass | Yes |
| Security Tests | All pass | Yes |
| E2E Tests | All pass | Yes |
| Accessibility | WCAG 2.1 AA | Yes |
| Performance | SLOs met | Yes (main only) |
| Flaky Rate | <1% | Yes |

---

## Test Maintenance

### Flaky Test Protocol

1. **Detection** - CI flags test as flaky (non-deterministic failures)
2. **Quarantine** - Mark with `@pytest.mark.flaky` and skip in CI
3. **Investigation** - Root cause analysis within 24 hours
4. **Fix** - Stabilize or rewrite test
5. **Re-enable** - Remove flaky marker after 5 consecutive passes

### Test Debt Tracking

<!-- KPI_TABLE_START -->
_Last measured on: 2026-05-12 07:18 UTC_

| Metric | Target | Current | CI Warn | CI Fail | Source-of-truth pipeline/job |
|---|---|---:|---:|---:|---|
| Unit Test Count | 1000+ | 636 | 95% of target | 100% breach | pr-checks / layer jobs + cross-layer |
| Integration Test Count | 200+ | 43 | 95% of target | 100% breach | pr-checks / Integration Tests (Docker) |
| E2E Test Count | 50+ | 118 | 95% of target | 100% breach | pr-checks / Frontend + Playwright |
| Line Coverage | ≥80% | 80.0% (CI gate) | <82% | <80% | pr-checks / test-results-*-coverage.xml |
| Branch Coverage | ≥70% | 70.0% (CI gate) | <72% | <70% | pr-checks / frontend coverage + backend thresholds |
| Flaky Test Rate | <1% | 0.0% (no quarantined flaky markers) | >0.5% | >1.0% | pr-checks / pytest + flaky quarantine tracker |
| Avg Unit Test Time | <100ms | 95ms (latest CI target) | >80ms | >100ms | pr-checks / per-layer pytest runtime |
<!-- KPI_TABLE_END -->



---

## Best Practices

### Unit Tests

- Fast (<100ms), isolated, deterministic
- One assertion per test (ideally)
- Use factories for test data
- Mock external APIs, not your own code
- Follow AAA pattern: Arrange, Act, Assert

### Integration Tests

- Use Testcontainers for real dependencies
- Test service boundaries
- Verify data flows between layers
- Clean up test data after each test

### E2E Tests

- Test critical user journeys only
- Use Page Object Model pattern
- Avoid testing implementation details
- Parallel execution with independent test data

### Security Tests

- Test each OWASP category comprehensively
- Include both positive and negative cases
- Automate in CI/CD pipeline
- Regular penetration testing supplement

### Accessibility Tests

- Run axe-core on all critical pages
- Test keyboard navigation
- Verify screen reader announcements
- Include mobile viewport testing

---

## Monitoring & Alerting

### Test Metrics

- Test execution time trends
- Coverage trends by layer
- Flaky test rate
- Test failure rates

### Alerts

- Coverage drops below threshold
- Flaky test rate exceeds 1%
- E2E test failures in main branch
- Security test failures

---

## Future Enhancements

1. **Visual Regression Testing** - Chromatic/Storybook
2. **Mutation Testing** - mutmut for Python
3. **Chaos Engineering** - Fault injection tests
4. **Contract Testing Expansion** - Pact for cross-service
5. **Performance Baselines** - Automated regression detection
6. **Test Impact Analysis** - Run only affected tests

---

## Appendix

### A. Test File Naming Conventions

- Unit tests: `test_*.py` or `*_test.py`
- Integration tests: `test_*_integration.py`
- Contract tests: `test_*_contract.py`
- E2E tests: `*.spec.ts`
- Accessibility tests: `*.a11y.spec.ts`

### B. Marker Usage

```python
@pytest.mark.unit                    # Fast unit test
@pytest.mark.integration             # Needs real services
@pytest.mark.e2e                     # Full browser test
@pytest.mark.contract                # API contract test
@pytest.mark.performance             # SLO benchmark
@pytest.mark.security                # Security test
@pytest.mark.slow                    # >1s execution
@pytest.mark.flaky                   # Known instability
@pytest.mark.requires_postgres       # Needs PostgreSQL
@pytest.mark.requires_redis          # Needs Redis
@pytest.mark.requires_neo4j          # Needs Neo4j
```

### C. Coverage Exclusions

```ini
omit =
    */tests/*
    */test_*
    */migrations/*
    */venv/*
    */.venv/*
```

---

**Document Owner:** Value Fabric Engineering
**Review Cycle:** Quarterly
**Next Review:** July 19, 2026
