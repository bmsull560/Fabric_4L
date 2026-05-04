# Frontend E2E Test Suite

Production-quality Playwright tests for the Value Fabric frontend.

## Overview

This test suite provides end-to-end coverage for critical user journeys, with a focus on:
- **Behavioral testing**: Verifying user workflows, not just element existence
- **Resilient selectors**: Using semantic/accessible selectors over brittle CSS
- **Deterministic execution**: Proper waiting, no arbitrary sleeps
- **Access control validation**: Testing tier-based permissions across canonical routes
- **Production confidence**: Tests suitable for CI gating

## Test Structure

```
e2e/
├── fixtures/                        # Test data and helpers
│   ├── test-data.ts                 # Test data factories
│   ├── tier-helpers.ts              # Access control utilities (canonical routes)
│   └── index.ts                     # Central exports
├── pages/                           # Page Objects
│   ├── AppShellPage.ts              # Navigation, sidebar, global controls
│   ├── CommandCenterPage.ts         # Home dashboard (/home)
│   ├── GraphExplorerPage.ts         # Graph visualization (/discover/knowledge/graph)
│   ├── ExtractionEnginePage.ts      # Extraction pipeline (/discover/extraction)
│   ├── BusinessCasePage.ts          # ROI display (/deliver/cases)
│   ├── FormulaBuilderPage.ts        # Formula editor (/model/value-studio/formulas)
│   ├── ValueTreeExplorerPage.ts     # Tree visualization (/model/value-studio/explorer)
│   ├── DecisionTracePage.ts         # Audit trail (/evidence/traces)
│   ├── AdminPage.ts                 # Governance screens (/admin/*)
│   └── index.ts                     # Central exports
├── command-center.spec.ts           # Home dashboard tests
├── graph-explorer.spec.ts           # Graph visualization tests
├── navigation.spec.ts               # Access control & routing tests
├── extraction-engine.spec.ts        # Extraction pipeline tests
├── business-case.spec.ts            # Business case output tests
├── formula-builder.spec.ts          # Formula editing tests
├── value-tree-explorer.spec.ts      # Tree visualization tests
├── decision-trace.spec.ts           # Audit trail tests
├── admin.spec.ts                    # Governance workflow tests
└── README.md
```

## Canonical Route Taxonomy

The app uses a single-spine navigation with progressive disclosure:

| Spine    | Route Prefix       | Tier      | Component(s)                |
|----------|--------------------|-----------|-----------------------------|
| Home     | `/home`            | standard  | CommandCenter               |
| Library  | `/library/*`       | standard  | ValuePacks, PackManagement  |
| Discover | `/discover/*`      | standard+ | Accounts, Extraction, Graph |
| Model    | `/model/*`         | advanced  | ValueTreeExplorer, FormulaBuilder |
| Deliver  | `/deliver/*`       | standard+ | BusinessCase, AgentWorkflows |
| Evidence | `/evidence/*`      | standard+ | DecisionTrace               |
| Govern   | `/admin/*`         | admin     | FormulaGovernance, BenchmarkPolicies, VariableRegistry |

## Page Objects

Page Objects encapsulate page-specific interactions, providing:
- **Stable API**: Tests survive UI refactoring
- **Reusable patterns**: Common actions in one place
- **Clear intent**: Method names describe behavior

### Available Page Objects

| Page Object             | Route                          | Purpose                                 |
|-------------------------|--------------------------------|-----------------------------------------|
| `CommandCenterPage`     | `/home`                        | Domain submission, KPI display, jobs    |
| `GraphExplorerPage`     | `/discover/knowledge/graph`    | Graph visualization, search, node interaction |
| `ExtractionEnginePage`  | `/discover/extraction`         | Pipeline steps, terminal logs, entities |
| `BusinessCasePage`      | `/deliver/cases`               | ROI card, actions, recommendations      |
| `FormulaBuilderPage`    | `/model/value-studio/formulas` | Tabs, editor, variables, governance     |
| `ValueTreeExplorerPage` | `/model/value-studio/explorer` | Tree view, entity badges, outline       |
| `DecisionTracePage`     | `/evidence/traces`             | Audit table, provenance, export         |
| `AdminPage`             | `/admin/*`                     | Formula governance, benchmarks, variables |
| `AppShellPage`          | (global)                       | Navigation spine, sidebar, tier switcher |

