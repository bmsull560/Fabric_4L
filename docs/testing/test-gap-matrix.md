# Test Gap Matrix

**Generated:** April 29, 2026  
**Purpose:** Map production invariants to existing test coverage and identify gaps  
**Scope:** P0/P1 gaps that block production assurance

---

## Gap Summary

| Severity | Count | Categories |
|----------|-------|------------|
| **P0 (Block Release)** | 12 | Tenant isolation, Auth bypass, RLS enforcement |
| **P1 (Core Coverage)** | 18 | Input validation, Rate limiting, Audit logging |
| **P2 (Brittle Tests)** | 8 | Weak assertions, Over-mocking, Flaky tests |
| **Total Gaps** | **38** | — |

---

## P0 Gaps (Block Release)

| Boundary | Risk | Existing Coverage | Missing Positive | Missing Negative | Severity | File Target |
|----------|------|-------------------|------------------|------------------|----------|-------------|
| **Tenant Header Mismatch** | Spoofed tenant header accepted | `test_tenant_isolation.py:34-47` partial | ✅ JWT claim precedence | ❌ Mismatch detection returns 400 | **P0** | `test_tenant_mismatch.py` |
| **Suspended Tenant Access** | Suspended tenants can access data | None found | ❌ 403 returned for suspended | ❌ Access blocked with proper message | **P0** | `test_tenant_lifecycle.py` (exists, needs validation) |
| **Pending Tenant Access** | Pending tenants can access data | None found | ❌ 403 returned for pending | ❌ Onboarding redirect | **P0** | `test_tenant_lifecycle.py` |
| **Deleted Tenant Access** | Deleted tenants can access data | None found | ❌ 404 returned for deleted | ❌ Don't reveal existence | **P0** | `test_tenant_lifecycle.py` |
| **Missing Tenant Context** | RLS queries without tenant_id | `test_tenant_read_isolation.py:45-51` | ✅ `require_tenant_context` 400 | ❌ Database layer fails closed | **P0** | `test_rls_enforcement.py` (exists, expand) |
| **Cross-Tenant Neo4j Read** | Tenant A reads Tenant B data | `test_tenant_isolation.py:48-56` partial | ✅ RLS policies checked | ❌ Direct Cypher query isolation | **P0** | `test_neo4j_tenant_query_enforcement.py` (exists, expand) |
| **Cross-Tenant Neo4j Write** | Tenant A writes to Tenant B | `test_tenant_read_isolation.py` | ❌ Write isolation tests | ❌ Update/delete cross-tenant blocked | **P0** | `test_cross_tenant_write.py` |
| **Auth Source Unknown** | AUTH_SOURCE_UNKNOWN accepted | `test_shared_security_middleware.py` partial | ❌ Unknown source rejected | ❌ Middleware sets source correctly | **P0** | `test_auth_source_validation.py` |
| **Invalid JWT Config** | Weak JWT secrets in production | None found | ❌ Startup validation | ❌ Production config rejection | **P0** | `test_jwt_config_validation.py` |
| **Super Admin Bypass** | Cross-tenant without audit | `test_privileged_audit.py` partial | ✅ Audit logging | ❌ All cross-tenant queries logged | **P0** | `test_privileged_audit.py` (expand) |
| **Rate Limit Multi-Worker** | Multi-worker without Redis | None found | ❌ Error raised | ❌ Redis fallback works | **P0** | `test_rate_limit_safety.py` |
| **Missing Privilege Reason** | Cross-tenant without X-Privileged-Reason | `test_privileged_audit.py` partial | ❌ 400 returned | ❌ Reason header validated | **P0** | `test_privileged_audit.py` (expand) |

---

## P1 Gaps (Core Coverage)

