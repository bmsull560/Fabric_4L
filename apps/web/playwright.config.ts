import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Value Fabric frontend E2E tests
 *
 * Test layers:
 *   1. contracts/  — Isolated page-level contract tests (fast, mocked)
 *   2. journeys/   — Chained user journey tests (live or contract mode)
 *   3. accessibility/ — Accessibility audits
 *
 * Standards:
 * - Journey tests run against real backend when PLAYWRIGHT_BACKEND_URL is set
 * - Contract tests always use mocks (no backend required)
 * - Parallel execution where safe
 * - Trace/screenshot on failure for debugging
 * - Accessibility-conscious selectors preferred
 */

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3001';
const CI = process.env.CI === 'true';

export default defineConfig({
  testDir: "./e2e",

  /* Run tests in files in parallel where safe */
  fullyParallel: !CI,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: CI,

  /* Retry on CI only - helps with flaky environments */
  retries: CI ? 2 : 1,

  /* Limit workers to prevent resource contention, but allow parallelism */
  workers: CI ? 2 : undefined,

  /* Reporter configuration */
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'e2e-results/junit.xml' }],
  ],

  /* Shared settings for all projects */
  use: {
    /* Base URL for all tests */
    baseURL: BASE_URL,

    /* Collect trace on first retry, screenshot on failure */
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',

    /* Action timeout - generous for slower operations */
    actionTimeout: 15000,

    /* Navigation timeout */
    navigationTimeout: 30000,

    /* Viewport - desktop default */
    viewport: { width: 1280, height: 720 },

    /* Ignore HTTPS errors in local dev */
    ignoreHTTPSErrors: true,
  },

  /* Configure projects for different test layers and browsers */
  projects: [
    // ── Layer 1: Contract Tests (fast, mocked, chromium-only in dev) ──────
    {
      name: 'contracts',
      testDir: "./e2e",
      use: { ...devices['Desktop Chrome'] },
    },
    // ── Layer 2: Journey Tests (chained workflows, chromium-only in dev) ──
    {
      name: 'journeys',
      testDir: "./e2e",
      use: { ...devices['Desktop Chrome'] },
    },
    // ── Cross-browser: Contracts on Firefox ──────────────────────────────
    {
      name: 'contracts-firefox',
      testDir: "./e2e",
      use: { ...devices['Desktop Firefox'] },
    },
    // ── Cross-browser: Contracts on WebKit ───────────────────────────────
    {
      name: 'contracts-webkit',
      testDir: "./e2e",
      use: { ...devices['Desktop Safari'] },
    },
    // ── Mobile: Contracts on Mobile Chrome ───────────────────────────────
    {
      name: 'contracts-mobile-chrome',
      testDir: "./e2e",
      use: { ...devices['Pixel 5'] },
    },
    // ── Mobile: Contracts on Mobile Safari ───────────────────────────────
    {
      name: 'contracts-mobile-safari',
      testDir: "./e2e",
      use: { ...devices['iPhone 12'] },
    },
  ],

  /* Run local dev server before starting tests */
  webServer: {
    command: 'pnpm dev',
    url: BASE_URL,
    reuseExistingServer: !CI,
    timeout: 120000,
  },

  /* Output directories */
  outputDir: 'e2e-results/',

  /* Global setup/teardown if needed */
  // globalSetup: require.resolve('./e2e/global-setup'),
  // globalTeardown: require.resolve('./e2e/global-teardown'),
});

