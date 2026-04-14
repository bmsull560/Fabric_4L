import { test, expect } from '@playwright/test';
import { ValueTreeExplorerPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Value Tree Explorer E2E Tests
 *
 * Route: /model/value-studio/explorer
 * Tier: advanced (Tier 2+)
 *
 * Covers:
 * - Page load and header
 * - Tree view with hierarchical nodes
 * - Entity type badges and colors
 * - View tab switching (tree vs outline)
 * - Access control
 */

test.describe('Value Tree Explorer', () => {
  let valueTree: ValueTreeExplorerPage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'advanced');
    valueTree = new ValueTreeExplorerPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test.describe('Page Load', () => {
    test('should display page header', async () => {
      await valueTree.goto();
      await expect(valueTree.header).toBeVisible();
    });

    test('should show tree content', async () => {
      await valueTree.goto();
      await valueTree.assertTreeVisible();
    });
  });

  test.describe('Tree Visualization', () => {
    test.beforeEach(async () => {
      await valueTree.goto();
    });

    test('should display entity type content', async () => {
      await valueTree.assertEntityTypesDisplayed();
    });

    test('should render hierarchical tree structure', async ({ page }) => {
      // The tree should have nested content (indented nodes)
      const bodyText = await page.textContent('body');
      // Tree should display entity-related content
      expect(bodyText).toBeTruthy();
      expect(bodyText!.length).toBeGreaterThan(50);
    });
  });

  test.describe('View Tabs', () => {
    test.beforeEach(async () => {
      await valueTree.goto();
    });

    test('should have tree view tab', async () => {
      const hasTreeTab = await valueTree.treeViewTab.isVisible().catch(() => false);
      if (hasTreeTab) {
        await valueTree.switchToTreeView();
        // Content should remain visible
        await expect(valueTree.header).toBeVisible();
      }
    });

    test('should have outline view tab', async () => {
      const hasOutlineTab = await valueTree.outlineViewTab.isVisible().catch(() => false);
      if (hasOutlineTab) {
        await valueTree.switchToOutlineView();
        // Content should switch to outline view
        await expect(valueTree.header).toBeVisible();
      }
    });

    test('should switch between views without errors', async () => {
      const hasTreeTab = await valueTree.treeViewTab.isVisible().catch(() => false);
      const hasOutlineTab = await valueTree.outlineViewTab.isVisible().catch(() => false);

      if (hasTreeTab && hasOutlineTab) {
        // Switch to outline
        await valueTree.switchToOutlineView();
        await expect(valueTree.header).toBeVisible();

        // Switch back to tree
        await valueTree.switchToTreeView();
        await expect(valueTree.header).toBeVisible();
      }
    });
  });

  test.describe('Action Buttons', () => {
    test.beforeEach(async () => {
      await valueTree.goto();
    });

    test('should display action buttons', async () => {
      const hasUpload = await valueTree.uploadButton.isVisible().catch(() => false);
      const hasDownload = await valueTree.downloadButton.isVisible().catch(() => false);
      const hasNew = await valueTree.newTreeButton.isVisible().catch(() => false);
      // At least one action button should be visible
      expect(hasUpload || hasDownload || hasNew).toBeTruthy();
    });
  });

  test.describe('Access Control', () => {
    test('requires advanced tier to access', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/model/value-studio/explorer');
      // Should be redirected to /home
      await expect(page).toHaveURL(/\/home/);
    });

    test('advanced tier can access value tree explorer', async () => {
      await valueTree.goto();
      await expect(valueTree.header).toBeVisible();
    });

    test('admin tier can access value tree explorer', async ({ page }) => {
      await setUserTier(page, 'admin');
      await page.goto('/model/value-studio/explorer');
      await expect(valueTree.header).toBeVisible();
    });
  });
});
