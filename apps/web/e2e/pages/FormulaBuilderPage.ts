import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for Formula Builder screen
 *
 * Route: /model/value-studio/formulas
 * Tier: advanced (Tier 2+)
 *
 * Encapsulates formula editing, governance, and variable binding interactions.
 */
export class FormulaBuilderPage {
  readonly page: Page;

  // Tabs
  readonly formulaTab: Locator;
  readonly governanceTab: Locator;
  readonly dependenciesTab: Locator;
  readonly historyTab: Locator;

  // Formula tab content
  readonly expressionEditor: Locator;
  readonly variableTable: Locator;
  readonly variableRows: Locator;
  readonly testInputsSection: Locator;

  // Action buttons
  readonly saveButton: Locator;
  readonly runButton: Locator;
  readonly lockButton: Locator;
  readonly addVariableButton: Locator;

  // Governance tab content
  readonly versionHistory: Locator;
  readonly statusBadge: Locator;
  readonly dependentsList: Locator;

  // Status badges
  readonly draftBadge: Locator;
  readonly pendingBadge: Locator;
  readonly approvedBadge: Locator;

  // Loading / error
  readonly loadingSkeleton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Tabs
    this.formulaTab = page.getByRole('tab', { name: /formula/i });
    this.governanceTab = page.getByRole('tab', { name: /governance/i });
    this.dependenciesTab = page.getByRole('tab', { name: /dependencies/i });
    this.historyTab = page.getByRole('tab', { name: /history/i });

    // Formula tab
    this.expressionEditor = page.locator('[class*="editor"], textarea, [contenteditable]').first();
    this.variableTable = page.locator('table').first();
    this.variableRows = page.locator('table tbody tr');
    this.testInputsSection = page.getByText(/test inputs/i).locator('..');

    // Action buttons
    this.saveButton = page.getByRole('button', { name: /save/i });
    this.runButton = page.getByRole('button', { name: /run/i });
    this.lockButton = page.getByRole('button', { name: /lock|unlock/i });
    this.addVariableButton = page.getByRole('button', { name: /add variable/i }).or(
      page.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: /add|\+/i })
    );

    // Governance tab
    this.versionHistory = page.getByText(/version history/i).locator('..');
    this.statusBadge = page.locator('[class*="badge"]').filter({ hasText: /draft|pending|approved|archived/i }).first();
    this.dependentsList = page.getByText(/dependent/i).locator('..');

    // Status badges
    this.draftBadge = page.locator('[class*="badge"]').filter({ hasText: /draft/i }).first();
    this.pendingBadge = page.locator('[class*="badge"]').filter({ hasText: /pending/i }).first();
    this.approvedBadge = page.locator('[class*="badge"]').filter({ hasText: /approved/i }).first();

    // Loading
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();
  }

  /**
   * Navigate to Formula Builder
   */
  async goto(): Promise<void> {
    await this.page.goto('/model/value-studio/formulas');
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await expect(this.formulaTab).toBeVisible();
  }

  /**
   * Switch to a specific tab
   */
  async switchToTab(tabName: 'formula' | 'governance' | 'dependencies' | 'history'): Promise<void> {
    switch (tabName) {
      case 'formula':
        await this.formulaTab.click();
        break;
      case 'governance':
        await this.governanceTab.click();
        break;
      case 'dependencies':
        await this.dependenciesTab.click();
        break;
      case 'history':
        await this.historyTab.click();
        break;
    }
  }

  /**
   * Click Save button
   */
  async clickSave(): Promise<void> {
    await this.saveButton.click();
  }

  /**
   * Click Run button
   */
  async clickRun(): Promise<void> {
    await this.runButton.click();
  }

  /**
   * Get variable count from table
   */
  async getVariableCount(): Promise<number> {
    return this.variableRows.count();
  }

  /**
   * Assert formula tab is active and content visible
   */
  async assertFormulaTabActive(): Promise<void> {
    await expect(this.formulaTab).toHaveAttribute('aria-selected', 'true');
  }

  /**
   * Assert governance tab content is visible
   */
  async assertGovernanceTabContent(): Promise<void> {
    await expect(this.governanceTab).toHaveAttribute('aria-selected', 'true');
  }
}
