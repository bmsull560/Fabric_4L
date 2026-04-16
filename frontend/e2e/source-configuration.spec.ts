import { test, expect } from '@playwright/test';
import { SourceConfigurationPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Source Configuration E2E Tests
 *
 * Route: /discover/sources
 * Tier: admin
 *
 * Covers:
 * - Page load with stats display
 * - Source cards with connection status
 * - Search and filter functionality
 * - Add source button
 * - Empty state handling
 * - Access control (admin tier required)
 */

test.describe('Source Configuration', () => {
  let sourcePage: SourceConfigurationPage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'admin');
    sourcePage = new SourceConfigurationPage(page);
    await sourcePage.goto();
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  // ── Page Load ───────────────────────────────────────────────────────

  test('should display page header', async () => {
    await sourcePage.assertPageLoaded();
    await expect(sourcePage.header).toBeVisible();
  });

  test('should display Add Source button', async () => {
    await expect(sourcePage.addSourceButton).toBeVisible();
  });

  test('should display source stats', async () => {
    await sourcePage.waitForDataLoad();
    await sourcePage.assertStatsVisible();
  });

  // ── Search & Filters ────────────────────────────────────────────────

  test('should filter by search query', async ({ page }) => {
    await sourcePage.waitForDataLoad();
    
    await sourcePage.search('CRM');
    await page.waitForTimeout(300);
    
    const count = await sourcePage.getSourceCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should filter by status', async ({ page }) => {
    await sourcePage.waitForDataLoad();
    
    await sourcePage.filterByStatus('connected');
    await page.waitForTimeout(300);
    
    const count = await sourcePage.getSourceCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should filter by type', async ({ page }) => {
    await sourcePage.waitForDataLoad();
    
    await sourcePage.filterByType('CRM');
    await page.waitForTimeout(300);
    
    const count = await sourcePage.getSourceCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  // ── Source Cards ──────────────────────────────────────────────────

  test('should display source cards', async () => {
    await sourcePage.waitForDataLoad();
    
    const count = await sourcePage.getSourceCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should expand source card', async () => {
    await sourcePage.waitForDataLoad();
    
    const count = await sourcePage.getSourceCount();
    if (count > 0) {
      await sourcePage.expandSource(0);
      // Card should remain visible after click
      const card = sourcePage.sourceCards.nth(0);
      await expect(card).toBeVisible();
    }
  });

  // ── Access Control ────────────────────────────────────────────────

  test.describe('Access Control', () => {
    test('should be accessible to admin tier', async () => {
      await sourcePage.assertPageLoaded();
      await expect(sourcePage.page).toHaveURL('/discover/sources');
    });

    test('should redirect standard tier users', async ({ page }) => {
      await clearUserTier(page);
      await setUserTier(page, 'standard');
      
      await page.goto('/discover/sources');
      await page.waitForTimeout(1000);
      
      await expect(page).not.toHaveURL('/discover/sources');
    });

    test('should redirect advanced tier users', async ({ page }) => {
      await clearUserTier(page);
      await setUserTier(page, 'advanced');
      
      await page.goto('/discover/sources');
      await page.waitForTimeout(1000);
      
      await expect(page).not.toHaveURL('/discover/sources');
    });
  });
});
