import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for WhitespaceAnalysis
 *
 * Route: /deliver/whitespace
 * Tier: advanced
 *
 * Covers product penetration matrix and whitespace visualization
 */
export class WhitespaceAnalysisPage {
  readonly page: Page;

  // Header elements
  readonly header: Locator;
  readonly subtitle: Locator;

  // Stats cards
  readonly totalAccountsCard: Locator;
  readonly avgPenetrationCard: Locator;
  readonly whitespaceValueCard: Locator;

  // Filters
  readonly industryFilter: Locator;
  readonly revenueFilter: Locator;
  readonly viewToggle: Locator;

  // View content
  readonly matrixView: Locator;
  readonly summaryView: Locator;
  readonly matrixCells: Locator;
  readonly accountRows: Locator;

  // Loading / error
  readonly loadingSkeleton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading', { name: /whitespace analysis|product penetration/i });
    this.subtitle = page.locator('text=/identify gaps|penetration matrix/i');

    // Stats cards
    this.totalAccountsCard = page.locator('text=/Total Accounts|accounts/i').locator('..');
    this.avgPenetrationCard = page.locator('text=/Avg Penetration|penetration/i').locator('..');
    this.whitespaceValueCard = page.locator('text=/Whitespace Value|value/i').locator('..');

    // Filters
    this.industryFilter = page.locator('select').filter({ hasText: /all industries/i }).first();
    this.revenueFilter = page.locator('select').filter({ hasText: /all revenue|revenue ranges/i }).first();
    this.viewToggle = page.getByRole('button', { name: /matrix|summary/i }).or(
      page.locator('button').filter({ hasText: /matrix|summary/i })
    );

    // View content
    this.matrixView = page.locator('[class*="matrix"], table').first();
    this.summaryView = page.locator('[class*="summary"], [class*="list"]').first();
    this.matrixCells = page.locator('td, [class*="cell"]').first();
    this.accountRows = page.locator('tr, [class*="row"]').filter({ has: page.locator('text=/company|account/i') });

    // Loading / error
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();
    this.errorMessage = page.getByRole('alert').or(page.getByText(/failed to load/i));
  }

  // ── Navigation ────────────────────────────────────────────────────

  /**
   * Navigate to Whitespace Analysis
   */
  async goto(): Promise<void> {
    await this.page.goto('/deliver/whitespace');
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Wait for data to load
   */
  async waitForDataLoad(): Promise<void> {
    const hasSkeleton = await this.loadingSkeleton.isVisible().catch(() => false);
    if (hasSkeleton) {
      await expect(this.loadingSkeleton).toBeHidden({ timeout: 10000 });
    }
  }

  // ── Actions ───────────────────────────────────────────────────────

  /**
   * Filter by industry
   */
  async filterByIndustry(industry: string): Promise<void> {
    await this.industryFilter.selectOption(industry);
  }

  /**
   * Filter by revenue range
   */
  async filterByRevenue(range: string): Promise<void> {
    await this.revenueFilter.selectOption(range);
  }

  /**
   * Switch to matrix view
   */
  async switchToMatrixView(): Promise<void> {
    const matrixBtn = this.page.getByRole('button', { name: /matrix/i });
    await matrixBtn.click();
  }

  /**
   * Switch to summary view
   */
  async switchToSummaryView(): Promise<void> {
    const summaryBtn = this.page.getByRole('button', { name: /summary/i });
    await summaryBtn.click();
  }

  // ── Getters ────────────────────────────────────────────────────────

  /**
   * Get account row count
   */
  async getAccountCount(): Promise<number> {
    return this.accountRows.count();
  }

  // ── Assertions ─────────────────────────────────────────────────────

  /**
   * Assert page loaded successfully
   */
  async assertPageLoaded(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Assert matrix view is displayed
   */
  async assertMatrixViewVisible(): Promise<void> {
    await expect(this.matrixView).toBeVisible();
  }

  /**
   * Assert summary view is displayed
   */
  async assertSummaryViewVisible(): Promise<void> {
    await expect(this.summaryView).toBeVisible();
  }
}
