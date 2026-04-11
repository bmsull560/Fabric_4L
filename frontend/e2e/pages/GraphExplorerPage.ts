import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for Graph Explorer screen
 *
 * Handles interactions with the knowledge graph visualization,
 * including search, node selection, and graph navigation.
 */
export class GraphExplorerPage {
  readonly page: Page;

  // Page header and navigation
  readonly header: Locator;
  readonly searchInput: Locator;
  readonly refreshButton: Locator;

  // Graph visualization
  readonly graphContainer: Locator;
  readonly graphSvg: Locator;
  readonly loadingSpinner: Locator;
  readonly errorMessage: Locator;

  // Node elements
  readonly graphNodes: Locator;
  readonly nodeLabels: Locator;

  // Sidebar / context panel
  readonly contextPanel: Locator;
  readonly entityTypeBadge: Locator;
  readonly entityDescription: Locator;
  readonly relatedEntitiesList: Locator;

  // Tabs
  readonly graphExplorerTab: Locator;
  readonly queryTab: Locator;
  readonly communitiesTab: Locator;

  // Stats
  readonly nodeCount: Locator;
  readonly edgeCount: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header and controls
    this.header = page.getByRole('heading', { name: /graph explorer/i });
    this.searchInput = page.getByPlaceholder(/search entities/i).or(
      page.getByRole('searchbox')
    );
    this.refreshButton = page.getByRole('button', { name: /refresh/i }).or(
      page.getByLabel(/refresh graph/i)
    );

    // Graph container
    this.graphContainer = page.locator('[data-testid="graph-container"]').or(
      page.locator('svg').filter({ has: page.locator('circle') }).first()
    );
    this.graphSvg = page.locator('svg').filter({ has: page.locator('circle, [class*="node"]') }).first();
    this.loadingSpinner = page.locator('[data-testid="graph-loading"]').or(
      page.getByRole('status').filter({ hasText: /loading/i })
    );
    this.errorMessage = page.locator('[data-testid="graph-error"]').or(
      page.getByRole('alert').filter({ hasText: /error/i })
    );

    // Nodes
    this.graphNodes = this.graphSvg.locator('circle, [class*="node"], g[data-entity-id]');
    this.nodeLabels = this.graphSvg.locator('text');

    // Context panel
    this.contextPanel = page.locator('[data-testid="context-panel"]').or(
      page.locator('aside').or(page.locator('[class*="sidebar"]')).first()
    );
    this.entityTypeBadge = this.contextPanel.locator('[data-testid="entity-type"]').or(
      this.contextPanel.locator('.rounded-full').first()
    );
    this.entityDescription = this.contextPanel.locator('[data-testid="entity-description"]').or(
      this.contextPanel.locator('p').first()
    );
    this.relatedEntitiesList = this.contextPanel.locator('[data-testid="related-entities"]').or(
      this.contextPanel.locator('ul, [class*="list"]').first()
    );

    // Tabs
    this.graphExplorerTab = page.getByRole('tab', { name: /graph explorer/i });
    this.queryTab = page.getByRole('tab', { name: /query/i });
    this.communitiesTab = page.getByRole('tab', { name: /communities/i });

    // Stats
    this.nodeCount = page.locator('[data-testid="node-count"]').or(
      page.getByText(/nodes?/i).first()
    );
    this.edgeCount = page.locator('[data-testid="edge-count"]').or(
      page.getByText(/edges?/i).first()
    );
  }

  /**
   * Navigate to Graph Explorer
   */
  async goto(): Promise<void> {
    await this.page.goto('/graph/explorer');
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Wait for graph to finish loading
   */
  async waitForGraphLoad(): Promise<void> {
    await expect(this.loadingSpinner).toBeHidden();
    await expect(this.graphContainer.or(this.errorMessage)).toBeVisible();
  }

  /**
   * Search for entities in the graph
   */
  async searchEntities(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }

  /**
   * Click on a graph node by index
   */
  async clickNodeByIndex(index: number): Promise<void> {
    const node = this.graphNodes.nth(index);
    await node.click();
  }

  /**
   * Click on a graph node by entity name
   */
  async clickNodeByName(name: string): Promise<void> {
    const node = this.graphSvg.locator('text').filter({ hasText: name }).locator('..').locator('circle').first();
    await node.click();
  }

  /**
   * Get count of visible nodes
   */
  async getNodeCount(): Promise<number> {
    return this.graphNodes.count();
  }

  /**
   * Check if context panel is showing entity details
   */
  async isContextPanelOpen(): Promise<boolean> {
    return this.contextPanel.isVisible();
  }

  /**
   * Get selected entity name from context panel
   */
  async getSelectedEntityName(): Promise<string | null> {
    const heading = this.contextPanel.locator('h2, h3, [class*="title"]').first();
    return heading.textContent();
  }

  /**
   * Get selected entity type
   */
  async getSelectedEntityType(): Promise<string | null> {
    return this.entityTypeBadge.textContent();
  }

  /**
   * Refresh the graph
   */
  async refreshGraph(): Promise<void> {
    await this.refreshButton.click();
    await this.waitForGraphLoad();
  }

  /**
   * Switch to Query tab
   */
  async switchToQueryTab(): Promise<void> {
    await this.queryTab.click();
  }

  /**
   * Switch to Communities tab
   */
  async switchToCommunitiesTab(): Promise<void> {
    await this.communitiesTab.click();
  }

  /**
   * Assert graph is in loading state
   */
  async assertLoadingState(): Promise<void> {
    await expect(this.loadingSpinner).toBeVisible();
    await expect(this.graphSvg).toBeHidden();
  }

  /**
   * Assert graph loaded successfully with nodes
   */
  async assertGraphLoaded(): Promise<void> {
    await expect(this.loadingSpinner).toBeHidden();
    await expect(this.graphSvg).toBeVisible();
    const nodeCount = await this.getNodeCount();
    expect(nodeCount).toBeGreaterThan(0);
  }

  /**
   * Assert error state is displayed
   */
  async assertErrorState(): Promise<void> {
    await expect(this.loadingSpinner).toBeHidden();
    await expect(this.errorMessage).toBeVisible();
  }

  /**
   * Assert node selection shows context panel
   */
  async assertNodeSelectionShowsContext(): Promise<void> {
    await this.clickNodeByIndex(0);
    await expect(this.contextPanel).toBeVisible();
    const entityName = await this.getSelectedEntityName();
    expect(entityName).not.toBeNull();
  }
}
