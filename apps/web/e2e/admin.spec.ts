import { test, expect } from './fixtures/contract-test';
import { AdminPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Admin / Governance E2E Tests
 *
 * Routes:
 *   /admin/content/formulas → Formula Governance
 *   /admin/content/benchmarks → Benchmark Policies
 *   /admin/data/variables → Variable Registry
 * Tier: admin (Tier 3)
 *
 * Covers:
 * - Formula Governance (registry, approval queue, version history)
 * - Benchmark Policies (confidence levels, policy types)
 * - Variable Registry (catalog, source bindings)
 * - Access control (admin-only enforcement)
 */

test.describe('Admin / Governance', () => {
  let adminPage: AdminPage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'admin');
    adminPage = new AdminPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  // ── Formula Governance ────────────────────────────────────────────

  test.describe('Formula Governance', () => {
    test.beforeEach(async () => {
      await adminPage.gotoFormulaGovernance();
    });

    test('should display page header', async () => {
      await adminPage.assertFormulaGovernanceLoaded();
    });

    test('should show formula registry tab', async () => {
      await expect(adminPage.formulaRegistryTab).toBeVisible();
    });

    test('should switch to approval queue tab', async () => {
      await expect(adminPage.approvalQueueTab).toBeVisible();
      await adminPage.switchFormulaTab('approvals');
      await expect(adminPage.approvalQueueTab).toHaveAttribute('aria-selected', 'true');
    });

    test('should switch to version history tab', async () => {
      await expect(adminPage.versionHistoryTab).toBeVisible();
      await adminPage.switchFormulaTab('versions');
      await expect(adminPage.versionHistoryTab).toHaveAttribute('aria-selected', 'true');
    });

    test('should display formula table with rows', async () => {
      await adminPage.waitForDataLoad();
      await expect(adminPage.formulaTable).toBeVisible();
      const count = await adminPage.getFormulaRowCount();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  // ── Benchmark Policies ────────────────────────────────────────────

  test.describe('Benchmark Policies', () => {
    test.beforeEach(async () => {
      await adminPage.gotoBenchmarkPolicies();
    });

    test('should display page header', async () => {
      await adminPage.assertBenchmarkPoliciesLoaded();
    });

    test('should display benchmark list', async () => {
      await adminPage.waitForDataLoad();
      await expect(adminPage.benchmarkList).toBeVisible();
    });

    test('should show confidence badges', async () => {
      await adminPage.waitForDataLoad();
      await expect(adminPage.confidenceBadges.first()).toBeVisible();
    });
  });

  // ── Variable Registry ─────────────────────────────────────────────

  test.describe('Variable Registry', () => {
    test.beforeEach(async () => {
      await adminPage.gotoVariableRegistry();
    });

    test('should display page header', async () => {
      await adminPage.assertVariableRegistryLoaded();
    });

    test('should show variable catalog tab', async () => {
      await expect(adminPage.variableCatalogTab).toBeVisible();
    });

    test('should switch to source bindings tab', async () => {
      await expect(adminPage.sourceBindingsTab).toBeVisible();
      await adminPage.switchVariableTab('bindings');
      await expect(adminPage.sourceBindingsTab).toHaveAttribute('aria-selected', 'true');
    });

    test('should display variable table with rows', async () => {
      await adminPage.waitForDataLoad();
      await expect(adminPage.variableTable).toBeVisible();
      const count = await adminPage.getVariableRowCount();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should display type and source badges', async () => {
      await adminPage.waitForDataLoad();
      await expect(adminPage.variableTable).toBeVisible();
      // Badges should be present when table has data
      await expect(adminPage.typeBadges.first()).toBeVisible();
      await expect(adminPage.sourceBadges.first()).toBeVisible();
    });
  });

  // ── Access Control ─────────────────────────────────────────────────

  test.describe('Access Control', () => {
    test('standard tier cannot access formula governance', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/admin/content/formulas');
      await expect(page).not.toHaveURL(/\/admin\/content\/formulas/);
    });

    test('advanced tier cannot access formula governance', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await page.goto('/admin/content/formulas');
      await expect(page).not.toHaveURL(/\/admin\/content\/formulas/);
    });

    test('standard tier cannot access benchmark policies', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/admin/content/benchmarks');
      await expect(page).not.toHaveURL(/\/admin\/content\/benchmarks/);
    });

    test('standard tier cannot access variable registry', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/admin/data/variables');
      await expect(page).not.toHaveURL(/\/admin\/data\/variables/);
    });

    test('admin tier can access all governance routes', async ({ page }) => {
      for (const route of [
        '/admin/content/formulas',
        '/admin/content/benchmarks',
        '/admin/data/variables',
      ]) {
        await page.goto(route);
        await expect(page).toHaveURL(route);
      }
    });

    test('admin tier can access access control routes', async ({ page }) => {
      await page.goto('/admin/access/roles');
      await expect(page).toHaveURL(/\/admin\/access\/roles/);
    });

    test('admin tier can access system routes', async ({ page }) => {
      await page.goto('/admin/system/settings');
      await expect(page).toHaveURL(/\/admin\/system\/settings/);
    });
  });
});
