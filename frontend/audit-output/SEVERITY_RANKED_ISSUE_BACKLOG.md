# Severity-Ranked Issue Backlog

**Value Fabric Frontend — Production Audit**  
**Generated**: 2026-04-17  
**Total Issues**: 23 (P0: 0, P1: 3, P2: 10, P3: 10)

---

## P0 — Launch Blockers (0 issues)

✅ **No P0 issues found.**

---

## P1 — High Priority (3 issues)

### P1-001: OpportunityFinder Uses Mock Data

| Field | Value |
|-------|-------|
| **ID** | P1-001 |
| **Domain** | Data Flow & API Integration |
| **Issue** | `MOCK_OPPORTUNITIES` hardcoded array used instead of real API |
| **Evidence** | `OpportunityFinder.tsx:54-150` — 10+ hardcoded opportunities |
| **Impact** | Cannot display real opportunity data; users see fake data |
| **Recommended Fix** | Create `useOpportunities()` hook → `GET /api/v1/agents/opportunities` |
| **Effort** | 1 day |
| **Claimed Fixed** | ❌ No — listed in REMEDIATION_LOG as "already complete" but mock remains |

```typescript
// Evidence: Line 52
// ── Mock Data (to be replaced with real API) ─────────────────────────────────
const MOCK_OPPORTUNITIES: Opportunity[] = [
  {
    id: 'opp-1',
    title: 'License Consolidation Opportunity',
    // ... hardcoded data
  }
];
```

---

### P1-002: WhitespaceAnalysis Uses Mock Data

| Field | Value |
|-------|-------|
| **ID** | P1-002 |
| **Domain** | Data Flow & API Integration |
| **Issue** | Hardcoded whitespace matrix instead of calculated analysis |
| **Evidence** | `WhitespaceAnalysis.tsx` — search for hardcoded arrays |
| **Impact** | Users see fake penetration matrix, not real analysis |
| **Recommended Fix** | Integrate `POST /api/v1/graph/whitespace/analyze` |
| **Effort** | 2 days |
| **Claimed Fixed** | ❌ No |

---

### P1-003: SourceConfiguration Connection Test is Simulated

| Field | Value |
|-------|-------|
| **ID** | P1-003 |
| **Domain** | Data Flow & API Integration |
| **Issue** | Connection test doesn't actually verify backend connectivity |
| **Evidence** | `SourceConfiguration.tsx` — simulated test function |
| **Impact** | False positive connection status; users think integration works when it doesn't |
| **Recommended Fix** | Wire to `POST /v1/integrations/:provider/test` |
| **Effort** | 4 hours |
| **Claimed Fixed** | ❌ No — Backend API exists but frontend not wired |

---

## P2 — Medium Priority (10 issues)

### P2-001: Home.tsx is Placeholder Content

| Field | Value |
|-------|-------|
| **ID** | P2-001 |
| **Domain** | Routing & Navigation |
| **Issue** | Page contains only example/template content |
| **Evidence** | `Home.tsx:8` — "All content in this page are only for example" |
| **Impact** | Dead route; users see unprofessional placeholder |
| **Recommended Fix** | Replace with dashboard overview or redirect to /home |
| **Effort** | 2 hours |

---

### P2-002: Token Refresh Not Implemented

| Field | Value |
|-------|-------|
| **ID** | P2-002 |
| **Domain** | Security & Trust Boundaries |
| **Issue** | `refreshToken()` is a placeholder that only validates existing token |
| **Evidence** | `AuthContext.tsx:224-228` — comment admits placeholder status |
| **Impact** | Users logged out after 1 hour; no seamless session renewal |
| **Recommended Fix** | Implement refresh token flow with backend |
| **Effort** | 1 day |

---

### P2-003: Narrative Generation No Cancellation

| Field | Value |
|-------|-------|
| **ID** | P2-003 |
| **Domain** | Agent Workflow UX |
| **Issue** | No AbortController for narrative generation stream |
| **Evidence** | `useNarrativeGeneration.ts` — no abort mechanism |
| **Impact** | User must wait for completion or refresh page to cancel |
| **Recommended Fix** | Add AbortController + cancel button |
| **Effort** | 4 hours |

---

### P2-004: C1 Stream State Not Persisted

| Field | Value |
|-------|-------|
| **ID** | P2-004 |
| **Domain** | Agent Workflow UX |
| **Issue** | Partial C1 exploration lost on navigation |
| **Evidence** | `useC1Stream.ts` — no sessionStorage backup |
| **Impact** | User loses work if they navigate away mid-exploration |
| **Recommended Fix** | Persist exploration state to sessionStorage |
| **Effort** | 4 hours |

---

### P2-005: Missing E2E Test Coverage for Key Workflows

