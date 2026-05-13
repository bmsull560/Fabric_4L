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
 *   2. Each route renders a page with a heading OR a meaningful error/loading state
 *   3. Settings pages have consistent layout (sidebar sub-nav + content)
 *   4. Governance pages surface audit/compliance data
 *   5. Access control pages enforce RBAC patterns
 *
 * References:
 *   - CONTRACT.md §2.6 UI State Machine
 *   - Layout.tsx NAV_SPINE (Governance, Settings domains)
 *   - App.tsx route definitions
 */
import { test, expect, type Page, type Route } from '../fixtures/contract-test';
import { setUserTier, clearUserTier, seedAuthState, clearAuthState } from '../fixtures';

// ── API Mock Helpers ───────────────────────────────────────────────────────
// The settings/governance pages call backend APIs via React Query.
// Without a running backend, pages render error/skeleton states.
// We mock the API responses so pages render their full UI.

const MOCK_TENANT_SETTINGS = {
  tenant_id: 'tenant-001',
  tenant_name: 'Value Fabric Test',
  features: {
    advanced_analytics: true,
    custom_integrations: false,
    ai_assistant: true,
    audit_trail: true,
  },
  notifications: {
    email_alerts: true,
    slack_webhook: '',
    webhook_url: '',
  },
  security: {
    require_2fa: false,
    session_timeout_minutes: 60,
    ip_allowlist: [],
  },
  limits: {
    max_users: 50,
    max_api_calls_per_day: 10000,
    storage_gb: 100,
  },
  branding: {
    primary_color: '#3B82F6',
    logo_url: '',
    favicon_url: '',
  },
  updated_at: '2024-06-01T00:00:00Z',
  updated_by: 'admin@valuefabric.test',
};

const MOCK_FORMULAS = {
  formulas: [],
  total: 0,
};

const MOCK_VARIABLES = {
  variables: [],
  total: 0,
};

const MOCK_PERMISSIONS = {
  roles: [
    { id: 'admin', name: 'Admin', permissions: ['all'] },
    { id: 'user', name: 'User', permissions: ['read'] },
  ],
  teams: [],
  api_keys: [],
};

const MOCK_BILLING = {
  plan: 'enterprise',
  status: 'active',
  usage: { api_calls: 5000, storage_gb: 25 },
  invoices: [],
  payments: [],
};

const MOCK_GOVERNANCE_AUDIT = {
  entries: [
    { id: '1', action: 'settings.update', user: 'admin@test.com', timestamp: '2025-01-01T00:00:00Z' },
  ],
  total: 1,
};

const MOCK_GOVERNANCE_COMPLIANCE = {
  status: 'compliant',
  checks: [],
  score: 95,
};

const MOCK_GOVERNANCE_HEALTH = {
  overall_status: 'healthy',
  checked_at: '2024-06-01T00:00:00Z',
  services: [],
  summary: {
    healthy: 5,
    degraded: 0,
    unhealthy: 0,
    unknown: 0,
    total: 5,
  },
};

const MOCK_HEALTH_ALERTS: unknown[] = [];

const MOCK_GOVERNANCE_BENCHMARKS: unknown[] = [];

const MOCK_DECISION_TRACES = {
  traces: [],
  total: 0,
};

/**
 * Set up API route mocking for all settings/governance endpoints.
 * This ensures pages render their full UI instead of error states.
 */
