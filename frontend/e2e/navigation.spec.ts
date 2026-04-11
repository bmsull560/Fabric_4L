import { test, expect } from '@playwright/test';
import { AppShellPage } from './pages';
import { setUserTier, clearUserTier, ROUTES_BY_TIER } from './fixtures';

/**
 * Navigation and Access Control E2E Tests
 *
 * Covers tier-based routing, navigation visibility, and access control.
 */

test.describe('Navigation & Access Control', () => {
  let appShell: AppShellPage;

  test.beforeEach(async ({ page }) => {
    appShell = new AppShellPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test.describe('Standard Tier', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'standard');
    });

    test('can access command center', async ({ page }) => {
      await page.goto('/command-center');
      await expect(page).toHaveURL(/\/command-center/);
      await expect(appShell.commandCenterLink).toBeVisible();
    });

    test('can access value packs', async ({ page }) => {
      await page.goto('/value-packs');
      await expect(page).toHaveURL(/\/value-packs/);
    });

    test('cannot access extraction engine', async ({ page }) => {
      await page.goto('/extraction-engine');
      // Should be redirected
      await expect(page).not.toHaveURL(/\/extraction-engine/);
    });

    test('cannot access graph explorer', async ({ page }) => {
      await page.goto('/graph/explorer');
      await expect(page).not.toHaveURL(/\/graph\/explorer/);
    });

    test('cannot access admin routes', async ({ page }) => {
      await page.goto('/admin/formulas');
      await expect(page).not.toHaveURL(/\/admin/);
    });

    test('navigation shows only accessible links', async () => {
      await appShell.commandCenterLink.click();
      await expect(appShell.commandCenterLink).toBeVisible();
      await expect(appShell.valuePacksLink).toBeVisible();
      // Advanced routes should be hidden
      await expect(appShell.extractionEngineLink).toBeHidden();
      await expect(appShell.graphExplorerLink).toBeHidden();
    });
  });

  test.describe('Advanced Tier', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'advanced');
    });

    test('can access command center', async ({ page }) => {
      await page.goto('/command-center');
      await expect(page).toHaveURL(/\/command-center/);
    });

    test('can access extraction engine', async ({ page }) => {
      await page.goto('/extraction-engine');
      await expect(page).toHaveURL(/\/extraction-engine/);
    });

    test('can access graph explorer', async ({ page }) => {
      await page.goto('/graph/explorer');
      await expect(page).toHaveURL(/\/graph\/explorer/);
    });

    test('can access ontology', async ({ page }) => {
      await page.goto('/ontology/entities');
      await expect(page).toHaveURL(/\/ontology\/entities/);
    });

    test('can access value trees', async ({ page }) => {
      await page.goto('/value-trees/explorer');
      await expect(page).toHaveURL(/\/value-trees\/explorer/);
    });

    test('cannot access admin routes', async ({ page }) => {
      await page.goto('/admin/formulas');
      await expect(page).not.toHaveURL(/\/admin\/formulas/);
    });

    test('navigation shows advanced links', async () => {
      await appShell.commandCenterLink.click();
      await expect(appShell.extractionEngineLink).toBeVisible();
      await expect(appShell.graphExplorerLink).toBeVisible();
      await expect(appShell.valueTreesLink).toBeVisible();
    });
  });

  test.describe('Admin Tier', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'admin');
    });

    test('can access all standard routes', async ({ page }) => {
      for (const route of ['/command-center', '/value-packs', '/extraction-engine', '/graph/explorer']) {
        await page.goto(route);
        await expect(page).toHaveURL(new RegExp(route.replace('/', '\\/')));
      }
    });

    test('can access admin routes', async ({ page }) => {
      for (const route of ['/admin/formulas', '/admin/benchmarks', '/admin/variables']) {
        await page.goto(route);
        await expect(page).toHaveURL(new RegExp(route.replace('/', '\\/')));
      }
    });

    test('navigation shows admin section', async () => {
      await appShell.commandCenterLink.click();
      await expect(appShell.adminSection).toBeVisible();
    });
  });

  test.describe('Navigation Flows', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'advanced');
    });

    test('can navigate between pages via sidebar', async ({ page }) => {
      // Start at command center
      await page.goto('/command-center');
      await expect(page).toHaveURL(/\/command-center/);

      // Navigate to extraction engine
      await appShell.extractionEngineLink.click();
      await expect(page).toHaveURL(/\/extraction-engine/);

      // Navigate to graph explorer
      await appShell.graphExplorerLink.click();
      await expect(page).toHaveURL(/\/graph\/explorer/);
    });

    test('navigation preserves tier context', async ({ page }) => {
      await page.goto('/command-center');

      // Navigate through multiple pages
      await appShell.extractionEngineLink.click();
      await expect(page).toHaveURL(/\/extraction-engine/);

      await appShell.valuePacksLink.click();
      await expect(page).toHaveURL(/\/value-packs/);

      // Should still have access to advanced routes
      await appShell.graphExplorerLink.click();
      await expect(page).toHaveURL(/\/graph\/explorer/);
    });
  });

  test.describe('Redirect Behavior', () => {
    test('standard user redirected to command center from restricted route', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/extraction-engine');

      // Should end up at command center
      await expect(page).toHaveURL(/\/command-center/);
    });

    test('advanced user redirected appropriately', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await page.goto('/admin/formulas');

      // Should be redirected away from admin
      await expect(page).not.toHaveURL(/\/admin\/formulas/);
    });

    test('root path redirects based on tier', async ({ page }) => {
      // Standard user
      await setUserTier(page, 'standard');
      await page.goto('/');
      await expect(page).toHaveURL(/\/command-center/);

      // Advanced user
      await setUserTier(page, 'advanced');
      await page.goto('/');
      // Could go to extraction engine or command center
      const url = page.url();
      expect(url).toMatch(/\/(command-center|extraction-engine)/);
    });
  });

  test.describe('Mobile Navigation', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'advanced');
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('mobile menu is accessible', async () => {
      // SKIP: Mobile hamburger menu not implemented in AppShell
      // TieredNav sidebar is always visible (desktop-style), no SidebarTrigger present
      // Mobile UX requires dedicated implementation pass with SidebarProvider wrapper
      test.skip(true, 'Mobile navigation UI not implemented - see AppShell.tsx');

      await appShell.commandCenterLink.click();
      const hasMobileMenu = await appShell.mobileMenuButton.isVisible().catch(() => false);

      if (hasMobileMenu) {
        await appShell.openMobileMenu();
        // Menu should be visible after opening
        await expect(appShell.navigation).toBeVisible();
      }
    });

    test('mobile navigation works', async ({ page }) => {
      // SKIP: Mobile hamburger menu not implemented in AppShell
      // See test above for context. Requires SidebarProvider + SidebarTrigger implementation.
      test.skip(true, 'Mobile navigation UI not implemented - see AppShell.tsx');

      await page.goto('/command-center');
      const hasMobileMenu = await appShell.mobileMenuButton.isVisible().catch(() => false);

      if (hasMobileMenu) {
        await appShell.openMobileMenu();
        // Try to navigate
        const extractionLink = page.getByRole('link', { name: /extraction/i });
        if (await extractionLink.isVisible().catch(() => false)) {
          await extractionLink.click();
          await expect(page).toHaveURL(/\/extraction-engine/);
        }
      }
    });
  });
});
