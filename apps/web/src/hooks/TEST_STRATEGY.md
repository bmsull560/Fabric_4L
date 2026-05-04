# Graph Query Module Test Strategy

**Module:** `useGraphQuery.ts` + Backend Layer 3 Graph API  
**Date:** April 21, 2026  
**Test Pyramid:** 5-Layer Comprehensive Coverage  
**Target Coverage:** >90% line coverage, 100% critical-path coverage  

---

## Executive Summary

This document defines the comprehensive testing strategy for the Graph Query module, which spans the full stack from frontend React hooks (`useGraphQuery`, `useSubgraph`, `useGraphViewState`) to the Layer 3 Knowledge Graph API backend.

### Module Scope

| Component | File | Lines | Exports |
|-----------|------|-------|---------|
| Graph Query Hooks | `useGraphQuery.ts` | ~400 | 7 hooks, 8 interfaces |
| Backend API | `layer3-knowledge/src/api/` | ~3000 | Subgraph, Entity, Query endpoints |

---

## Test Pyramid Structure

```
                    /\
                   /  \      L5: Contract Tests (5%)
                  /    \     API Contracts, Schema Validation
                 /------\
                /        \   L4: Performance Tests (5%)
               /          \  Latency, Memory, Regression
              /------------\
             /              \ L3: Property Tests (5%)
            /                \Generative Testing, Invariants
           /------------------\
          /                    \L2: Integration Tests (20%)
         /                      \API Boundaries, Auth, DB
        /------------------------\
       /                          \L1: Unit Tests (70%)
      /                            \Pure Functions, Hooks
     --------------------------------
```

### Layer Distribution

| Layer | Test Count | Target Time | Framework |
|-------|------------|-------------|-----------|
| L1 Unit | ~140 tests | <100ms each | Vitest + React Testing Library |
| L2 Integration | ~40 tests | <500ms each | Vitest + MSW |
| L3 Property | ~20 tests | <1s each | Custom generators (fast-check style) |
| L4 Performance | ~15 tests | <10s total | Vitest + Performance APIs |
| L5 Contract | ~30 tests | <100ms each | pytest + jsonschema |
| **Total** | **~245 tests** | **<30s full suite** | - |

---

## Layer 1: Unit Tests (70%)

### Coverage Targets

- **Pure Functions:** 100% branch coverage
- **React Hooks:** All return values, state transitions, memoization
- **Error Handling:** All error paths, boundary conditions

### File Structure

```
frontend/client/src/hooks/
├── useGraphQuery.ts                  # Source module
├── useGraphQuery.test.ts             # Original tests (maintained)
├── useGraphQuery.comprehensive.test.ts   # L1: Unit tests (NEW)
├── useGraphQuery.integration.test.ts     # L2: Integration tests (NEW)
├── useGraphQuery.property.test.ts        # L3: Property tests (NEW)
└── useGraphQuery.performance.test.ts     # L4: Performance tests (NEW)
```

### Test Categories

#### 1.1 Pure State Logic (`useGraphViewState`)

| Test Type | Count | Focus |
|-----------|-------|-------|
| Happy Path | 6 | Zoom in/out, pan, reset |
| Boundary | 5 | Min/max zoom, empty pan, clamps |
| Functional Updates | 3 | Concurrent operations, stability |

**Key Assertions:**
- Zoom bounds: `[0.5, 3.0]` enforced
- Pan operations are cumulative
- Reset is idempotent

#### 1.2 Async Data Hooks (`useSubgraph`, `useEntityContext`, `useGraphQuery`)

| Test Type | Count | Focus |
|-----------|-------|-------|
| Happy Path | 8 | Successful queries, data structure |
| Boundary | 6 | Empty results, single node, max limits |
| Error Cases | 6 | 404, 500, timeout, malformed data |
| Async Patterns | 4 | Loading states, cancellation, caching |

**Key Assertions:**
- Response always contains required fields
- Loading states transition correctly
- Errors are caught and reported
- Cache is properly invalidated

#### 1.3 Type Safety

- GraphNode/GraphRelationship structure validation
- Confidence score bounds checking
- Optional field handling

---

## Layer 2: Integration Tests (20%)

### Scope

- Full request/response cycles
- Authentication/authorization matrix
- Database state verification
- Cascade behavior
- Idempotency

### Test Scenarios

| Scenario | Description |
|----------|-------------|
| Full Cycle | Frontend hook → MSW mock → Response validation |
| Auth Matrix | Admin/Analyst/Viewer/Guest role permissions |
| Data Integrity | Entity relationships, referential integrity |
| Cache Behavior | Stale-while-revalidate, cache invalidation |
| Error Propagation | Network errors → Hook error states |

### Mock Service Worker (MSW) Patterns

```typescript
// Mock handler with dynamic responses
server.use(
  http.get('/api/v1/graph/subgraph', ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('query');
    
    return HttpResponse.json(generateMockResponse(query));
  })
);
```

---

## Layer 3: Property-Based Tests (5%)

### Generators (Custom Implementation)

Without external `fast-check` dependency, we implement custom generators:

```typescript
const randomNode = (): GraphNode => ({
  id: randomString(5, 20),
  name: randomString(5, 50),
  entity_type: randomChoice(['Capability', 'UseCase', 'ValueDriver']),
  confidence_score: randomNumber(0, 1),
  // ...
});
```

### Properties Tested

| Property | Invariant |
|----------|-----------|
| Response Coherence | All edge endpoints exist in nodes |
| Bounds | Confidence ∈ [0,1], density ∈ [0,1] |
| No Throws | Valid inputs never throw |
| Zoom Bounds | zoom ∈ [0.5, 3.0] always |
| Pan Linearity | Multiple pans compose additively |

### Shrinking Strategy

