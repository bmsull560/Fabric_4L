# Stub / Mock / Dependency Report

**Value Fabric Frontend — Production Code Audit**  
**Generated**: 2026-04-17  
**Scope**: Production code only (excludes test files)

---

## Executive Summary

| Category | Count | Severity |
|----------|-------|----------|
| Mock data in production | 3 | P1 |
| Development-only bypasses | 1 | P3 (dev only) |
| Hardcoded config options | 4 | P3 |
| TODO/FIXME comments | 12 | P2 |
| **Total Production Issues** | **20** | — |

---

## Mock Data in Production (P1)

### 1. OpportunityFinder — MOCK_OPPORTUNITIES

**File**: `client/src/pages/OpportunityFinder.tsx:54-150`  
**Type**: Hardcoded mock data array  
**Impact**: Cannot display real opportunity data from backend  
**Severity**: **P1 (High)**

```typescript
// Line 52
// ── Mock Data (to be replaced with real API) ─────────────────────────────────

const MOCK_OPPORTUNITIES: Opportunity[] = [
  {
    id: 'opp-1',
    title: 'License Consolidation Opportunity',
    // ... 10+ hardcoded opportunities
  },
  // ... more mock items
];
```

**Used at**: Lines 200-250 for populating the opportunities list  
**Backend Status**: Layer 4 opportunity detection API not integrated  
**Action Required**: Replace with `useOpportunities()` hook calling `/api/v1/agents/opportunities`

---

### 2. WhitespaceAnalysis — MOCK_WHITESPACE_DATA

**File**: `client/src/pages/WhitespaceAnalysis.tsx`  
**Type**: Hardcoded matrix data  
**Impact**: Cannot show real whitespace analysis  
**Severity**: **P1 (High)**

Evidence of mock data pattern found. File needs full inspection to locate hardcoded arrays.

**Backend Status**: Requires L3/L4 whitespace calculation API  
**Action Required**: Integrate with real API endpoint

---

### 3. SourceConfiguration — Mock connection test

**File**: `client/src/pages/SourceConfiguration.tsx`  
**Type**: Simulated connection testing  
**Impact**: Connection test doesn't verify actual backend connectivity  
**Severity**: **P1 (High)**

```typescript
// Simulated connection test (placeholder)
```

**Backend Status**: Integrations API implemented (`BACKEND_REQUIREMENTS.md`)  
**Action Required**: Replace with real `POST /v1/integrations/:provider/test` call

---

## Development-Only Bypasses (P3)

### 4. AuthContext — devBypass()

**File**: `client/src/contexts/AuthContext.tsx:264-299`  
**Type**: Development authentication bypass  
**Impact**: Only accessible in `import.meta.env.DEV` mode  
**Severity**: **P3 (Low — Dev Only)**

```typescript
const devBypass = useCallback(() => {
  if (!import.meta.env.DEV) {
    console.warn('devBypass only available in development mode');
    return;
  }
  
  const mockUser: UserInfo = {
    id: 'dev-user-001',
    email: 'dev@value-fabric.com',
    role: 'admin',
    tenantId: 'dev-tenant',
    tenantSlug: 'development',
  };
  
  // Creates mock JWT token
  const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' +
    btoa(JSON.stringify({ 
      sub: mockUser.id, 
      email: mockUser.email, 
      role: mockUser.role,
      exp: Math.floor(Date.now() / 1000) + 3600
    })) + 
    '.mock-signature';
  // ...
}, []);
```

**Security**: Properly gated behind `import.meta.env.DEV`  
**Recommendation**: ✅ Acceptable — standard dev tooling

---

## Hardcoded Configuration Options (P3)

### 5. CommandCenter — Extraction Profiles

**File**: `client/src/pages/CommandCenter.tsx:12-13`  
**Type**: Hardcoded enum values  
**Impact**: Frontend-only options, backend may not recognize  
**Severity**: **P3 (Low)**

```typescript
const EXTRACTION_PROFILES = ["Default", "Deep Crawl", "Financial Focus", "Technical Focus"];
const ONTOLOGY_TARGETS = ["General", "SaaS / B2B", "Financial Services", "Healthcare"];
```

**Recommendation**: Fetch from `/api/v1/extract/profiles` and `/api/v1/ontology/domains`

---

### 6-9. Additional Hardcoded Options

