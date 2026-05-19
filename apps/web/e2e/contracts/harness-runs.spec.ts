/**
 * CONTRACT TEST: Harness Runs UI
 *
 * TDD-first spec for the Harness Runs tab inside AgentWorkflows (/context/agents).
 * All tests are expected to FAIL until the UI is implemented.
 *
 * Covers (AC-01 through AC-17):
 *   AC-01  AgentWorkflows renders a "Harness Runs" tab
 *   AC-02  Tab is visible for advanced and admin tiers
 *   AC-03  Harness runs list renders from mocked GET /api/v1/agents/harness/runs
 *   AC-04  Each run row shows ID, workflow type, status badge, current state
 *   AC-05  Clicking a run opens HarnessRunDetail panel
 *   AC-06  Detail panel shows run metadata (ID, trace ID, type, status, state)
 *   AC-07  Checkpoints render in chronological order
 *   AC-08  Pending human gate renders approve and reject buttons
 *   AC-09  Approve button calls POST /api/v1/agents/harness/gates/:gateId/decide with { decision: "approved" }
 *   AC-10  Reject button calls POST /api/v1/agents/harness/gates/:gateId/decide with { decision: "rejected" }
 *   AC-11  Buttons are disabled while mutation is pending
 *   AC-12  Terminal gate renders as read-only (no approve/reject buttons)
 *   AC-13  Non-terminal run triggers polling within 6 s
 *   AC-14  Terminal run does not trigger polling after initial load
 *   AC-15  Loading state renders skeleton/spinner
 *   AC-16  Empty state renders "No harness runs found."
 *   AC-17  Error state renders error message
 *
 * All API routes are mocked — no backend required.
 * Uses the contract-test fixture which auto-installs the API harness.
 *
 * Harness UI is implemented and contract gaps are resolved. All tests are
 * expected to pass. The TDD red phase (test.fail()) has been removed.
 */
import { test, expect, type Page } from '../fixtures/contract-test';
import { setUserTier, clearUserTier } from '../fixtures/tier-helpers';
import { seedAuthState, clearAuthState } from '../fixtures/auth-helpers';
import { AgentWorkflowsPage } from '../pages/AgentWorkflowsPage';
import { HarnessRunDetailPage } from '../pages/HarnessRunDetailPage';
import {
  HARNESS_RUNS_LIST,
  EMPTY_HARNESS_RUNS_LIST,
  WAITING_RUN_LIST,
  RUNNING_RUN,
  COMPLETED_RUN,
  WAITING_RUN,
  RUNNING_RUN_CHECKPOINTS,
  PENDING_GATE,
  APPROVED_GATE,
} from '../fixtures/harness-fixtures';

// ── Shared mock helpers ──────────────────────────────────────────────────────

/**
 * Register harness API mocks on the page.
 * Must be called before page.goto() so routes are in place before navigation.
 * These override the DEFAULT_MOCKS empty-list fallback from the API harness.
 */
async function mockHarnessRunsList(page: Page, body: unknown, status = 200): Promise<void> {
  // Trailing ** matches optional query strings (e.g. ?tenant_id=...).
  // The URL check ensures this only intercepts the list endpoint, not
  // sub-resources like /runs/123 or /runs/123/checkpoints.
  await page.route('**/api/v1/agents/harness/runs**', async (route) => {
    const url = new URL(route.request().url());
    const isListEndpoint = /\/harness\/runs\/?$/.test(url.pathname);
    if (route.request().method() === 'GET' && isListEndpoint) {
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
    } else {
      await route.continue();
    }
  });
}

async function mockHarnessRunDetail(page: Page, runId: string, body: unknown): Promise<void> {
  await page.route(`**/api/v1/agents/harness/runs/${runId}`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
    } else {
      await route.continue();
    }
  });
}

async function mockHarnessCheckpoints(
  page: Page,
  runId: string,
  body: unknown,
): Promise<void> {
  await page.route(`**/api/v1/agents/harness/runs/${runId}/checkpoints`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
    } else {
      await route.continue();
    }
  });
}

async function mockHarnessGates(page: Page, runId: string, body: unknown): Promise<void> {
  await page.route(`**/api/v1/agents/harness/runs/${runId}/gates`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
    } else {
      await route.continue();
    }
  });
}

async function mockGateDecide(
  page: Page,
  gateId: string,
  responseBody: unknown,
  status = 200,
): Promise<void> {
  await page.route(
    `**/api/v1/agents/harness/gates/${gateId}/decide`,
    async (route) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(responseBody),
      });
    },
  );
}

// ── Test suite ───────────────────────────────────────────────────────────────

