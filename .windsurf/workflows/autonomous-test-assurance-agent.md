---
name: autonomous-test-assurance-agent
description: Autonomous Level 3 agent for transforming test suites from functional confirmation into production assurance with positive, negative, and adversarial coverage
---

# Autonomous Test Assurance Agent

An autonomous Level 3 task agent that inspects the repository, identifies test gaps, makes focused multi-file changes, runs validation commands, and produces PR-ready remediation reports.

## Mission

Transform this repository's test suite from functional confirmation into production assurance.

## Primary Objective

Create and refactor tests so that every critical security, isolation, authorization, validation, reliability, and governance boundary is verified by executable tests. The suite must prove both that valid behavior works and that invalid, unauthorized, malformed, cross-tenant, and adversarial behavior fails safely.

## Operating Mode

Act as a **Level 3 task agent**:
- Inspect the repository
- Identify test gaps
- Make focused multi-file changes
- Run validation commands
- Produce a PR-ready remediation report

Do not make broad architecture changes unless a test cannot be made meaningful without a minimal production fix.

## Core Rule

Every important production invariant must have at least:
1. **One positive test** proving intended behavior works
2. **One negative/adversarial test** proving forbidden behavior is blocked
3. **A regression test** for every discovered violation

---

## Phase 1: Repository Inspection

### 1.1 Map Repository Structure

```bash
# Identify apps, packages, services
ls -la value-fabric/
ls -la frontend/client/src/
ls -la packs/
ls -la shared/

# Map API routes
grep -r "@router\." value-fabric/*/src/api/ --include="*.py"
grep -r "app\." value-fabric/*/src/api/ --include="*.py" | grep -E "(get|post|put|delete)"
```

### 1.2 Identify Auth Middleware

```bash
# Find auth middleware
grep -r "middleware" value-fabric/*/src/ --include="*.py" | grep -i auth
grep -r "require_auth\|authenticate\|verify_token" value-fabric/*/src/ --include="*.py"

# Find tenant resolution
grep -r "tenant_id\|tenant_context\|x-tenant" value-fabric/*/src/ --include="*.py"
```

### 1.3 Map Database Access & RLS

```bash
# Find RLS policies
grep -r "RLS\|row_level_security\|USING\|WITH CHECK" value-fabric/*/migrations/ --include="*.sql"
grep -r "tenant_id" value-fabric/*/migrations/ --include="*.sql"

# Find DB session creation
grep -r "get_db\|get_session\|async_session" value-fabric/*/src/ --include="*.py"
```

### 1.4 Identify Test Pyramid

```bash
# Unit tests
find value-fabric -name "test_*.py" -o -name "*_test.py" | head -20
find frontend -name "*.test.ts" -o -name "*.test.tsx" | head -20

# Integration tests
grep -r "@pytest.mark.integration" value-fabric/ --include="*.py" | head -10

# E2E tests
ls -la frontend/e2e/
find frontend/e2e -name "*.spec.ts" | head -10

# CI gates
ls -la .github/workflows/
cat .github/workflows/*.yml | grep -E "(test|pytest|vitest|playwright)" | head -20
```

### 1.5 Document Test Inventory

Create `artifacts/testing/test-inventory.md`:

```markdown
# Test Inventory

## Backend Tests
| Layer | Unit Tests | Integration Tests | Security Tests | E2E Tests |
|-------|-----------|-------------------|----------------|-----------|
| Layer 1 (Ingestion) | | | | |
| Layer 2 (Extraction) | | | | |
| Layer 3 (Knowledge) | | | | |
| Layer 4 (Agents) | | | | |
| Layer 5 (Ground Truth) | | | | |
| Shared | | | | |

## Frontend Tests
| Category | Count | Framework |
|----------|-------|-----------|
| Unit/Component | | Vitest |
| Integration | | Vitest + MSW |
| E2E | | Playwright |

## CI Gates
| Gate | Status | Command |
|------|--------|---------|
| Unit | | |
| Integration | | |
| E2E Smoke | | |
| Security | | |
```

---

## Phase 2: Define Production Invariants

### 2.1 Extract Security Invariants

Inspect and document non-negotiable rules:

