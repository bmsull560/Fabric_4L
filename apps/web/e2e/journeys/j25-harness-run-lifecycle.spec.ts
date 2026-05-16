/**
 * Journey 25: Harness Run Lifecycle — Backend-Integrated Smoke
 *
 * Traceability: HARNESS-SMOKE-001, HARNESS-SMOKE-002, HARNESS-SMOKE-003.
 *
 * Thin smoke paths that verify the real /v1/harness/* API contract still
 * matches the frontend client. All tests are tagged @backend and are
 * skipped unless PLAYWRIGHT_BACKEND_URL is set.
 *
 * Covers (AC-18):
 *   HARNESS-SMOKE-001  List harness runs from real backend
 *   HARNESS-SMOKE-002  Open one run detail from real backend
 *   HARNESS-SMOKE-003  Harness Runs tab is visible on /context/agents
 *
 * These tests are intentionally thin — they verify the API contract and
 * basic rendering, not the full interaction model (covered by the mocked
 * contract spec in e2e/contracts/harness-runs.spec.ts).
 *
 * TDD Status: FAILING until backend /v1/harness/* routes are registered
 * and the frontend HarnessRuns tab is implemented.
 *
 * TODO(j25): Once /v1/harness/* endpoints are merged and included in
 * backend-integrated CI, replace journeyTest.skip(!isLiveMode(), ...) with
 * requireBackendOrThrow() to match the hard-fail posture of j11/j16/j19.
 * Trigger: Harness backend API merged + present in integration-tests.yml.
 */
import { journeyTest, expect, isLiveMode } from '../helpers/journey-fixture';
import { AgentWorkflowsPage } from '../pages/AgentWorkflowsPage';
import { HarnessRunDetailPage } from '../pages/HarnessRunDetailPage';

journeyTest.describe('Journey 25: Harness Run Lifecycle @backend', () => {
  let workflowsPage: AgentWorkflowsPage;
  let detailPage: HarnessRunDetailPage;

  journeyTest.beforeEach(async ({ authedPage }) => {
    workflowsPage = new AgentWorkflowsPage(authedPage);
    detailPage = new HarnessRunDetailPage(authedPage);
  });

  // ── HARNESS-SMOKE-001: List runs from real backend ────────────────────

  journeyTest(
    'HARNESS-SMOKE-001: Harness Runs tab renders runs from real backend @backend',
    async ({ authedPage }) => {
      journeyTest.skip(!isLiveMode(), 'requires PLAYWRIGHT_BACKEND_URL');

      await workflowsPage.goto();
      await authedPage.waitForLoadState('domcontentloaded');

      // Tab must be present
      await expect(workflowsPage.harnessRunsTab).toBeVisible({ timeout: 10000 });

      await workflowsPage.openHarnessRunsTab();

      // Either runs are listed or the empty state is shown — both are valid
      // depending on backend seed data. What must NOT happen is an error state.
      await expect(workflowsPage.errorMessage).not.toBeVisible({ timeout: 5000 });

      // The section itself must render
      const hasRuns = await workflowsPage.harnessRunRows.count().then((n) => n > 0);
      const hasEmpty = await workflowsPage.emptyMessage.isVisible().catch(() => false);

      expect(hasRuns || hasEmpty).toBe(true);
    },
  );

  // ── HARNESS-SMOKE-002: Open run detail from real backend ──────────────

  journeyTest(
    'HARNESS-SMOKE-002: selecting a run opens HarnessRunDetail from real backend @backend',
    async ({ authedPage }) => {
      journeyTest.skip(!isLiveMode(), 'requires PLAYWRIGHT_BACKEND_URL');

      await workflowsPage.goto();
      await authedPage.waitForLoadState('domcontentloaded');
      await workflowsPage.openHarnessRunsTab();

      // Only proceed if there are runs to click
      const runCount = await workflowsPage.harnessRunRows.count();
      journeyTest.skip(runCount === 0, 'no harness runs in backend seed data — skipping detail test');

      await workflowsPage.clickRunRow(0);

      // Detail panel must open
      await detailPage.assertOpen();

      // No error state in the panel
      await expect(detailPage.errorMessage).not.toBeVisible({ timeout: 5000 });
    },
  );

  // ── HARNESS-SMOKE-003: Tab visible on /context/agents ─────────────────

  journeyTest(
    'HARNESS-SMOKE-003: Harness Runs tab is visible on /context/agents @backend',
    async ({ authedPage }) => {
      journeyTest.skip(!isLiveMode(), 'requires PLAYWRIGHT_BACKEND_URL');

      await authedPage.goto('/context/agents', { waitUntil: 'domcontentloaded' });

      await expect(workflowsPage.harnessRunsTab).toBeVisible({ timeout: 10000 });
    },
  );
});
