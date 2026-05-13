/**
 * Accessibility Test Base
 *
 * Extends Playwright's base test with automatic API harness installation
 * for a11y scans. Uses non-strict mocking so pages render with empty data
 * rather than crashing on aborted requests.
 */
import { test as base, expect } from '@playwright/test';
import { installApiHarness } from '../helpers/api-harness';

export const test = base.extend({
  page: async ({ page }, use) => {
    // Install API harness with relaxed mocking — empty 200 for anything
    // we haven't explicitly mocked so the DOM renders for axe.
    const teardown = await installApiHarness(page, { strictMocking: false });
    await use(page);
    await teardown();
  },
});

export { expect };