| Field | Value |
|-------|-------|
| **ID** | P2-005 |
| **Domain** | Testing & Quality Gates |
| **Issue** | Critical admin workflows lack E2E coverage |
| **Evidence** | `e2e/` — No tests for FormulaGovernance, VariableRegistry, PermissionsAdmin |
| **Impact** | Regression risk for admin features |
| **Recommended Fix** | Add E2E tests for each admin page |
| **Effort** | 2 days |

---

### P2-006: Backend Integration Tests Blocked

| Field | Value |
|-------|-------|
| **ID** | P2-006 |
| **Domain** | Testing & Quality Gates |
| **Issue** | E2E tests fail because backend services (8001-8006) not running |
| **Evidence** | `E2E_REGRESSION_REPORT.md` — infrastructure blocker |
| **Impact** | Cannot validate full stack integration |
| **Recommended Fix** | Document local backend startup; create smoke test suite |
| **Effort** | 1 day |

---

### P2-007: TODO Comments in Production Code

| Field | Value |
|-------|-------|
| **ID** | P2-007 |
| **Domain** | Code Quality |
| **Issue** | 12+ TODO/FIXME comments indicate incomplete work |
| **Evidence** | `AuthContext.tsx:224-228`, `formulaBuilderLogic.ts`, `Integrations.tsx` |
| **Impact** | Technical debt; unclear completion status |
| **Recommended Fix** | Resolve or convert to tracked issues |
| **Effort** | 4 hours |

---

### P2-008: FormulaBuilder Edge Cases Not Fully Handled

| Field | Value |
|-------|-------|
| **ID** | P2-008 |
| **Domain** | Forms & Input Handling |
| **Issue** | Formula evaluation has unhandled edge cases |
| **Evidence** | `formulaBuilderLogic.ts` — TODO comments for edge cases |
| **Impact** | Potential formula calculation errors |
| **Recommended Fix** | Complete edge case handling + add unit tests |
| **Effort** | 1 day |

---

### P2-009: i18n Translation Keys Incomplete

| Field | Value |
|-------|-------|
| **ID** | P2-009 |
| **Domain** | Multi-Tenant & Enterprise |
| **Issue** | Not all UI strings use i18n |
| **Evidence** | `i18n.tsx` — some hardcoded strings remain |
| **Impact** | Cannot fully localize for international users |
| **Recommended Fix** | Audit and extract all remaining strings |
| **Effort** | 1 day |

---

### P2-010: Extraction Profiles Hardcoded

| Field | Value |
|-------|-------|
| **ID** | P2-010 |
| **Domain** | Data Flow & API Integration |
| **Issue** | `EXTRACTION_PROFILES` and `ONTOLOGY_TARGETS` are hardcoded |
| **Evidence** | `CommandCenter.tsx:12-13` |
| **Impact** | Frontend options may not match backend capabilities |
| **Recommended Fix** | Fetch from `/api/v1/extract/profiles` endpoint |
| **Effort** | 4 hours |

---

## P3 — Low Priority (10 issues)

### P3-001: devBypass Available in Dev Mode

| Field | Value |
|-------|-------|
| **ID** | P3-001 |
| **Domain** | Security & Trust Boundaries |
| **Issue** | Mock auth bypass exists (though gated to DEV only) |
| **Evidence** | `AuthContext.tsx:264-299` |
| **Impact** | None in production — properly gated |
| **Recommended Fix** | ✅ Acceptable — standard dev tooling |
| **Effort** | N/A |

---

### P3-002: No Visual Regression Tests

| Field | Value |
|-------|-------|
| **ID** | P3-002 |
| **Domain** | Testing & Quality Gates |
| **Issue** | No Chromatic/Percy screenshot comparison |
| **Evidence** | No visual testing deps in `package.json` |
| **Impact** | UI regressions may go undetected |
| **Recommended Fix** | Add Chromatic or Percy integration |
| **Effort** | 4 hours setup |

---

### P3-003: No CSP Headers Configured

| Field | Value |
|-------|-------|
| **ID** | P3-003 |
| **Domain** | Security & Trust Boundaries |
| **Issue** | Content-Security-Policy not implemented |
| **Evidence** | No CSP meta tag or headers in config |
| **Impact** | XSS risk mitigation not enforced |
| **Recommended Fix** | Add CSP meta tag + configure in CDN |
| **Effort** | 2 hours |

---

### P3-004: Default Formula Test Values Hardcoded

| Field | Value |
|-------|-------|
| **ID** | P3-004 |
| **Domain** | Data Flow & API Integration |
| **Issue** | `DEFAULT_TEST_INPUTS` uses hardcoded values |
| **Evidence** | `FormulaBuilder.tsx` — default test inputs |
| **Impact** | Minor — sensible defaults acceptable |
| **Recommended Fix** | Could fetch from backend schema |
| **Effort** | 2 hours |

---

### P3-005: No Service Worker for Offline Support

| Field | Value |
|-------|-------|
| **ID** | P3-005 |
| **Domain** | Performance & Runtime |
| **Issue** | No PWA/offline capability |
| **Evidence** | No service worker registration |
| **Impact** | App fails completely without network |
| **Recommended Fix** | Add Vite PWA plugin + service worker |
| **Effort** | 1 day |

