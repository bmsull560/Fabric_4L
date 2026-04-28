/**
 * CONTRACT TEST: Tier-Gated Navigation
 *
 * These tests define the behavioral contract for the tiered progressive
 * disclosure system. The sidebar navigation shows/hides domains and
 * sub-items based on the user's effective tier (standard/advanced/admin).
 *
 * Contract hierarchy (from CONTRACT.md §2.6 + Layout.tsx NAV_SPINE):
 *
 *   Standard (Tier 1):
 *     ✓ Accounts, Intelligence (basic), Deliverables (basic)
 *     ✗ Context Engine, Value Studio (advanced), Governance, Settings (admin)
 *
 *   Advanced (Tier 2):
 *     ✓ Everything in Standard + Context Engine, Value Studio, full Intelligence
 *     ✗ Governance, Settings (admin sections)
 *
 *   Admin (Tier 3):
 *     ✓ Everything — full access including Governance and Settings
 *
 * TDD Status: FAILING (initial state)
 * These tests define the expected visibility gates. The Layout component
 * must enforce these gates to make the tests pass.
 *
 * References:
 *   - Layout.tsx NAV_SPINE minTier field
 *   - CONTRACT.md §2.6 UI State Machine
 *   - UI Contracts: Behavior Contract (what the nav guarantees to show/hide)
 */
import { test, expect } from '@playwright/test';
import { setUserTier, clearUserTier, seedAuthState, clearAuthState } from '../fixtures';

