import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for Admin / Governance screens
 *
 * Routes:
 *   /admin/content/formulas → FormulaGovernance
 *   /admin/content/benchmarks → BenchmarkPolicies
 *   /admin/data/variables → VariableRegistry
 * Tier: admin (Tier 3)
 *
 * Encapsulates common admin screen patterns plus specialized locators.
 */
export class AdminPage {
  readonly page: Page;

  // Common admin elements
  readonly header: Locator;
  readonly searchInput: Locator;
  readonly refreshButton: Locator;

  // ── Formula Governance ───────────────────────────────────────────
  readonly formulaGovernanceHeader: Locator;
  readonly formulaRegistryTab: Locator;
  readonly approvalQueueTab: Locator;
  readonly versionHistoryTab: Locator;
  readonly formulaTable: Locator;
  readonly formulaRows: Locator;
  readonly approveButton: Locator;
  readonly rejectButton: Locator;

  // ── Benchmark Policies ───────────────────────────────────────────
  readonly benchmarkPoliciesHeader: Locator;
  readonly benchmarkList: Locator;
  readonly confidenceBadges: Locator;
  readonly policyCards: Locator;

  // ── Variable Registry ────────────────────────────────────────────
  readonly variableRegistryHeader: Locator;
  readonly variableCatalogTab: Locator;
  readonly sourceBindingsTab: Locator;
  readonly variableTable: Locator;
  readonly variableRows: Locator;
  readonly addVariableButton: Locator;
  readonly typeBadges: Locator;
  readonly sourceBadges: Locator;
  readonly validationIcons: Locator;

  // Loading / error
  readonly loadingSkeleton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Common
    this.header = page.getByRole('heading').first();
    this.searchInput = page.getByPlaceholder(/search/i).or(
      page.locator('input[type="search"], input[type="text"]').first()
    );
    this.refreshButton = page.getByRole('button', { name: /refresh/i });

    // Formula Governance
    this.formulaGovernanceHeader = page.getByRole('heading', { name: /formula governance/i });
    this.formulaRegistryTab = page.getByRole('tab', { name: /formula registry|registry/i });
    this.approvalQueueTab = page.getByRole('tab', { name: /approval queue|approvals/i });
    this.versionHistoryTab = page.getByRole('tab', { name: /version history|versions/i });
    this.formulaTable = page.locator('table').first();
    this.formulaRows = page.locator('table tbody tr');
    this.approveButton = page.getByRole('button', { name: /approve/i });
    this.rejectButton = page.getByRole('button', { name: /reject/i });

    // Benchmark Policies
    this.benchmarkPoliciesHeader = page.getByRole('heading', { name: /benchmark policies/i });
    this.benchmarkList = page.locator('[class*="list"], table').first();
    this.confidenceBadges = page.locator('[class*="badge"]').filter({
      hasText: /high|medium|low/i,
    });
    this.policyCards = page.locator('[class*="card"], [class*="policy"]');

    // Variable Registry
    this.variableRegistryHeader = page.getByRole('heading', { name: /variable registry/i });
    this.variableCatalogTab = page.getByRole('tab', { name: /variable catalog|catalog/i });
    this.sourceBindingsTab = page.getByRole('tab', { name: /source bindings|bindings/i });
    this.variableTable = page.locator('table').first();
    this.variableRows = page.locator('table tbody tr');
    this.addVariableButton = page.getByRole('button', { name: /add variable/i }).or(
      page.locator('button').filter({ hasText: /add|\+/i }).first()
    );
    this.typeBadges = page.locator('[class*="badge"]').filter({
      hasText: /rate|currency|integer|float|boolean|string/i,
    });
    this.sourceBadges = page.locator('[class*="badge"]').filter({
      hasText: /CRM|Billing|ERP|Manual|Model|API|Database/i,
    });
    this.validationIcons = page.locator('[class*="emerald"], [class*="amber"], [class*="red"]').filter({
      has: page.locator('svg'),
    });

    // Loading / error
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();
    this.errorMessage = page.getByRole('alert').or(
      page.locator('[class*="error"]').filter({ hasText: /error/i })
    );
  }

  // ── Navigation ────────────────────────────────────────────────────

  /**
   * Navigate to Formula Governance
   */
  async gotoFormulaGovernance(): Promise<void> {
    await this.page.goto('/admin/content/formulas');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to Benchmark Policies
   */
  async gotoBenchmarkPolicies(): Promise<void> {
    await this.page.goto('/admin/content/benchmarks');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to Variable Registry
   */
  async gotoVariableRegistry(): Promise<void> {
    await this.page.goto('/admin/data/variables');
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

  // ── Formula Governance Actions ─────────────────────────────────────

  /**
   * Switch formula governance tab
   */
  async switchFormulaTab(tab: 'registry' | 'approvals' | 'versions'): Promise<void> {
    switch (tab) {
      case 'registry':
        await this.formulaRegistryTab.click();
        break;
      case 'approvals':
        await this.approvalQueueTab.click();
        break;
      case 'versions':
        await this.versionHistoryTab.click();
        break;
    }
  }

  /**
   * Get formula row count
   */
  async getFormulaRowCount(): Promise<number> {
    return this.formulaRows.count();
  }

  // ── Variable Registry Actions ──────────────────────────────────────

  /**
   * Switch variable registry tab
   */
  async switchVariableTab(tab: 'catalog' | 'bindings'): Promise<void> {
    switch (tab) {
      case 'catalog':
        await this.variableCatalogTab.click();
        break;
      case 'bindings':
        await this.sourceBindingsTab.click();
        break;
    }
  }

  /**
   * Get variable row count
   */
  async getVariableRowCount(): Promise<number> {
    return this.variableRows.count();
  }

  // ── Assertions ──────────────────────────────────────────────────────

  /**
   * Assert Formula Governance page loaded
   */
  async assertFormulaGovernanceLoaded(): Promise<void> {
    await expect(this.formulaGovernanceHeader).toBeVisible();
  }

  /**
   * Assert Benchmark Policies page loaded
   */
  async assertBenchmarkPoliciesLoaded(): Promise<void> {
    await expect(this.benchmarkPoliciesHeader).toBeVisible();
  }

  /**
   * Assert Variable Registry page loaded
   */
  async assertVariableRegistryLoaded(): Promise<void> {
    await expect(this.variableRegistryHeader).toBeVisible();
  }
}
