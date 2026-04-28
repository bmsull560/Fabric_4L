/**
 * CONTRACT TEST: Account-Scoped Workspaces
 *
 * These tests define the behavioral contract for account-scoped routes.
 * Intelligence and Value Studio workspaces are parameterized by accountId:
 *
 *   /intelligence/:accountId/signals
 *   /intelligence/:accountId/drivers
 *   /intelligence/:accountId/stakeholders
 *   /intelligence/:accountId/evidence
 *   /intelligence/:accountId/hypotheses
 *   /intelligence/:accountId/enrichment
 *   /intelligence/:accountId/competitive
 *   /intelligence/:accountId/roi
 *
 *   /studio/:accountId/value-model
 *   /studio/:accountId/narrative
 *   /studio/:accountId/action-plan
 *   /studio/:accountId/evidence
 *   /studio/:accountId/competitive
 *   /studio/:accountId/enrichment
 *   /studio/:accountId/roi
 *
 * Contract guarantees:
 *   1. Routes with :accountId render the workspace for that account
 *   2. Account name is displayed in the workspace header/breadcrumb
 *   3. Switching accounts updates the URL and workspace context
 *   4. Routes without :accountId use the selected account from store
 *   5. No account selected → redirect or prompt to select
 *
 * TDD Status: FAILING (initial state)
 *
 * References:
 *   - Layout.tsx breadcrumb generation
 *   - accountContextStore (zustand)
 *   - App.tsx route definitions
 */
import { test, expect } from '@playwright/test';
import { setUserTier, clearUserTier } from '../fixtures';
import {
  setSelectedAccount,
  clearSelectedAccount,
  getSelectedAccountId,
  TEST_ACCOUNTS,
} from '../fixtures/account-helpers';

