import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for Business Case screen
 *
 * Route: /deliver/cases
 * Tier: standard (all tiers)
 *
 * Encapsulates interactions with the business case output page including:
 * - ROI hero card
 * - Recommendations section
 * - Export and navigation actions
 */
export class BusinessCasePage {
  readonly page: Page;

  // Page header / breadcrumbs
  readonly header: Locator;
  readonly breadcrumbs: Locator;

  // Action buttons
  readonly exploreButton: Locator;
  readonly exportPdfButton: Locator;
  readonly viewTraceButton: Locator;

  // Hero ROI card
  readonly heroCard: Locator;
  readonly totalValueDisplay: Locator;
  readonly roiRatio: Locator;
  readonly paybackPeriod: Locator;
  readonly confidenceScore: Locator;
  readonly implementationCost: Locator;

  // Content sections
  readonly recommendationsSection: Locator;
  readonly executiveSummary: Locator;

  // Loading / error
  readonly loadingSkeleton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading').first();
    this.breadcrumbs = page.locator('[class*="breadcrumb"]').or(
      page.getByText(/agent workflows/i).locator('..')
    );

    // Actions
    this.exploreButton = page.getByRole('button', { name: /explore/i });
    this.exportPdfButton = page.getByRole('button', { name: /export pdf/i });
    this.viewTraceButton = page.getByRole('button', { name: /view trace/i });

    // Hero ROI card (blue gradient background)
    this.heroCard = page.locator('[class*="gradient"]').or(
      page.locator('div').filter({ hasText: /total estimated value/i }).first()
    );
    this.totalValueDisplay = page.getByText(/\$[\d,]+/).first();
    this.roiRatio = page.getByText(/roi ratio/i).locator('..');
    this.paybackPeriod = page.getByText(/payback/i).locator('..');
    this.confidenceScore = page.getByText(/confidence/i).locator('..');
    this.implementationCost = page.getByText(/implementation cost/i).locator('..');

    // Content sections
    this.recommendationsSection = page.getByText(/recommendations/i).locator('..');
    this.executiveSummary = page.getByText(/executive summary/i).locator('..');

    // Loading / error
    this.loadingSkeleton = page.locator('[class*="skeleton"], [class*="animate-pulse"]').first();
    this.errorMessage = page.getByRole('alert').or(
      page.locator('[class*="error"]').filter({ hasText: /error/i })
    );
  }

  /**
   * Navigate to Business Cases page
   */
  async goto(): Promise<void> {
    await this.page.goto('/deliver/cases');
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Wait for business case data to load
   */
  async waitForDataLoad(): Promise<void> {
    const hasData = await this.heroCard.isVisible().catch(() => false);
    const hasError = await this.errorMessage.isVisible().catch(() => false);
    if (!hasData && !hasError) {
      await expect(this.loadingSkeleton).toBeHidden({ timeout: 10000 });
    }
  }

  /**
   * Click Explore button (navigates to interactive business case)
   */
  async clickExplore(): Promise<void> {
    await this.exploreButton.click();
  }

  /**
   * Click Export PDF button
   */
  async clickExportPdf(): Promise<void> {
    await this.exportPdfButton.click();
  }

  /**
   * Click View Trace button (navigates to decision trace)
   */
  async clickViewTrace(): Promise<void> {
    await this.viewTraceButton.click();
  }

  /**
   * Assert page shows the ROI hero card with values
   */
  async assertHeroCardVisible(): Promise<void> {
    await expect(this.heroCard).toBeVisible();
    await expect(this.totalValueDisplay).toBeVisible();
  }

  /**
   * Assert page shows action buttons
   */
  async assertActionsVisible(): Promise<void> {
    await expect(this.exploreButton).toBeVisible();
    await expect(this.exportPdfButton).toBeVisible();
    await expect(this.viewTraceButton).toBeVisible();
  }

  /**
   * Assert error state is displayed
   */
  async assertErrorState(): Promise<void> {
    await expect(this.errorMessage).toBeVisible();
  }
}