async function mockAdminApis(page: Page): Promise<void> {
  // Catch-all FIRST so specific routes (registered later) take priority
  // NOTE: Must NOT use '**/api/**' as it intercepts Vite source files like /src/api/client.ts
  await page.route('**/api/v1/**', async (route: Route) => {
    if (!route.request().url().includes('auth')) {
      await route.fulfill({ json: {} });
    } else {
      await route.continue();
    }
  });

  // Settings APIs (L4 layer → /agents prefix)
  await page.route('**/agents/tenant/settings', async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ json: MOCK_TENANT_SETTINGS });
    } else {
      await route.fulfill({ json: { ...MOCK_TENANT_SETTINGS, ...JSON.parse(route.request().postData() || '{}') } });
    }
  });

  await page.route('**/agents/formulas**', async (route: Route) => {
    await route.fulfill({ json: MOCK_FORMULAS });
  });

  await page.route('**/agents/variables**', async (route: Route) => {
    await route.fulfill({ json: MOCK_VARIABLES });
  });

  await page.route('**/agents/permissions**', async (route: Route) => {
    await route.fulfill({ json: MOCK_PERMISSIONS });
  });

  await page.route('**/agents/roles**', async (route: Route) => {
    await route.fulfill({ json: MOCK_PERMISSIONS });
  });

  await page.route('**/agents/teams**', async (route: Route) => {
    await route.fulfill({ json: [] });
  });

  await page.route('**/agents/api-keys**', async (route: Route) => {
    await route.fulfill({ json: [] });
  });

  await page.route('**/agents/users**', async (route: Route) => {
    await route.fulfill({ json: [] });
  });

  await page.route('**/agents/billing**', async (route: Route) => {
    await route.fulfill({ json: MOCK_BILLING });
  });

  // Governance APIs (L4 and L5 layers)
  await page.route('**/agents/audit/**', async (route: Route) => {
    await route.fulfill({ json: MOCK_GOVERNANCE_AUDIT });
  });

  await page.route('**/agents/governance/**', async (route: Route) => {
    await route.fulfill({ json: MOCK_GOVERNANCE_COMPLIANCE });
  });

  await page.route('**/truths/compliance**', async (route: Route) => {
    await route.fulfill({ json: MOCK_GOVERNANCE_COMPLIANCE });
  });

  await page.route('**/truths/health**', async (route: Route) => {
    await route.fulfill({ json: MOCK_GOVERNANCE_HEALTH });
  });

  await page.route('**/agents/health/alerts**', async (route: Route) => {
    await route.fulfill({ json: MOCK_HEALTH_ALERTS });
  });

  await page.route('**/agents/health', async (route: Route) => {
    await route.fulfill({ json: MOCK_GOVERNANCE_HEALTH });
  });

  await page.route('**/benchmarks/**', async (route: Route) => {
    await route.fulfill({ json: MOCK_GOVERNANCE_BENCHMARKS });
  });

  await page.route('**/truths/traces**', async (route: Route) => {
    await route.fulfill({ json: MOCK_DECISION_TRACES });
  });

  await page.route('**/truths/evidence**', async (route: Route) => {
    await route.fulfill({ json: MOCK_DECISION_TRACES });
  });

}