## Test Coverage

### Command Center (`command-center.spec.ts`)

- ✅ Page load with header and input
- ✅ KPI cards display
- ✅ Domain submission workflow
- ✅ Button state management (enabled/disabled)
- ✅ Advanced configuration panel
- ✅ Jobs table loading and display
- ✅ Access control for all tiers

### Graph Explorer (`graph-explorer.spec.ts`)

- ✅ Page load and graph initialization
- ✅ Loading states
- ✅ Node visualization
- ✅ Node selection and context panel
- ✅ Search functionality
- ✅ Tab navigation
- ✅ Access control (requires advanced tier)
- ✅ Error handling

### Navigation & Access Control (`navigation.spec.ts`)

- ✅ Standard tier route restrictions
- ✅ Advanced tier route access (Model, Extraction, Knowledge)
- ✅ Admin tier full access (Govern section)
- ✅ Single-spine navigation visibility per tier
- ✅ Redirect behavior (all restricted → `/home`)
- ✅ Root redirect to `/home`
- ✅ Mobile navigation rail coverage (implemented and required)

### Extraction Engine (`extraction-engine.spec.ts`)

- ✅ Page load and header display
- ✅ Back navigation link
- ✅ Terminal/log viewer display
- ✅ Job status indicators
- ✅ Access control (advanced tier for `/discover/extraction`, standard for `/discover/jobs`)
- ✅ Error handling

### Business Case (`business-case.spec.ts`)

- ✅ Page load and header
- ✅ Hero ROI card with total value display
- ✅ Action buttons (Explore, Export PDF, View Trace)
- ✅ Recommendations and executive summary sections
- ✅ Export PDF workflow
- ✅ View Trace navigation
- ✅ Access control (all tiers)

### Formula Builder (`formula-builder.spec.ts`)

- ✅ Tab navigation (Formula, Governance, Dependencies, History)
- ✅ Expression editor display
- ✅ Variable binding table
- ✅ Save/Run action buttons
- ✅ Governance tab with status badges
- ✅ Access control (requires advanced tier)

### Value Tree Explorer (`value-tree-explorer.spec.ts`)

- ✅ Page load and header
- ✅ Tree view with hierarchical nodes
- ✅ Entity type display
- ✅ View tab switching (tree vs outline)
- ✅ Action buttons (upload, download, new)
- ✅ Access control (requires advanced tier)

### Decision Trace (`decision-trace.spec.ts`)

- ✅ Audit logs table display
- ✅ Status badges in audit rows
- ✅ Export and refresh controls
- ✅ Progressive disclosure (traces → lineage → changelog)
- ✅ Access control per evidence sub-route

### Admin / Governance (`admin.spec.ts`)

- ✅ Formula Governance: registry, approval queue, version history tabs
- ✅ Benchmark Policies: list display, confidence badges
- ✅ Variable Registry: catalog, source bindings tabs, type/source badges
- ✅ Access control (admin-only enforcement for all govern routes)
- ✅ System and access control sub-routes

## Running Tests

### Prerequisites

```bash
# Install dependencies (includes Playwright)
pnpm install

# Install Playwright browsers
pnpm exec playwright install
```

### Local Development

```bash
# Run all tests (starts dev server automatically)
pnpm test:e2e

# Run with UI for debugging
pnpm test:e2e:ui

# Run in headed mode (see browser)
pnpm test:e2e:headed

# Run specific browser
pnpm test:e2e:chromium
pnpm test:e2e:firefox
pnpm test:e2e:webkit

# Debug specific test
pnpm test:e2e:debug

# View HTML report
pnpm test:e2e:report
```

### CI/Headless Execution

```bash
# Production-like run (headless, retries enabled)
CI=true pnpm test:e2e

# Specific test file
pnpm test:e2e extraction-engine.spec.ts

# With tracing for failures
pnpm test:e2e --trace=on
```

## Configuration

### Playwright Config (`playwright.config.ts`)

