import { test, expect, Page } from '@playwright/test';
import { ValueTreeExplorerPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

type MockState = 'success' | 'empty' | 'error' | 'loading';

const ROOT_ENTITY_ID = 'cap-root-1';

const mockEntitiesResponse = {
  results: [
    {
      id: ROOT_ENTITY_ID,
      name: 'Customer Success Automation',
      entity_type: 'Capability',
      domain: 'SaaS',
      status: 'validated',
      confidence: 0.92,
      confidence_label: 'high',
      updated_at: '2026-01-15T00:00:00.000Z',
    },
  ],
  total_count: 1,
  filtered_count: 1,
  limit: 25,
  offset: 0,
  has_more: false,
  available_domains: ['SaaS'],
  available_sources: ['test'],
};

const mockTreeResponse = {
  root_entity_id: ROOT_ENTITY_ID,
  direction: 'upward',
  nodes: [
    {
      id: ROOT_ENTITY_ID,
      label: 'Customer Success Automation',
      type: 'Capability',
      layer: 1,
      confidence: 0.9,
      properties: {},
    },
    {
      id: 'use-1',
      label: 'Reduce Churn',
      type: 'UseCase',
      layer: 2,
      confidence: 0.8,
      properties: {},
    },
    {
      id: 'driver-1',
      label: 'Net Revenue Retention',
      type: 'ValueDriver',
      layer: 3,
      confidence: 0.85,
      properties: {},
    },
  ],
  edges: [
    { source: ROOT_ENTITY_ID, target: 'use-1', type: 'ENABLES', weight: 0.9 },
    { source: 'use-1', target: 'driver-1', type: 'DRIVES', weight: 0.8 },
  ],
  paths: [{ length: 3, nodes: [ROOT_ENTITY_ID, 'use-1', 'driver-1'] }],
  stats: {
    total_nodes: 3,
    total_edges: 2,
    max_depth: 3,
    by_layer: { '1': 1, '2': 1, '3': 1 },
  },
};

async function mockValueTreeApi(page: Page, state: MockState): Promise<void> {
  await page.route('**/api/graph/entities**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockEntitiesResponse),
    });
  });

  await page.route('**/api/graph/value-trees/**', async (route) => {
    if (state === 'error') {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Synthetic value-tree failure' }),
      });
      return;
    }

    if (state === 'loading') {
      await new Promise((resolve) => setTimeout(resolve, 1200));
    }

    const body = state === 'empty'
      ? { ...mockTreeResponse, nodes: [], edges: [], stats: { ...mockTreeResponse.stats, total_nodes: 0, total_edges: 0, max_depth: 0, by_layer: {} } }
      : mockTreeResponse;

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}

test.describe('Value Tree Explorer', () => {
  let valueTree: ValueTreeExplorerPage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'advanced');
    valueTree = new ValueTreeExplorerPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test('renders root entity selector and view toggles', async ({ page }) => {
    await mockValueTreeApi(page, 'success');
    await valueTree.goto(ROOT_ENTITY_ID);

    await expect(valueTree.rootEntitySelector).toBeVisible();
    await valueTree.openRootEntitySelector();
    await expect(page.getByRole('button', { name: /Customer Success Automation/i })).toBeVisible();

    await expect(valueTree.visualToggle).toBeVisible();
    await expect(valueTree.outlineToggle).toBeVisible();

    await valueTree.switchToOutlineView();
    await expect(valueTree.outlineCanvas).toBeVisible();

    await valueTree.switchToVisualView();
    await expect(valueTree.treeCanvas).toBeVisible();
  });

  test('renders value-tree stats from API response', async ({ page }) => {
    await mockValueTreeApi(page, 'success');
    await valueTree.goto(ROOT_ENTITY_ID);

    await expect(valueTree.statsBar).toBeVisible();
    await expect(valueTree.nodesStatValue).toContainText('3');
    await expect(valueTree.edgesStatValue).toContainText('2');
    await expect(valueTree.maxDepthStatValue).toContainText('3');
  });

  test('shows loading skeleton while value-tree API is pending', async ({ page }) => {
    await mockValueTreeApi(page, 'loading');
    await valueTree.goto(ROOT_ENTITY_ID);

    await expect(valueTree.loadingSkeleton).toBeVisible();
  });

  test('shows empty state when no root entity is selected', async ({ page }) => {
    await mockValueTreeApi(page, 'success');
    await valueTree.goto();

    await expect(valueTree.emptyNoEntityState).toBeVisible();
    await expect(page.getByText(/Select a root entity/i)).toBeVisible();
  });

  test('shows empty tree state when API returns no graph nodes', async ({ page }) => {
    await mockValueTreeApi(page, 'empty');
    await valueTree.goto(ROOT_ENTITY_ID);

    await expect(valueTree.emptyNoTreeState).toBeVisible();
    await expect(page.getByText(/connected value relationships/i)).toBeVisible();
  });

  test('shows API-backed error state when value-tree API fails', async ({ page }) => {
    await mockValueTreeApi(page, 'error');
    await valueTree.goto(ROOT_ENTITY_ID);

    await expect(valueTree.errorState).toBeVisible();
    await expect(page.getByText(/Synthetic value-tree failure|Failed to fetch/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Retry/i })).toBeVisible();
  });

  test.describe('Access Control', () => {
    test('requires advanced tier to access', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/studio/value-model');
      await expect(page).toHaveURL(/\/home/);
    });
  });
});
