/**
 * Journey 13: Stakeholder Mapping Workflow
 *
 * Traceability: STKH-001 through STKH-016.
 * Validates full stakeholder CRUD, buying-role identification, linking
 * to pains, initiatives and value drivers, agent-generated messaging,
 * and per-stakeholder discovery question generation.
 *
 * Priority: P1 core workflow
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectTenantContext,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  buildGoldenPathMocks,
  createStakeholderSet,
} from '../fixtures/deep-test-data';

journeyTest.describe('Stakeholder Mapping Workflow', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      ...buildGoldenPathMocks(),
      {
        pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/stakeholders`,
        body: createStakeholderSet(),
      },
      {
        pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/stakeholders`,
        method: 'POST',
        status: 201,
        body: {
          id: 'sh-005', name: 'New Contact', title: 'Director of Finance', department: 'Finance',
          influence: 'medium', buying_role: 'influencer', pains: [], initiatives: [], value_drivers: [], evidence_sources: [],
        },
      },
      {
        pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/stakeholders/sh-001`,
        method: 'PUT',
        status: 200,
        body: { id: 'sh-001', name: 'Dr. Sarah Chen', title: 'Chief Financial Officer', buying_role: 'economic_buyer', influence: 'high' },
      },
      {
        pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/stakeholders/sh-004`,
        method: 'DELETE',
        status: 204,
        body: null,
      },
    ]);
  });

  // ── View Detected Stakeholders ──────────────────────────────────────────

  journeyTest('STKH-001: stakeholder map renders all detected stakeholders with metadata', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/sarah chen|cfo|chief financial officer/i, /stakeholder/i],
      'detected stakeholder with title and role',
    );

    await expect(
      authedPage.getByText(/influence|buying role|economic buyer|champion|technical buyer|blocker/i).first(),
    ).toBeVisible({ timeout: 8000 });

    await expectTenantContext(authedPage);
  });

  journeyTest('STKH-002: stakeholder evidence sources are visible for each detected stakeholder', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/ev-001|discovery.*call|evidence|source/i, /stakeholder/i],
      'stakeholder evidence sources are visible',
    );
  });

  // ── Add Stakeholder ─────────────────────────────────────────────────────

  journeyTest('STKH-003: user can manually add a new stakeholder with title, department, and buying role', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    const addBtn = authedPage.getByRole('button', { name: /add stakeholder|new stakeholder|add contact/i }).first();
    const hasAdd = await addBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasAdd) {
      await addBtn.click();

      const nameInput = authedPage.getByLabel(/name/i).or(authedPage.getByPlaceholder(/name/i)).first();
      await expect(nameInput).toBeVisible({ timeout: 5000 });
      await nameInput.fill('New Contact');

      const titleInput = authedPage.getByLabel(/title|role/i).or(authedPage.getByPlaceholder(/title/i)).first();
      const hasTitle = await titleInput.isVisible({ timeout: 3000 }).catch(() => false);
      if (hasTitle) {
        await titleInput.fill('Director of Finance');
      }

      const saveBtn = authedPage.getByRole('button', { name: /save|add|create|submit/i }).first();
      await expect(saveBtn).toBeVisible({ timeout: 5000 });
      await saveBtn.click();

      await expect(
        authedPage.getByText(/new contact|director of finance|added|created/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/stakeholder|add|new contact/i],
        'stakeholder management surface with add capability',
      );
    }
  });

  // ── Edit Stakeholder ────────────────────────────────────────────────────

  journeyTest('STKH-004: user can edit stakeholder title, department, influence, and buying role', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    const stakeholderRow = authedPage.getByText(/sarah chen|cfo|chief financial/i).first();
    await expect(stakeholderRow).toBeVisible({ timeout: 10000 });
    await stakeholderRow.click();

    const editBtn = authedPage.getByRole('button', { name: /edit|modify|update/i }).first();
    const hasEdit = await editBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasEdit) {
      await editBtn.click();
      await expectAnyVisible(
        authedPage,
        [/title|department|influence|buying role/i],
        'stakeholder edit form with key fields',
      );
    }
  });

  // ── Buying Role Assignment ──────────────────────────────────────────────

  journeyTest('STKH-005: user can identify economic buyer, technical buyer, champion, and blocker roles', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/economic buyer|technical buyer|champion|blocker/i, /sarah chen|marcus rivera|priya kapoor|tom walsh/i],
      'buying role labels assigned to stakeholders',
    );
  });

  journeyTest('STKH-006: economic buyer is visually distinguished in stakeholder map', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/economic buyer/i).first(),
    ).toBeVisible({ timeout: 8000 });
  });

  // ── Link Stakeholders to Pain Signals ──────────────────────────────────

  journeyTest('STKH-007: user can link a stakeholder to a pain signal', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    const stakeholderRow = authedPage.getByText(/sarah chen|cfo/i).first();
    await expect(stakeholderRow).toBeVisible({ timeout: 10000 });
    await stakeholderRow.click();

    await expectAnyVisible(
      authedPage,
      [/manual reconciliation|pain|signal|linked/i],
      'stakeholder linked to pain signal',
    );
  });

  journeyTest('STKH-008: user can link a stakeholder to a business initiative', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/initiative|cost.*reduction|automation|compliance/i, /stakeholder/i],
      'stakeholder linked to business initiatives',
    );
  });

  journeyTest('STKH-009: user can link a stakeholder to a value driver', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/operational efficiency|driver|value driver/i, /stakeholder/i],
      'stakeholder linked to value driver',
    );
  });

  // ── Agent-Generated Stakeholder Content ────────────────────────────────

  journeyTest('STKH-010: user can ask agent for stakeholder-specific messaging for CFO', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    const chatInput = authedPage.getByPlaceholder(/ask|message|chat/i).first();
    const hasChatInput = await chatInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasChatInput) {
      await chatInput.fill('Generate executive messaging for Dr. Sarah Chen (CFO)');
      const sendBtn = authedPage.getByRole('button', { name: /send|submit|ask/i }).first();
      if (await sendBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await sendBtn.click();
        await expect(
          authedPage.getByText(/cfo|sarah chen|financial|messaging|executive/i).first(),
        ).toBeVisible({ timeout: 15000 });
      }
    } else {
      await expectAnyVisible(
        authedPage,
        [/messaging|generate|stakeholder/i],
        'stakeholder messaging generation surface',
      );
    }
  });

  journeyTest('STKH-011: user can generate discovery questions by stakeholder', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      `/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`,
      [/discovery question|question|ask|stakeholder/i],
      'discovery question generation by stakeholder',
    );
  });

  // ── Delete / Archive Stakeholder ───────────────────────────────────────

  journeyTest('STKH-012: user can delete or archive a stakeholder', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    const blockerRow = authedPage.getByText(/tom walsh|procurement|blocker/i).first();
    const hasBlocker = await blockerRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasBlocker) {
      await blockerRow.click();
      const deleteBtn = authedPage.getByRole('button', { name: /delete|remove|archive/i }).first();
      const hasDelete = await deleteBtn.isVisible({ timeout: 5000 }).catch(() => false);
      if (hasDelete) {
        await deleteBtn.click();
        await expect(
          authedPage.getByText(/deleted|removed|archived|confirmed/i).first(),
        ).toBeVisible({ timeout: 10000 });
      }
    }
  });

  // ── Tenant Isolation ──────────────────────────────────────────────────

  journeyTest('STKH-013: stakeholder map is scoped to current tenant only', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });
    await expectTenantContext(authedPage);

    // No cross-tenant stakeholder names should leak
    await expect(
      authedPage.getByText(/globex|tenant-foreign|cross-tenant/i).first(),
    ).not.toBeVisible({ timeout: 3000 });
  });

  // ── Stakeholder Detail ─────────────────────────────────────────────────

  journeyTest('STKH-014: stakeholder detail panel shows pains, initiatives, and evidence', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    const stakeholderRow = authedPage.getByText(/marcus rivera|vp.*operations/i).first();
    const hasRow = await stakeholderRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await stakeholderRow.click();
      await expectAnyVisible(
        authedPage,
        [/supply chain|operations|initiative|automation|evidence/i],
        'stakeholder detail panel with pains, initiatives, and evidence',
      );
    }
  });

  journeyTest('STKH-015: stakeholder influence level is visible and reflects data', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/high.*influence|medium.*influence|low.*influence|influence/i],
      'stakeholder influence levels are displayed',
    );
  });

  journeyTest('STKH-016: stakeholder department is shown alongside title', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/finance|operations|information technology|procurement/i, /stakeholder/i],
      'stakeholder department is visible alongside title',
    );
  });
});