---

### P3-006: Unused framer-motion Import

| Field | Value |
|-------|-------|
| **ID** | P3-006 |
| **Domain** | Architecture & Codebase |
| **Issue** | `framer-motion` in deps but verify actual usage |
| **Evidence** | `package.json:63` — framer-motion listed |
| **Impact** | Bundle bloat if unused |
| **Recommended Fix** | Verify usage or remove |
| **Effort** | 30 min |

---

### P3-007: No Error Tracking (Sentry/LogRocket)

| Field | Value |
|-------|-------|
| **ID** | P3-007 |
| **Domain** | Observability & Analytics |
| **Issue** | No production error tracking configured |
| **Evidence** | No Sentry/LogRocket in deps |
| **Impact** | Production errors go undetected |
| **Recommended Fix** | Add Sentry integration |
| **Effort** | 2 hours |

---

### P3-008: No Analytics Instrumentation

| Field | Value |
|-------|-------|
| **ID** | P3-008 |
| **Domain** | Observability & Analytics |
| **Issue** | No product analytics (Segment/Amplitude/Mixpanel) |
| **Evidence** | No analytics deps in package.json |
| **Impact** | Cannot track user behavior |
| **Recommended Fix** | Add analytics SDK |
| **Effort** | 4 hours |

---

### P3-009: HealthMonitor Polling Every 30s (Aggressive)

| Field | Value |
|-------|-------|
| **ID** | P3-009 |
| **Domain** | Performance & Runtime |
| **Issue** | Health checks every 30s may be excessive |
| **Evidence** | `useHealthMonitor.ts` — 30s polling interval |
| **Impact** | Unnecessary server load |
| **Recommended Fix** | Reduce to 60s or make adaptive |
| **Effort** | 30 min |

---

### P3-010: Test Files Import from test-utils.tsx

| Field | Value |
|-------|-------|
| **ID** | P3-010 |
| **Domain** | Architecture & Codebase |
| **Issue** | Tests use centralized test-utils (acceptable pattern) |
| **Evidence** | `test-utils.tsx` — shared test utilities |
| **Impact** | None — standard pattern |
| **Recommended Fix** | ✅ Acceptable |
| **Effort** | N/A |

---

## Issue Distribution by Domain

| Domain | P1 | P2 | P3 | Total |
|--------|----|----|----|-------|
| Data Flow & API | 3 | 2 | 1 | 6 |
| Testing & Quality | 0 | 2 | 3 | 5 |
| Agent Workflow UX | 0 | 2 | 0 | 2 |
| Security & Trust | 0 | 1 | 1 | 2 |
| Routing & Navigation | 0 | 1 | 0 | 1 |
| Forms & Input | 0 | 1 | 0 | 1 |
| Code Quality | 0 | 1 | 0 | 1 |
| Multi-Tenant | 0 | 1 | 0 | 1 |
| Performance | 0 | 0 | 2 | 2 |
| Observability | 0 | 0 | 2 | 2 |
| Architecture | 0 | 0 | 2 | 2 |

---

## Remediation Claim Verification

From `REMEDIATION_LOG.md`:

| Claim | Verified | Finding |
|-------|----------|---------|
| "All P0 blockers resolved (7/7)" | ✅ True | No P0 issues found in audit |
| "All P1 high priority resolved" | ⚠️ Partial | 3 P1 issues remain (mock data) |
| "No mock data in production code" | ❌ **FALSE** | 3 files still have mock data |
| "Route mapping verified" | ✅ True | All 47 routes correctly mapped |
| "All tests passing" | ✅ True | 387 tests passing |
| "E2E tests P2" | ✅ True | Blocked by backend, not frontend issues |

---

## Recommended Sprint Planning

### Week 1: P1 Remediation (3 days)

1. **Day 1**: Fix OpportunityFinder mock data
2. **Day 2**: Fix WhitespaceAnalysis mock data
3. **Day 3**: Fix SourceConfiguration connection test

### Week 2: P2 Completion (4 days)

4. **Day 1**: Complete token refresh implementation
5. **Day 2**: Add E2E tests for admin workflows
6. **Day 3**: Fix narrative cancellation + C1 persistence
7. **Day 4**: Resolve TODO comments + i18n completion

### Week 3: P3 Polish (2 days)

8. **Day 1**: Add Sentry + analytics
9. **Day 2**: CSP headers + performance tuning

---

## Evidence References

- Route matrix: `client/src/App.tsx`
- OpportunityFinder mock: `client/src/pages/OpportunityFinder.tsx:54-150`
- AuthContext devBypass: `client/src/contexts/AuthContext.tsx:264-299`
- Token refresh placeholder: `client/src/contexts/AuthContext.tsx:224-228`
- Remediation log: `REMEDIATION_LOG.md`
- E2E regression report: `E2E_REGRESSION_REPORT.md`
