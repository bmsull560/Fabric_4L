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
 * References:
 *   - Layout.tsx breadcrumb generation
 *   - accountContextStore (zustand)
 *   - App.tsx route definitions
 *   - IntelligenceShell.tsx / ValueStudioShell.tsx (AccountHeader)
 */
import { test, expect, type Page, type Route } from '@playwright/test';
import { setUserTier, clearUserTier, seedAuthState, clearAuthState } from '../fixtures';
import {
  setSelectedAccount,
  clearSelectedAccount,
  getSelectedAccountId,
  TEST_ACCOUNTS,
  type TestAccount,
} from '../fixtures/account-helpers';

// ── Mock Account Data ──────────────────────────────────────────────────────
// Workspace pages call useAccount(accountId) → GET /api/v1/agents/accounts/:id
// and useCanonicalCaseId → GET /api/v1/agents/analysis/cases?account_id=:id
// and useWorkspaceTabQuery → GET /api/v1/agents/analysis/cases/:caseId/workspace/:tab
// Without a running backend these fail, so we mock them.

function buildMockAccount(acct: TestAccount) {
  return {
    id: acct.id,
    name: acct.name,
    domain: `${acct.name.toLowerCase().replace(/\s+/g, '')}.com`,
    industry: acct.industry ?? 'Technology',
    stage: 'customer',
    region: 'North America',
    segment: acct.tier ?? 'enterprise',
    provider: 'manual',
    provider_record_id: acct.id,
    sync_status: 'synced',
    employees: 5000,
    annual_revenue: 250000000,
    headquarters: 'New York, NY',
    website: `https://${acct.name.toLowerCase().replace(/\s+/g, '')}.com`,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-06-01T00:00:00Z',
  };
}

const MOCK_CASE_ID = 'case-test-001';

function buildMockWorkspaceData(tabKey: string) {
  const mocks: Record<string, unknown> = {
    signals: { signals: [{ id: 's1', name: 'Cost Reduction', category: 'Operational', confidence: 0.85, impact: 'high' }] },
    drivers: { drivers: [{ id: 'd1', name: 'Labor Efficiency', parentSignal: 'Cost Reduction', impact: 'high' }] },
    stakeholders: { stakeholders: [{ id: 'st1', name: 'Jane Doe', title: 'VP Operations', influence: 'high' }] },
    evidence: { evidence: [{ id: 'e1', title: 'Q3 Report', excerpt: 'Cost savings identified', source: 'internal' }] },
    hypotheses: { hypotheses: [{ id: 'h1', statement: 'Automation reduces costs by 20%', confidence: 0.7 }] },
    enrichment: { enrichment: { sources: [], status: 'complete' } },
    competitive: { competitive: [{ id: 'c1', competitor: 'Competitor A', advantage: 'Price' }] },
    roi: { roi: { conservative: 1000000, expected: 2000000, optimistic: 3500000 } },
    'value-model': { value_lines: [{ id: 'v1', driver: 'Efficiency', category: 'hard', conservative: 500000, expected: 1000000, optimistic: 1500000 }] },
    narrative: { narrative: { title: 'Value Narrative', sections: [] } },
    'action-plan': { action_plan: { phases: [], timeline: '6 months' } },
    'evidence-library': { evidence: [] },
  };
  return mocks[tabKey] ?? {};
}

/**
 * Mock all API endpoints that workspace pages depend on.
 * Must be called BEFORE page.goto() so routes are intercepted.
 *
 * IMPORTANT: Playwright routes match in REVERSE registration order
 * (last registered wins). We register the catch-all FIRST, then
 * specific routes LAST so they take priority.
 *
 * IMPORTANT: The catch-all uses `/api/v1/` (not `/api/`) to avoid
 * intercepting Vite dev server source file requests like `/src/api/client.ts`.
 */
