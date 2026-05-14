import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for TargetsAdmin
 *
 * Route: /context/targets
 * Tier: admin
 */
export class TargetsAdminPage {
  readonly page: Page;

  // Header
  readonly heading: Locator;
  readonly newTargetButton: Locator;
  readonly refreshButton: Locator;

  // Stats strip
  readonly statsStrip: Locator;

  // Tabs
  readonly allTargetsTab: Locator;
  readonly scheduledTab: Locator;
  readonly complianceFailuresTab: Locator;
  readonly eventsTab: Locator;

  // Filter bar
  readonly searchInput: Locator;

  // Table
  readonly table: Locator;
  readonly emptyState: Locator;
  readonly loadingSkeleton: Locator;

  // Bulk toolbar
  readonly bulkToolbar: Locator;
  readonly bulkPauseButton: Locator;
  readonly bulkRunButton: Locator;
  readonly bulkArchiveButton: Locator;
  readonly bulkClearButton: Locator;

  // Archive dialog
  readonly archiveDialog: Locator;
  readonly archiveConfirmButton: Locator;
  readonly archiveCancelButton: Locator;

  // Side panels
  readonly detailPanel: Locator;
  readonly formPanel: Locator;

  constructor(page: Page) {
    this.page = page;

    this.heading = page.getByRole('heading', { name: /^targets$/i });
    this.newTargetButton = page.getByRole('button', { name: /new target/i });
    this.refreshButton = page.getByRole('button', { name: /refresh/i }).first();

    this.statsStrip = page.locator('[class*="grid"][class*="grid-cols"]').first();

    this.allTargetsTab = page.getByRole('tab', { name: /all targets/i });
    this.scheduledTab = page.getByRole('tab', { name: /scheduled/i });
    this.complianceFailuresTab = page.getByRole('tab', { name: /compliance failures/i });
    this.eventsTab = page.getByRole('tab', { name: /events/i });

    this.searchInput = page.getByPlaceholder('Search targets…');

    this.table = page.locator('table');
    this.emptyState = page.getByText('No targets found');
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();

    this.bulkToolbar = page.getByText(/\d+ selected/);
    this.bulkPauseButton = page.getByRole('button', { name: /^pause$/i });
    this.bulkRunButton = page.getByRole('button', { name: /^run$/i });
    this.bulkArchiveButton = page.getByRole('button', { name: /^archive$/i });
    this.bulkClearButton = page.getByRole('button', { name: /^clear$/i });

    this.archiveDialog = page.getByRole('alertdialog');
    this.archiveConfirmButton = page.getByRole('alertdialog').getByRole('button', { name: /archive/i });
    this.archiveCancelButton = page.getByRole('alertdialog').getByRole('button', { name: /cancel/i });

    this.detailPanel = page.locator('[data-state="open"]').first();
    this.formPanel = page.locator('[data-state="open"]').first();
  }

  // ── Navigation ────────────────────────────────────────────────────

  async goto(): Promise<void> {
    await this.page.goto('/context/targets');
    await this.waitForPageLoad();
  }

  async waitForPageLoad(): Promise<void> {
    await expect(this.heading).toBeVisible({ timeout: 10000 });
  }

  async waitForDataLoad(): Promise<void> {
    // Wait for skeletons to disappear
    await this.page.waitForFunction(() => {
      const skeletons = document.querySelectorAll('[class*="skeleton"]');
      return skeletons.length === 0;
    }, { timeout: 10000 }).catch(() => {
      // Skeletons may not appear at all if data loads fast
    });
  }

  // ── Actions ───────────────────────────────────────────────────────

  async clickNewTarget(): Promise<void> {
    await this.newTargetButton.click();
  }

  async clickRefresh(): Promise<void> {
    await this.refreshButton.click();
  }

  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
  }

  async clickTab(tab: 'all' | 'scheduled' | 'failures' | 'events'): Promise<void> {
    const tabMap = {
      all: this.allTargetsTab,
      scheduled: this.scheduledTab,
      failures: this.complianceFailuresTab,
      events: this.eventsTab,
    };
    await tabMap[tab].click();
  }

  async clickRowByName(name: string): Promise<void> {
    await this.page.getByRole('cell', { name }).click();
  }

  async openRowActions(rowIndex = 0): Promise<void> {
    const actionBtns = this.page.getByRole('button', { name: /target actions/i });
    await actionBtns.nth(rowIndex).click();
  }

  async clickRowAction(action: 'Run now' | 'Pause' | 'Resume' | 'Archive'): Promise<void> {
    await this.page.getByRole('menuitem', { name: new RegExp(action, 'i') }).click();
  }

  async selectRowCheckbox(rowIndex: number): Promise<void> {
    // Index 0 is "select all"; row checkboxes start at 1
    const checkboxes = this.page.getByRole('checkbox');
    await checkboxes.nth(rowIndex + 1).click();
  }

  async selectAllCheckbox(): Promise<void> {
    await this.page.getByRole('checkbox').first().click();
  }

  async confirmArchive(): Promise<void> {
    await this.archiveConfirmButton.click();
  }

  async cancelArchive(): Promise<void> {
    await this.archiveCancelButton.click();
  }

  // ── Assertions ─────────────────────────────────────────────────────

  async assertPageLoaded(): Promise<void> {
    await expect(this.heading).toBeVisible();
    await expect(this.newTargetButton).toBeVisible();
  }

  async assertTabsVisible(): Promise<void> {
    await expect(this.allTargetsTab).toBeVisible();
    await expect(this.scheduledTab).toBeVisible();
    await expect(this.complianceFailuresTab).toBeVisible();
    await expect(this.eventsTab).toBeVisible();
  }

  async assertTargetVisible(name: string): Promise<void> {
    await expect(this.page.getByText(name)).toBeVisible();
  }

  async assertEmptyState(): Promise<void> {
    await expect(this.emptyState).toBeVisible();
  }

  async assertBulkToolbarVisible(count: number): Promise<void> {
    await expect(this.page.getByText(`${count} selected`)).toBeVisible();
  }

  async assertArchiveDialogVisible(): Promise<void> {
    await expect(this.archiveDialog).toBeVisible();
    await expect(this.page.getByText('Archive this target?')).toBeVisible();
  }

  async getRowCount(): Promise<number> {
    return this.table.locator('tbody tr').count();
  }
}