When a property fails, we report:
- Minimal failing input
- Expected vs actual behavior
- Seed for reproduction

---

## Layer 4: Performance Tests (5%)

### SLOs (Service Level Objectives)

| Operation | Target | Budget |
|-----------|--------|--------|
| Small graph (<50 nodes) | p95 < 100ms | 100ms |
| Medium graph (100-500) | p95 < 200ms | 200ms |
| Large graph (500+) | p95 < 500ms | 500ms |
| State updates (zoom/pan) | p95 < 1ms | 1ms |
| UI refresh (60fps) | p95 < 16ms | 16ms |

### Metrics Collected

```typescript
interface PerformanceMetrics {
  mean: number;
  stdDev: number;
  min: number;
  max: number;
  p95: number;
  p99: number;
  cv: number;  // Coefficient of variation (stdDev/mean)
}
```

### Regression Detection

- Standard deviation < 10% of mean (flakiness guard)
- No memory growth between iterations
- 1000x iterations for statistical significance

---

## Layer 5: Contract Tests

### Consumer-Provider Contract

**Consumer:** `value-fabric-frontend`  
**Provider:** `layer3-knowledge-api`

### Schema Validation

| Endpoint | Schema File | Tests |
|----------|-------------|-------|
| `GET /subgraph` | `SUBGRAPH_RESPONSE_SCHEMA` | 8 |
| `GET /entity/{id}/context` | `ENTITY_CONTEXT_SCHEMA` | 6 |
| `POST /query/graph` | `GRAPH_QUERY_*_SCHEMA` | 8 |

### Version Compatibility

- Safe changes: Adding optional fields, expanding enums
- Breaking changes: Removing fields, adding required fields
- Deprecation strategy: Keep old fields for 2 versions

---

## Test Execution

### Local Development

```bash
# Run all tests
pnpm test

# Run by layer
pnpm test -- useGraphQuery.comprehensive    # L1: Unit
pnpm test -- useGraphQuery.integration      # L2: Integration
pnpm test -- useGraphQuery.property         # L3: Property
pnpm test -- useGraphQuery.performance      # L4: Performance

# Run with coverage
pnpm test -- --coverage

# Watch mode
pnpm test:watch
```

### Backend Contract Tests

```bash
# From repo root
pytest tests/contract/test_graph_api_contract.py -v
```

### CI/CD Pipeline

```yaml
# .github/workflows/graph-module-tests.yml
- name: L1 Unit Tests
  run: pnpm test -- useGraphQuery.comprehensive --coverage
  
- name: L2 Integration Tests
  run: pnpm test -- useGraphQuery.integration
  
- name: L3 Property Tests
  run: pnpm test -- useGraphQuery.property
  
- name: L4 Performance Tests
  run: pnpm test -- useGraphQuery.performance
  
- name: L5 Contract Tests
  run: pytest tests/contract/test_graph_api_contract.py
```

---

## Coverage Requirements

| Category | Target | Gate |
|----------|--------|------|
| Line Coverage | ≥90% | Blocking |
| Branch Coverage | ≥80% | Blocking |
| Function Coverage | 100% | Blocking |
| Critical Path | 100% | Blocking |

### Critical Paths (100% Coverage Required)

1. `useSubgraph` data fetching and error handling
2. `useGraphViewState` zoom/pan bounds enforcement
3. `useEntityContext` neighborhood expansion
4. `useGraphQuery` mutation lifecycle

---

## Test Data Factories

### Factory Functions

```typescript
// Create mock graph node with defaults + overrides
const createMockNode = (overrides?: Partial<GraphNode>): GraphNode => ({
  id: `node-${randomId()}`,
  name: 'Test Entity',
  entity_type: 'Capability',
  confidence_score: 0.95,
  ...overrides,
});

// Create mock subgraph with N nodes, M edges
const createMockSubgraph = (nodeCount: number, edgeCount: number): SubgraphResponse => {
  // ... implementation
};
```

### Never Hardcode Rule

All test data must use factories. No hardcoded complex objects.

---

## CI Gates

| Gate | Requirement | Action on Failure |
|------|-------------|-------------------|
| Unit Tests | 100% pass | Block PR |
| Coverage | ≥90% line | Block PR |
| Performance | All SLOs met | Block PR |
| Contract | Schema validation | Block PR |
| Flaky Rate | <1% | Warn, create ticket |

---

## Maintenance

### Test Debt Tracking

| Metric | Target | Current |
|--------|--------|---------|
| Unit Test Count | 140+ | TBD |
| Integration Test Count | 40+ | TBD |
| Property Test Count | 20+ | TBD |
| Performance Test Count | 15+ | TBD |
| Line Coverage | ≥90% | TBD |
| Flaky Test Rate | <1% | TBD |

### Flaky Test Protocol

1. **Detection:** CI flags non-deterministic failures
2. **Quarantine:** Mark with `.skip` and create ticket
3. **Investigation:** Root cause analysis within 24h
4. **Fix:** Stabilize or rewrite
5. **Re-enable:** After 5 consecutive passes

---

## Appendix

### A. Running the Full Suite

```bash
# Complete test run (all layers)
make test-graph-module

# With coverage report
make test-graph-module-coverage
```

### B. Adding New Tests

1. Choose appropriate layer based on test type
2. Use factory functions for data
3. Follow AAA pattern: Arrange, Act, Assert
4. Add to correct `.test.ts` file
5. Run `pnpm test -- --changed` to verify

### C. Debugging Failed Tests

```bash
# Run single test with verbose output
pnpm test -- useGraphQuery.comprehensive --reporter=verbose --grep "zoom"

# Debug with UI
pnpm test:ui
```

---

**Owner:** Value Fabric Engineering  
**Review Cycle:** Monthly  
**Last Updated:** April 21, 2026