```markdown
## Production Invariants

### Tenant Isolation
- **Rule**: No cross-tenant reads or writes
- **Enforcement**: RLS policies, middleware validation
- **Code Path**: [cite specific files]

### Authentication
- **Rule**: No unauthenticated access to protected resources
- **Enforcement**: Auth middleware, route guards
- **Code Path**: [cite specific files]

### Authorization
- **Rule**: No authorization bypass via headers, params, body fields, or stale context
- **Enforcement**: Role checks, permission validators
- **Code Path**: [cite specific files]

### Input Validation
- **Rule**: No unvalidated input reaching persistence, queues, tools, or LLM calls
- **Enforcement**: Pydantic schemas, validators
- **Code Path**: [cite specific files]

### Secrets Protection
- **Rule**: No secrets exposed in logs, errors, responses, bundles, or snapshots
- **Enforcement**: Redaction middleware, audit filters
- **Code Path**: [cite specific files]

### Destructive Operations
- **Rule**: No destructive operation without ownership and authorization proof
- **Enforcement**: Ownership checks, confirmation flows
- **Code Path**: [cite specific files]

### Idempotency
- **Rule**: No webhook/job/event processed twice without idempotency protection
- **Enforcement**: Idempotency keys, deduplication
- **Code Path**: [cite specific files]

### Agent/LLM Safety
- **Rule**: No agent/LLM output trusted without schema validation and provenance
- **Enforcement**: Structured output validators, evidence tracking
- **Code Path**: [cite specific files]
```

### 2.2 Identify Boundary Locations

```bash
# Find boundary enforcement points
grep -r "raise.*Forbidden\|raise.*Unauthorized\|HTTPException.*403\|HTTPException.*401" value-fabric/*/src/ --include="*.py"
grep -r "Depends.*auth\|require_auth\|get_current_user" value-fabric/*/src/ --include="*.py"
```

---

## Phase 3: Build Test Gap Matrix

### 3.1 Create Gap Matrix

Create `artifacts/testing/test-gap-matrix.md`:

```markdown
# Test Gap Matrix

| Boundary | Risk | Existing Coverage | Missing Positive | Missing Negative | Layer | Severity | File Target | Validation Command |
|----------|------|-------------------|------------------|------------------|-------|----------|-------------|-------------------|
| Tenant resolver | Spoofed tenant header accepted | Unit happy path only | Header/body/route mismatch rejected | Cross-tenant access blocked | Unit + Integration | P0 | tenant-context.test.ts | pnpm test tenant |
| Protected API route | Unauthenticated access | Functional route test | 200 with valid auth | 401 on missing/invalid token | Integration | P0 | auth.api.test.ts | pnpm test api |
| RLS policy | Cross-tenant data read | None | Tenant A can read own data | Tenant A cannot read tenant B | DB Integration | P0 | rls.test.ts | pnpm test db |
| Webhook handler | Duplicate delivery | Happy path only | First delivery succeeds | Same event processed once | Integration | P1 | webhook.test.ts | pnpm test webhooks |
| Frontend route guard | Protected page visible | UI happy path | Authenticated user sees page | Redirects unauthenticated | E2E | P1 | auth.spec.ts | pnpm e2e auth |
```

### 3.2 Severity Definitions

- **P0**: Data/security boundary untested or bypassable - BLOCKS RELEASE
- **P1**: Core production workflow lacks failure/negative coverage
- **P2**: Brittle, incomplete, or overly mocked coverage
- **P3**: Cleanup or maintainability improvement

### 3.3 Prioritize P0/P1 Gaps

Sort by:
1. Security boundaries (tenant, auth, authorization)
2. Data integrity boundaries (RLS, validation)
3. Operational boundaries (idempotency, webhooks)
4. Frontend boundaries (route guards, workflow safety)

---

## Phase 4: Write Tests Before Fixes

### 4.1 Test Writing Principles

For each P0/P1 gap:

1. **Identify the production invariant**
2. **Locate the code path enforcing it**
3. **Locate existing tests**
4. **Add the missing positive test** (proves intended behavior)
5. **Add the missing negative/adversarial test** (proves forbidden behavior)
6. **Confirm the negative test fails** on unfixed code if a gap exists
7. **Apply the smallest production fix only if required**
8. **Re-run the narrow test**
9. **Re-run the relevant broader gate**
10. **Record evidence**

