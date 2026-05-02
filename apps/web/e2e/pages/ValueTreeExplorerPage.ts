import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for Value Tree Explorer screen.
 *
 * Mounted route currently resolves under studio workspace account routing.
 */
export class ValueTreeExplorerPage {
  readonly page: Page;

  readonly header: Locator;
  readonly rootEntitySelector: Locator;
  readonly rootEntityMenuLabel: Locator;

  readonly visualToggle: Locator;
  readonly outlineToggle: Locator;

  readonly statsBar: Locator;
  readonly nodesStatValue: Locator;
  readonly edgesStatValue: Locator;
  readonly maxDepthStatValue: Locator;

  readonly loadingSkeleton: Locator;
  readonly emptyNoEntityState: Locator;
  readonly emptyNoTreeState: Locator;
  readonly errorState: Locator;

  readonly treeCanvas: Locator;
  readonly outlineCanvas: Locator;

  constructor(page: Page) {
    this.page = page;

    this.header = page.getByRole('heading', { name: /^Tree Explorer$/i });
    this.rootEntitySelector = page.getByRole('button', {
      name: /select tree|change root entity|select entity/i,
    });
    this.rootEntityMenuLabel = page.getByText(/select root entity/i);

    this.visualToggle = page.getByRole('button', { name: /^Visual$/i });
    this.outlineToggle = page.getByRole('button', { name: /^Outline$/i });

    this.statsBar = page.locator('div').filter({ hasText: /^Nodes\d+Edges\d+Max Depth\d+/ }).first();
    this.nodesStatValue = page.locator('div').filter({ has: page.getByText(/^Nodes$/i) }).locator('p').first();
    this.edgesStatValue = page.locator('div').filter({ has: page.getByText(/^Edges$/i) }).locator('p').first();
    this.maxDepthStatValue = page.locator('div').filter({ has: page.getByText(/^Max Depth$/i) }).locator('p').first();

    this.loadingSkeleton = page.locator('.animate-pulse').first();
    this.emptyNoEntityState = page.getByRole('heading', { name: /No Entity Selected/i });
    this.emptyNoTreeState = page.getByRole('heading', { name: /No Value Tree Found/i });
    this.errorState = page.getByRole('heading', { name: /Failed to load value tree/i });

    this.treeCanvas = page.locator('div').filter({ has: page.getByText(/▲|▼/) }).first();
    this.outlineCanvas = page.locator('div').filter({ has: page.getByText(/─/) }).first();
  }

  async goto(entityId?: string): Promise<void> {
    const query = entityId ? `?entityId=${encodeURIComponent(entityId)}` : '';
    await this.page.goto(`/studio/value-model${query}`);
    await this.waitForPageLoad();
  }

  async waitForPageLoad(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  async openRootEntitySelector(): Promise<void> {
    await this.rootEntitySelector.click();
    await expect(this.rootEntityMenuLabel).toBeVisible();
  }

  async switchToOutlineView(): Promise<void> {
    await this.outlineToggle.click();
  }

  async switchToVisualView(): Promise<void> {
    await this.visualToggle.click();
  }
}
