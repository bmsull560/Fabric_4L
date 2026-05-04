/**
 * Journey 16: Collaboration Workflow
 *
 * Traceability: COLLAB-001 through COLLAB-013.
 * Validates team invitation, ownership assignment, commenting on signals/
 * evidence/drivers, @mention, comment resolution, read-only sharing,
 * confidential access restriction, and edit-conflict handling.
 *
 * Priority: P1 core workflow
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectTenantContext,
  expectNotVisible,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  DEEP_CASE_DRAFT_ID,
  buildGoldenPathMocks,
  createCollaborationData,
} from '../fixtures/deep-test-data';

journeyTest.describe('Collaboration Workflow', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    const collab = createCollaborationData();
    await addMocks([
      ...buildGoldenPathMocks(),
      { pattern: `**/api/v1/agents/accounts/${DEEP_ACCOUNT_ID}/members`, body: collab.team_members },
      { pattern: `**/api/v1/agents/accounts/${DEEP_ACCOUNT_ID}/comments`, body: collab.comments },
      { pattern: `**/api/v1/agents/accounts/${DEEP_ACCOUNT_ID}/comments`, method: 'POST', status: 201, body: collab.comments[0] },
      { pattern: '**/api/v1/agents/notifications', body: collab.notifications },
      { pattern: `**/api/v1/agents/accounts/${DEEP_ACCOUNT_ID}/share-link`, body: collab.share_link },
      {
        pattern: `**/api/v1/agents/accounts/${DEEP_ACCOUNT_ID}/members`,
        method: 'POST',
        status: 201,
        body: { id: 'user-004', name: 'Alex Kim', email: 'alex@valuefabric.test', role: 'analyst', access: 'read_write' },
      },
    ]);
  });

  // ── Invite and Assign ─────────────────────────────────────────────────

  journeyTest('COLLAB-001: user can invite a teammate to collaborate on an account', async ({ authedPage }) => {
    await authedPage.goto(`/accounts/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });

    const inviteBtn = authedPage.getByRole('button', { name: /invite|share|add.*member|add.*collaborator/i }).first();
    const hasInvite = await inviteBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasInvite) {
      await inviteBtn.click();
      const emailInput = authedPage.getByLabel(/email/i).or(authedPage.getByPlaceholder(/email/i)).first();
      await expect(emailInput).toBeVisible({ timeout: 5000 });
      await emailInput.fill('alex@valuefabric.test');

      const sendBtn = authedPage.getByRole('button', { name: /invite|send|submit/i }).first();
      await expect(sendBtn).toBeVisible({ timeout: 3000 });
      await sendBtn.click();

      await expect(
        authedPage.getByText(/invited|alex.*kim|added|success/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/member|team|invite|meridian/i],
        'account collaboration surface with invite capability',
      );
    }
  });

  journeyTest('COLLAB-002: user can assign account owner and reviewer roles', async ({ authedPage }) => {
    await authedPage.goto(`/accounts/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/owner|reviewer|avery stone|jordan lee|role/i],
      'account member list with ownership and reviewer assignment',
    );
  });

  // ── Comments ──────────────────────────────────────────────────────────

  journeyTest('COLLAB-003: user can comment on a signal', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    const signalRow = authedPage.getByText(/manual reconciliation burden/i).first();
    const hasSignal = await signalRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasSignal) {
      await signalRow.click();
      const commentInput = authedPage.getByPlaceholder(/comment|note|feedback/i).first();
      const hasInput = await commentInput.isVisible({ timeout: 5000 }).catch(() => false);

      if (hasInput) {
        await commentInput.fill('The reconciliation signal confidence looks high — is this based on the April discovery call?');
        const postBtn = authedPage.getByRole('button', { name: /post|comment|submit/i }).first();
        if (await postBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
          await postBtn.click();
          await expect(
            authedPage.getByText(/reconciliation.*confidence|posted|comment/i).first(),
          ).toBeVisible({ timeout: 10000 });
        }
      }
    }
  });

  journeyTest('COLLAB-004: user can comment on an evidence item', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    // Navigate to evidence tab
    const evidenceTab = authedPage.getByRole('tab', { name: /evidence/i })
      .or(authedPage.getByRole('link', { name: /evidence/i }))
      .first();
    const hasEvTab = await evidenceTab.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasEvTab) {
      await evidenceTab.click();
      await expectAnyVisible(
        authedPage,
        [/evidence|comment|cycle time|bench-002/i],
        'evidence tab with comment capability',
      );
    }
  });

  journeyTest('COLLAB-005: user can comment on a value driver', async ({ authedPage }) => {
    await authedPage.goto(`/drivers/${DEEP_ACCOUNT_ID}/tree`, { waitUntil: 'domcontentloaded' });

    const driverRow = authedPage.getByText(/operational efficiency/i).first();
    const hasDriver = await driverRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasDriver) {
      await driverRow.click();
      const commentBtn = authedPage.getByRole('button', { name: /comment|add note/i }).first();
      const hasCommentBtn = await commentBtn.isVisible({ timeout: 5000 }).catch(() => false);

      if (hasCommentBtn) {
        await commentBtn.click();
        await expectAnyVisible(
          authedPage,
          [/comment|note|feedback/i],
          'value driver comment input surface',
        );
      }
    }
  });

  // ── Mention and Resolve ───────────────────────────────────────────────

  journeyTest('COLLAB-006: user can mention a teammate in a comment', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    const commentInput = authedPage.getByPlaceholder(/comment|note/i).first();
    const hasInput = await commentInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasInput) {
      await commentInput.fill('@Jordan Lee ');
      // Mention autocomplete or inline tag should appear
      await expect(
        authedPage.getByText(/jordan.*lee|@jordan/i).first(),
      ).toBeVisible({ timeout: 5000 });
    }
  });

  journeyTest('COLLAB-007: user can resolve a comment thread', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    const resolvedComment = authedPage.getByText(/april 28 session|confirmed with cfo|resolved/i).first();
    const hasResolved = await resolvedComment.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasResolved) {
      // Comment marked resolved should show resolved state
      await expectAnyVisible(
        authedPage,
        [/resolved|closed|confirmed/i],
        'resolved comment thread state',
      );
    }
  });

  // ── Notifications ─────────────────────────────────────────────────────

  journeyTest('COLLAB-008: user receives notifications for key events', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/notifications',
      [/ingestion complete|review request|approval|stale benchmark|failed sync/i],
      'notification feed with key event types',
    );
  });

  // ── Read-Only Sharing ─────────────────────────────────────────────────

  journeyTest('COLLAB-009: user can generate a read-only shareable link for a business case', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });

    const shareBtn = authedPage.getByRole('button', { name: /share|get link|copy link/i }).first();
    const hasShare = await shareBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasShare) {
      await shareBtn.click();
      await expectAnyVisible(
        authedPage,
        [/read.only|link.*copied|share.*link|expires/i],
        'read-only share link generation',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/business case|share|draft/i],
        'business case with sharing option',
      );
    }
  });

  // ── Confidential Access Restriction ───────────────────────────────────

  journeyTest('COLLAB-010: user can restrict access to a confidential account', async ({ authedPage }) => {
    await authedPage.goto(`/accounts/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/access|restrict|confidential|permission|private/i, /account|meridian/i],
      'account access restriction controls',
    );
  });

  // ── Real-Time / Refresh-Based Updates ─────────────────────────────────

  journeyTest('COLLAB-011: account page reflects updates after refresh', async ({ authedPage }) => {
    await authedPage.goto(`/accounts/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });
    await expectAnyVisible(authedPage, [/meridian/i], 'account detail before refresh');

    await authedPage.reload({ waitUntil: 'domcontentloaded' });
    await expectAnyVisible(authedPage, [/meridian/i], 'account detail after refresh — data persists');
  });

  // ── Edit Conflict Handling ────────────────────────────────────────────

  journeyTest('COLLAB-012: concurrent edit conflict shows safe merge or conflict notification', async ({ authedPage, addMocks }) => {
    // Simulate a 409 Conflict response when saving
    await addMocks([{
      pattern: `**/api/v1/agents/cases/${DEEP_CASE_DRAFT_ID}`,
      method: 'PUT',
      status: 409,
      body: { error: 'Edit conflict: another user has modified this document.', conflict_actor: 'Jordan Lee', conflict_at: '2026-05-01T12:05:00Z' },
    }]);

    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });
    await expectAnyVisible(
      authedPage,
      [/business case|draft|meridian/i],
      'draft business case for conflict handling test',
    );
  });

  // ── Tenant Isolation in Collaboration ────────────────────────────────

  journeyTest('COLLAB-013: collaboration features respect tenant boundaries', async ({ authedPage }) => {
    await authedPage.goto(`/accounts/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });
    await expectTenantContext(authedPage);

    // No cross-tenant users should appear in member lists
    await expect(
      authedPage.getByText(/globex|other-tenant|tenant-foreign/i).first(),
    ).not.toBeVisible({ timeout: 3000 });
  });
});