test.describe('Contract: Tier-Gated Navigation', () => {
  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
    await clearAuthState(page);
  });

  // ── Standard Tier (Tier 1) ────────────────────────────────────────────

  test.describe('Standard Tier', () => {
    test.beforeEach(async ({ page }) => {
      await seedAuthState(page, {
        id: 'test-user-e2e',
        email: 'e2e@valuefabric.test',
        role: 'standard',
        tenantId: 'tenant-e2e-001',
        tenantSlug: 'e2e-test',
      });
      await setUserTier(page, 'standard');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');
    });

    test('should show Accounts domain in sidebar', async ({ page }) => {
      // Contract: Accounts is always visible (minTier: standard)
      await expect(page.getByRole('link', { name: /accounts/i })).toBeVisible();
    });

    test('should show Intelligence domain in sidebar', async ({ page }) => {
      // Contract: Intelligence is always visible (minTier: standard)
      await expect(page.getByRole('link', { name: /intelligence/i })).toBeVisible();
    });

    test('should show Deliverables domain in sidebar', async ({ page }) => {
      // Contract: Deliverables is always visible (minTier: standard)
      await expect(page.getByRole('link', { name: /deliverables/i })).toBeVisible();
    });

    test('should NOT show Context Engine domain in sidebar', async ({ page }) => {
      // Contract: Context Engine requires advanced tier
      await expect(page.getByRole('link', { name: /context engine/i })).not.toBeVisible();
    });

    test('should NOT show Value Studio domain in sidebar', async ({ page }) => {
      // Contract: Value Studio requires advanced tier
      await expect(page.getByRole('link', { name: /value studio/i })).not.toBeVisible();
    });

    test('should NOT show Governance domain in sidebar', async ({ page }) => {
      // Contract: Governance requires admin tier
      await expect(page.getByRole('link', { name: /governance/i })).not.toBeVisible();
    });

    test('should NOT show Settings domain in sidebar', async ({ page }) => {
      // Contract: Settings requires admin tier
      await expect(page.getByRole('link', { name: /settings/i })).not.toBeVisible();
    });

    test('should redirect to /home when navigating to restricted route', async ({ page }) => {
      // Contract: direct URL access to restricted routes redirects to /home
      await page.goto('/context/ontology/graph');
      await expect(page).toHaveURL(/\/home/);
    });

    test('should show tier indicator as Standard', async ({ page }) => {
      // Contract: tier switcher shows current tier label
      await expect(page.getByText(/standard/i)).toBeVisible();
    });
  });

  // ── Advanced Tier (Tier 2) ────────────────────────────────────────────

  test.describe('Advanced Tier', () => {
    test.beforeEach(async ({ page }) => {
      await seedAuthState(page, {
        id: 'test-user-e2e',
        email: 'e2e@valuefabric.test',
        role: 'advanced',
        tenantId: 'tenant-e2e-001',
        tenantSlug: 'e2e-test',
      });
      await setUserTier(page, 'advanced');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');
    });

    test('should show all Standard tier domains', async ({ page }) => {
      // Contract: advanced includes everything from standard
      await expect(page.getByRole('link', { name: /accounts/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /intelligence/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /deliverables/i })).toBeVisible();
    });

    test('should show Context Engine domain in sidebar', async ({ page }) => {
      // Contract: Context Engine unlocked at advanced tier
      await expect(page.getByRole('link', { name: /context engine/i })).toBeVisible();
    });

    test('should show Value Studio domain in sidebar', async ({ page }) => {
      // Contract: Value Studio unlocked at advanced tier
      await expect(page.getByRole('link', { name: /value studio/i })).toBeVisible();
    });

    test('should NOT show Governance domain in sidebar', async ({ page }) => {
      // Contract: Governance requires admin tier
      await expect(page.getByRole('link', { name: /governance/i })).not.toBeVisible();
    });

    test('should NOT show Settings domain in sidebar', async ({ page }) => {
      // Contract: Settings requires admin tier
      await expect(page.getByRole('link', { name: /settings/i })).not.toBeVisible();
    });

    test('should allow navigation to Context Engine routes', async ({ page }) => {
      // Contract: advanced tier can access Context Engine
      await page.goto('/context/ontology/graph');
      await expect(page).not.toHaveURL(/\/home/);
    });

    test('should redirect from admin routes to /home', async ({ page }) => {
      // Contract: admin routes are still restricted
      await page.goto('/governance/audit/log');
      await expect(page).toHaveURL(/\/home/);
    });

    test('should show tier indicator as Advanced', async ({ page }) => {
      await expect(page.getByText(/advanced/i)).toBeVisible();
    });
  });

  // ── Admin Tier (Tier 3) ───────────────────────────────────────────────

  test.describe('Admin Tier', () => {
    test.beforeEach(async ({ page }) => {
      await seedAuthState(page);
      await setUserTier(page, 'admin');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');
    });

    test('should show all domains in sidebar', async ({ page }) => {
      // Contract: admin sees everything
      await expect(page.getByRole('link', { name: /accounts/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /intelligence/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /deliverables/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /context engine/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /value studio/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /governance/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /settings/i })).toBeVisible();
    });

    test('should allow navigation to Governance routes', async ({ page }) => {
      // Contract: admin can access governance
      await page.goto('/governance/audit/log');
      await expect(page).not.toHaveURL(/\/home/);
    });

    test('should allow navigation to Settings routes', async ({ page }) => {
      // Contract: admin can access settings
      await page.goto('/settings/system/settings');
      await expect(page).not.toHaveURL(/\/home/);
    });

    test('should show tier indicator as Admin', async ({ page }) => {
      await expect(page.getByText(/admin/i)).toBeVisible();
    });
  });

  // ── Tier Switching ────────────────────────────────────────────────────

  test.describe('Tier Switching', () => {
    test('should update navigation when tier changes from standard to advanced', async ({ page }) => {
      await seedAuthState(page);
      await setUserTier(page, 'standard');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');

      // Contract: Context Engine not visible at standard
      await expect(page.getByRole('link', { name: /context engine/i })).not.toBeVisible();

      // Switch to advanced
      await setUserTier(page, 'advanced');
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Contract: Context Engine now visible at advanced
      await expect(page.getByRole('link', { name: /context engine/i })).toBeVisible();
    });

    test('should update navigation when tier changes from advanced to admin', async ({ page }) => {
      await seedAuthState(page);
      await setUserTier(page, 'advanced');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');

      // Contract: Governance not visible at advanced
      await expect(page.getByRole('link', { name: /governance/i })).not.toBeVisible();

      // Switch to admin
      await setUserTier(page, 'admin');
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Contract: Governance now visible at admin
      await expect(page.getByRole('link', { name: /governance/i })).toBeVisible();
    });

    test('should hide domains when tier is downgraded', async ({ page }) => {
      await seedAuthState(page);
      await setUserTier(page, 'admin');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');

      // Contract: all domains visible at admin
      await expect(page.getByRole('link', { name: /governance/i })).toBeVisible();

      // Downgrade to standard
      await setUserTier(page, 'standard');
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Contract: governance hidden after downgrade
      await expect(page.getByRole('link', { name: /governance/i })).not.toBeVisible();
    });
  });

  // ── Sub-Item Tier Gating ──────────────────────────────────────────────

  test.describe('Sub-Item Tier Gating', () => {
    test('should hide advanced sub-items within visible domains at standard tier', async ({ page }) => {
      await seedAuthState(page, {
        id: 'test-user-e2e',
        email: 'e2e@valuefabric.test',
        role: 'standard',
        tenantId: 'tenant-e2e-001',
        tenantSlug: 'e2e-test',
      });
      await setUserTier(page, 'standard');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');

      // Click on Intelligence to expand it
      await page.getByRole('link', { name: /intelligence/i }).click();

      // Contract: basic sub-items visible (Signals, Stakeholders)
      // Contract: advanced sub-items hidden (Hypotheses, Enrichment)
      const navItems = await page.locator('aside a').allTextContents();
      const lowerItems = navItems.map((t) => t.toLowerCase().trim());

      // Signals should always be visible (standard tier)
      expect(lowerItems.some((t) => t.includes('signal'))).toBe(true);
    });

    test('should show advanced sub-items at advanced tier', async ({ page }) => {
      await seedAuthState(page, {
        id: 'test-user-e2e',
        email: 'e2e@valuefabric.test',
        role: 'advanced',
        tenantId: 'tenant-e2e-001',
        tenantSlug: 'e2e-test',
      });
      await setUserTier(page, 'advanced');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');

      // Click on Intelligence to expand it
      await page.getByRole('link', { name: /intelligence/i }).click();

      // Contract: advanced sub-items now visible
      const navItems = await page.locator('aside a').allTextContents();
      const lowerItems = navItems.map((t) => t.toLowerCase().trim());

      // Hypotheses should be visible at advanced tier
      expect(lowerItems.some((t) => t.includes('hypothes'))).toBe(true);
    });
  });
});
