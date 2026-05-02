import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for BusinessCaseList
 *
 * Route: /deliver/cases
 * Tier: standard+
 *
 * Covers list view with filtering, sorting, and case creation
 */
export class BusinessCaseListPage {
  readonly page: Page;

  // Header elements
  readonly header: Locator;
  readonly subtitle: Locator;
  readonly newCaseButton: Locator;

  // Stats cards
  readonly totalValueCard: Locator;
  readonly activeCountCard: Locator;
  readonly draftCountCard: Locator;
  readonly companiesCountCard: Locator;

  // Filters
  readonly searchInput: Locator;
  readonly statusFilter: Locator;
  readonly sortBySelect: Locator;
  readonly sortDirectionButton: Locator;

  // Case list
  readonly caseCards: Locator;
  readonly emptyState: Locator;
  readonly emptyStateCreateButton: Locator;

  // Loading / error
  readonly loadingSkeleton: Locator;
  readonly errorMessage: Locator;
  readonly retryButton: Locator;

  // Modal
  readonly newCaseModal: Locator;
  readonly modalCaseNameInput: Locator;
  readonly modalCompanyInput: Locator;
  readonly modalCancelButton: Locator;
  readonly modalCreateButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading', { name: /business cases/i });
    this.subtitle = page.locator('text=/\\d+ cases/');
    this.newCaseButton = page.getByRole('button', { name: /new case/i });

    // Stats cards
    this.totalValueCard = page.locator('text=/Total Value/i').locator('..');
    this.activeCountCard = page.locator('text=/Active/i').locator('..');
    this.draftCountCard = page.locator('text=/Drafts/i').locator('..');
    this.companiesCountCard = page.locator('text=/Companies/i').locator('..');

    // Filters
    this.searchInput = page.getByPlaceholder(/search cases/i);
    this.statusFilter = page.locator('select').filter({ hasText: /all status|active|draft/i }).first();
    this.sortBySelect = page.locator('select').filter({ hasText: /last updated|name|company|value/i }).first();
    this.sortDirectionButton = page.locator('button').filter({ hasText: /↑|↓/ });

    // Case list
    this.caseCards = page.locator('.bg-white.border.border-neutral-200.rounded-xl');
    this.emptyState = page.getByText(/no business cases found/i);
    this.emptyStateCreateButton = page.locator('text=/no business cases found/i').locator('..').getByRole('button', { name: /create case/i });

    // Loading / error
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();
    this.errorMessage = page.getByRole('alert').or(page.getByText(/failed to load/i));
    this.retryButton = page.getByRole('button', { name: /try again/i });

    // Modal
    this.newCaseModal = page.locator('.fixed.inset-0').filter({ has: page.getByText(/create new business case/i) });
    this.modalCaseNameInput = page.locator('input[placeholder*="Q2 Expansion"]').or(
      page.locator('label:has-text("Case Name") + input')
    );
    this.modalCompanyInput = page.locator('input[placeholder*="Acme Corporation"]').or(
      page.locator('label:has-text("Company") + input')
    );
    this.modalCancelButton = page.getByRole('button', { name: /cancel/i });
    this.modalCreateButton = page.getByRole('button', { name: /create$/i });
  }

  // ── Navigation ────────────────────────────────────────────────────

  /**
   * Navigate to Business Case List
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
   * Search for cases
   */
  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
  }

  /**
   * Filter by status
   */
  async filterByStatus(status: 'all' | 'active' | 'draft' | 'archived'): Promise<void> {
    await this.statusFilter.selectOption(status);
  }

  /**
   * Sort by field
   */
  async sortBy(field: 'updatedAt' | 'name' | 'company' | 'totalValue' | 'confidence'): Promise<void> {
    await this.sortBySelect.selectOption(field);
  }

  /**
   * Toggle sort direction
   */
  async toggleSortDirection(): Promise<void> {
    await this.sortDirectionButton.click();
  }

  /**
   * Open new case modal
   */
  async openNewCaseModal(): Promise<void> {
    await this.newCaseButton.click();
    await expect(this.newCaseModal).toBeVisible();
  }

  /**
   * Create a new case
   */
  async createCase(name: string, company: string): Promise<void> {
    await this.openNewCaseModal();
    await this.modalCaseNameInput.fill(name);
    await this.modalCompanyInput.fill(company);
    await this.modalCreateButton.click();
  }

  /**
   * Close new case modal
   */
  async closeModal(): Promise<void> {
    await this.modalCancelButton.click();
  }

  /**
   * Archive a case by index
   */
  async archiveCase(index: number): Promise<void> {
    const card = this.caseCards.nth(index);
    const archiveBtn = card.locator('button[title="Archive"]').or(
      card.locator('button').filter({ has: card.page().locator('svg') }).last()
    );
    await archiveBtn.click();
    // Handle confirmation dialog
    this.page.once('dialog', dialog => dialog.accept());
  }

  /**
   * View case details
   */
  async viewCase(index: number): Promise<void> {
    const card = this.caseCards.nth(index);
    const viewBtn = card.locator('button[title="View details"]').first();
    await viewBtn.click();
  }

  // ── Getters ────────────────────────────────────────────────────────

  /**
   * Get case count
   */
  async getCaseCount(): Promise<number> {
    return this.caseCards.count();
  }

  /**
   * Get case name at index
   */
  async getCaseName(index: number): Promise<string | null> {
    const card = this.caseCards.nth(index);
    return card.locator('h3').textContent();
  }

  /**
   * Get case company at index
   */
  async getCaseCompany(index: number): Promise<string | null> {
    const card = this.caseCards.nth(index);
    return card.locator('text=/^[^·]+/').first().textContent();
  }

  // ── Assertions ─────────────────────────────────────────────────────

  /**
   * Assert page loaded successfully
   */
  async assertPageLoaded(): Promise<void> {
    await expect(this.header).toBeVisible();
    await expect(this.newCaseButton).toBeVisible();
  }

  /**
   * Assert stats are displayed
   */
  async assertStatsVisible(): Promise<void> {
    await expect(this.totalValueCard).toBeVisible();
    await expect(this.activeCountCard).toBeVisible();
  }
}