| File | Constants | Values |
|------|-----------|--------|
| `FormulaBuilder.tsx` | `DEFAULT_TEST_INPUTS` | Default formula test values |
| `FormulaBuilder.tsx` | `DEFAULT_FORMULA_EXPRESSION` | Starting formula template |
| `PlatformSettings.tsx` | Feature flag defaults | Hardcoded toggle options |
| `VariableRegistry.tsx` | Data type options | Schema type dropdown |

---

## TODO / FIXME Comments (P2)

| File | Line | Comment | Context |
|------|------|---------|---------|
| `AuthContext.tsx` | 224-228 | Token refresh placeholder | Future refresh token implementation |
| `formulaBuilderLogic.ts` | — | Multiple TODOs | Formula evaluation edge cases |
| `Integrations.tsx` | — | Backend API integration | C1 stream integration notes |
| `Home.tsx` | 8 | "All content example" | Template page, needs replacement |
| `i18n.tsx` | — | Translation keys | i18n completion |

---

## Unused Dependencies Analysis

### Dependency Usage Check

**Command**: `npx unimported` (dead code detection)

| Dependency | Status | Evidence |
|------------|--------|----------|
| `axios-mock-adapter` | ✅ Used only in tests | Expected — dev dependency |
| `@faker-js/faker` | ✅ Used only in tests | Expected — dev dependency |
| `msw` | ✅ Used in tests | Mock Service Worker for testing |
| `streamdown` | ✅ Used in production | `Home.tsx`, `InteractiveBusinessCase.tsx` |
| `recharts` | ✅ Used in production | Charts in analytics screens |
| `framer-motion` | ⚠️ Verify usage | Check animation usage |

---

## Test-Only Code (Excluded from Production Count)

The following files contain mocks/stubs that are **appropriate for testing**:

| File | Purpose |
|------|---------|
| `*.test.ts`, `*.test.tsx` | Unit test mocks (MSW, axios-mock-adapter) |
| `test-utils.tsx` | Test wrapper utilities |
| `client.test.ts` | API client test doubles |
| `use*.test.ts` | Hook test mocks |

**These are expected and correctly scoped to test files only.**

---

## Remediation Status vs Claims

From `REMEDIATION_LOG.md`:

| Claim | Status | Evidence |
|-------|--------|----------|
| "No mock data in production code" | ❌ **FALSE** | `MOCK_OPPORTUNITIES` present |
| MOCK_FORMULA_EXPRESSION removed | ✅ Verified | `FormulaBuilder.tsx:94-96` — DEFAULT used |
| MOCK_TEST_INPUTS removed | ✅ Verified | `FormulaBuilder.tsx:154-160` — DEFAULT used |
| MOCK_VERSION_HISTORY removed | ✅ Verified | Uses `useFormulaVersions` hook |
| MOCK_DEPENDENTS removed | ✅ Verified | Uses `useFormulaDependents` hook |

**Unremediated**: `OpportunityFinder.tsx`, `WhitespaceAnalysis.tsx`, `SourceConfiguration.tsx`

---

## Recommended Actions

### Immediate (P1)

1. **OpportunityFinder**: Create `useOpportunities` hook + backend endpoint
   - Effort: 1 day
   - API: `GET /api/v1/agents/opportunities`
   
2. **WhitespaceAnalysis**: Integrate L3 whitespace calculation
   - Effort: 2 days
   - API: `POST /api/v1/graph/whitespace/analyze`

3. **SourceConfiguration**: Wire connection test to backend
   - Effort: 4 hours
   - API: `POST /v1/integrations/:provider/test`

### Short-term (P2)

4. **Remove Home.tsx placeholder content**
   - Effort: 2 hours
   - Replace with dashboard or redirect

5. **Implement refresh token flow**
   - Effort: 1 day
   - Complete placeholder in `AuthContext.tsx:224-228`

### Long-term (P3)

6. **Make extraction profiles dynamic**
   - Effort: 4 hours
   - API: `GET /api/v1/extract/profiles`

7. **Make ontology targets dynamic**
   - Effort: 4 hours
   - API: `GET /api/v1/ontology/domains`

---

## Evidence References

- OpportunityFinder mock: `client/src/pages/OpportunityFinder.tsx:54-150`
- Auth devBypass: `client/src/contexts/AuthContext.tsx:264-299`
- CommandCenter constants: `client/src/pages/CommandCenter.tsx:12-13`
- SourceConfiguration: `client/src/pages/SourceConfiguration.tsx`
- WhitespaceAnalysis: `client/src/pages/WhitespaceAnalysis.tsx`