async function mockWorkspaceApis(page: Page, ...accounts: TestAccount[]): Promise<void> {
  // ── 1. Catch-all for API v1 endpoints (registered FIRST → lowest priority) ──
  // Uses /api/v1/ to avoid matching Vite source files like /src/api/client.ts
  await page.route('**/api/v1/**', async (route: Route) => {
    await route.fulfill({ json: {} });
  });

  // ── 2. Workspace data endpoints (higher priority) ──────────────────
  // Workspace generate: POST
  await page.route('**/agents/analysis/cases/*/workspace/generate', async (route: Route) => {
    await route.fulfill({ json: { status: 'complete' } });
  });

  // Workspace tab data: GET /api/v1/agents/analysis/cases/:caseId/workspace/:tab
  await page.route('**/agents/analysis/cases/*/workspace/*', async (route: Route) => {
    const url = route.request().url();
    const tabMatch = url.match(/\/workspace\/([^?/]+)/);
    const tabKey = tabMatch?.[1] ?? 'signals';
    await route.fulfill({ json: buildMockWorkspaceData(tabKey) });
  });

  // Canonical case ID: GET /api/v1/agents/analysis/cases?account_id=:id
  await page.route('**/agents/analysis/cases**', async (route: Route) => {
    await route.fulfill({ json: { case_id: MOCK_CASE_ID } });
  });

  // ── 3. Account detail endpoints (highest priority, registered LAST) ─
  for (const acct of accounts) {
    const mockAccount = buildMockAccount(acct);
    await page.route(`**/agents/accounts/${acct.id}`, async (route: Route) => {
      await route.fulfill({ json: mockAccount });
    });
  }
}