test.describe('Contract: Harness Runs UI', () => {

  let workflowsPage: AgentWorkflowsPage;
  let detailPage: HarnessRunDetailPage;

  test.beforeEach(async ({ page }) => {
    await seedAuthState(page);
    await setUserTier(page, 'admin');
    workflowsPage = new AgentWorkflowsPage(page);
    detailPage = new HarnessRunDetailPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
    await clearAuthState(page);
  });

  // ── AC-01: Harness Runs tab exists ────────────────────────────────────

  test.describe('Harness Runs tab', () => {
    test('AC-01: AgentWorkflows renders a Harness Runs tab', async ({ page }) => {
      await mockHarnessRunsList(page, HARNESS_RUNS_LIST);
      await workflowsPage.goto();
      await page.waitForLoadState('domcontentloaded');

      await expect(workflowsPage.harnessRunsTab).toBeVisible({ timeout: 5000 });
    });

    // ── AC-02: Tier visibility ────────────────────────────────────────

    test('AC-02: Harness Runs tab is visible for advanced tier', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await mockHarnessRunsList(page, HARNESS_RUNS_LIST);
      await workflowsPage.goto();
      await page.waitForLoadState('domcontentloaded');

      await expect(workflowsPage.harnessRunsTab).toBeVisible({ timeout: 5000 });
    });

    test('AC-02: Harness Runs tab is visible for admin tier', async ({ page }) => {
      await mockHarnessRunsList(page, HARNESS_RUNS_LIST);
      await workflowsPage.goto();
      await page.waitForLoadState('domcontentloaded');

      await expect(workflowsPage.harnessRunsTab).toBeVisible({ timeout: 5000 });
    });
  });

  // ── AC-03 / AC-04: Runs list renders ─────────────────────────────────

  test.describe('Harness Runs list', () => {
    test('AC-03: harness runs list renders from mocked API', async ({ page }) => {
      await mockHarnessRunsList(page, HARNESS_RUNS_LIST);
      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      // Both runs from the fixture should appear
      await expect(page.getByText(RUNNING_RUN.id)).toBeVisible({ timeout: 5000 });
      await expect(page.getByText(COMPLETED_RUN.id)).toBeVisible({ timeout: 5000 });
    });

    test('AC-04: each run row shows ID, workflow type, status badge, current state', async ({
      page,
    }) => {
      await mockHarnessRunsList(page, HARNESS_RUNS_LIST);
      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      // Run ID
      await expect(page.getByText(RUNNING_RUN.id)).toBeVisible({ timeout: 5000 });
      // Workflow type (human-readable or raw enum value)
      await expect(
        page.getByText(/business.case.generation|business case/i).first(),
      ).toBeVisible({ timeout: 5000 });
      // Status — "running" badge
      await expect(page.getByText(/running/i).first()).toBeVisible({ timeout: 5000 });
      // Current state
      await expect(page.getByText(/VALIDATE_CLAIMS|validate.claims/i).first()).toBeVisible({
        timeout: 5000,
      });
    });
  });

  // ── AC-05 / AC-06: Run detail panel ──────────────────────────────────

  test.describe('HarnessRunDetail panel', () => {
    test('AC-05: clicking a run opens HarnessRunDetail panel', async ({ page }) => {
      await mockHarnessRunsList(page, HARNESS_RUNS_LIST);
      await mockHarnessRunDetail(page, RUNNING_RUN.id, RUNNING_RUN);
      await mockHarnessCheckpoints(page, RUNNING_RUN.id, RUNNING_RUN_CHECKPOINTS);
      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      await workflowsPage.clickRunRow(0);

      await detailPage.assertOpen();
    });

    test('AC-06: detail panel shows run metadata', async ({ page }) => {
      await mockHarnessRunsList(page, HARNESS_RUNS_LIST);
      await mockHarnessRunDetail(page, RUNNING_RUN.id, RUNNING_RUN);
      await mockHarnessCheckpoints(page, RUNNING_RUN.id, RUNNING_RUN_CHECKPOINTS);
      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      await workflowsPage.clickRunRow(0);
      await detailPage.assertOpen();

      // Run ID visible in panel
      await detailPage.assertRunIdVisible(RUNNING_RUN.id);
      // Trace ID visible in panel
      await detailPage.assertTraceIdVisible(RUNNING_RUN.trace_id);
    });
  });

  // ── AC-07: Checkpoint timeline ────────────────────────────────────────

  test.describe('Checkpoint timeline', () => {
    test('AC-07: checkpoints render in chronological order', async ({ page }) => {
      await mockHarnessRunsList(page, HARNESS_RUNS_LIST);
      await mockHarnessRunDetail(page, RUNNING_RUN.id, RUNNING_RUN);
      await mockHarnessCheckpoints(page, RUNNING_RUN.id, RUNNING_RUN_CHECKPOINTS);
      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      await workflowsPage.clickRunRow(0);
      await detailPage.assertOpen();

      // All three checkpoint state names should be visible
      await detailPage.assertCheckpointVisible('INIT');
      await detailPage.assertCheckpointVisible('RESOLVE_CONTEXT');
      await detailPage.assertCheckpointVisible('GENERATE_HYPOTHESES');

      // Verify chronological order in a single atomic DOM snapshot to avoid
      // race conditions between two separate evaluate() calls.
      const [initIndex, genIndex] = await page.evaluate(() => {
        const items = Array.from(
          document.querySelectorAll('[data-testid="checkpoint-item"], [class*="checkpoint"]'),
        );
        const textOf = (el: Element) => el.textContent ?? '';
        return [
          items.findIndex((el) => textOf(el).includes('INIT')),
          items.findIndex((el) => textOf(el).includes('GENERATE_HYPOTHESES')),
        ];
      });
      // Guard: both must be found in the timeline (not -1) before comparing order
      expect(initIndex).toBeGreaterThanOrEqual(0);
      expect(genIndex).toBeGreaterThanOrEqual(0);
      // INIT (index 0 in fixture) should appear before GENERATE_HYPOTHESES (index 2)
      expect(initIndex).toBeLessThan(genIndex);
    });
  });

  // ── AC-08 / AC-09 / AC-10 / AC-11: Human gate actions ────────────────

  test.describe('Human gate actions', () => {
    test('AC-08: pending gate renders approve and reject buttons', async ({ page }) => {
      await mockHarnessRunsList(page, WAITING_RUN_LIST);
      await mockHarnessRunDetail(page, WAITING_RUN.id, WAITING_RUN);
      await mockHarnessCheckpoints(page, WAITING_RUN.id, []);
      await mockHarnessGates(page, WAITING_RUN.id, [PENDING_GATE]);
      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      await workflowsPage.clickRunRow(0);
      await detailPage.assertOpen();

      await detailPage.assertGateActionsVisible();
    });

    test('AC-09: approve button calls decide endpoint with "approved"', async ({ page }) => {
      await mockHarnessRunsList(page, WAITING_RUN_LIST);
      await mockHarnessRunDetail(page, WAITING_RUN.id, WAITING_RUN);
      await mockHarnessCheckpoints(page, WAITING_RUN.id, []);
      await mockHarnessGates(page, WAITING_RUN.id, [PENDING_GATE]);
      await mockGateDecide(page, PENDING_GATE.id, { ...PENDING_GATE, status: 'approved' });

      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');
      await workflowsPage.clickRunRow(0);
      await detailPage.assertOpen();
      await detailPage.assertGateActionsVisible();

      // Arm the request interceptor before clicking so we don't miss it
      const decideRequest = page.waitForRequest(
        (req) =>
          req.url().includes(`/harness/gates/${PENDING_GATE.id}/decide`) &&
          req.method() === 'POST',
      );
      await detailPage.clickApprove();
      const req = await decideRequest;
      expect(JSON.parse(req.postData() ?? '{}')).toMatchObject({ decision: 'approved' });
    });

    test('AC-10: reject button calls decide endpoint with "rejected"', async ({ page }) => {
      await mockHarnessRunsList(page, WAITING_RUN_LIST);
      await mockHarnessRunDetail(page, WAITING_RUN.id, WAITING_RUN);
      await mockHarnessCheckpoints(page, WAITING_RUN.id, []);
      await mockHarnessGates(page, WAITING_RUN.id, [PENDING_GATE]);
      await mockGateDecide(page, PENDING_GATE.id, { ...PENDING_GATE, status: 'rejected' });

      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');
      await workflowsPage.clickRunRow(0);
      await detailPage.assertOpen();
      await detailPage.assertGateActionsVisible();

      const decideRequest = page.waitForRequest(
        (req) =>
          req.url().includes(`/harness/gates/${PENDING_GATE.id}/decide`) &&
          req.method() === 'POST',
      );
      await detailPage.clickReject();
      const req = await decideRequest;
      expect(JSON.parse(req.postData() ?? '{}')).toMatchObject({ decision: 'rejected' });
    });

    test('AC-11: approve/reject buttons are disabled while mutation is pending', async ({
      page,
    }) => {
      await mockHarnessRunsList(page, WAITING_RUN_LIST);
      await mockHarnessRunDetail(page, WAITING_RUN.id, WAITING_RUN);
      await mockHarnessCheckpoints(page, WAITING_RUN.id, []);
      await mockHarnessGates(page, WAITING_RUN.id, [PENDING_GATE]);

      // Slow decide response to catch the pending state
      await page.route(
        `**/api/v1/agents/harness/gates/${PENDING_GATE.id}/decide`,
        async (route) => {
          await new Promise((resolve) => setTimeout(resolve, 2000));
          await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ ...PENDING_GATE, status: 'approved' }),
          });
        },
      );

      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');
      await workflowsPage.clickRunRow(0);
      await detailPage.assertOpen();
      await detailPage.assertGateActionsVisible();

      // Click approve — buttons should become disabled immediately
      await detailPage.clickApprove();
      await detailPage.assertApproveDisabled();
      await detailPage.assertRejectDisabled();
    });
  });

  // ── AC-12: Terminal gate is read-only ─────────────────────────────────

  test.describe('Terminal gate', () => {
    test('AC-12: approved gate renders as read-only (no approve/reject buttons)', async ({
      page,
    }) => {
      // Use the completed run which has an approved gate
      const completedRunList = {
        items: [COMPLETED_RUN],
        total: 1,
        has_more: false,
      };
      await mockHarnessRunsList(page, completedRunList);
      await mockHarnessRunDetail(page, COMPLETED_RUN.id, COMPLETED_RUN);
      await mockHarnessCheckpoints(page, COMPLETED_RUN.id, []);
      await mockHarnessGates(page, COMPLETED_RUN.id, [APPROVED_GATE]);

      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');
      await workflowsPage.clickRunRow(0);
      await detailPage.assertOpen();

      // Approved gate status should be visible
      await expect(page.getByText(/approved/i).first()).toBeVisible({ timeout: 5000 });
      // No approve/reject action buttons
      await detailPage.assertGateActionsHidden();
    });
  });

  // ── AC-13 / AC-14: Polling behaviour ─────────────────────────────────

  test.describe('Polling behaviour', () => {
    test('AC-13: non-terminal run triggers polling within 6 s', async ({ page }) => {
      await mockHarnessRunsList(page, HARNESS_RUNS_LIST);
      await mockHarnessRunDetail(page, RUNNING_RUN.id, RUNNING_RUN);
      await mockHarnessCheckpoints(page, RUNNING_RUN.id, RUNNING_RUN_CHECKPOINTS);

      // Count how many times the runs list is fetched
      let fetchCount = 0;
      await page.route('**/api/v1/agents/harness/runs', async (route) => {
        if (route.request().method() === 'GET') {
          fetchCount++;
          await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify(HARNESS_RUNS_LIST),
          });
        } else {
          await route.continue();
        }
      });

      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      // Wait 6 s for a second fetch (poll interval is 5 s)
      await page.waitForTimeout(6000);

      // Should have fetched at least twice (initial + at least one poll)
      expect(fetchCount).toBeGreaterThanOrEqual(2);
    });

    test('AC-14: terminal run does not trigger polling after initial load', async ({ page }) => {
      const terminalList = { items: [COMPLETED_RUN], total: 1, has_more: false };

      let fetchCount = 0;
      await page.route('**/api/v1/agents/harness/runs', async (route) => {
        if (route.request().method() === 'GET') {
          fetchCount++;
          await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify(terminalList),
          });
        } else {
          await route.continue();
        }
      });

      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      // Wait 6 s — if polling is correctly disabled, only the initial fetch fires
      await page.waitForTimeout(6000);

      // Only the initial fetch should have occurred
      expect(fetchCount).toBe(1);
    });
  });

  // ── AC-15 / AC-16 / AC-17: Loading / empty / error states ────────────

  test.describe('Loading, empty, and error states', () => {
    test('AC-15: loading state renders skeleton or spinner', async ({ page }) => {
      // Delay the response to catch the loading state
      await page.route('**/api/v1/agents/harness/runs', async (route) => {
        if (route.request().method() === 'GET') {
          await new Promise((resolve) => setTimeout(resolve, 1500));
          await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify(HARNESS_RUNS_LIST),
          });
        } else {
          await route.continue();
        }
      });

      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();

      // Loading indicator should be visible before data arrives
      await expect(
        page.locator('[class*="animate-spin"], [class*="skeleton"], [class*="Skeleton"]').first(),
      ).toBeVisible({ timeout: 3000 });
    });

    test('AC-16: empty state renders "No harness runs found."', async ({ page }) => {
      await mockHarnessRunsList(page, EMPTY_HARNESS_RUNS_LIST);
      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      await expect(workflowsPage.emptyMessage).toBeVisible({ timeout: 5000 });
    });

    test('AC-17: error state renders error message', async ({ page }) => {
      // Return a 500 error from the runs endpoint
      await page.route('**/api/v1/agents/harness/runs', async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Internal server error' }),
          });
        } else {
          await route.continue();
        }
      });

      await workflowsPage.goto();
      await workflowsPage.openHarnessRunsTab();
      await page.waitForLoadState('domcontentloaded');

      await expect(workflowsPage.errorMessage).toBeVisible({ timeout: 5000 });
    });
  });
});
