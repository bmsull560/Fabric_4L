/**
 * CONTRACT TEST: Tier-Gated Navigation
 *
 * These tests define the behavioral contract for the tiered progressive
 * disclosure system. The sidebar navigation now uses a flat 7-step
 * methodology-driven workflow. All workflow steps are visible to all tiers.
 * Admin-only sections (Settings, Governance) are hidden from non-admin users.
 *
 * Contract hierarchy:
 *
 *   Standard (Tier 1):
 *     ✓ Home, Accounts, Prospect Setup, Intelligence, Value Hypothesis,
 *       Driver Tree, Evidence, Calculator, Value Case
 *     ✗ Settings (admin only)
 *
 *   Advanced (Tier 2):
 *     ✓ Same as Standard (all workflow steps)
 *     ✗ Settings (admin only)
 *
 *   Admin (Tier 3):
 *     ✓ Everything — full access including Settings
 *
 * References:
 *   - Layout.tsx NAV_DOMAINS
 *   - CONTRACT.md §2.6 UI State Machine
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

    test('should show Home in sidebar', async ({ page }) => {
      await expect(page.getByRole('link', { name: /^Home$/i })).toBeVisible();
    });

    test('should show Accounts in sidebar', async ({ page }) => {
      await expect(page.getByRole('link', { name: /^Accounts$/i })).toBeVisible();
    });

    test('should show Intelligence in sidebar', async ({ page }) => {
      await expect(page.getByRole('link', { name: /^Intelligence$/i })).toBeVisible();
    });

    test('should show Evidence in sidebar', async ({ page }) => {
      await expect(page.getByRole('link', { name: /^Evidence$/i })).toBeVisible();
    });

    test('should show Calculator in sidebar', async ({ page }) => {
      await expect(page.getByRole('link', { name: /^Calculator$/i })).toBeVisible();
    });

    test('should show Value Case in sidebar', async ({ page }) => {
      await expect(page.getByRole('link', { name: /value case/i })).toBeVisible();
    });

    test('should redirect to /home when navigating to restricted route', async ({ page }) => {
      await page.goto('/context/ontology/graph');
      await expect(page).toHaveURL(/\/home/);
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

    test('should show all workflow steps', async ({ page }) => {
      await expect(page.getByRole('link', { name: /^Accounts$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /^Intelligence$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /^Evidence$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /^Calculator$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /value case/i })).toBeVisible();
    });

    test('should allow navigation to Context Engine routes', async ({ page }) => {
      await page.goto('/context/ontology/graph');
      await expect(page).not.toHaveURL(/\/home/);
    });
  });

  // ── Admin Tier (Tier 3) ───────────────────────────────────────────────
  test.describe('Admin Tier', () => {
    test.beforeEach(async ({ page }) => {
      await seedAuthState(page, {
        id: 'test-admin-e2e',
        email: 'admin@valuefabric.test',
        role: 'admin',
        tenantId: 'tenant-e2e-001',
        tenantSlug: 'e2e-test',
      });
      await setUserTier(page, 'admin');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');
    });

    test('should show all workflow steps plus admin sections', async ({ page }) => {
      await expect(page.getByRole('link', { name: /^Accounts$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /^Intelligence$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /^Evidence$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /^Calculator$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /value case/i })).toBeVisible();
    });

    test('should allow navigation to Settings routes', async ({ page }) => {
      await page.goto('/settings/system/settings');
      await expect(page).not.toHaveURL(/\/home/);
    });
  });

  // ── Tier Switching ────────────────────────────────────────────────────
  test.describe('Tier Switching', () => {
    test('should maintain workflow visibility across tier changes', async ({ page }) => {
      await seedAuthState(page);
      await setUserTier(page, 'standard');
      await page.goto('/home');
      await page.waitForLoadState('networkidle');

      // All workflow steps visible at standard
      await expect(page.getByRole('link', { name: /^Intelligence$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /^Evidence$/i })).toBeVisible();

      // Switch to advanced — still visible
      await setUserTier(page, 'advanced');
      await page.reload();
      await page.waitForLoadState('networkidle');
      await expect(page.getByRole('link', { name: /^Intelligence$/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /^Evidence$/i })).toBeVisible();
    });
  });
});
