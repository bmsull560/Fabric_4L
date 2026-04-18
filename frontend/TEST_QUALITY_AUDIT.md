# Test Quality Audit

**Date**: 2026-04-18  
**Auditor**: Refinement Workflow  
**Scope**: Frontend Vitest Tests (31 files, 446 tests)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Test Files | 31 |
| Total Tests | 446 |
| Passing | 431 (96.6%) |
| Failing | 14 (3.1%) |
| Skipped | 1 (0.2%) |
| P0 Issues | 3 |
| P1 Issues | 8 |
| P2 Issues | 5 |

---

## Failing Tests (P0 - Critical)

### 1. GraphExplorer.test.tsx (4 tests failing)

**Issue**: Brittle text selectors break when UI text changes

```typescript
// Line 120 - FAILING
expect(screen.getByText('Layout: Force ▾')).toBeInTheDocument();
```

**Root Cause**: 
- Uses exact text match including dropdown arrow character
- Component likely renders different text or structure

**Principle Violations**:
- ❌ **Maintainable** (3/5) - Coupled to exact UI text
- ❌ **Clear** (3/5) - Uses magic string without context

**Fix**: Use `getByRole('button', { name: /layout/i })` or add `data-testid`

---

### 2. ValuePacks.test.tsx (3 tests failing)

**Issue**: Error state assertion expects text that doesn't appear

```typescript
// Line 326 - FAILING
await waitFor(() => {
  const packActions = screen.getByTestId('pack-actions');
  expect(packActions).toHaveTextContent(/Failed to deploy pack|Entity not found/i);
});
```

**Root Cause**:
- Error message format in UI doesn't match test expectation
- Either UI changed or error handling path differs

**Principle Violations**:
- ❌ **Behavior-Focused** (3/5) - Testing error text not error behavior
- ❌ **Deterministic** (3/5) - Timing/async issues with waitFor

**Fix**: Assert error state presence, not exact message text

---

### 3. Other failing tests (7 tests across remaining files)

Similar patterns:
- Brittle selectors
- Timing issues with async operations
- Implementation-detail assertions

---

## Quality Issues by File

### P1 - Material Issues

#### GraphExplorer.test.tsx
| Issue | Line | Principle | Severity |
|-------|------|-----------|----------|
| `document.querySelector('svg')` | 153 | Maintainable | P1 |
| `getAllByText` with loose assertions | 109 | Focused | P1 |
| Uses `fireEvent` not `userEvent` | 73 | Behavior | P2 |

#### ValuePacks.test.tsx
| Issue | Line | Principle | Severity |
|-------|------|-----------|----------|
| `document.querySelectorAll('.animate-pulse')` | 54 | Maintainable | P1 |
| `fireEvent.click` instead of `userEvent` | 317 | Behavior | P1 |
| `fireEvent.click` with `closest('button')` | 321 | Behavior | P1 |
| `getByText` for specific pack names | 63 | Maintainable | P1 |

#### IngestionJobs.test.tsx
| Issue | Line | Principle | Severity |
|-------|------|-----------|----------|
| Uses direct API mocking, not MSW | 9 | Isolation | P2 |
| Large mock data structures inline | 28-100 | Maintainable | P2 |
| No beforeEach server reset | - | Isolation | P1 |

### P2 - Improvements

- Test descriptions could be more behavior-focused
- Some tests combine multiple assertions that could be split
- Missing error boundary/edge case coverage

---

## Rewrite Priority Queue

### P0 - Fix Failing Tests (Immediate)
1. [ ] **GraphExplorer.test.tsx** - Fix brittle selectors (lines 120, 153)
2. [ ] **ValuePacks.test.tsx** - Fix error state assertions (lines 326)

### P1 - Material Improvements (This Sprint)
1. [ ] **GraphExplorer.test.tsx** - Replace implementation queries
2. [ ] **ValuePacks.test.tsx** - Use userEvent, add testid attributes
3. [ ] **IngestionJobs.test.tsx** - Add MSW server reset, refactor mocks

### P2 - Polish (Opportunistic)
1. [ ] Add error state coverage to all page tests
2. [ ] Extract common mock factories
3. [ ] Standardize on userEvent over fireEvent

---

## Recommended Patterns

### Selector Priority (Best to Worst)
1. ✅ `getByRole('button', { name: /submit/i })` - Accessible, resilient
2. ✅ `getByTestId('pack-actions')` - Explicit test contract
3. ⚠️ `getByText('Exact Text')` - Brittle to copy changes
4. ❌ `document.querySelector('.class')` - Implementation coupling

### Async Pattern
```typescript
// ❌ fireEvent (synchronous, less realistic)
fireEvent.click(screen.getByText('Submit'));

// ✅ userEvent (asynchronous, realistic)
const user = userEvent.setup();
await user.click(screen.getByRole('button', { name: /submit/i }));
```

### MSW Handler Reset
```typescript
// ❌ Missing reset - handlers leak between tests
beforeEach(() => {
  server.resetHandlers(); // ✅ Add this
});
```

---

## Success Criteria

- [ ] All 14 failing tests pass
- [ ] No `document.querySelector` in tests
- [ ] No `fireEvent` (use `userEvent`)
- [ ] All async interactions use `userEvent` + `waitFor`
- [ ] MSW handlers reset in `beforeEach`
