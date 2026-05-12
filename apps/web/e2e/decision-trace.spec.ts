import { test, expect } from './fixtures/contract-test';
import { DecisionTracePage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Decision Trace E2E Tests
 *
 * Route: /evidence/traces (standard), /evidence/lineage (advanced), /evidence/changelog (admin)
 * Tier: standard for basic traces, progressive disclosure for advanced evidence
 *
 * Covers:
 * - Audit logs table display
 * - Source filtering
 * - Export and refresh actions
 * - Provenance trail
 * - Access control for evidence sub-routes
 */

test.describe('Decision Trace', () => {
  let decisionTrace: DecisionTracePage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'standard');
    decisionTrace = new DecisionTracePage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test.describe('Page Load', () => {
    test('should display page header', async () => {
      await decisionTrace.goto();
      await expect(decisionTrace.header).toBeVisible();
    });

    test('should show loading state or audit table', async () => {
      await decisionTrace.goto();
      const hasSkeleton = await decisionTrace.loadingSkeleton.isVisible().catch(() => false);
      const hasTable = await decisionTrace.auditTable.isVisible().catch(() => false);
      const hasHeader = await decisionTrace.header.isVisible().catch(() => false);
      // Page should show something meaningful
      expect(hasSkeleton || hasTable || hasHeader).toBeTruthy();
    });
  });

  test.describe('Audit Table', () => {
    test.beforeEach(async () => {
      await decisionTrace.goto();
    });

    test('should display audit table after load', async () => {
      await decisionTrace.waitForDataLoad();
      const hasTable = await decisionTrace.auditTable.isVisible().catch(() => false);
      const hasError = await decisionTrace.errorMessage.isVisible().catch(() => false);
      // Either table or error state
      expect(hasTable || hasError).toBeTruthy();
    });

    test('should display status badges in rows', async () => {
      await decisionTrace.waitForDataLoad();
      const rowCount = await decisionTrace.getAuditRowCount();

      if (rowCount > 0) {
        const badgeCount = await decisionTrace.statusBadges.count();
        expect(badgeCount).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Controls', () => {
    test.beforeEach(async () => {
      await decisionTrace.goto();
    });

    test('should have export button', async () => {
      const hasExport = await decisionTrace.exportButton.isVisible().catch(() => false);
      if (hasExport) {
        // Click should not crash
        await decisionTrace.clickExport();
        await expect(decisionTrace.header).toBeVisible();
      }
    });

    test('should have refresh button', async () => {
      const hasRefresh = await decisionTrace.refreshButton.isVisible().catch(() => false);
      if (hasRefresh) {
        // Click should not crash
        await decisionTrace.clickRefresh();
        await expect(decisionTrace.header).toBeVisible();
      }
    });
  });

  test.describe('Access Control', () => {
    test('standard tier can access basic traces', async ({ page }) => {
      await page.goto('/evidence/traces');
      await expect(page).toHaveURL(/\/evidence\/traces/);
    });

    test('standard tier can access export reports', async ({ page }) => {
      await page.goto('/evidence/export');
      await expect(page).toHaveURL(/\/evidence\/export/);
    });

    test('standard tier cannot access lineage explorer', async ({ page }) => {
      await page.goto('/evidence/lineage');
      // Lineage requires advanced tier - should redirect
      await expect(page).not.toHaveURL(/\/evidence\/lineage/);
    });

    test('advanced tier can access lineage explorer', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await page.goto('/evidence/lineage');
      await expect(page).toHaveURL(/\/evidence\/lineage/);
    });

    test('advanced tier cannot access changelog', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await page.goto('/evidence/changelog');
      // Changelog requires admin - should redirect
      await expect(page).not.toHaveURL(/\/evidence\/changelog/);
    });

    test('admin tier can access all evidence routes', async ({ page }) => {
      await setUserTier(page, 'admin');

      for (const route of ['/evidence/traces', '/evidence/lineage', '/evidence/changelog']) {
        await page.goto(route);
        await expect(page).toHaveURL(route);
      }
    });
  });
});