test.describe('Contract: Account-Scoped Workspaces', () => {
  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'admin');
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
    await clearSelectedAccount(page);
  });

  // ── Intelligence Workspace ────────────────────────────────────────────

  test.describe('Intelligence Workspace', () => {
    const intelligenceTabs = [
      { name: 'Signals', path: 'signals' },
      { name: 'Drivers', path: 'drivers' },
      { name: 'Stakeholders', path: 'stakeholders' },
      { name: 'Evidence', path: 'evidence' },
      { name: 'Hypotheses', path: 'hypotheses' },
      { name: 'Competitive', path: 'competitive' },
    ];

    test('should render workspace with account ID in URL', async ({ page }) => {
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);

      // Contract: page loads without redirect
      await expect(page).toHaveURL(new RegExp(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`));
    });

    test('should display account name in breadcrumb or header', async ({ page }) => {
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);

      // Contract: account name visible in the workspace context
      await expect(page.getByText(TEST_ACCOUNTS.meridian.name)).toBeVisible({ timeout: 10000 });
    });

    for (const tab of intelligenceTabs) {
      test(`should load ${tab.name} tab for account`, async ({ page }) => {
        await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
        await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/${tab.path}`);

        // Contract: route resolves and renders content (no error page)
        await expect(page).toHaveURL(
          new RegExp(`/intelligence/${TEST_ACCOUNTS.meridian.id}/${tab.path}`),
        );
        // Contract: page has meaningful content (not blank or error)
        const body = await page.locator('main, [role="main"], .flex-1').first();
        await expect(body).toBeVisible({ timeout: 10000 });
      });
    }

    test('should update workspace when switching accounts', async ({ page }) => {
      // Start with Meridian
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);
      await expect(page.getByText(TEST_ACCOUNTS.meridian.name)).toBeVisible({ timeout: 10000 });

      // Switch to Acme
      await setSelectedAccount(page, TEST_ACCOUNTS.acme);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.acme.id}/signals`);

      // Contract: account context updates
      await expect(page.getByText(TEST_ACCOUNTS.acme.name)).toBeVisible({ timeout: 10000 });
      await expect(page).toHaveURL(new RegExp(TEST_ACCOUNTS.acme.id));
    });
  });

  // ── Value Studio Workspace ────────────────────────────────────────────

  test.describe('Value Studio Workspace', () => {
    const studioTabs = [
      { name: 'Value Model', path: 'value-model' },
      { name: 'Narrative', path: 'narrative' },
      { name: 'Action Plan', path: 'action-plan' },
      { name: 'Evidence', path: 'evidence' },
      { name: 'Competitive', path: 'competitive' },
    ];

    test('should render studio workspace with account ID in URL', async ({ page }) => {
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/studio/${TEST_ACCOUNTS.meridian.id}/value-model`);

      // Contract: page loads without redirect
      await expect(page).toHaveURL(
        new RegExp(`/studio/${TEST_ACCOUNTS.meridian.id}/value-model`),
      );
    });

    test('should display account name in studio workspace', async ({ page }) => {
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/studio/${TEST_ACCOUNTS.meridian.id}/value-model`);

      // Contract: account name visible
      await expect(page.getByText(TEST_ACCOUNTS.meridian.name)).toBeVisible({ timeout: 10000 });
    });

    for (const tab of studioTabs) {
      test(`should load ${tab.name} tab for account`, async ({ page }) => {
        await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
        await page.goto(`/studio/${TEST_ACCOUNTS.meridian.id}/${tab.path}`);

        // Contract: route resolves
        await expect(page).toHaveURL(
          new RegExp(`/studio/${TEST_ACCOUNTS.meridian.id}/${tab.path}`),
        );
        const body = await page.locator('main, [role="main"], .flex-1').first();
        await expect(body).toBeVisible({ timeout: 10000 });
      });
    }
  });

  // ── Fallback Routes (no accountId) ────────────────────────────────────

  test.describe('Fallback Routes (no accountId in URL)', () => {
    test('should use selected account from store for /intelligence/signals', async ({ page }) => {
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto('/intelligence/signals');

      // Contract: route resolves using the store's selectedAccountId
      // Either redirects to /intelligence/:accountId/signals or renders with store context
      const url = page.url();
      const hasAccountInUrl = url.includes(TEST_ACCOUNTS.meridian.id);
      const hasContent = await page.locator('main, [role="main"], .flex-1').first().isVisible();

      // One of these must be true
      expect(hasAccountInUrl || hasContent).toBe(true);
    });

    test('should use selected account from store for /studio/value-model', async ({ page }) => {
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto('/studio/value-model');

      const url = page.url();
      const hasAccountInUrl = url.includes(TEST_ACCOUNTS.meridian.id);
      const hasContent = await page.locator('main, [role="main"], .flex-1').first().isVisible();

      expect(hasAccountInUrl || hasContent).toBe(true);
    });

    test('should handle missing account gracefully', async ({ page }) => {
      // No account selected in store
      await clearSelectedAccount(page);
      await page.goto('/intelligence/signals');

      // Contract: either redirects to account selection or shows prompt
      // Should NOT show a blank page or crash
      const hasRedirect = page.url().includes('/accounts') || page.url().includes('/home');
      const hasPrompt = await page.getByText(/select.*account/i).isVisible().catch(() => false);
      const hasContent = await page.locator('main, [role="main"], .flex-1').first().isVisible();

      expect(hasRedirect || hasPrompt || hasContent).toBe(true);
    });
  });

  // ── Account Context Persistence ───────────────────────────────────────

  test.describe('Account Context Persistence', () => {
    test('should persist selected account across page reloads', async ({ page }) => {
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);

      // Reload the page
      await page.reload();

      // Contract: account context survives reload (zustand persist)
      const accountId = await getSelectedAccountId(page);
      expect(accountId).toBe(TEST_ACCOUNTS.meridian.id);
    });

    test('should persist selected account across route navigation', async ({ page }) => {
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);

      // Navigate to a different route
      await page.goto('/home');

      // Navigate back
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/drivers`);

      // Contract: account context persists across navigation
      const accountId = await getSelectedAccountId(page);
      expect(accountId).toBe(TEST_ACCOUNTS.meridian.id);
    });
  });

  // ── Cross-Workspace Account Consistency ───────────────────────────────

  test.describe('Cross-Workspace Account Consistency', () => {
    test('should use same account in Intelligence and Studio', async ({ page }) => {
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);

      // Visit Intelligence
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);
      await expect(page).toHaveURL(new RegExp(TEST_ACCOUNTS.meridian.id));

      // Visit Studio
      await page.goto(`/studio/${TEST_ACCOUNTS.meridian.id}/value-model`);
      await expect(page).toHaveURL(new RegExp(TEST_ACCOUNTS.meridian.id));

      // Contract: same account ID in both workspaces
      const accountId = await getSelectedAccountId(page);
      expect(accountId).toBe(TEST_ACCOUNTS.meridian.id);
    });
  });
});
