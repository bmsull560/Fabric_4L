# Frontend E2E Test Suite

Production-quality Playwright tests for the Value Fabric frontend.

## Overview

This test suite provides end-to-end coverage for critical user journeys, with a focus on:
- **Behavioral testing**: Verifying user workflows, not just element existence
- **Resilient selectors**: Using semantic/accessible selectors over brittle CSS
- **Deterministic execution**: Proper waiting, no arbitrary sleeps
- **Access control validation**: Testing tier-based permissions
- **Production confidence**: Tests suitable for CI gating

## Test Structure

```
e2e/
├── fixtures/           # Test data and helpers
│   ├── test-data.ts    # Test data factories
│   ├── tier-helpers.ts # Access control utilities
│   └── index.ts        # Central exports
├── pages/              # Page Objects
│   ├── CommandCenterPage.ts
│   ├── GraphExplorerPage.ts
│   ├── AppShellPage.ts
│   └── index.ts
├── command-center.spec.ts    # Ingestion workflow tests
├── graph-explorer.spec.ts    # Graph visualization tests
├── navigation.spec.ts        # Access control & routing tests
└── README.md
```

## Page Objects

Page Objects encapsulate page-specific interactions, providing:
- **Stable API**: Tests survive UI refactoring
- **Reusable patterns**: Common actions in one place
- **Clear intent**: Method names describe behavior

### Available Page Objects

| Page Object | Purpose |
|-------------|---------|
| `CommandCenterPage` | Domain submission, KPI display, jobs table |
| `GraphExplorerPage` | Graph visualization, search, node interaction |
| `AppShellPage` | Navigation, sidebar, global controls |

## Test Coverage

### Command Center (`command-center.spec.ts`)

- ✅ Page load with header and input
- ✅ KPI cards display
- ✅ Domain submission workflow
- ✅ Button state management (enabled/disabled)
- ✅ Advanced configuration panel
- ✅ Jobs table loading and display
- ✅ Access control for standard tier

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
- ✅ Advanced tier route access
- ✅ Admin tier full access
- ✅ Sidebar navigation visibility
- ✅ Redirect behavior
- ✅ Mobile navigation (responsive)

## Running Tests

### Prerequisites

```bash
# Install dependencies (includes Playwright)
pnpm install

# Install Playwright browsers
npx playwright install
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
pnpm test:e2e command-center.spec.ts

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
| `baseURL` | `http://localhost:3000` | App base URL |
| `trace` | `on-first-retry` | Debug artifacts |
| `screenshot` | `only-on-failure` | Failure evidence |

### Environment Variables

| Variable | Purpose |
|------------|---------|
| `PLAYWRIGHT_BASE_URL` | Override base URL for tests |
| `CI` | Enable CI mode (headless, retries) |

### Test Data & Tier Management

Tests use localStorage to simulate user tier:

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

test.describe('Feature', () => {
  test('should do something meaningful', async ({ page }) => {
    // Arrange
    const myPage = new MyPage(page);
    await myPage.goto();

    // Act
    await myPage.performAction();

    // Assert
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
    PLAYWRIGHT_BASE_URL: http://localhost:3000

- name: Upload test results
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: e2e-results/
```

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

## Current Status

| Suite | Tests | Status |
|-------|-------|--------|
| Command Center | 12 | Ready |
| Graph Explorer | 17 | Ready |
| Navigation | 15 | Ready |
| **Total** | **44** | **Production Ready** |

## Known Limitations

1. **Backend mocking**: Tests run against real app; backend must be available
2. **Data variability**: Jobs table content depends on backend state
3. **Graph data**: Node visualization depends on L3 API availability

## Next Expansion Areas

Priority for future test additions:

1. **Extraction Engine** - Real-time job progress, logs streaming
2. **Business Case** - ROI display, PDF export workflow
3. **Formula Builder** - Formula editing, validation
4. **Value Tree Explorer** - Tree navigation, formula linking
5. **Decision Trace** - Audit trail, provenance display
6. **Admin Screens** - Governance workflows (admin tier)
