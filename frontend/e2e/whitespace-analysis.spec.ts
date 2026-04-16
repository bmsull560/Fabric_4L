import { test, expect } from '@playwright/test';
import { WhitespaceAnalysisPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Whitespace Analysis E2E Tests
 *
 * Route: /deliver/whitespace
 * Tier: advanced
 *
 * Covers:
 * - Page load and stats display
 * - Matrix view with product penetration
 * - Summary view with account breakdown
 * - Industry and revenue filters
 * - View switching (matrix ↔ summary)
 * - Access control (advanced tier required)
 */

test.describe('Whitespace Analysis', () => {
  let wsPage: WhitespaceAnalysisPage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'advanced');
    wsPage = new WhitespaceAnalysisPage(page);
    await wsPage.goto();
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  // ── Page Load ───────────────────────────────────────────────────────

  test('should display page header', async () => {
    await wsPage.assertPageLoaded();
    await expect(wsPage.header).toBeVisible();
  });

  test('should display stats cards', async () => {
    await wsPage.waitForDataLoad();
    await expect(wsPage.totalAccountsCard).toBeVisible();
    await expect(wsPage.avgPenetrationCard).toBeVisible();
  });

  // ── View Switching ──────────────────────────────────────────────────

  test('should display matrix view by default', async () => {
    await wsPage.waitForDataLoad();
    await wsPage.assertMatrixViewVisible();
  });

  test('should switch to summary view', async () => {
    await wsPage.waitForDataLoad();
    await wsPage.switchToSummaryView();
    await wsPage.assertSummaryViewVisible();
  });

  test('should switch back to matrix view', async () => {
    await wsPage.waitForDataLoad();
    await wsPage.switchToSummaryView();
    await wsPage.switchToMatrixView();
    await wsPage.assertMatrixViewVisible();
  });

  // ── Filters ─────────────────────────────────────────────────────────

  test('should filter by industry', async ({ page }) => {
    await wsPage.waitForDataLoad();
    
    await wsPage.filterByIndustry('Technology');
    await page.waitForTimeout(300);
    
    // View should still be visible after filter
    await wsPage.assertMatrixViewVisible();
  });

  test('should filter by revenue range', async ({ page }) => {
    await wsPage.waitForDataLoad();
    
    await wsPage.filterByRevenue('$1M - $10M');
    await page.waitForTimeout(300);
    
    // View should still be visible after filter
    await wsPage.assertMatrixViewVisible();
  });

  // ── Access Control ────────────────────────────────────────────────

  test.describe('Access Control', () => {
    test('should be accessible to advanced tier', async () => {
      await wsPage.assertPageLoaded();
      await expect(wsPage.page).toHaveURL('/deliver/whitespace');
    });

    test('should be accessible to admin tier', async ({ page }) => {
      await clearUserTier(page);
      await setUserTier(page, 'admin');
      
      const adminPage = new WhitespaceAnalysisPage(page);
      await adminPage.goto();
      
      await adminPage.assertPageLoaded();
    });

    test('should redirect standard tier users', async ({ page }) => {
      await clearUserTier(page);
      await setUserTier(page, 'standard');
      
      // Try to navigate - should be redirected
      await page.goto('/deliver/whitespace');
      await page.waitForTimeout(1000);
      
      // Should be redirected away from whitespace
      await expect(page).not.toHaveURL('/deliver/whitespace');
    });
  });
});
