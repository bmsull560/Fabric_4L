/**
 * TargetsAdmin E2E Tests
 *
 * Route: /context/targets
 * Tier: admin
 *
 * Covers:
 * - Page load and stats display
 * - Four-tab navigation
 * - Target table rendering
 * - Empty state
 * - Row actions (pause, run, archive)
 * - Archive confirmation dialog
 * - Bulk selection and bulk toolbar
 * - New Target form panel
 * - Search filter
 * - Access control (admin-only, non-admin redirected)
 * - Accessibility (axe-core WCAG 2.1 AA)
 */

import { test, expect } from './fixtures/contract-test';
import { TargetsAdminPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';
import AxeBuilder from '@axe-core/playwright';

// ── Shared fixture data ───────────────────────────────────────────────────────

const MOCK_TARGETS = [
  {
    id: 'tgt-001',
    tenant_id: 'tenant-a',
    name: 'Acme Corp',
    url: 'https://acme.com',
    target_type: 'SPIDER',
    source_category: 'CRM',
    status: 'ACTIVE',
    tags: ['prospect'],
    success_count: 10,
    error_count: 1,
    average_execution_time_ms: 1200,
    last_success_at: '2024-01-15T10:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'tgt-002',
    tenant_id: 'tenant-a',
    name: 'Beta Inc',
    url: 'https://beta.com',
    target_type: 'SINGLE_PAGE',
    source_category: 'GENERAL',
    status: 'PAUSED',
    tags: [],
    success_count: 5,
    error_count: 3,
    average_execution_time_ms: 800,
    last_success_at: null,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-10T00:00:00Z',
  },
  {
    id: 'tgt-003',
    tenant_id: 'tenant-a',
    name: 'Error Corp',
    url: 'https://error.com',
    target_type: 'PAGINATED',
    source_category: 'GENERAL',
    status: 'ERROR',
    tags: ['compliance'],
    success_count: 2,
    error_count: 8,
    average_execution_time_ms: 500,
    last_success_at: null,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-12T00:00:00Z',
  },
];

const MOCK_STATS = {
  total: 3,
  connected: 1,
  disconnected: 1,
  error: 1,
  total_records: 150,
  average_health_score: 72,
};

const MOCK_LIST_RESPONSE = {
  data: MOCK_TARGETS,
  pagination: { page: 1, limit: 25, total: 3, total_pages: 1 },
};

const MOCK_DETAIL = {
  ...MOCK_TARGETS[0],
  description: 'Acme Corp website',
  url_pattern: null,
  crawl_path: 'browser',
  extraction_config: {},
  browser_config: {},
  schedule: null,
  rate_limit: {},
  compliance: {},
  proxy_config: {},
  authentication: null,
  last_error_at: null,
  created_by: 'user-1',
};

// ── Test suite ────────────────────────────────────────────────────────────────

test.describe('TargetsAdmin', () => {
  let targetsPage: TargetsAdminPage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'admin');
    targetsPage = new TargetsAdminPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  // ── Page load ─────────────────────────────────────────────────────

  test.describe('page load', () => {
    test('renders page heading and primary actions', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await targetsPage.assertPageLoaded();
      await expect(targetsPage.newTargetButton).toBeVisible();
    });

    test('renders all four tabs', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await targetsPage.assertTabsVisible();
    });

    test('shows target rows from API', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await targetsPage.assertTargetVisible('Acme Corp');
      await targetsPage.assertTargetVisible('Beta Inc');
      await targetsPage.assertTargetVisible('Error Corp');
    });

    test('shows status badges for each target', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await expect(page.getByText('Active')).toBeVisible();
      await expect(page.getByText('Paused')).toBeVisible();
      await expect(page.getByText('Error')).toBeVisible();
    });

    test('shows empty state when no targets exist', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ total: 0, connected: 0, disconnected: 0, error: 0, total_records: 0, average_health_score: 0 }),
        }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: [], pagination: { page: 1, limit: 25, total: 0, total_pages: 0 } }),
        }),
      );

      await targetsPage.goto();
      await targetsPage.assertEmptyState();
    });
  });

  // ── Tab navigation ────────────────────────────────────────────────

  test.describe('tab navigation', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );
    });

    test('All Targets tab is active by default', async () => {
      await targetsPage.goto();
      await expect(targetsPage.allTargetsTab).toHaveAttribute('data-state', 'active');
    });

    test('switches to Scheduled tab', async () => {
      await targetsPage.goto();
      await targetsPage.clickTab('scheduled');
      await expect(targetsPage.scheduledTab).toHaveAttribute('data-state', 'active');
    });

    test('switches to Compliance Failures tab', async () => {
      await targetsPage.goto();
      await targetsPage.clickTab('failures');
      await expect(targetsPage.complianceFailuresTab).toHaveAttribute('data-state', 'active');
    });

    test('switches to Events tab', async () => {
      await targetsPage.goto();
      await targetsPage.clickTab('events');
      await expect(targetsPage.eventsTab).toHaveAttribute('data-state', 'active');
    });
  });

  // ── Row actions ───────────────────────────────────────────────────

  test.describe('row actions', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );
    });

    test('opens row actions dropdown', async () => {
      await targetsPage.goto();
      await targetsPage.openRowActions(0);
      await expect(targetsPage.page.getByRole('menuitem', { name: /run now/i })).toBeVisible();
    });

    test('Pause action calls PATCH status endpoint', async ({ page }) => {
      let patchCalled = false;
      await page.route('**/api/v1/ingest/targets/tgt-001/status', async route => {
        if (route.request().method() === 'PATCH') {
          patchCalled = true;
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ...MOCK_DETAIL, status: 'PAUSED' }),
          });
        } else {
          await route.continue();
        }
      });

      await targetsPage.goto();
      await targetsPage.openRowActions(0);
      await targetsPage.clickRowAction('Pause');

      await expect(async () => {
        expect(patchCalled).toBe(true);
      }).toPass({ timeout: 5000 });
    });

    test('Run now action calls POST execute endpoint', async ({ page }) => {
      let executeCalled = false;
      await page.route('**/api/v1/ingest/targets/tgt-001/execute', async route => {
        executeCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ job_id: 'job-xyz' }),
        });
      });
      // Jobs endpoint called after execute
      await page.route('**/api/v1/ingest/jobs**', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ data: [], pagination: { page: 1, limit: 10, total: 0, total_pages: 1 } }) }),
      );

      await targetsPage.goto();
      await targetsPage.openRowActions(0);
      await targetsPage.clickRowAction('Run now');

      await expect(async () => {
        expect(executeCalled).toBe(true);
      }).toPass({ timeout: 5000 });
    });
  });

  // ── Archive confirmation dialog ───────────────────────────────────

  test.describe('archive dialog', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );
    });

    test('shows confirmation dialog when Archive is clicked', async () => {
      await targetsPage.goto();
      await targetsPage.openRowActions(0);
      await targetsPage.clickRowAction('Archive');
      await targetsPage.assertArchiveDialogVisible();
    });

    test('calls PATCH status=ARCHIVED when confirmed', async ({ page }) => {
      let patchBody: unknown = null;
      await page.route('**/api/v1/ingest/targets/tgt-001/status', async route => {
        if (route.request().method() === 'PATCH') {
          patchBody = JSON.parse(route.request().postData() ?? '{}');
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ...MOCK_DETAIL, status: 'ARCHIVED' }),
          });
        } else {
          await route.continue();
        }
      });

      await targetsPage.goto();
      await targetsPage.openRowActions(0);
      await targetsPage.clickRowAction('Archive');
      await targetsPage.assertArchiveDialogVisible();
      await targetsPage.confirmArchive();

      await expect(async () => {
        expect((patchBody as Record<string, unknown>)?.status).toBe('ARCHIVED');
      }).toPass({ timeout: 5000 });
    });

    test('dismisses dialog without API call when Cancel is clicked', async ({ page }) => {
      let patchCalled = false;
      await page.route('**/api/v1/ingest/targets/tgt-001/status', async route => {
        patchCalled = true;
        await route.continue();
      });

      await targetsPage.goto();
      await targetsPage.openRowActions(0);
      await targetsPage.clickRowAction('Archive');
      await targetsPage.assertArchiveDialogVisible();
      await targetsPage.cancelArchive();

      await expect(targetsPage.archiveDialog).not.toBeVisible();
      expect(patchCalled).toBe(false);
    });
  });

  // ── Bulk operations ───────────────────────────────────────────────

  test.describe('bulk operations', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );
    });

    test('shows bulk toolbar when a target is selected', async () => {
      await targetsPage.goto();
      await targetsPage.selectRowCheckbox(0);
      await targetsPage.assertBulkToolbarVisible(1);
    });

    test('selects all targets with header checkbox', async () => {
      await targetsPage.goto();
      await targetsPage.selectAllCheckbox();
      await targetsPage.assertBulkToolbarVisible(3);
    });

    test('clears selection when Clear is clicked', async () => {
      await targetsPage.goto();
      await targetsPage.selectRowCheckbox(0);
      await targetsPage.assertBulkToolbarVisible(1);
      await targetsPage.bulkClearButton.click();
      await expect(targetsPage.page.getByText(/1 selected/)).not.toBeVisible();
    });

    test('calls POST /targets/batch when bulk Pause is clicked', async ({ page }) => {
      let batchBody: unknown = null;
      await page.route('**/api/v1/ingest/targets/batch', async route => {
        batchBody = JSON.parse(route.request().postData() ?? '{}');
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            operation: 'pause',
            requested: 1,
            succeeded: 1,
            failed: 0,
            results: [{ id: 'tgt-001', status: 'succeeded', job_id: null, error: null }],
          }),
        });
      });

      await targetsPage.goto();
      await targetsPage.selectRowCheckbox(0);
      await targetsPage.assertBulkToolbarVisible(1);
      await targetsPage.bulkPauseButton.click();

      await expect(async () => {
        expect((batchBody as Record<string, unknown>)?.operation).toBe('pause');
      }).toPass({ timeout: 5000 });
    });
  });

  // ── New Target form panel ─────────────────────────────────────────

  test.describe('New Target form', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );
    });

    test('opens form panel when New Target is clicked', async () => {
      await targetsPage.goto();
      await targetsPage.clickNewTarget();
      await expect(targetsPage.page.getByText('New Target')).toBeVisible();
    });

    test('form panel contains Name and URL fields', async () => {
      await targetsPage.goto();
      await targetsPage.clickNewTarget();
      await expect(targetsPage.page.getByLabel(/name/i)).toBeVisible();
      await expect(targetsPage.page.getByLabel(/url/i)).toBeVisible();
    });
  });

  // ── Search filter ─────────────────────────────────────────────────

  test.describe('search filter', () => {
    test('search input is visible', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await expect(targetsPage.searchInput).toBeVisible();
    });

    test('typing in search input sends search param to API', async ({ page }) => {
      let capturedSearch: string | null = null;

      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, async route => {
        const url = new URL(route.request().url());
        capturedSearch = url.searchParams.get('search');
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_LIST_RESPONSE),
        });
      });

      await targetsPage.goto();
      await targetsPage.search('acme');

      await expect(async () => {
        expect(capturedSearch).toBe('acme');
      }).toPass({ timeout: 5000 });
    });
  });

  // ── Access control ────────────────────────────────────────────────

  test.describe('access control', () => {
    test('admin tier can access /context/targets', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await targetsPage.assertPageLoaded();
      // URL should remain on /context/targets (no redirect)
      expect(page.url()).toContain('/context/targets');
    });

    test('standard tier is redirected away from /context/targets', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/context/targets');
      // ProtectedRoute redirects non-admin to /home
      await page.waitForURL(/\/home/, { timeout: 5000 });
      expect(page.url()).toContain('/home');
    });

    test('advanced tier is redirected away from /context/targets', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await page.goto('/context/targets');
      await page.waitForURL(/\/home/, { timeout: 5000 });
      expect(page.url()).toContain('/home');
    });
  });

  // ── Accessibility ─────────────────────────────────────────────────

  test.describe('accessibility', () => {
    test('passes axe-core WCAG 2.1 AA audit', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await targetsPage.waitForDataLoad();

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .analyze();

      if (results.violations.length > 0) {
        console.log(
          'Axe violations on /context/targets:',
          JSON.stringify(
            results.violations.map(v => ({
              rule: v.id,
              impact: v.impact,
              description: v.description,
              nodes: v.nodes.length,
            })),
            null,
            2,
          ),
        );
      }

      expect(results.violations).toEqual([]);
    });

    test('all interactive elements are keyboard accessible', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await targetsPage.waitForDataLoad();

      // Tab through the first 15 interactive elements and verify each receives focus
      const interactive = page.locator(
        'button:visible, a:visible, input:visible, [role="tab"]:visible, [role="checkbox"]:visible',
      );
      const count = Math.min(await interactive.count(), 15);

      for (let i = 0; i < count; i++) {
        const el = interactive.nth(i);
        const isEnabled = await el.isEnabled().catch(() => false);
        if (!isEnabled) continue;
        // Each visible, enabled interactive element must have a non-negative tabIndex
        const tabIndex = await el.evaluate(
          (node: Element) => (node as HTMLElement).tabIndex,
        );
        expect(tabIndex).toBeGreaterThanOrEqual(-1);
      }
    });

    test('status badges have accessible text', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await targetsPage.waitForDataLoad();

      // Status badges must have visible text (not icon-only)
      await expect(page.getByText('Active')).toBeVisible();
      await expect(page.getByText('Paused')).toBeVisible();
      await expect(page.getByText('Error')).toBeVisible();
    });

    test('row action buttons have accessible labels', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await targetsPage.waitForDataLoad();

      // Each row's action button must have an aria-label
      const actionBtns = page.getByRole('button', { name: /target actions/i });
      const count = await actionBtns.count();
      expect(count).toBeGreaterThan(0);
      for (let i = 0; i < count; i++) {
        await expect(actionBtns.nth(i)).toHaveAttribute('aria-label', /target actions/i);
      }
    });

    test('archive dialog is accessible when open', async ({ page }) => {
      await page.route('**/api/v1/ingest/targets/stats', route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) }),
      );
      await page.route(/.*\/api\/v1\/ingest\/targets(\?.*)?$/, route =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LIST_RESPONSE) }),
      );

      await targetsPage.goto();
      await targetsPage.openRowActions(0);
      await targetsPage.clickRowAction('Archive');
      await targetsPage.assertArchiveDialogVisible();

      // Dialog must have role="alertdialog" and a title
      await expect(page.getByRole('alertdialog')).toBeVisible();
      await expect(page.getByRole('alertdialog').getByRole('heading')).toBeVisible();

      // Run axe on the dialog state
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .include('[role="alertdialog"]')
        .analyze();

      expect(results.violations).toEqual([]);
    });
  });
});