### 4.2 Required Test Style

Tests must be:
- **Deterministic**: Same input → same output every time
- **Self-contained**: No shared state between tests
- **Explicit preconditions**: Setup is clear and documented
- **Exact expected values**: No fuzzy assertions
- **Atomic assertions**: One concept per assertion
- **Stable selectors**: role/label/text/test-id, not position/CSS
- **Bounded scope**: Test the boundary, not implementation details

### 4.3 Security Test Requirements

For each boundary:

```markdown
## Security Test Checklist

### Authentication
- [ ] Missing auth fails (401)
- [ ] Invalid auth fails (401)
- [ ] Expired token fails (401)
- [ ] Malformed token fails (401)

### Authorization
- [ ] Wrong role fails (403)
- [ ] User accessing another user's resource fails
- [ ] Admin-only actions require admin role

### Tenant Isolation
- [ ] Wrong tenant fails
- [ ] Spoofed tenant headers fail/rejected
- [ ] Route/body/query tenant mismatch fails
- [ ] Missing tenant context fails closed

### Input Validation
- [ ] Malformed input fails safely
- [ ] Unknown fields rejected (or ignored by policy)
- [ ] Unsafe strings sanitized
- [ ] Invalid enum/state transition rejected
- [ ] Oversized payloads rejected

### Destructive Actions
- [ ] Require ownership proof
- [ ] Require authorization proof
- [ ] Require confirmation (frontend)

### Secrets Protection
- [ ] Sensitive fields not in errors
- [ ] Sensitive fields not in logs
- [ ] Sensitive fields not in responses
- [ ] API keys redacted in audit logs

### Idempotency
- [ ] Duplicate webhook doesn't double-apply
- [ ] Failed job retries safely
- [ ] Poison messages go to DLQ
- [ ] Missing idempotency key handled safely
```

### 4.4 Example Test Patterns

**Python (pytest) - Tenant Isolation:**

```python
# Positive test
async def test_user_can_read_own_tenant_data(client, auth_headers, tenant_a):
    """Proves tenant A user can read tenant A data."""
    response = await client.get(
        "/api/entities",
        headers={**auth_headers, "X-Tenant-ID": tenant_a.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(e["tenant_id"] == tenant_a.id for e in data)

# Negative test  
async def test_user_cannot_read_other_tenant_data(client, auth_headers, tenant_a, tenant_b):
    """Proves tenant A user cannot read tenant B data."""
    # Create entity in tenant B
    entity_b = await create_entity(tenant_id=tenant_b.id)
    
    # Try to access as tenant A user
    response = await client.get(
        f"/api/entities/{entity_b.id}",
        headers={**auth_headers, "X-Tenant-ID": tenant_a.id}
    )
    assert response.status_code == 404  # Not 403 - don't reveal existence
```

**TypeScript (Vitest) - Auth Guard:**

```typescript
// Positive test
it('allows authenticated users to access protected route', async () => {
  const wrapper = render(<ProtectedRoute />, {
    wrapper: createAuthWrapper({ isAuthenticated: true, user: mockUser })
  });
  
  await waitFor(() => {
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
  });
});

// Negative test
it('redirects unauthenticated users to login', async () => {
  const wrapper = render(<ProtectedRoute />, {
    wrapper: createAuthWrapper({ isAuthenticated: false })
  });
  
  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });
});
```

---

## Phase 5: Refactor Brittle Tests

### 5.1 Identify Weak Tests

Find and fix:
- Happy-path-only tests
- Vague assertions (`toBeTruthy`, `not.toBeNull`)
- Compound assertions (multiple concepts in one test)
- Tests that pass without asserting meaningful behavior
- Tests coupled to CSS classes or DOM position
- Over-mocked tests that bypass auth, tenant, validation, or DB behavior
- Duplicate tests covering the same weak assertion
- Flaky timing assumptions
- Tests missing explicit preconditions
- Tests missing negative cases
- Tests that do not fail on broken production behavior

### 5.2 Refactoring Rules

- Preserve the original intent
- Strengthen assertions
- Split compound assertions into atomic assertions
- Prefer role/label/text/test-id selectors over position
- Add negative tests near the corresponding positive tests
- Do not delete tests unless they are redundant and replaced with stronger coverage
- Do not hide failures by loosening assertions
- Do not mock the security boundary being tested

