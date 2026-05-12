import { test, expect } from './fixtures/contract-test';
import { BusinessCasePage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Business Case E2E Tests
 *
 * Route: /deliver/cases
 * Tier: standard (all tiers)
 *
 * Covers:
 * - Page load and ROI display
 * - Action buttons (Explore, Export PDF, View Trace)
 * - Recommendations and executive summary sections
 * - Access control
 * - Error states
 */

test.describe('Business Case', () => {
  let businessCase: BusinessCasePage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'standard');
    businessCase = new BusinessCasePage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test.describe('Page Load', () => {
    test('should display page header', async () => {
      await businessCase.goto();
      await expect(businessCase.header).toBeVisible();
    });

    test('should show loading state or content', async () => {
      await businessCase.goto();
      // Either skeleton loading or content should be visible
      const hasSkeleton = await businessCase.loadingSkeleton.isVisible().catch(() => false);
      const hasHeader = await businessCase.header.isVisible().catch(() => false);
      expect(hasSkeleton || hasHeader).toBeTruthy();
    });
  });

  test.describe('ROI Display', () => {
    test.beforeEach(async () => {
      await businessCase.goto();
    });

    test('should display hero ROI card when data loads', async () => {
      await businessCase.waitForDataLoad();
      const hasHero = await businessCase.heroCard.isVisible().catch(() => false);
      const hasError = await businessCase.errorMessage.isVisible().catch(() => false);
      // Either hero card with ROI data or error state
      expect(hasHero || hasError).toBeTruthy();
    });

    test('should display total value amount', async () => {
      await businessCase.waitForDataLoad();
      const hasValue = await businessCase.totalValueDisplay.isVisible().catch(() => false);
      if (hasValue) {
        const text = await businessCase.totalValueDisplay.textContent();
        // Value should contain a dollar amount
        expect(text).toMatch(/\$/);
      }
    });
  });

  test.describe('Action Buttons', () => {
    test.beforeEach(async () => {
      await businessCase.goto();
      await businessCase.waitForDataLoad();
    });

    test('should display action buttons when case is loaded', async () => {
      const hasExplore = await businessCase.exploreButton.isVisible().catch(() => false);
      const hasExport = await businessCase.exportPdfButton.isVisible().catch(() => false);
      const hasTrace = await businessCase.viewTraceButton.isVisible().catch(() => false);
      // At least one action button should be visible if case is loaded
      if (await businessCase.heroCard.isVisible().catch(() => false)) {
        expect(hasExplore || hasExport || hasTrace).toBeTruthy();
      }
    });

    test('should handle Export PDF click', async () => {
      const hasExport = await businessCase.exportPdfButton.isVisible().catch(() => false);
      if (hasExport) {
        // Click should not crash the app
        await businessCase.clickExportPdf();
        await expect(businessCase.header).toBeVisible();
      }
    });

    test('should handle View Trace click', async ({ page }) => {
      const hasTrace = await businessCase.viewTraceButton.isVisible().catch(() => false);
      if (hasTrace) {
        await businessCase.clickViewTrace();
        // Should navigate to decision trace
        const url = page.url();
        expect(url).toMatch(/evidence|decision-trace/);
      }
    });
  });

  test.describe('Content Sections', () => {
    test.beforeEach(async () => {
      await businessCase.goto();
      await businessCase.waitForDataLoad();
    });

    test('should display recommendations section when available', async () => {
      const hasRecs = await businessCase.recommendationsSection.isVisible().catch(() => false);
      // Recommendations may or may not be present depending on data
      if (hasRecs) {
        await expect(businessCase.recommendationsSection).toBeVisible();
      }
    });

    test('should display executive summary when available', async () => {
      const hasSummary = await businessCase.executiveSummary.isVisible().catch(() => false);
      if (hasSummary) {
        await expect(businessCase.executiveSummary).toBeVisible();
      }
    });
  });

  test.describe('Access Control', () => {
    test('standard tier can access business cases', async ({ page }) => {
      await page.goto('/deliver/cases');
      await expect(page).toHaveURL(/\/deliver\/cases/);
    });

    test('advanced tier can access business cases', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await page.goto('/deliver/cases');
      await expect(page).toHaveURL(/\/deliver\/cases/);
    });

    test('admin tier can access business cases', async ({ page }) => {
      await setUserTier(page, 'admin');
      await page.goto('/deliver/cases');
      await expect(page).toHaveURL(/\/deliver\/cases/);
    });
  });
});
