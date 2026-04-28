/**
 * CONTRACT TEST: Settings & Governance Admin Surface
 *
 * These tests define the behavioral contract for the admin-only
 * Settings and Governance domains. Both require admin tier (Tier 3).
 *
 * Settings routes (/settings/*):
 *   - /settings/system/settings   → Platform Settings
 *   - /settings/system/billing    → Billing & Usage
 *   - /settings/content/formulas  → Formula Management
 *   - /settings/content/approvals → Approval Workflows
 *   - /settings/content/versions  → Version Control
 *   - /settings/data/variables    → Variable Registry
 *   - /settings/data/bindings     → Data Bindings
 *   - /settings/data/quality      → Data Quality
 *   - /settings/access/roles      → Role Management
 *   - /settings/access/teams      → Team Management
 *   - /settings/access/keys       → API Key Management
 *
 * Governance routes (/governance/*):
 *   - /governance/audit/log       → Audit Log
 *   - /governance/audit/changes   → Change History
 *   - /governance/compliance      → Compliance Dashboard
 *   - /governance/health          → System Health
 *   - /governance/integrity       → Data Integrity
 *   - /governance/provenance      → Data Provenance
 *   - /governance/benchmarks      → Benchmark Policies
 *   - /governance/traces          → Decision Traces
 *   - /governance/evidence        → Evidence Chain
 *
 * Contract guarantees:
 *   1. All routes require admin tier — non-admin users are redirected
 *   2. Each route renders a page with a heading and primary content area
 *   3. Settings pages have consistent layout (sidebar sub-nav + content)
 *   4. Governance pages surface audit/compliance data
 *   5. Access control pages enforce RBAC patterns
 *
 * TDD Status: FAILING (initial state)
 *
 * References:
 *   - CONTRACT.md §2.6 UI State Machine
 *   - Layout.tsx NAV_SPINE (Governance, Settings domains)
 *   - App.tsx route definitions
 */
import { test, expect } from '@playwright/test';
import { setUserTier, clearUserTier } from '../fixtures';