### 5.3 Refactoring Patterns

**Before/After: Weak Assertion:**

```python
# Before - vague
assert result is not None

# After - explicit
assert result.status == "completed"
assert result.tenant_id == expected_tenant_id
```

**Before/After: Positional Selector:**

```typescript
// Before - fragile
const button = container.querySelector('button:nth-child(2)');

// After - stable
const button = screen.getByRole('button', { name: /submit/i });
```

**Before/After: Over-Mocked Security:**

```python
# Before - mocks bypass real auth
@patch('auth.verify_token', return_value=mock_user)
def test_route_with_auth(mock_verify):
    response = client.get("/protected")
    assert response.status_code == 200

# After - tests real boundary
def test_route_with_valid_token(client, valid_token):
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
```

---

## Phase 6: Verification Runner

### 6.1 Run Narrow Tests

```bash
# Run specific test file
pytest tests/security/test_tenant_isolation.py -v

# Run with specific marker
pytest -m "security" -v

# Run frontend test
pnpm test -- --grep "tenant isolation"
```

### 6.2 Run Broader Gates

```bash
# Layer-specific
make test-layer3
make test-layer4

# Full security suite
make test-security

# All integration tests
make test-integration

# E2E smoke
pnpm e2e:smoke
```

### 6.3 Failure Triage

| Category | Cause | Action |
|----------|-------|--------|
| Test Error | Bug introduced during test writing | Fix test |
| Production Gap | Test correctly finds vulnerability | Fix production code (minimal change) |
| Pre-existing | Was failing before changes | Document separately |
| Flaky | Environmental/timing | Fix determinism |

---

## Phase 7: Evidence Reporter

### 7.1 Produce Remediation Report

Create `artifacts/testing/assurance-remediation-report.md`:

```markdown
# Test Assurance Remediation Report

## Executive Summary
- Production invariants identified: N
- P0 gaps addressed: N
- P1 gaps addressed: N  
- Tests added: N positive, N negative
- Tests refactored: N
- Production fixes required: N (minimal)
- Production-assurance score before: X%
- Production-assurance score after: Y%

## Test Coverage Map
[Link to test-inventory.md]

## Production Invariants
[Link to invariants document]

## Test Gap Matrix
[Link to gap matrix with status updates]

## Tests Added

### Positive Tests
| File | Test | Boundary Covered | Status |
|------|------|------------------|--------|
| | | | |

### Negative/Adversarial Tests
| File | Test | Boundary Covered | Status |
|------|------|------------------|--------|
| | | | |

### Regression Tests
| File | Test | Violation Fixed | Status |
|------|------|-----------------|--------|
| | | | |

## Tests Refactored

| File | Change | Risk Covered |
|------|--------|--------------|
| | | |

## Production Code Changes

| File | Change | Reason |
|------|--------|--------|
| | | |

## Commands Run

```bash
# Narrow tests
pytest tests/security/test_tenant_isolation.py -v
# Result: X passed, Y failed

# Broader gate  
make test-security
# Result: All passed
```

## Remaining P0/P1 Gaps

| Boundary | Reason Not Addressed | Recommended Action |
|----------|---------------------|-------------------|
| | | |

## Residual Risk

- [ ] Description of remaining risk

## Recommended CI Production Gate

```yaml
# Suggested addition to CI
- name: Production Assurance Gate
  run: |
    pnpm test:security
    pnpm test:tenant-isolation
    pnpm test:authorization
```

## PR Review Checklist

- [ ] Tests are meaningful
- [ ] Negative tests fail on vulnerable behavior
- [ ] Mocks are not hiding the real boundary
- [ ] Selectors are stable
- [ ] Assertions are atomic
- [ ] CI is updated if needed
```

---

## High-Value First Targets

### Priority 1: Tenant Isolation
```bash
# Start here
grep -r "tenant_id" value-fabric/*/src/api/routes.py --include="*.py"
```

Tests to add:
- Cross-tenant read denied
- Cross-tenant write denied
- Spoofed tenant header ignored/rejected
- Missing tenant context fails closed
- Tenant ID in route/body/query cannot override authenticated context

