import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for OpportunityFinder
 *
 * Route: /discover/opportunities
 * Tier: standard+
 *
 * Covers AI opportunity discovery with filtering and expandable cards
 */
export class OpportunityFinderPage {
  readonly page: Page;

  // Header elements
  readonly header: Locator;
  readonly subtitle: Locator;

  // Stats cards
  readonly totalOpportunitiesCard: Locator;
  readonly highImpactCard: Locator;
  readonly totalValueCard: Locator;
  readonly newOpportunitiesCard: Locator;
  readonly avgScoreCard: Locator;

  // Filters
  readonly searchInput: Locator;
  readonly categoryFilter: Locator;
  readonly statusFilter: Locator;
  readonly impactFilter: Locator;
  readonly sortBySelect: Locator;

  // Opportunity list
  readonly opportunityCards: Locator;
  readonly emptyState: Locator;

  // Loading
  readonly loadingSkeleton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading', { name: /opportunity finder|value opportunities/i });
    this.subtitle = page.locator('text=/AI-discovered|value opportunities/i');

    // Stats cards
    this.totalOpportunitiesCard = page.locator('text=/Total|Opportunities/i').locator('..');
    this.highImpactCard = page.locator('text=/High Impact/i').locator('..');
    this.totalValueCard = page.locator('text=/Total Value/i').locator('..');
    this.newOpportunitiesCard = page.locator('text=/New/i').locator('..');
    this.avgScoreCard = page.locator('text=/Avg Score|AI Score/i').locator('..');

    // Filters
    this.searchInput = page.getByPlaceholder(/search opportunities/i);
    this.categoryFilter = page.locator('select').filter({ hasText: /all categories/i }).first();
    this.statusFilter = page.locator('select').filter({ hasText: /all status/i }).first();
    this.impactFilter = page.locator('select').filter({ hasText: /all impact/i }).first();
    this.sortBySelect = page.locator('select').filter({ hasText: /AI Score|value|confidence|date/i }).first();

    // Opportunity list
    this.opportunityCards = page.locator('.bg-white.border.rounded-xl');
    this.emptyState = page.getByText(/no opportunities found/i);

    // Loading
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();
  }

  // ── Navigation ────────────────────────────────────────────────────

  /**
   * Navigate to Opportunity Finder
   */
  async goto(): Promise<void> {
    await this.page.goto('/discover/opportunities');
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
   * Search for opportunities
   */
  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
  }

  /**
   * Filter by category
   */
  async filterByCategory(category: string): Promise<void> {
    await this.categoryFilter.selectOption(category);
  }

  /**
   * Filter by status
   */
  async filterByStatus(status: string): Promise<void> {
    await this.statusFilter.selectOption(status);
  }

  /**
   * Filter by impact level
   */
  async filterByImpact(impact: 'all' | 'high' | 'medium' | 'low'): Promise<void> {
    await this.impactFilter.selectOption(impact);
  }

  /**
   * Sort by field
   */
  async sortBy(field: 'aiScore' | 'value' | 'confidence' | 'discoveredAt'): Promise<void> {
    await this.sortBySelect.selectOption(field);
  }

  /**
   * Expand an opportunity card
   */
  async expandOpportunity(index: number): Promise<void> {
    const card = this.opportunityCards.nth(index);
    await card.click();
  }

  /**
   * Click View Account button on expanded card
   */
  async viewAccount(index: number): Promise<void> {
    const card = this.opportunityCards.nth(index);
    const viewBtn = card.getByRole('button', { name: /view account/i });
    await viewBtn.click();
  }

  /**
   * Click Create Case button on expanded card
   */
  async createCaseFromOpportunity(index: number): Promise<void> {
    const card = this.opportunityCards.nth(index);
    const createBtn = card.getByRole('button', { name: /create case/i });
    await createBtn.click();
  }

  // ── Getters ────────────────────────────────────────────────────────

  /**
   * Get opportunity count
   */
  async getOpportunityCount(): Promise<number> {
    return this.opportunityCards.count();
  }

  /**
   * Get opportunity title at index
   */
  async getOpportunityTitle(index: number): Promise<string | null> {
    const card = this.opportunityCards.nth(index);
    return card.locator('h3').textContent();
  }

  /**
   * Check if opportunity is expanded
   */
  async isOpportunityExpanded(index: number): Promise<boolean> {
    const card = this.opportunityCards.nth(index);
    const hasExpanded = await card.locator('text=/AI Insights|Recommended Actions/i').isVisible().catch(() => false);
    return hasExpanded;
  }

  // ── Assertions ─────────────────────────────────────────────────────

  /**
   * Assert page loaded successfully
   */
  async assertPageLoaded(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Assert stats are displayed
   */
  async assertStatsVisible(): Promise<void> {
    await expect(this.totalOpportunitiesCard).toBeVisible();
    await expect(this.totalValueCard).toBeVisible();
  }
}
