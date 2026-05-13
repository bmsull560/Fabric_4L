/**
 * Contract Test Base
 *
 * Extends Playwright's base test with automatic API harness installation
 * for hermetic contract tests. Any unhandled API request aborts immediately
 * with a clear error instead of falling through to the Vite proxy and timing out.
 *
 * Usage:
 *   import { test, expect } from '../fixtures/contract-test';
 *
 * Backend-integrated tests should continue using `@playwright/test` directly
 * or the `journeyTest` fixture (which is a no-op in live mode).
 */
import { test as base, expect } from '@playwright/test';
import { installApiHarness } from '../helpers/api-harness';

export const test = base.extend({
  page: async ({ page }, use) => {
    // Install API harness with relaxed mocking so pages render quickly.
    // Unhandled requests return empty 200 instead of aborting, preventing
    // TanStack Query retry loops that stall networkidle.
    const teardown = await installApiHarness(page, { strictMocking: false });
    await use(page);
    await teardown();
  },
});

export { expect };