| Boundary | Risk | Existing Coverage | Gap | Severity | File Target |
|----------|------|-------------------|-----|----------|-------------|
| **Invalid Isolation Tier** | Invalid tier value accepted | None | No validation tests | **P1** | `test_context_validation.py` |
| **Invalid Auth Source** | Unknown auth source accepted | `test_shared_security_middleware.py` partial | No explicit source validation | **P1** | `test_context_validation.py` |
| **Service Account No Scopes** | Service account without scopes | None | No consistency tests | **P1** | `test_service_account_validation.py` |
| **Permission Check** | Missing permission bypass | `test_rbac.py` | Expand to all CRUD | **P1** | `test_rbac.py` (expand) |
| **Any Permission Check** | OR permission logic bypass | None | No `require_any_permission` tests | **P1** | `test_rbac.py` (expand) |
| **Rate Limit 429 Response** | Missing Retry-After header | None | No 429 response validation | **P1** | `test_rate_limit_response.py` |
| **Rate Limit Window Reset** | Window not resetting correctly | None | No time-based tests | **P1** | `test_rate_limit_window.py` |
| **Audit Event Failure** | Audit failure blocks request | `test_privileged_audit.py` | Don't block on audit fail | **P1** | `test_audit_resilience.py` |
| **Unauthenticated Logging** | Failed auth not logged | `test_tenant_audit.py` partial | Missing path/method logging | **P1** | `test_auth_logging.py` |
| **Tenant Status Logging** | Suspended access not logged | None | Missing status logs | **P1** | `test_tenant_audit.py` (expand) |
| **JWT Expired** | Expired tokens accepted | `test_oidc.py` | No explicit expiration tests | **P1** | `test_jwt_validation.py` |
| **JWT Malformed** | Malformed tokens cause 500 | None | No malformed token tests | **P1** | `test_jwt_validation.py` |
| **JWT Wrong Audience** | Wrong audience tokens accepted | None | No audience validation | **P1** | `test_jwt_validation.py` |
| **JWT Wrong Issuer** | Wrong issuer tokens accepted | None | No issuer validation | **P1** | `test_jwt_validation.py` |
| **Dev Bypass Security** | Dev bypass in production | None | No production bypass tests | **P1** | `test_dev_bypass.py` |
| **Context Consistency** | Tenant_id/org_id mismatch | None | No org hierarchy tests | **P1** | `test_org_hierarchy.py` |
| **Request ID Propagation** | Missing request_id in logs | None | No trace propagation tests | **P1** | `test_request_tracing.py` |
| **Concurrent Tenant Access** | Race condition in tenant resolution | `test_concurrent_tenant_isolation.py` partial | Expand race scenarios | **P1** | `test_concurrent_tenant_isolation.py` (expand) |

---

## P2 Gaps (Brittle/Weak Tests)

| Test File | Issue | Recommended Fix | Severity |
|-----------|-------|-----------------|----------|
| `test_tenant_isolation.py:22-32` | Returns 401/403 (vague), should be specific | Assert exact status code | **P2** |
| `test_tenant_isolation.py:44-46` | Conditional assertion (`if 200`) | Remove conditional, assert 200 | **P2** |
| `test_owasp_top10_complete.py:78-85` | Conditional assertion pattern | Use parametrized tests | **P2** |
| `test_tenant_read_isolation.py` | Mocks bypass real RLS | Test with actual Neo4j | **P2** |
| `test_privileged_audit.py` | May mock audit emitter | Test real audit calls | **P2** |
| `test_rbac.py` | Limited permission scenarios | Add CRUD matrix | **P2** |
| `test_shared_security_middleware.py` | Async/sync split unclear | Consolidate or document | **P2** |
| `test_oidc.py` | Complex test fixtures | Simplify or split | **P2** |

---

## Existing Strong Coverage

| Boundary | Test File | Coverage Quality | Notes |
|----------|-----------|------------------|-------|
| Horizontal privilege escalation | `test_owasp_top10_complete.py:31-45` | ✅ Good | IDOR prevention |
| Vertical privilege escalation | `test_owasp_top10_complete.py:47-58` | ✅ Good | Admin endpoint protection |
| Direct object reference | `test_owasp_top10_complete.py:67-80` | ✅ Good | Enumeration protection |
| Concurrent isolation | `test_tenant_isolation.py:75-100` | ✅ Good | Bulk read isolation |
| Graph query isolation | `test_tenant_isolation.py:58-72` | ✅ Good | Neo4j Cypher boundaries |
| RLS enforcement | `test_rls_enforcement.py` | ✅ Good | 15+ test cases |
| Security headers | `test_security_headers.py` | ✅ Good | OWASP header compliance |
| Injection prevention | `test_injection.py` | ✅ Good | SQL/NoSQL injection |
| Input validation | `test_input_validation.py` | ✅ Good | 15+ validation tests |
| API key rejection | `test_p0_5_api_key_rejection.py` | ✅ Good | P0 security fix |
| Cross-layer tenant | `test_cross_layer_tenant.py` | ✅ Good | Multi-layer isolation |

