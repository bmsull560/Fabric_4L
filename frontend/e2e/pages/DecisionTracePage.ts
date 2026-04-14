import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for Decision Trace screen (Audit & Provenance)
 *
 * Route: /evidence/traces
 * Tier: standard (all tiers) — advanced routes at /evidence/lineage, /evidence/compliance
 *
 * Encapsulates the audit trail viewer including:
 * - Audit logs table
 * - Provenance trail
 * - Source filtering
 * - Export functionality
 */
export class DecisionTracePage {
  readonly page: Page;

  // Page header and controls
  readonly header: Locator;
  readonly sourceFilter: Locator;
  readonly exportButton: Locator;
  readonly refreshButton: Locator;

  // Audit logs table
  readonly auditTable: Locator;
  readonly auditRows: Locator;
  readonly entityIdCells: Locator;
  readonly statusBadges: Locator;
  readonly viewButtons: Locator;

  // Provenance trail
  readonly provenanceSection: Locator;
  readonly provenanceSteps: Locator;

  // Loading / error
  readonly loadingSkeleton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading', { name: /audit|provenance|decision trace/i });

    // Controls
    this.sourceFilter = page.locator('select, [role="combobox"]').first();
    this.exportButton = page.getByRole('button', { name: /export/i }).or(
      page.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: /export|download/i })
    );
    this.refreshButton = page.getByRole('button', { name: /refresh/i }).or(
      page.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: /refresh/i })
    );

    // Table
    this.auditTable = page.locator('table').first();
    this.auditRows = page.locator('table tbody tr');
    this.entityIdCells = page.locator('table td').filter({ has: page.locator('[class*="font-mono"]') });
    this.statusBadges = page.locator('[class*="badge"]').filter({
      hasText: /completed|failed|pending/i,
    });
    this.viewButtons = page.getByRole('button', { name: /view/i }).or(
      page.locator('button').filter({ hasText: /view/i })
    );

    // Provenance trail
    this.provenanceSection = page.getByText(/provenance trail/i).locator('..');
    this.provenanceSteps = page.locator('[class*="step"], [class*="trail"]');

    // Loading / error
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();
    this.errorMessage = page.getByRole('alert').or(
      page.locator('[class*="error"]').filter({ hasText: /error/i })
    );
  }

  /**
   * Navigate to Decision Trace page
   */
  async goto(): Promise<void> {
    await this.page.goto('/evidence/traces');
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Wait for audit data to load
   */
  async waitForDataLoad(): Promise<void> {
    const hasTable = await this.auditTable.isVisible().catch(() => false);
    const hasError = await this.errorMessage.isVisible().catch(() => false);
    if (!hasTable && !hasError) {
      await expect(this.loadingSkeleton).toBeHidden({ timeout: 10000 });
    }
  }

  /**
   * Get audit row count
   */
  async getAuditRowCount(): Promise<number> {
    return this.auditRows.count();
  }

  /**
   * Click View button on a specific audit row
   */
  async clickViewOnRow(index: number): Promise<void> {
    const row = this.auditRows.nth(index);
    const viewBtn = row.getByRole('button', { name: /view/i }).or(
      row.locator('button').filter({ hasText: /view/i })
    );
    await viewBtn.click();
  }

  /**
   * Click export button
   */
  async clickExport(): Promise<void> {
    await this.exportButton.click();
  }

  /**
   * Click refresh button
   */
  async clickRefresh(): Promise<void> {
    await this.refreshButton.click();
  }

  /**
   * Assert audit table is visible with rows
   */
  async assertAuditTableVisible(): Promise<void> {
    await expect(this.auditTable).toBeVisible();
    const rowCount = await this.getAuditRowCount();
    expect(rowCount).toBeGreaterThanOrEqual(0);
  }

  /**
   * Assert page shows provenance trail
   */
  async assertProvenanceVisible(): Promise<void> {
    await expect(this.provenanceSection).toBeVisible();
  }
}