### Priority 2: Authorization
```bash
grep -r "role\|permission\|admin" value-fabric/*/src/ --include="*.py" | grep -i "require\|check\|verify"
```

Tests to add:
- Unauthenticated request returns 401
- Authenticated wrong-role request returns 403
- User cannot access another user's resource
- Admin-only actions require admin role

### Priority 3: Input Validation
```bash
grep -r "BaseModel\|validator\|Field" value-fabric/*/src/models/ --include="*.py"
```

Tests to add:
- Malformed payload rejected
- Unknown fields rejected or ignored by policy
- Unsafe strings sanitized
- Invalid enum/state transition rejected

### Priority 4: Database/RLS
```bash
grep -r "USING\|WITH CHECK" value-fabric/*/migrations/ --include="*.sql"
```

Tests to add:
- Tenant A cannot SELECT tenant B
- Tenant A cannot UPDATE tenant B
- Tenant A cannot DELETE tenant B

### Priority 5: Webhook/Job Idempotency
```bash
grep -r "idempotency\|dedup" value-fabric/*/src/ --include="*.py"
```

Tests to add:
- Duplicate event does not duplicate side effects
- Failed job retries safely
- Poison message goes to DLQ

### Priority 6: Frontend Route Guards
```bash
grep -r "RouteGuard\|ProtectedRoute\|useAuth" frontend/client/src/ --include="*.tsx"
```

Tests to add:
- Protected routes redirect unauthenticated users
- Tenant switch clears stale state
- Forbidden resources show safe error state

---

## CI Gate Definition

### Production Assurance Gate

Required before merge:
```yaml
- pnpm lint
- pnpm typecheck
- pnpm test:unit
- pnpm test:integration
- pnpm test:security
- pnpm test:contracts
- pnpm test:e2e:smoke
- pnpm audit
- secret scan
- migration validation
- coverage check for critical security paths
```

Merge must fail if:
- Any P0/P1 security regression test fails
- Any tenant isolation test fails
- Any auth/authorization negative test fails
- Any contract test changes without approval
- Any test is skipped without a linked issue and expiration date
- Any new endpoint lacks positive and negative tests

---

## PR Review Contract

Every autonomous test PR must include:

1. **Scope**: What boundary or invariant was tested
2. **Evidence**: Which code paths and existing tests were inspected
3. **Test changes**: Which positive, negative, regression, or refactored tests were added
4. **Verification**: Exact commands run and results
5. **Risk reduction**: What production failure mode is now blocked
6. **Residual risk**: What remains untested and why
7. **Human review checklist**:
   - Are tests meaningful?
   - Do negative tests fail on vulnerable behavior?
   - Are mocks hiding the real boundary?
   - Are selectors stable?
   - Are assertions atomic?
   - Is CI updated if needed?

---

## One-Shot Master Prompt

Invoke this workflow with:

```
/execute autonomous-test-assurance-agent
```

Or start a specific phase:

```
Run Phase 1: Repository Inspection
- Map all API routes, auth middleware, tenant resolution
- Identify existing test pyramid
- Document test inventory

Then Phase 2: Define Production Invariants
- Extract security, isolation, validation rules
- Cite code paths for each invariant

Then Phase 3: Build Test Gap Matrix
- Compare invariants against existing tests
- Identify P0/P1 gaps
- Prioritize by security impact

Then Phase 4: Write Tests for Priority 1 (Tenant Isolation)
- Add positive tests
- Add negative/adversarial tests
- Confirm negative tests fail before fixes
- Apply minimal production fixes only if required
- Record evidence

Then Phase 5: Refactor Brittle Tests
- Identify weak tests
- Strengthen assertions
- Add negative cases

Then Phase 6: Run Verification
- Execute narrow tests
- Run broader gates
- Document results

Then Phase 7: Produce Remediation Report
- Executive summary
- Production-assurance score before/after
- Remaining gaps
- Recommended CI gate
```

---

## Configuration

Add to `.windsurf/config.yaml`:

```yaml
autonomous_test_assurance:
  enabled: true
  max_tests_per_session: 10
  auto_run_broader_gate: true
  require_negative_tests: true
  severity_threshold: P1  # Don't auto-address P2/P3
```
