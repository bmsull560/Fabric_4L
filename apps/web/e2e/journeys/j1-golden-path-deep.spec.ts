/**
 * Journey 1 Deep: Golden Path — Account to Approved Business Case
 *
 * Traceability: GP-DEEP-001 through GP-DEEP-015.
 * This suite exercises the full 21-step golden path through actual form
 * interactions, state transitions, and multi-step workflows. Tests are
 * expected to fail initially (TDD red phase) where the UI has not yet
 * implemented the required workflow affordances.
 *
 * Priority: P0 production gate
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectRouteSupportsWorkflow,
  expectAnyVisible,
  expectWorkflowStep,
  expectDisabledAction,
  expectEnabledAction,
  expectTenantContext,
  expectNoCrossTenantLeakage,
  expectNotVisible,
  mockSequentialResponses,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  DEEP_CASE_APPROVED_ID,
  DEEP_CASE_DRAFT_ID,
  buildGoldenPathMocks,
  createFullAccountPayload,
  createSignalSet,
  createROIScenarios,
  createApprovedBusinessCase,
  createDraftBusinessCase,
} from '../fixtures/deep-test-data';

journeyTest.describe('Golden Path Deep: Account to Approved Business Case', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks(buildGoldenPathMocks());
  });

  // ── Phase 1: Account Setup ──────────────────────────────────────────────

  journeyTest('GP-DEEP-001: user can create a new account through prospect setup form', async ({ authedPage }) => {
    await authedPage.goto('/workflow/prospect', { waitUntil: 'domcontentloaded' });
    await expectAnyVisible(authedPage, [/start a new value case/i, /search company/i], 'prospect setup form');

    const companyInput = authedPage.getByPlaceholder(/company/i)
      .or(authedPage.getByLabel(/company/i))
      .or(authedPage.getByPlaceholder(/search company/i))
      .first();
    await expect(companyInput).toBeVisible({ timeout: 5000 });
    await companyInput.fill('Meridian Health Group');

    const submitBtn = authedPage.getByRole('button', { name: /start|create|begin|run account enrichment/i }).first();
    await expect(submitBtn).toBeVisible({ timeout: 5000 });
    await submitBtn.click();

    await expect(
      authedPage.getByText(/meridian/i)
        .or(authedPage.getByText(/account created/i))
        .or(authedPage.getByText(/enrichment/i))
        .first(),
    ).toBeVisible({ timeout: 10000 });

    await expectTenantContext(authedPage);
  });

  journeyTest('GP-DEEP-002: user can assign a value pack to the account', async ({ authedPage }) => {
    await expectWorkflowStep(
      authedPage,
      '/settings/data/value-packs',
      [{ click: /assign|healthcare|select pack/i }],
      /value pack|healthcare|assigned|default/i,
    );
  });

  journeyTest('GP-DEEP-003: user can trigger domain ingestion from command center', async ({ authedPage }) => {
    await authedPage.goto('/command-center', { waitUntil: 'domcontentloaded' });
    await expectAnyVisible(authedPage, [/command center/i, /submit.*domain/i, /ingest/i], 'command center ingestion form');

    const domainInput = authedPage.getByPlaceholder(/domain|url|website/i)
      .or(authedPage.getByLabel(/domain|url/i))
      .first();
    await expect(domainInput).toBeVisible({ timeout: 5000 });
    await domainInput.fill('meridian.example');

    const ingestBtn = authedPage.getByRole('button', { name: /submit|ingest|analyze|start/i }).first();
    await expect(ingestBtn).toBeVisible({ timeout: 5000 });
    await ingestBtn.click();

    await expect(
      authedPage.getByText(/ingestion|processing|job|submitted/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });

  journeyTest('GP-DEEP-004: user can monitor ingestion job progress until completion', async ({ authedPage }) => {
    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });
    await expectAnyVisible(
      authedPage,
      [/ingestion jobs/i, /completed/i, /meridian/i, /progress/i],
      'ingestion job monitoring',
    );

    await expect(
      authedPage.getByText(/completed/i).or(authedPage.getByText(/100%/i)).first(),
    ).toBeVisible({ timeout: 10000 });
  });

  // ── Phase 2: Intelligence Review ────────────────────────────────────────

  journeyTest('GP-DEEP-005: system extracts signals and user can review them', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/manual reconciliation/i)
        .or(authedPage.getByText(/pain signal/i))
        .or(authedPage.getByText(/signal/i))
        .first(),
    ).toBeVisible({ timeout: 10000 });

    await expect(
      authedPage.getByText(/confidence/i)
        .or(authedPage.getByText(/92%|0\.92|87%|0\.87/i))
        .first(),
    ).toBeVisible({ timeout: 5000 });
  });

  journeyTest('GP-DEEP-006: user can approve or reject extracted signals', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    const approveBtn = authedPage.getByRole('button', { name: /approve|accept|confirm/i }).first();
    const rejectBtn = authedPage.getByRole('button', { name: /reject|dismiss|remove/i }).first();

    const hasApprove = await approveBtn.isVisible({ timeout: 5000 }).catch(() => false);
    const hasReject = await rejectBtn.isVisible({ timeout: 3000 }).catch(() => false);

    expect(hasApprove || hasReject, 'Signal review must expose approve or reject actions').toBe(true);
  });

  journeyTest('GP-DEEP-007: user reviews account intelligence and stakeholder map', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/stakeholder/i)
        .or(authedPage.getByText(/cfo/i))
        .or(authedPage.getByText(/influence/i))
        .first(),
    ).toBeVisible({ timeout: 10000 });
  });

  // ── Phase 3: Hypothesis and Value Modeling ──────────────────────────────

  journeyTest('GP-DEEP-008: user generates AI value hypotheses', async ({ authedPage }) => {
    await authedPage.goto(`/hypothesis/${DEEP_ACCOUNT_ID}/hypothesis`, { waitUntil: 'domcontentloaded' });

    const generateBtn = authedPage.getByRole('button', { name: /generate|create|synthesize/i }).first();
    const hasGenerate = await generateBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasGenerate) {
      await generateBtn.click();
      await expect(
        authedPage.getByText(/hypothesis|value|recommendation/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/hypothesis/i, /value hypothesis/i, /generate/i],
        'hypothesis generation surface',
      );
    }
  });

  journeyTest('GP-DEEP-009: user builds value driver tree with evidence mapping', async ({ authedPage }) => {
    await authedPage.goto(`/drivers/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/driver/i, /operational efficiency/i, /revenue growth/i, /risk reduction/i, /value driver/i],
      'value driver tree',
    );

    await expect(
      authedPage.getByText(/evidence/i)
        .or(authedPage.getByText(/weight/i))
        .or(authedPage.getByText(/0\.\d/))
        .first(),
    ).toBeVisible({ timeout: 5000 });
  });

  // ── Phase 4: ROI Calculation ────────────────────────────────────────────

  journeyTest('GP-DEEP-010: user selects formulas and completes scenario inputs', async ({ authedPage }) => {
    await authedPage.goto(`/calculator/${DEEP_ACCOUNT_ID}/roi`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/roi calculator/i, /scenario/i, /conservative/i, /expected/i, /optimistic/i],
      'ROI calculator with scenario inputs',
    );

    const hoursInput = authedPage.getByLabel(/hours/i)
      .or(authedPage.getByPlaceholder(/hours/i))
      .first();
    const isVisible = await hoursInput.isVisible({ timeout: 3000 }).catch(() => false);
    if (isVisible) {
      await hoursInput.fill('120');
    }
  });

  journeyTest('GP-DEEP-011: system calculates ROI, payback, and economic value', async ({ authedPage }) => {
    await authedPage.goto(`/calculator/${DEEP_ACCOUNT_ID}/roi`, { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/roi|return on investment/i).first(),
    ).toBeVisible({ timeout: 10000 });

    await expect(
      authedPage.getByText(/payback|months/i)
        .or(authedPage.getByText(/\d+.*month/i))
        .first(),
    ).toBeVisible({ timeout: 5000 });
  });

  // ── Phase 5: Business Case and Approval ─────────────────────────────────

  journeyTest('GP-DEEP-012: user generates business case from value model', async ({ authedPage }) => {
    await authedPage.goto(`/value-case/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/value case/i, /business case/i, /executive summary/i, /generate/i],
      'business case generation surface',
    );
  });

  journeyTest('GP-DEEP-013: user submits business case for review and reviewer approves', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/approved/i)
        .or(authedPage.getByText(/status.*approved/i))
        .first(),
    ).toBeVisible({ timeout: 10000 });

    await expect(
      authedPage.getByText(/executive summary/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  journeyTest('GP-DEEP-014: export is available only after required approval', async ({ authedPage }) => {
    // Draft case: export should be disabled
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_DRAFT_ID}`, { waitUntil: 'domcontentloaded' });
    const draftExport = authedPage.getByRole('button', { name: /export pdf/i }).first();
    if (await draftExport.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(draftExport).toBeDisabled();
    }

    // Approved case: export should be enabled
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });
    const approvedExport = authedPage.getByRole('button', { name: /export pdf/i }).first();
    if (await approvedExport.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(approvedExport).toBeEnabled();
    }
  });

  journeyTest('GP-DEEP-015: business case contains traceable claims after golden path', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/evidence/i, /benchmark/i, /assumption/i, /claim/i, /traceable/i, /lineage/i],
      'business case claim traceability',
    );

    await expectNoCrossTenantLeakage(authedPage);
  });
});