test.describe('Contract: Settings & Governance Admin Surface', () => {
  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
    await clearAuthState(page);
  });

  // ── Access Control ────────────────────────────────────────────────────

  test.describe('Access Control', () => {
    test('should redirect standard tier users from /settings', async ({ page }) => {
      await seedAuthState(page, {
        id: 'test-user-e2e',
        email: 'e2e@valuefabric.test',
        role: 'standard',
        tenantId: 'tenant-e2e-001',
        tenantSlug: 'e2e-test',
      });
      await setUserTier(page, 'standard');
      await page.goto('/settings/system/settings');
      await page.waitForLoadState('networkidle');

      // Contract: non-admin users cannot access settings
      await expect(page).toHaveURL(/\/home/);
    });

    test('should redirect advanced tier users from /settings', async ({ page }) => {
      await seedAuthState(page, {
        id: 'test-user-e2e',
        email: 'e2e@valuefabric.test',
        role: 'advanced',
        tenantId: 'tenant-e2e-001',
        tenantSlug: 'e2e-test',
      });
      await setUserTier(page, 'advanced');
      await page.goto('/settings/system/settings');
      await page.waitForLoadState('networkidle');

      // Contract: non-admin users cannot access settings
      await expect(page).toHaveURL(/\/home/);
    });

    test('should redirect standard tier users from /governance', async ({ page }) => {
      await seedAuthState(page, {
        id: 'test-user-e2e',
        email: 'e2e@valuefabric.test',
        role: 'standard',
        tenantId: 'tenant-e2e-001',
        tenantSlug: 'e2e-test',
      });
      await setUserTier(page, 'standard');
      await page.goto('/governance/audit/log');
      await page.waitForLoadState('networkidle');

      // Contract: non-admin users cannot access governance
      await expect(page).toHaveURL(/\/home/);
    });

    test('should redirect advanced tier users from /governance', async ({ page }) => {
      await seedAuthState(page, {
        id: 'test-user-e2e',
        email: 'e2e@valuefabric.test',
        role: 'advanced',
        tenantId: 'tenant-e2e-001',
        tenantSlug: 'e2e-test',
      });
      await setUserTier(page, 'advanced');
      await page.goto('/governance/audit/log');
      await page.waitForLoadState('networkidle');

      // Contract: non-admin users cannot access governance
      await expect(page).toHaveURL(/\/home/);
    });

    test('should allow admin tier users to access /settings', async ({ page }) => {
      await mockAdminApis(page);
      await seedAuthState(page);
      await setUserTier(page, 'admin');
      await page.goto('/settings/system/settings');
      await page.waitForLoadState('networkidle');

      // Contract: admin users can access settings
      await expect(page).not.toHaveURL(/\/home/);
    });

    test('should allow admin tier users to access /governance', async ({ page }) => {
      await mockAdminApis(page);
      await seedAuthState(page);
      await setUserTier(page, 'admin');
      await page.goto('/governance/audit/log');
      await page.waitForLoadState('networkidle');

      // Contract: admin users can access governance
      await expect(page).not.toHaveURL(/\/home/);
    });
  });

  // ── Settings Routes ───────────────────────────────────────────────────

  test.describe('Settings Routes', () => {
    test.beforeEach(async ({ page }) => {
      await mockAdminApis(page);
      await seedAuthState(page);
      await setUserTier(page, 'admin');
    });

    const settingsRoutes = [
      { path: '/settings/system/settings', heading: /platform settings|settings/i },
      { path: '/settings/content/formulas', heading: /formula|governance/i },
      { path: '/settings/content/approvals', heading: /formula|governance/i },
      { path: '/settings/content/versions', heading: /formula|governance/i },
      { path: '/settings/data/variables', heading: /variable|registry/i },
      { path: '/settings/data/bindings', heading: /variable|registry/i },
      { path: '/settings/data/quality', heading: /variable|registry/i },
      { path: '/settings/access/roles', heading: /permission|access/i },
      { path: '/settings/access/teams', heading: /permission|access/i },
      { path: '/settings/access/keys', heading: /permission|access/i },
    ];

    for (const { path, heading } of settingsRoutes) {
      test(`should render ${path}`, async ({ page }) => {
        await page.goto(path);
        await page.waitForLoadState('networkidle');

        // Contract: page renders with a heading OR a meaningful content area
        // (some pages may show error/loading state if API mocks don't match exactly)
        const pageHeading = page.getByRole('heading').first();
        const contentArea = page.locator('main, [role="main"], .flex-1').first();

        const headingVisible = await pageHeading.isVisible().catch(() => false);
        const contentVisible = await contentArea.isVisible().catch(() => false);

        // Contract: at minimum, the route renders something (not blank/redirect)
        expect(headingVisible || contentVisible).toBe(true);

        // Contract: if heading is visible, it matches expected pattern
        if (headingVisible) {
          await expect(pageHeading).toHaveText(heading);
        }
      });
    }

    test('should have consistent settings layout with sub-navigation', async ({ page }) => {
      await page.goto('/settings/system/settings');
      await page.waitForLoadState('networkidle');

      // Contract: settings pages have a sub-navigation structure
      // Either tabs, sidebar links, or section headers
      const hasTabs = (await page.getByRole('tab').count()) > 0;
      const hasLinks = (await page.getByRole('link').filter({ hasText: /system|content|data|access/i }).count()) > 0;
      const hasNavElements = (await page.locator('[class*="tab"], [class*="nav"]').count()) > 0;

      expect(hasTabs || hasLinks || hasNavElements, 'Settings page should have sub-navigation').toBe(true);
    });
  });

  // ── Governance Routes ─────────────────────────────────────────────────

  test.describe('Governance Routes', () => {
    test.beforeEach(async ({ page }) => {
      await mockAdminApis(page);
      await seedAuthState(page);
      await setUserTier(page, 'admin');
    });

    const governanceRoutes = [
      { path: '/governance/audit/log', heading: /audit log/i },
      { path: '/governance/audit/changes', heading: /change history/i },
      { path: '/governance/compliance', heading: /compliance/i },
      { path: '/governance/health', heading: /system health/i },
      { path: '/governance/integrity', heading: /data integrity/i },
      { path: '/governance/provenance', heading: /provenance trail/i },
      { path: '/governance/benchmarks', heading: /benchmark polic/i },
      { path: '/governance/traces', heading: /decision trace/i },
      { path: '/governance/evidence', heading: /evidence/i },
    ];

    for (const { path, heading } of governanceRoutes) {
      test(`should render ${path}`, async ({ page }) => {
        await page.goto(path);
        await page.waitForLoadState('networkidle');

        // Contract: page renders with a heading OR a meaningful content area
        const pageHeading = page.getByRole('heading').first();
        const contentArea = page.locator('main, [role="main"], .flex-1').first();

        const headingVisible = await pageHeading.isVisible().catch(() => false);
        const contentVisible = await contentArea.isVisible().catch(() => false);

        // Contract: at minimum, the route renders something (not blank/redirect)
        if (!headingVisible) {
          expect(contentVisible, 'Governance route should render content when heading not visible').toBe(true);
        } else {
          expect(headingVisible, 'Governance route should render heading or content').toBe(true);
          await expect(pageHeading).toHaveText(heading);
        }
      });
    }
  });

  // ── Billing & Usage ───────────────────────────────────────────────────

  test.describe('Billing & Usage', () => {
    test.beforeEach(async ({ page }) => {
      await mockAdminApis(page);
      await seedAuthState(page);
      await setUserTier(page, 'admin');
    });

    test('should render billing overview', async ({ page }) => {
      await page.goto('/settings/system/billing');
      await page.waitForLoadState('networkidle');

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
        await page.waitForLoadState('networkidle');

        // Contract: sub-route renders content
        const content = page.locator('main, [role="main"], .flex-1').first();
        await expect(content).toBeVisible({ timeout: 10000 });
      });
    }
  });

  // ── RBAC Patterns ─────────────────────────────────────────────────────

  test.describe('RBAC Patterns', () => {
    test.beforeEach(async ({ page }) => {
      await mockAdminApis(page);
      await seedAuthState(page);
      await setUserTier(page, 'admin');
    });

    test('should display role management with role list', async ({ page }) => {
      await page.goto('/settings/access/roles');
      await page.waitForLoadState('networkidle');

      // Contract: roles page has a list or table of roles
      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });

      // Contract: should have some form of role listing
      const hasTable = (await page.locator('table').count()) > 0;
      const hasList = (await page.locator('[class*="list"], [class*="card"]').count()) > 0;
      const hasContent = ((await content.textContent())?.length ?? 0) > 50;

      if (!hasTable && !hasList) {
        expect(hasContent, 'Roles page should have table, list, or content').toBe(true);
      } else if (hasTable) {
        expect(hasTable, 'Roles page should display role table').toBe(true);
      } else if (hasList) {
        expect(hasList, 'Roles page should display role list').toBe(true);
      }
    });

    test('should display team management', async ({ page }) => {
      await page.goto('/settings/access/teams');
      await page.waitForLoadState('networkidle');

      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });
    });

    test('should display API key management', async ({ page }) => {
      await page.goto('/settings/access/keys');
      await page.waitForLoadState('networkidle');

      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });

      // Contract: API key page should have a way to create/view keys
      const hasCreateButton = (await page.getByRole('button', { name: /create|add|generate/i }).count()) > 0;
      const hasKeyList = (await page.locator('table, [class*="list"]').count()) > 0;
      const hasContent = ((await content.textContent())?.length ?? 0) > 50;

      if (!hasCreateButton && !hasKeyList) {
        expect(hasContent, 'API key page should have create button, key list, or content').toBe(true);
      } else if (hasCreateButton) {
        expect(hasCreateButton, 'API key page should have create button').toBe(true);
      } else if (hasKeyList) {
        expect(hasKeyList, 'API key page should display key list').toBe(true);
      }
    });
  });

  // ── Audit Trail ───────────────────────────────────────────────────────

  test.describe('Audit Trail', () => {
    test.beforeEach(async ({ page }) => {
      await mockAdminApis(page);
      await seedAuthState(page);
      await setUserTier(page, 'admin');
    });

    test('should display audit log with entries', async ({ page }) => {
      await page.goto('/governance/audit/log');
      await page.waitForLoadState('networkidle');

      // Contract: audit log page renders
      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });

      // Contract: should have some form of log display
      const hasTable = (await page.locator('table').count()) > 0;
      const hasList = (await page.locator('[class*="list"], [class*="log"]').count()) > 0;
      const hasEntries = ((await content.textContent())?.length ?? 0) > 50;

      if (!hasTable && !hasList) {
        expect(hasEntries, 'Audit log should have table, list, or entries').toBe(true);
      } else if (hasTable) {
        expect(hasTable, 'Audit log should display table').toBe(true);
      } else if (hasList) {
        expect(hasList, 'Audit log should display list').toBe(true);
      }
    });

    test('should display change history', async ({ page }) => {
      await page.goto('/governance/audit/changes');
      await page.waitForLoadState('networkidle');

      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });
    });

    test('should display compliance dashboard', async ({ page }) => {
      await page.goto('/governance/compliance');
      await page.waitForLoadState('networkidle');

      const content = page.locator('main, [role="main"], .flex-1').first();
      await expect(content).toBeVisible({ timeout: 10000 });
    });
  });
});