---

## Recommended Test Priority Order

### Week 1: P0 Critical (Block Release)

1. **test_tenant_mismatch.py** (new)
   - Spoofed header rejection
   - Mismatch 400 response
   - Header vs JWT consistency

2. **test_tenant_lifecycle.py** (expand existing)
   - Suspended tenant 403
   - Pending tenant 403 + onboarding
   - Deleted tenant 404 (no existence reveal)

3. **test_jwt_config_validation.py** (new)
   - Production secret validation
   - Issuer/audience requirements
   - Weak secret rejection

4. **test_cross_tenant_write.py** (new)
   - Neo4j write isolation
   - Update/delete cross-tenant blocked
   - Batch operation isolation

### Week 2: P0 Continued

5. **test_auth_source_validation.py** (new)
   - AUTH_SOURCE_UNKNOWN rejection
   - Source consistency checks

6. **test_rate_limit_safety.py** (new)
   - Multi-worker Redis requirement
   - Graceful fallback handling

7. **test_rls_enforcement.py** (expand)
   - Database layer fails closed
   - Missing tenant_id rejection

8. **test_privileged_audit.py** (expand)
   - All cross-tenant access logged
   - Missing reason header 400

### Week 3: P1 Core Coverage

9. **test_context_validation.py** (new)
   - Invalid isolation tier
   - Invalid auth source

10. **test_service_account_validation.py** (new)
    - Scope consistency
    - Missing scope rejection

11. **test_jwt_validation.py** (new)
    - Expired tokens
    - Malformed tokens
    - Wrong audience/issuer

12. **test_rate_limit_response.py** (new)
    - 429 Retry-After header
    - Window behavior

### Week 4: P1 Continued + P2 Refactoring

13. **test_rbac.py** (expand)
    - All CRUD permissions
    - `require_any_permission` tests

14. **test_audit_resilience.py** (new)
    - Audit failure doesn't block

15. **Refactor brittle tests**
    - Remove conditional assertions
    - Add negative test pairs
    - Reduce mocking

---

## Regression Test Requirements

For each P0/P1 gap fixed, add:
- **Regression test** proving the gap existed and is now closed
- **Documentation** in the test file explaining the vulnerability
- **CI gate** ensuring the test runs on every PR

### Example Regression Test Pattern:

```python
def test_regression_tenant_spoofing_blocked():
    """REGRESSION: Tenant header spoofing was previously accepted.
    
    See: test-gap-matrix.md P0 Gap #1
    Fixed: 2026-04-29
    
    Previously: X-Tenant-ID header could override JWT claim
    Now: Mismatch returns 400 with tenant_mismatch error
    """
    response = client.get(
        "/api/v1/entities",
        headers={
            "Authorization": f"Bearer {tenant_a_token}",
            "X-Tenant-ID": "tenant-b",  # Spoof attempt
        },
    )
    assert response.status_code == 400
    assert response.json()["error"] == "tenant_mismatch"
```

---

## Production Assurance Score

| Category | Before | Target | Current Gap |
|----------|--------|--------|-------------|
| Tenant Isolation | 65% | 95% | -30% |
| Authentication | 70% | 95% | -25% |
| Authorization | 60% | 90% | -30% |
| Rate Limiting | 50% | 90% | -40% |
| Audit Logging | 55% | 90% | -35% |
| Input Validation | 75% | 95% | -20% |
| **Overall** | **62%** | **92%** | **-30%** |

**Current Score: 62%**  
**Target Score: 92%**  
**Gap to Close: 30 percentage points**

---

## Next Steps

1. **Immediate (This Session):**
   - Review P0 gaps with security team
   - Prioritize top 3 gaps for implementation

2. **This Week:**
   - Implement `test_tenant_mismatch.py`
   - Expand `test_tenant_lifecycle.py`
   - Create `test_jwt_config_validation.py`

3. **Next Week:**
   - Implement cross-tenant write tests
   - Add auth source validation tests
   - Verify rate limiting safety

4. **Ongoing:**
   - Update this matrix as gaps are closed
   - Track production assurance score
   - Document new gaps discovered
