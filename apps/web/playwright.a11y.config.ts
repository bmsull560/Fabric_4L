import { defineConfig, devices } from "@playwright/test";

/**
 * Minimal Playwright config for accessibility tests against an already-running server.
 * Used in CI where `pnpm preview` is started externally before running a11y checks.
 */
export default defineConfig({
  testDir: "./e2e/accessibility",
  fullyParallel: false,
  forbidOnly: true,
  retries: 1,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:4173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    ...devices["Desktop Chrome"],
  },
});