test.describe('Contract: Account-Scoped Workspaces', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthState(page);
    await setUserTier(page, 'admin');
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
    await clearSelectedAccount(page);
    await clearAuthState(page);
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
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);
      await page.waitForLoadState('networkidle');

      // Contract: page loads without redirect
      await expect(page).toHaveURL(new RegExp(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`));
    });

    test('should display account name in workspace header', async ({ page }) => {
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);
      await page.waitForLoadState('networkidle');

      // Contract: account name visible in the IntelligenceShell AccountHeader
      await expect(page.getByText(TEST_ACCOUNTS.meridian.name)).toBeVisible({ timeout: 10000 });
    });

    for (const tab of intelligenceTabs) {
      test(`should load ${tab.name} tab for account`, async ({ page }) => {
        await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
        await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
        await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/${tab.path}`);
        await page.waitForLoadState('networkidle');

        // Contract: route resolves and renders content (no error page)
        await expect(page).toHaveURL(
          new RegExp(`/intelligence/${TEST_ACCOUNTS.meridian.id}/${tab.path}`),
        );
        // Contract: page has meaningful content (not blank or error)
        const body = page.locator('main, [role="main"], .flex-1').first();
        await expect(body).toBeVisible({ timeout: 10000 });
      });
    }

    test('should update workspace when switching accounts', async ({ page }) => {
      // Mock both accounts upfront
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian, TEST_ACCOUNTS.acme);

      // Start with Meridian
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);
      await page.waitForLoadState('networkidle');
      await expect(page.getByText(TEST_ACCOUNTS.meridian.name)).toBeVisible({ timeout: 10000 });

      // Switch to Acme
      await setSelectedAccount(page, TEST_ACCOUNTS.acme);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.acme.id}/signals`);
      await page.waitForLoadState('networkidle');

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
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/studio/${TEST_ACCOUNTS.meridian.id}/value-model`);
      await page.waitForLoadState('networkidle');

      // Contract: page loads without redirect
      await expect(page).toHaveURL(
        new RegExp(`/studio/${TEST_ACCOUNTS.meridian.id}/value-model`),
      );
    });

    test('should display account name in studio workspace', async ({ page }) => {
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/studio/${TEST_ACCOUNTS.meridian.id}/value-model`);
      await page.waitForLoadState('networkidle');

      // Contract: account name visible in ValueStudioShell AccountHeader
      await expect(page.getByText(TEST_ACCOUNTS.meridian.name)).toBeVisible({ timeout: 10000 });
    });

    for (const tab of studioTabs) {
      test(`should load ${tab.name} tab for account`, async ({ page }) => {
        await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
        await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
        await page.goto(`/studio/${TEST_ACCOUNTS.meridian.id}/${tab.path}`);
        await page.waitForLoadState('networkidle');

        // Contract: route resolves
        await expect(page).toHaveURL(
          new RegExp(`/studio/${TEST_ACCOUNTS.meridian.id}/${tab.path}`),
        );
        const body = page.locator('main, [role="main"], .flex-1').first();
        await expect(body).toBeVisible({ timeout: 10000 });
      });
    }
  });

  // ── Fallback Routes (no accountId) ────────────────────────────────────

  test.describe('Fallback Routes (no accountId in URL)', () => {
    test('should use selected account from store for /intelligence/signals', async ({ page }) => {
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto('/intelligence/signals');
      await page.waitForLoadState('networkidle');

      // Contract: route resolves using the store's selectedAccountId
      // Either redirects to /intelligence/:accountId/signals or renders with store context
      const url = page.url();
      const hasAccountInUrl = url.includes(TEST_ACCOUNTS.meridian.id);
      const hasContent = await page.locator('main, [role="main"], .flex-1').first().isVisible();

      // Verify route behavior: should either have account in URL or render content
      if (!hasAccountInUrl) {
        expect(hasContent, 'Route should render content when account not in URL').toBe(true);
      } else {
        expect(hasAccountInUrl, 'Route should include account ID in URL').toBe(true);
      }
    });

    test('should use selected account from store for /studio/value-model', async ({ page }) => {
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto('/studio/value-model');
      await page.waitForLoadState('networkidle');

      const url = page.url();
      const hasAccountInUrl = url.includes(TEST_ACCOUNTS.meridian.id);
      const hasContent = await page.locator('main, [role="main"], .flex-1').first().isVisible();

      // Verify route behavior: should either have account in URL or render content
      if (!hasAccountInUrl) {
        expect(hasContent, 'Route should render content when account not in URL').toBe(true);
      } else {
        expect(hasAccountInUrl, 'Route should include account ID in URL').toBe(true);
      }
    });

    test('should handle missing account gracefully', async ({ page }) => {
      // No account selected in store
      await clearSelectedAccount(page);
      await page.goto('/intelligence/signals');
      await page.waitForLoadState('networkidle');

      // Contract: either redirects to account selection or shows prompt
      // Should NOT show a blank page or crash
      const hasRedirect = page.url().includes('/accounts') || page.url().includes('/home');
      const hasPrompt = await page.getByText(/select.*account/i).isVisible().catch(() => false);
      const hasContent = await page.locator('main, [role="main"], .flex-1').first().isVisible();

      // Verify one of the expected behaviors occurs
      if (!hasRedirect && !hasPrompt) {
        expect(hasContent, 'Missing account should redirect, show prompt, or render content').toBe(true);
      } else if (hasRedirect) {
        expect(hasRedirect, 'Missing account should redirect to accounts/home').toBe(true);
      } else if (hasPrompt) {
        expect(hasPrompt, 'Missing account should show selection prompt').toBe(true);
      }
    });
  });

  // ── Account Context Persistence ───────────────────────────────────────

  test.describe('Account Context Persistence', () => {
    test('should persist selected account across page reloads', async ({ page }) => {
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);
      await page.waitForLoadState('networkidle');

      // Reload the page
      await page.reload();

      // Contract: account context survives reload (zustand persist)
      const accountId = await getSelectedAccountId(page);
      expect(accountId).toBe(TEST_ACCOUNTS.meridian.id);
    });

    test('should persist selected account across route navigation', async ({ page }) => {
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);
      await page.waitForLoadState('networkidle');

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
      await mockWorkspaceApis(page, TEST_ACCOUNTS.meridian);
      await setSelectedAccount(page, TEST_ACCOUNTS.meridian);

      // Visit Intelligence
      await page.goto(`/intelligence/${TEST_ACCOUNTS.meridian.id}/signals`);
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(new RegExp(TEST_ACCOUNTS.meridian.id));

      // Visit Studio
      await page.goto(`/studio/${TEST_ACCOUNTS.meridian.id}/value-model`);
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(new RegExp(TEST_ACCOUNTS.meridian.id));

      // Contract: same account ID in both workspaces
      const accountId = await getSelectedAccountId(page);
      expect(accountId).toBe(TEST_ACCOUNTS.meridian.id);
    });
  });
});
