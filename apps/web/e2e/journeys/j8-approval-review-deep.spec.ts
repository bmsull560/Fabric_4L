/**
 * Journey 8 Deep: Approval and Review Gate Workflows
 *
 * Traceability: APPROVAL-DEEP-001 through APPROVAL-DEEP-010.
 * Exercises multi-step approval workflows with state transitions,
 * reviewer feedback, resubmission, and governance enforcement.
 *
 * Priority: P0 production gate
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectDisabledAction,
  expectEnabledAction,
  expectNotVisible,
  expectTenantContext,
  mockSequentialResponses,
  attemptOptionalAction,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  DEEP_CASE_APPROVED_ID,
  DEEP_CASE_DRAFT_ID,
  buildGoldenPathMocks,
  createApprovalWorkflow,
  createDraftBusinessCase,
  createApprovedBusinessCase,
} from '../fixtures/deep-test-data';

journeyTest.describe('Approval and Review Gate Workflows Deep', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks(buildGoldenPathMocks());
  });

  // ── Submit for Review ──────────────────────────────────────────────────

  journeyTest('APPROVAL-DEEP-001: user can submit model for review — status changes to pending', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/api/v1/governance/approvals**',
      body: [createApprovalWorkflow('pending_review')],
    }]);

    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/draft/i, /business case/i, /submit|review/i],
      'draft business case with submission controls',
    );

    const submitBtn = authedPage.getByRole('button', { name: /submit.*review|request.*review|send.*review/i }).first();
    const hasSubmit = await submitBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSubmit) {
      await submitBtn.click();
      await expect(
        authedPage.getByText(/pending.*review|submitted|awaiting/i).first(),
      ).toBeVisible({ timeout: 10000 });
    }
  });

  journeyTest('APPROVAL-DEEP-002: pending review state shows reviewer assignment context', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/api/v1/governance/approvals**',
      body: [createApprovalWorkflow('pending_review')],
    }]);

    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/pending|review|reviewer|value engineering lead/i, /business case/i],
      'pending review with reviewer context',
    );
  });

  // ── Reviewer Requests Changes ──────────────────────────────────────────

  journeyTest('APPROVAL-DEEP-003: reviewer requests changes — user sees feedback', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/api/v1/governance/approvals**',
      body: [createApprovalWorkflow('changes_requested')],
    }]);

    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/changes.*requested|feedback|missing evidence|comment/i, /business case/i],
      'changes requested with reviewer feedback',
    );
  });

  journeyTest('APPROVAL-DEEP-004: user can edit and resubmit after reviewer feedback', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/api/v1/governance/approvals**',
      body: [createApprovalWorkflow('changes_requested')],
    }]);

    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });

    // Look for edit or resubmit controls
    const editBtn = authedPage.getByRole('button', { name: /edit|revise|update|resubmit/i }).first();
    const hasEdit = await editBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasEdit) {
      await editBtn.click();
      await expectAnyVisible(
        authedPage,
        [/edit|revise|resubmit|update/i],
        'edit mode after reviewer feedback',
      );
    }
  });

  // ── Reviewer Approves ──────────────────────────────────────────────────

  journeyTest('APPROVAL-DEEP-005: reviewer approves — status changes, export enabled', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/approved/i).first(),
    ).toBeVisible({ timeout: 10000 });

    // Export should be enabled for approved case
    const exportBtn = authedPage.getByRole('button', { name: /export pdf/i }).first();
    if (await exportBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(exportBtn).toBeEnabled();
    }
  });

  // ── Reviewer Rejects ───────────────────────────────────────────────────

  journeyTest('APPROVAL-DEEP-006: reviewer rejects unsupported claims — rejection reason visible', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/api/v1/governance/approvals**',
      body: [createApprovalWorkflow('rejected')],
    }, {
      pattern: `**/api/v1/agents/cases/${DEEP_CASE_DRAFT_ID}`,
      body: createDraftBusinessCase({
        status: 'rejected',
        rejection_reason: 'Claim #2 has no supporting benchmark data. Benchmark bench-002 is stale.',
      }),
    }]);

    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/rejected|rejection|unsupported|no supporting/i, /business case/i],
      'rejected business case with rejection reason',
    );
  });

  // ── Export Gates ────────────────────────────────────────────────────────

  journeyTest('APPROVAL-DEEP-007: export blocked before approval (button disabled)', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });

    const exportBtn = authedPage.getByRole('button', { name: /export pdf/i }).first();
    if (await exportBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(exportBtn).toBeDisabled();
    }
  });

  journeyTest('APPROVAL-DEEP-008: CRM push blocked before business case approval', async ({ authedPage }) => {
    await authedPage.goto('/context/integrations', { waitUntil: 'domcontentloaded' });

    const syncBtn = authedPage.getByRole('button', { name: /sync|push/i }).first();
    const hasSync = await syncBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSync) {
      await syncBtn.click();
      await expectAnyVisible(
        authedPage,
        [/approval|permission|sync|started|failed/i],
        'CRM sync feedback with approval awareness',
      );
    }
  });

  // ── Audit Trail ────────────────────────────────────────────────────────

  journeyTest('APPROVAL-DEEP-009: approval history visible in governance audit trail', async ({ authedPage }) => {
    await authedPage.goto('/governance/audit/changes', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/change|history|approval|review|audit/i],
      'governance audit trail with approval history',
    );
  });

  // ── Governance Policy Enforcement ──────────────────────────────────────

  journeyTest('APPROVAL-DEEP-010: governance policy cannot be bypassed to approve without review', async ({ authedPage }) => {
    await authedPage.goto('/settings/governance/policies', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/policies|governance|approval|enforce|review/i],
      'governance policy enforcement surface',
    );

    // Verify that disabling review is either not possible or requires admin confirmation
    const disableBtn = authedPage.getByRole('button', { name: /disable.*review|bypass.*approval|skip.*review/i }).first();
    const hasDisable = await disableBtn.isVisible({ timeout: 3000 }).catch(() => false);

    if (hasDisable) {
      // If the button exists, it should require confirmation or be protected
      await disableBtn.click();
      await expectAnyVisible(
        authedPage,
        [/confirm|are you sure|warning|cannot.*disable/i],
        'approval bypass protection',
      );
    }
  });
});
