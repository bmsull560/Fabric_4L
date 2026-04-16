import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for SourceConfiguration
 *
 * Route: /discover/sources
 * Tier: admin
 *
 * Covers data source management with connection status and field mappings
 */
export class SourceConfigurationPage {
  readonly page: Page;

  // Header elements
  readonly header: Locator;
  readonly subtitle: Locator;
  readonly addSourceButton: Locator;

  // Stats
  readonly totalSourcesBadge: Locator;
  readonly connectedBadge: Locator;
  readonly errorsBadge: Locator;

  // Filters
  readonly searchInput: Locator;
  readonly statusFilter: Locator;
  readonly typeFilter: Locator;

  // Source cards
  readonly sourceCards: Locator;
  readonly emptyState: Locator;
  readonly emptyStateAddButton: Locator;

  // Loading / error
  readonly loadingSkeleton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading', { name: /source configuration|data sources/i });
    this.subtitle = page.locator('text=/sources.*connected|manage connections/i');
    this.addSourceButton = page.getByRole('button', { name: /add source/i });

    // Stats
    this.totalSourcesBadge = page.locator('text=/total|sources/i').first();
    this.connectedBadge = page.locator('text=/connected/i').first();
    this.errorsBadge = page.locator('text=/error/i').first();

    // Filters
    this.searchInput = page.getByPlaceholder(/search sources/i);
    this.statusFilter = page.locator('select').filter({ hasText: /all status/i }).first();
    this.typeFilter = page.locator('select').filter({ hasText: /all types/i }).first();

    // Source cards
    this.sourceCards = page.locator('.bg-white.border.rounded-xl');
    this.emptyState = page.getByText(/no sources found/i);
    this.emptyStateAddButton = page.locator('text=/no sources/i').locator('..').getByRole('button', { name: /add/i });

    // Loading / error
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();
    this.errorMessage = page.getByRole('alert').or(page.getByText(/failed to load/i));
  }

  // ── Navigation ────────────────────────────────────────────────────

  /**
   * Navigate to Source Configuration
   */
  async goto(): Promise<void> {
    await this.page.goto('/discover/sources');
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
   * Search for sources
   */
  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
  }

  /**
   * Filter by status
   */
  async filterByStatus(status: string): Promise<void> {
    await this.statusFilter.selectOption(status);
  }

  /**
   * Filter by type
   */
  async filterByType(type: string): Promise<void> {
    await this.typeFilter.selectOption(type);
  }

  /**
   * Click Add Source button
   */
  async clickAddSource(): Promise<void> {
    await this.addSourceButton.click();
  }

  /**
   * Expand a source card
   */
  async expandSource(index: number): Promise<void> {
    const card = this.sourceCards.nth(index);
    await card.click();
  }

  // ── Getters ────────────────────────────────────────────────────────

  /**
   * Get source count
   */
  async getSourceCount(): Promise<number> {
    return this.sourceCards.count();
  }

  // ── Assertions ─────────────────────────────────────────────────────

  /**
   * Assert page loaded successfully
   */
  async assertPageLoaded(): Promise<void> {
    await expect(this.header).toBeVisible();
    await expect(this.addSourceButton).toBeVisible();
  }

  /**
   * Assert stats are displayed
   */
  async assertStatsVisible(): Promise<void> {
    await expect(this.totalSourcesBadge).toBeVisible();
  }
}
