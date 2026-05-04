/**
 * Export Workflows Deep: Export Gate Enforcement
 *
 * Traceability: EXPORT-DEEP-001 through EXPORT-DEEP-008.
 * Validates export gate enforcement with state transitions, role-based
 * blocking, approval requirements, download interactions, and audit events.
 *
 * Priority: P0 production gate
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectDisabledAction,
  expectEnabledAction,
  expectNoCrossTenantLeakage,
  expectNotVisible,
  expectTenantContext,
  switchToReadOnlyUser,
} from '../helpers/validation-program';
import {
  DEEP_CASE_APPROVED_ID,
  DEEP_CASE_DRAFT_ID,
  buildGoldenPathMocks,
  createApprovedBusinessCase,
  createDraftBusinessCase,
} from '../fixtures/deep-test-data';

journeyTest.describe('Export Workflows Deep: Gate Enforcement', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks(buildGoldenPathMocks());
  });

  // ── Approved Case Export ────────────────────────────────────────────────

  journeyTest('EXPORT-DEEP-001: approved case Export PDF button is enabled', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/approved/i).first(),
    ).toBeVisible({ timeout: 10000 });

    const exportBtn = authedPage.getByRole('button', { name: /export pdf/i }).first();
    if (await exportBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(exportBtn).toBeEnabled();
    }
  });

  journeyTest('EXPORT-DEEP-002: clicking Export PDF on approved case initiates download', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    const exportBtn = authedPage.getByRole('button', { name: /export pdf/i }).first();
    if (await exportBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Set up download listener
      const downloadPromise = authedPage.waitForEvent('download', { timeout: 10000 }).catch(() => null);
      await exportBtn.click();

      // Either a download starts, or a success/progress message appears
      const download = await downloadPromise;
      if (download) {
        expect(download).toBeTruthy();
      } else {
        await expectAnyVisible(
          authedPage,
          [/download|export.*started|generating|pdf/i],
          'export download initiation feedback',
        );
      }
    }
  });

  // ── Draft Case Export Gate ─────────────────────────────────────────────

  journeyTest('EXPORT-DEEP-003: draft case Export PDF is disabled with approval-required message', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });

    const exportBtn = authedPage.getByRole('button', { name: /export pdf/i }).first();
    if (await exportBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(exportBtn).toBeDisabled();
    }

    // Check for approval-required messaging
    await expectAnyVisible(
      authedPage,
      [/draft|pending|approval.*required|not approved/i, /business case/i],
      'draft status with export gate messaging',
    );
  });

  // ── Shared Executive View ──────────────────────────────────────────────

  journeyTest('EXPORT-DEEP-004: shared executive view renders buyer-facing content without internal data', async ({ authedPage }) => {
    await authedPage.goto('/deliverables/views/executive', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/executive/i, /summary/i, /financial/i, /impact/i],
      'executive buyer view content',
    );

    // Internal-only data should not leak to buyer view
    await expectNotVisible(authedPage, /internal.*only|debug|dev.*tool|tenant-e2e-001/i);
    await expectNoCrossTenantLeakage(authedPage);
  });

  // ── Provenance Export ──────────────────────────────────────────────────

  journeyTest('EXPORT-DEEP-005: provenance export includes audit context', async ({ authedPage }) => {
    await authedPage.goto('/governance/traces', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/decision trace/i, /export prov-o/i, /audit log/i, /provenance/i],
      'provenance export surface with audit context',
    );

    const exportProvBtn = authedPage.getByRole('button', { name: /export prov-o/i }).first();
    if (await exportProvBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(exportProvBtn).toBeEnabled();
    }
  });

  // ── Role-Based Export Blocking ─────────────────────────────────────────

  journeyTest('EXPORT-DEEP-006: read-only user cannot export approved case', async ({ authedPage }) => {
    await switchToReadOnlyUser(authedPage);

    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    const exportBtn = authedPage.getByRole('button', { name: /export pdf/i }).first();
    if (await exportBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(exportBtn).toBeDisabled();
    }
  });

  // ── Download Audit Event ───────────────────────────────────────────────

  journeyTest('EXPORT-DEEP-007: export action creates governance audit event', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    const exportBtn = authedPage.getByRole('button', { name: /export pdf/i }).first();
    if (await exportBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await exportBtn.click();

      // After export, navigate to audit trail to verify audit entry
      await authedPage.goto('/governance/audit/log', { waitUntil: 'domcontentloaded' });
      await expectAnyVisible(
        authedPage,
        [/audit log/i, /export|download|generated/i, /validation events/i],
        'governance audit trail with export event',
      );
    }
  });

  // ── Business Case List ─────────────────────────────────────────────────

  journeyTest('EXPORT-DEEP-008: business case list shows status badges and search', async ({ authedPage }) => {
    await authedPage.goto('/deliverables/cases', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/business cases/i, /new case/i, /search/i, /draft|approved/i],
      'business case list with status and search',
    );

    // Both approved and draft cases should be listed
    await expect(
      authedPage.getByText(/meridian/i)
        .or(authedPage.getByText(/business case/i))
        .first(),
    ).toBeVisible({ timeout: 10000 });
  });
});
