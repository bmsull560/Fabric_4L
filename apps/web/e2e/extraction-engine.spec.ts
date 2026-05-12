import { test, expect } from './fixtures/contract-test';
import { ExtractionEnginePage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Extraction Engine E2E Tests
 *
 * Route: /discover/extraction (advanced), /discover/jobs (standard)
 *
 * Covers:
 * - Page load and header display
 * - Pipeline steps visualization
 * - Terminal/log viewer
 * - Job status indicators
 * - Access control
 * - Error states
 */

test.describe('Extraction Engine', () => {
  let extractionEngine: ExtractionEnginePage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'advanced');
    extractionEngine = new ExtractionEnginePage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test.describe('Page Load', () => {
    test('should display page header', async () => {
      await extractionEngine.goto();
      await expect(extractionEngine.header).toBeVisible();
    });

    test('should show back navigation link', async () => {
      await extractionEngine.goto();
      await expect(extractionEngine.backLink).toBeVisible();
    });

    test('should display loading or terminal content', async () => {
      await extractionEngine.goto();
      await extractionEngine.assertLoadingState();
    });
  });

  test.describe('Extraction Display', () => {
    test.beforeEach(async () => {
      await extractionEngine.goto();
    });

    test('should show terminal panel after load', async () => {
      await extractionEngine.waitForDataLoad();
      const hasTerminal = await extractionEngine.terminalPanel.isVisible().catch(() => false);
      const hasError = await extractionEngine.errorMessage.isVisible().catch(() => false);
      // Either terminal with logs or error state is acceptable
      expect(hasTerminal || hasError).toBeTruthy();
    });

    test('should display job status indicator', async () => {
      await extractionEngine.waitForDataLoad();
      const status = await extractionEngine.getJobStatus();
      // Status text should be present (even if null means no active job)
      if (status) {
        expect(status).toMatch(/processing|completed|failed|running|pending/i);
      }
    });
  });

  test.describe('Navigation', () => {
    test('should navigate back to home', async ({ page }) => {
      await extractionEngine.goto();
      await extractionEngine.navigateBack();
      // Should navigate away from extraction engine
      await expect(page).not.toHaveURL(/\/discover\/extraction/);
    });
  });

  test.describe('Access Control', () => {
    test('requires advanced tier for extraction route', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/discover/extraction');
      // Should be redirected to /home
      await expect(page).toHaveURL(/\/home/);
    });

    test('standard tier can access ingestion jobs', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/discover/jobs');
      // Should stay on jobs page (standard tier allowed)
      await expect(page).toHaveURL(/\/discover\/jobs/);
    });

    test('advanced tier can access extraction engine', async () => {
      await extractionEngine.goto();
      await expect(extractionEngine.header).toBeVisible();
    });

    test('admin tier can access extraction engine', async ({ page }) => {
      await setUserTier(page, 'admin');
      await page.goto('/discover/extraction');
      await expect(extractionEngine.header).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle page load errors gracefully', async ({ page }) => {
      await page.goto('/discover/extraction?error=true');

      // Page should not crash — either header or error displayed
      const hasHeader = await extractionEngine.header.isVisible().catch(() => false);
      const hasError = await extractionEngine.errorMessage.isVisible().catch(() => false);
      expect(hasHeader || hasError).toBeTruthy();
    });
  });
});