test.describe('Contract: Settings & Governance Admin Surface', () => {
  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  // ── Access Control ────────────────────────────────────────────────────

  test.describe('Access Control', () => {
    test('should redirect standard tier users from /settings', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/settings/system/settings');

      // Contract: non-admin users cannot access settings
      await expect(page).toHaveURL(/\/home/);
    });

    test('should redirect advanced tier users from /settings', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await page.goto('/settings/system/settings');

      // Contract: non-admin users cannot access settings
      await expect(page).toHaveURL(/\/home/);
    });

    test('should redirect standard tier users from /governance', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/governance/audit/log');

      // Contract: non-admin users cannot access governance
      await expect(page).toHaveURL(/\/home/);
    });

    test('should redirect advanced tier users from /governance', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await page.goto('/governance/audit/log');

      // Contract: non-admin users cannot access governance
      await expect(page).toHaveURL(/\/home/);
    });

    test('should allow admin tier users to access /settings', async ({ page }) => {
      await setUserTier(page, 'admin');
      await page.goto('/settings/system/settings');

      // Contract: admin users can access settings
      await expect(page).not.toHaveURL(/\/home/);
    });

    test('should allow admin tier users to access /governance', async ({ page }) => {
      await setUserTier(page, 'admin');
      await page.goto('/governance/audit/log');

      // Contract: admin users can access governance
      await expect(page).not.toHaveURL(/\/home/);
    });
  });

  // ── Settings Routes ───────────────────────────────────────────────────

  test.describe('Settings Routes', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'admin');
    });

    const settingsRoutes = [
      { path: '/settings/system/settings', heading: /platform settings|settings/i },
      { path: '/settings/content/formulas', heading: /formula|content/i },
      { path: '/settings/content/approvals', heading: /approval|workflow/i },
      { path: '/settings/content/versions', heading: /version|content/i },
      { path: '/settings/data/variables', heading: /variable|registry/i },
      { path: '/settings/data/bindings', heading: /binding|data/i },
      { path: '/settings/data/quality', heading: /quality|data/i },
      { path: '/settings/access/roles', heading: /role|access/i },
      { path: '/settings/access/teams', heading: /team|access/i },
      { path: '/settings/access/keys', heading: /key|api/i },
    ];

    for (const { path, heading } of settingsRoutes) {
      test(`should render ${path}`, async ({ page }) => {
        await page.goto(path);

        // Contract: page renders with a heading
        const pageHeading = page.getByRole('heading').first();
        await expect(pageHeading).toBeVisible({ timeout: 10000 });

        // Contract: heading matches expected pattern
        await expect(pageHeading).toHaveText(heading);

        // Contract: main content area is visible
        const content = page.locator('main, [role="main"], .flex-1').first();
        await expect(content).toBeVisible();
      });
    }

    test('should have consistent settings layout with sub-navigation', async ({ page }) => {
      await page.goto('/settings/system/settings');

      // Contract: settings pages have a sub-navigation structure
      // Either tabs, sidebar links, or section headers
      const hasSubNav =
        (await page.getByRole('tab').count()) > 0 ||
        (await page.getByRole('link').filter({ hasText: /system|content|data|access/i }).count()) > 0 ||
        (await page.locator('[class*="tab"], [class*="nav"]').count()) > 0;

      expect(hasSubNav).toBe(true);
    });
  });

  // ── Governance Routes ─────────────────────────────────────────────────

  test.describe('Governance Routes', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'admin');
    });

    const governanceRoutes = [
      { path: '/governance/audit/log', heading: /audit|log/i },
      { path: '/governance/audit/changes', heading: /change|audit/i },
      { path: '/governance/compliance', heading: /compliance/i },
      { path: '/governance/health', heading: /health|system/i },
      { path: '/governance/integrity', heading: /integrity|data/i },
      { path: '/governance/provenance', heading: /provenance|data/i },
      { path: '/governance/benchmarks', heading: /benchmark|polic/i },
      { path: '/governance/traces', heading: /trace|decision/i },
      { path: '/governance/evidence', heading: /evidence|chain/i },
    ];

    for (const { path, heading } of governanceRoutes) {
      test(`should render ${path}`, async ({ page }) => {
        await page.goto(path);

        // Contract: page renders with a heading
        const pageHeading = page.getByRole('heading').first();
        await expect(pageHeading).toBeVisible({ timeout: 10000 });

        // Contract: heading matches expected pattern
        await expect(pageHeading).toHaveText(heading);

        // Contract: main content area is visible
        const content = page.locator('main, [role="main"], .flex-1').first();
        await expect(content).toBeVisible();
      });
    }
  });

  // ── Billing & Usage ───────────────────────────────────────────────────

  test.describe('Billing & Usage', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'admin');
    });

    test('should render billing overview', async ({ page }) => {
      await page.goto('/settings/system/billing');

      // Contract: billing page loads
      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });
    });

    const billingSubRoutes = [
      { path: '/settings/system/billing/usage', label: /usage/i },
      { path: '/settings/system/billing/invoices', label: /invoice/i },
      { path: '/settings/system/billing/payments', label: /payment/i },
    ];

    for (const { path, label } of billingSubRoutes) {
      test(`should render ${path}`, async ({ page }) => {
        await page.goto(path);

        // Contract: sub-route renders content
        const content = page.locator('main, [role="main"], .flex-1').first();
        await expect(content).toBeVisible({ timeout: 10000 });
      });
    }
  });

  // ── RBAC Patterns ─────────────────────────────────────────────────────

  test.describe('RBAC Patterns', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'admin');
    });

    test('should display role management with role list', async ({ page }) => {
      await page.goto('/settings/access/roles');

      // Contract: roles page has a list or table of roles
      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });

      // Contract: should have some form of role listing
      const hasTable = (await page.locator('table').count()) > 0;
      const hasList = (await page.locator('[class*="list"], [class*="card"]').count()) > 0;
      const hasContent = (await content.textContent())?.length ?? 0 > 50;

      expect(hasTable || hasList || hasContent).toBe(true);
    });

    test('should display team management', async ({ page }) => {
      await page.goto('/settings/access/teams');

      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });
    });

    test('should display API key management', async ({ page }) => {
      await page.goto('/settings/access/keys');

      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });

      // Contract: API key page should have a way to create/view keys
      const hasCreateButton = (await page.getByRole('button', { name: /create|add|generate/i }).count()) > 0;
      const hasKeyList = (await page.locator('table, [class*="list"]').count()) > 0;
      const hasContent = (await content.textContent())?.length ?? 0 > 50;

      expect(hasCreateButton || hasKeyList || hasContent).toBe(true);
    });
  });

  // ── Audit Trail ───────────────────────────────────────────────────────

  test.describe('Audit Trail', () => {
    test.beforeEach(async ({ page }) => {
      await setUserTier(page, 'admin');
    });

    test('should display audit log with entries', async ({ page }) => {
      await page.goto('/governance/audit/log');

      // Contract: audit log page renders
      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });

      // Contract: should have some form of log display
      const hasTable = (await page.locator('table').count()) > 0;
      const hasList = (await page.locator('[class*="list"], [class*="log"]').count()) > 0;
      const hasEntries = (await content.textContent())?.length ?? 0 > 50;

      expect(hasTable || hasList || hasEntries).toBe(true);
    });

    test('should display change history', async ({ page }) => {
      await page.goto('/governance/audit/changes');

      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });
    });

    test('should display compliance dashboard', async ({ page }) => {
      await page.goto('/governance/compliance');

      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });
    });
  });
});