| Setting | Value | Purpose |
|---------|-------|---------|
| `testDir` | `./e2e` | Test file location |
| `retries` | 2 (CI only) | Flake tolerance |
| `workers` | 2 (CI) / undefined | Parallelism |
| `baseURL` | `http://localhost:3001` | App base URL |
| `trace` | `on-first-retry` | Debug artifacts |
| `screenshot` | `only-on-failure` | Failure evidence |

### Environment Variables

| Variable | Purpose |
|------------|---------|
| `PLAYWRIGHT_BASE_URL` | Override base URL for tests |
| `CI` | Enable CI mode (headless, retries) |

### Test Data & Tier Management

Tests use localStorage to simulate user tier via the Zustand persist middleware:

```typescript
// Set user tier before tests
await setUserTier(page, 'advanced');

// Clear after tests
await clearUserTier(page);
```

## Writing New Tests

### Pattern

```typescript
import { test, expect } from '@playwright/test';
import { MyPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

test.describe('Feature', () => {
  let myPage: MyPage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'advanced');
    myPage = new MyPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test('should do something meaningful', async ({ page }) => {
    await myPage.goto();
    await myPage.performAction();
    await expect(page).toHaveURL(/\/expected/);
    await expect(myPage.resultElement).toBeVisible();
  });
});
```

### Principles

1. **Use Page Objects**: Don't repeat selector logic
2. **Semantic selectors**: Prefer `getByRole`, `getByText` over CSS
3. **Wait properly**: Use `toBeVisible()` etc. with auto-retry
4. **Clean state**: Use `beforeEach`/`afterEach` for setup/teardown
5. **Clear names**: Test names describe behavior, not implementation
6. **Graceful degradation**: Use `.catch(() => false)` for optional elements

### Selector Priority

1. `getByRole('button', { name: 'Submit' })` — accessible, resilient
2. `getByLabel('Email')` — form fields
3. `getByPlaceholder('Enter email')` — when label missing
4. `getByText('Welcome')` — visible text
5. `getByTestId('submit-btn')` — last resort

**Never use**: Raw CSS like `.btn-primary` or XPath unless absolutely necessary.

## CI Integration

### GitHub Actions Example

```yaml
- name: Run E2E Tests
  run: pnpm test:e2e
  env:
    CI: true
    PLAYWRIGHT_BASE_URL: http://localhost:3001

- name: Upload test results
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: frontend/e2e-results/
```

## Current Status

| Suite | Tests | Status |
|-------|-------|--------|
| Command Center | 12 | Ready |
| Graph Explorer | 17 | Ready |
| Navigation | 16 | Ready |
| Extraction Engine | 10 | Ready |
| Business Case | 13 | Ready |
| Formula Builder | 13 | Ready |
| Value Tree Explorer | 10 | Ready |
| Decision Trace | 12 | Ready |
| Admin / Governance | 15 | Ready |
| **Total** | **~118** | **Production Ready** |

## Known Limitations

1. **Backend dependency**: Tests run against real app; backend must be available or mocked
2. **Data variability**: Table content depends on backend state
3. **Graph data**: Node visualization depends on L3 API availability
4. **Mobile navigation**: Persistent mobile rail is implemented and covered; skipped mobile-navigation claims are rejected by the E2E guard

## Troubleshooting

### Tests fail intermittently

1. Check for race conditions in async operations
2. Ensure proper waiting (don't use `waitForTimeout`)
3. Increase `actionTimeout` if needed
4. Enable tracing: `pnpm test:e2e --trace=on`

### Element not found

1. Verify selector uses semantic attributes
2. Check if element is in iframe (use `frameLocator`)
3. Ensure element is not inside closed shadow DOM

### Timeout errors

1. Check network conditions (test against local server)
2. Verify dev server starts before tests
3. Increase `navigationTimeout` if needed


### Critical Journey Guard

Run `pnpm test:e2e:guard` before committing E2E changes. The guard fails if the mobile navigation or backend My Models CRUD journeys are converted back to `test.skip`, `test.fixme`, or a backend skip-valve pattern. Backend-integrated runs also seed deterministic E2E data automatically when `PLAYWRIGHT_BACKEND_URL` is set.
