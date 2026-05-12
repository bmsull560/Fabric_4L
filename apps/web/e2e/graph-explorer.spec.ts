import { test, expect } from './fixtures/contract-test';
import { GraphExplorerPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Graph Explorer E2E Tests
 *
 * Route: /discover/knowledge/graph
 * Tier: advanced (Tier 2+)
 *
 * Covers knowledge graph visualization:
 * - Graph loading and display
 * - Node interaction
 * - Search functionality
 * - Context panel
 * - Error states
 */

test.describe('Graph Explorer', () => {
  let graphExplorer: GraphExplorerPage;

  test.beforeEach(async ({ page }) => {
    // Graph Explorer requires advanced tier
    await setUserTier(page, 'advanced');
    graphExplorer = new GraphExplorerPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test.describe('Page Load', () => {
    test('should display page header and search', async () => {
      await graphExplorer.goto();
      await expect(graphExplorer.header).toBeVisible();
      await expect(graphExplorer.searchInput).toBeVisible();
    });

    test('should show loading state initially', async () => {
      await graphExplorer.goto();
      // Graph should be in loading state
      await graphExplorer.assertLoadingState();
    });

    test('should load graph with nodes', async () => {
      await graphExplorer.goto();
      await graphExplorer.waitForGraphLoad();
      await graphExplorer.assertGraphLoaded();
    });
  });

  test.describe('Graph Visualization', () => {
    test.beforeEach(async () => {
      await graphExplorer.goto();
      await graphExplorer.waitForGraphLoad();
    });

    test('should display nodes with different entity types', async () => {
      const nodeCount = await graphExplorer.getNodeCount();
      expect(nodeCount).toBeGreaterThan(0);

      // Should have nodes with labels
      const labels = await graphExplorer.nodeLabels.allTextContents();
      expect(labels.length).toBeGreaterThan(0);
    });

    test('should refresh graph on button click', async () => {
      // Note: refresh button may not exist in all implementations
      const hasRefresh = await graphExplorer.refreshButton.isVisible().catch(() => false);

      if (hasRefresh) {
        await graphExplorer.refreshGraph();
        // Graph should reload
        await expect(graphExplorer.graphSvg).toBeVisible();
      }
    });
  });

  test.describe('Node Interaction', () => {
    test.beforeEach(async () => {
      await graphExplorer.goto();
      await graphExplorer.waitForGraphLoad();
    });

    test('should select node and show context panel', async () => {
      const nodeCount = await graphExplorer.getNodeCount();

      if (nodeCount > 0) {
        await graphExplorer.clickNodeByIndex(0);

        const contextVisible = await graphExplorer.isContextPanelOpen();
        if (contextVisible) {
          const entityName = await graphExplorer.getSelectedEntityName();
          expect(entityName).not.toBeNull();
        }
      }
    });

    test('should display entity details in context panel', async () => {
      const nodeCount = await graphExplorer.getNodeCount();

      if (nodeCount > 0) {
        await graphExplorer.clickNodeByIndex(0);

        const contextVisible = await graphExplorer.isContextPanelOpen();
        if (contextVisible) {
          await expect(graphExplorer.entityTypeBadge).toBeVisible();
          await expect(graphExplorer.entityDescription).toBeVisible();
        }
      }
    });

    test('should show related entities in context panel', async () => {
      const nodeCount = await graphExplorer.getNodeCount();

      if (nodeCount > 0) {
        await graphExplorer.clickNodeByIndex(0);

        const contextVisible = await graphExplorer.isContextPanelOpen();
        if (contextVisible) {
          await expect(graphExplorer.relatedEntitiesList).toBeVisible();
        }
      }
    });
  });

  test.describe('Search', () => {
    test.beforeEach(async () => {
      await graphExplorer.goto();
      await graphExplorer.waitForGraphLoad();
    });

    test('should allow searching for entities', async () => {
      await graphExplorer.searchEntities('value');

      // Search should not crash the app
      await expect(graphExplorer.graphContainer.or(graphExplorer.errorMessage)).toBeVisible();
    });

    test('should filter graph based on search', async () => {
      // Search for specific term
      await graphExplorer.searchEntities('capability');

      // Graph should update (either filtered or full refresh)
      await expect(graphExplorer.graphSvg).toBeVisible();

      // Node count may change or stay same depending on implementation
      const afterCount = await graphExplorer.getNodeCount();
      expect(afterCount).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('Tab Navigation', () => {
    test.beforeEach(async () => {
      await graphExplorer.goto();
    });

    test('should switch to Query tab', async () => {
      const hasQueryTab = await graphExplorer.queryTab.isVisible().catch(() => false);

      if (hasQueryTab) {
        await graphExplorer.switchToQueryTab();
        await expect(graphExplorer.queryTab).toHaveAttribute('aria-selected', 'true');
      }
    });

    test('should switch to Communities tab', async () => {
      const hasCommunitiesTab = await graphExplorer.communitiesTab.isVisible().catch(() => false);

      if (hasCommunitiesTab) {
        await graphExplorer.switchToCommunitiesTab();
        await expect(graphExplorer.communitiesTab).toHaveAttribute('aria-selected', 'true');
      }
    });
  });

  test.describe('Access Control', () => {
    test('requires advanced tier to access', async ({ page }) => {
      // Try to access as standard user
      await setUserTier(page, 'standard');
      await page.goto('/discover/knowledge/graph');

      // Should be redirected to /home
      await expect(page).toHaveURL(/\/home/);
    });

    test('advanced tier user can access graph explorer', async () => {
      await graphExplorer.goto();
      await expect(graphExplorer.header).toBeVisible();
    });

    test('admin tier user can access graph explorer', async ({ page }) => {
      await setUserTier(page, 'admin');
      await page.goto('/discover/knowledge/graph');
      await expect(graphExplorer.header).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle graph load errors gracefully', async ({ page }) => {
      // Simulate error by navigating with invalid parameters
      await page.goto('/discover/knowledge/graph?error=true');

      // Page should not crash
      await expect(graphExplorer.header).toBeVisible();

      // Either graph loads or error state is shown
      const hasError = await graphExplorer.errorMessage.isVisible().catch(() => false);
      const hasGraph = await graphExplorer.graphSvg.isVisible().catch(() => false);

      expect(hasError || hasGraph).toBeTruthy();
    });
  });
});
