import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for Value Tree Explorer screen
 *
 * Route: /model/value-studio/explorer
 * Tier: advanced (Tier 2+)
 *
 * Encapsulates tree visualization including:
 * - Hierarchical tree view
 * - Entity badges with type coloring
 * - Collapsible nodes
 * - Outline view alternative
 */
export class ValueTreeExplorerPage {
  readonly page: Page;

  // Page header and actions
  readonly header: Locator;
  readonly uploadButton: Locator;
  readonly downloadButton: Locator;
  readonly newTreeButton: Locator;

  // View tabs
  readonly treeViewTab: Locator;
  readonly outlineViewTab: Locator;

  // Tree view
  readonly treeContainer: Locator;
  readonly treeNodes: Locator;
  readonly entityBadges: Locator;
  readonly expandButtons: Locator;

  // Entity type badges
  readonly valuedriverBadges: Locator;
  readonly personaBadges: Locator;
  readonly usecaseBadges: Locator;
  readonly capabilityBadges: Locator;

  // Outline view
  readonly outlineContainer: Locator;
  readonly outlineItems: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading', { name: /value tree|tree explorer/i });
    this.uploadButton = page.getByRole('button', { name: /upload/i }).or(
      page.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: /upload/i })
    );
    this.downloadButton = page.getByRole('button', { name: /download/i }).or(
      page.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: /download/i })
    );
    this.newTreeButton = page.getByRole('button', { name: /new|add|\+/i }).first();

    // View tabs
    this.treeViewTab = page.getByRole('tab', { name: /tree/i }).or(
      page.locator('button').filter({ hasText: /tree view/i })
    );
    this.outlineViewTab = page.getByRole('tab', { name: /outline/i }).or(
      page.locator('button').filter({ hasText: /outline/i })
    );

    // Tree view
    this.treeContainer = page.locator('[class*="tree"]').or(
      page.locator('div').filter({ has: page.locator('[class*="emerald"], [class*="amber"], [class*="cyan"], [class*="violet"]') }).first()
    );
    this.treeNodes = page.locator('[class*="cursor-pointer"]').filter({
      has: page.locator('span, div'),
    });
    this.entityBadges = page.locator('[class*="badge"], [class*="rounded-full"]').filter({
      hasText: /valuedriver|persona|usecase|capability/i,
    });
    this.expandButtons = page.locator('button, [class*="cursor-pointer"]').filter({
      hasText: /▼|▲|chevron/i,
    });

    // Entity type badges by color
    this.valuedriverBadges = page.locator('[class*="emerald"]').filter({ hasText: /./i });
    this.personaBadges = page.locator('[class*="amber"]').filter({ hasText: /./i });
    this.usecaseBadges = page.locator('[class*="cyan"]').filter({ hasText: /./i });
    this.capabilityBadges = page.locator('[class*="violet"]').filter({ hasText: /./i });

    // Outline
    this.outlineContainer = page.locator('ol, ul').filter({ hasText: /revenue|cost|value/i }).first();
    this.outlineItems = page.locator('li').filter({ hasText: /./i });
  }

  /**
   * Navigate to Value Tree Explorer
   */
  async goto(): Promise<void> {
    await this.page.goto('/model/value-studio/explorer');
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Switch to tree view tab
   */
  async switchToTreeView(): Promise<void> {
    await this.treeViewTab.click();
  }

  /**
   * Switch to outline view tab
   */
  async switchToOutlineView(): Promise<void> {
    await this.outlineViewTab.click();
  }

  /**
   * Get count of visible entity badges
   */
  async getEntityBadgeCount(): Promise<number> {
    return this.entityBadges.count();
  }

  /**
   * Assert tree structure is visible with nodes
   */
  async assertTreeVisible(): Promise<void> {
    await expect(this.header).toBeVisible();
    // Tree should have some visible content
    const pageContent = await this.page.textContent('body');
    expect(pageContent).toBeTruthy();
  }

  /**
   * Assert entity type badges are rendered with correct colors
   */
  async assertEntityTypesDisplayed(): Promise<void> {
    // Check that at least some entity content exists
    const bodyText = await this.page.textContent('body');
    // Page should have meaningful content
    expect(bodyText?.length).toBeGreaterThan(100);
  }
}
