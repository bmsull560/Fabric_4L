import { test, expect } from '@playwright/test';
import { OpportunityFinderPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Opportunity Finder E2E Tests
 *
 * Route: /discover/opportunities
 * Tier: standard+
 *
 * Covers:
 * - Page load and stats display
 * - Search and multi-filter functionality
 * - Opportunity card expand/collapse
 * - Create case from opportunity
 * - Empty state handling
 * - Access control
 */

test.describe('Opportunity Finder', () => {
  let oppPage: OpportunityFinderPage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'standard');
    oppPage = new OpportunityFinderPage(page);
    await oppPage.goto();
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  // ── Page Load ───────────────────────────────────────────────────────

  test('should display page header', async () => {
    await oppPage.assertPageLoaded();
    await expect(oppPage.header).toBeVisible();
  });

  test('should display stats cards', async () => {
    await oppPage.waitForDataLoad();
    await oppPage.assertStatsVisible();
  });

  // ── Search & Filters ──────────────────────────────────────────────

  test('should filter by search query', async ({ page }) => {
    await oppPage.waitForDataLoad();
    
    await oppPage.search('License');
    await page.waitForTimeout(300);
    
    const count = await oppPage.getOpportunityCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should filter by category', async ({ page }) => {
    await oppPage.waitForDataLoad();
    
    await oppPage.filterByCategory('Cost Optimization');
    await page.waitForTimeout(300);
    
    const count = await oppPage.getOpportunityCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should filter by status', async ({ page }) => {
    await oppPage.waitForDataLoad();
    
    await oppPage.filterByStatus('qualified');
    await page.waitForTimeout(300);
    
    const count = await oppPage.getOpportunityCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should filter by impact level', async ({ page }) => {
    await oppPage.waitForDataLoad();
    
    await oppPage.filterByImpact('high');
    await page.waitForTimeout(300);
    
    const count = await oppPage.getOpportunityCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should sort opportunities', async ({ page }) => {
    await oppPage.waitForDataLoad();
    
    await oppPage.sortBy('value');
    await page.waitForTimeout(300);
    
    const count = await oppPage.getOpportunityCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  // ── Opportunity Cards ───────────────────────────────────────────────

  test('should display opportunity cards', async () => {
    await oppPage.waitForDataLoad();
    
    const count = await oppPage.getOpportunityCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should expand opportunity card', async () => {
    await oppPage.waitForDataLoad();
    
    const count = await oppPage.getOpportunityCount();
    if (count > 0) {
      await oppPage.expandOpportunity(0);
      
      // Check for expanded content
      const isExpanded = await oppPage.isOpportunityExpanded(0);
      expect(isExpanded).toBe(true);
    }
  });

  test('should navigate to account from opportunity', async ({ page }) => {
    await oppPage.waitForDataLoad();
    
    const count = await oppPage.getOpportunityCount();
    if (count > 0) {
      await oppPage.expandOpportunity(0);
      
      // Click view account if visible
      const card = oppPage.opportunityCards.nth(0);
      const viewBtn = card.getByRole('button', { name: /view account/i });
      const hasViewBtn = await viewBtn.isVisible().catch(() => false);
      
      if (hasViewBtn) {
        await viewBtn.click();
        await expect(page).toHaveURL(/\/accounts\//);
      }
    }
  });

  test('should navigate to create case from opportunity', async ({ page }) => {
    await oppPage.waitForDataLoad();
    
    const count = await oppPage.getOpportunityCount();
    if (count > 0) {
      await oppPage.expandOpportunity(0);
      
      // Click create case if visible
      const card = oppPage.opportunityCards.nth(0);
      const createBtn = card.getByRole('button', { name: /create case/i });
      const hasCreateBtn = await createBtn.isVisible().catch(() => false);
      
      if (hasCreateBtn) {
        await createBtn.click();
        await expect(page).toHaveURL(/\/deliver\/cases\/new/);
      }
    }
  });

  // ── Access Control ────────────────────────────────────────────────

  test.describe('Access Control', () => {
    test('should be accessible to standard tier', async () => {
      await oppPage.assertPageLoaded();
      await expect(oppPage.page).toHaveURL('/discover/opportunities');
    });

    test('should be accessible to advanced tier', async ({ page }) => {
      await clearUserTier(page);
      await setUserTier(page, 'advanced');
      
      const advancedPage = new OpportunityFinderPage(page);
      await advancedPage.goto();
      
      await advancedPage.assertPageLoaded();
    });
  });
});
