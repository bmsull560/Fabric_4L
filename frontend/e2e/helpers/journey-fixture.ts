/**
 * Journey Test Fixture
 *
 * Extends the base Playwright test with a pre-configured environment
 * for chained user journey tests. Each journey test gets:
 *
 * - An authenticated session (admin by default, overridable)
 * - A selected account context
 * - The API harness installed (live or contract mode)
 * - Page objects for common pages
 *
 * Usage:
 *   import { journeyTest } from '../helpers/journey-fixture';
 *
 *   journeyTest('ingestion to value tree', async ({ authedPage, apiHarness }) => {
 *     // authedPage is already authenticated and has API harness installed
 *     await authedPage.goto('/home');
 *     // ...
 *   });
 */
import { test as base, Page, expect } from '@playwright/test';
import { seedAuthState, DEFAULT_TEST_USER, type TestUserInfo } from '../fixtures/auth-helpers';
import { setSelectedAccount, TEST_ACCOUNTS, type TestAccount } from '../fixtures/account-helpers';
import { setUserTier, type UserTier } from '../fixtures/tier-helpers';
import { installApiHarness, isLiveMode, type MockEndpoint } from './api-harness';

// Re-export for convenience
export { expect } from '@playwright/test';
export { isLiveMode } from './api-harness';

// ── Fixture Types ───────────────────────────────────────────────────────────

interface JourneyFixtures {
  /** A page that is already authenticated with the API harness installed */
  authedPage: Page;
  /** The test account that is pre-selected */
  testAccount: TestAccount;
  /** Function to change the user tier mid-test */
  switchTier: (tier: UserTier) => Promise<void>;
  /** Function to add additional API mocks mid-test */
  addMocks: (mocks: MockEndpoint[]) => Promise<void>;
  /** Whether the test is running against a live backend */
  isLive: boolean;
}

// ── Journey Test Definition ─────────────────────────────────────────────────

export const journeyTest = base.extend<JourneyFixtures>({
  testAccount: [TEST_ACCOUNTS.meridian, { option: true }],

  authedPage: async ({ page, testAccount }, use) => {
    // 1. Seed auth state
    await seedAuthState(page, DEFAULT_TEST_USER);

    // 2. Set admin tier (journey tests need full access by default)
    await setUserTier(page, 'admin', 'admin');

    // 3. Set account context
    await setSelectedAccount(page, testAccount);

    // 4. Install API harness
    const teardown = await installApiHarness(page);

    // 5. Provide the page to the test
    await use(page);

    // 6. Cleanup
    await teardown();
  },

  switchTier: async ({ page }, use) => {
    const fn = async (tier: UserTier) => {
      await setUserTier(page, tier, tier);
      await page.reload();
    };
    await use(fn);
  },

  addMocks: async ({ page }, use) => {
    const fn = async (mocks: MockEndpoint[]) => {
      for (const mock of mocks) {
        await page.route(mock.pattern, async (route) => {
          if (mock.delay) {
            await new Promise((resolve) => setTimeout(resolve, mock.delay));
          }
          await route.fulfill({
            status: mock.status ?? 200,
            contentType: 'application/json',
            body: JSON.stringify(mock.body),
          });
        });
      }
    };
    await use(fn);
  },

  isLive: async ({}, use) => {
    await use(isLiveMode());
  },
});

// ── Assertion Helpers ───────────────────────────────────────────────────────

/**
 * Assert that the page navigated to the expected URL pattern.
 * Waits for navigation to complete before checking.
 */
export async function expectUrl(page: Page, pattern: string | RegExp): Promise<void> {
  if (typeof pattern === 'string') {
    await expect(page).toHaveURL(pattern);
  } else {
    await expect(page).toHaveURL(pattern);
  }
}

/**
 * Assert that a specific element is visible on the page.
 * Uses getByRole or getByText for accessibility-conscious selectors.
 */
export async function expectVisible(page: Page, text: string | RegExp): Promise<void> {
  await expect(page.getByText(text).first()).toBeVisible({ timeout: 10000 });
}

/**
 * Assert that the page does NOT contain a specific error message.
 * Useful for verifying that a page loaded successfully.
 */
export async function expectNoErrors(page: Page): Promise<void> {
  const errorPatterns = [
    /failed to load/i,
    /something went wrong/i,
    /error loading/i,
    /cannot read properties/i,
    /unexpected token/i,
  ];

  for (const pattern of errorPatterns) {
    const errorElement = page.getByText(pattern).first();
    await expect(errorElement).not.toBeVisible({ timeout: 3000 }).catch(() => {
      // If the element is visible, the test should fail with a clear message
      throw new Error(`Page contains error text matching: ${pattern}`);
    });
  }
}

/**
 * Wait for the page to finish loading (no pending network requests).
 */
export async function waitForPageReady(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {
    // networkidle can be flaky; fall back to domcontentloaded
  });
}

/**
 * Navigate to a route and wait for it to be ready.
 */
export async function navigateAndWait(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded' });
  await waitForPageReady(page);
}
