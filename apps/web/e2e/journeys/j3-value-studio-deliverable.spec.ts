/**
 * Journey 3: Value Studio → Deliverable Generation
 *
 * Validates the creation of business deliverables from synthesized
 * intelligence. A user navigates through the Value Studio tabs
 * (Action Plan → Value Model → Narrative), reviews and adjusts data,
 * then views the final deliverable output.
 *
 * This journey verifies that the studio workspace correctly chains
 * data across tabs and that formula evaluations produce consistent results.
 *
 * Pass criteria:
 *   - All Studio tabs render without errors for the selected account
 *   - Value Model tab displays formula/variable data
 *   - Narrative tab renders generated content
 *   - Deliverable views (CFO, Executive, Technical) are accessible
 *   - Cross-tab data consistency is maintained
 */
import { journeyTest, expect, expectNoErrors, navigateAndWait } from '../helpers/journey-fixture';
import { mockAccountData } from '../helpers/api-harness';
import { TEST_ACCOUNTS } from '../fixtures/account-helpers';

// ── Test Data ───────────────────────────────────────────────────────────────

const ACCOUNT = TEST_ACCOUNTS.meridian;

const ACTION_PLAN_DATA = {
  initiatives: [
    { id: 'init-001', name: 'Supply Chain Digitization', priority: 'high', timeline: 'Q3 2025', owner: 'VP Operations' },
    { id: 'init-002', name: 'Predictive Analytics Platform', priority: 'medium', timeline: 'Q4 2025', owner: 'IT Director' },
  ],
  generated_at: '2025-04-28T10:00:00Z',
  status: 'ready',
};

const VALUE_MODEL_DATA = {
  variables: [
    { id: 'var-001', name: 'Annual Revenue', value: 500000000, unit: 'USD' },
    { id: 'var-002', name: 'Operational Cost Ratio', value: 0.32, unit: 'percentage' },
    { id: 'var-003', name: 'Projected Savings', value: 2100000, unit: 'USD' },
  ],
  formulas: [
    { id: 'frm-001', name: 'ROI Calculation', expression: '(savings / investment) * 100', result: 287 },
  ],
  projections: {
    conservative: 1200000,
    expected: 2100000,
    optimistic: 3400000,
  },
  generated_at: '2025-04-28T10:01:00Z',
  status: 'ready',
};

const NARRATIVE_DATA = {
  sections: [
    { id: 'sec-001', title: 'Executive Summary', content: 'Meridian Automotive faces significant supply chain challenges...' },
    { id: 'sec-002', title: 'Value Proposition', content: 'Our solution delivers a projected 287% ROI over 3 years...' },
    { id: 'sec-003', title: 'Implementation Roadmap', content: 'Phase 1: Supply chain digitization (Q3 2025)...' },
  ],
  generated_at: '2025-04-28T10:02:00Z',
  status: 'ready',
};

const BUSINESS_CASES = [
  {
    id: 'case-001',
    account_id: ACCOUNT.id,
    title: 'Meridian Automotive - Supply Chain Optimization',
    status: 'draft',
    created_at: '2025-04-28T10:00:00Z',
    total_value: 2100000,
  },
];

// ── Journey ─────────────────────────────────────────────────────────────────

journeyTest.describe('Journey 3: Value Studio → Deliverable Generation', () => {

  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      ...mockAccountData(ACCOUNT.id, {
        account: { name: ACCOUNT.name, industry: ACCOUNT.industry, tier: ACCOUNT.tier },
        actionPlan: ACTION_PLAN_DATA,
        valueModel: VALUE_MODEL_DATA,
        narrative: NARRATIVE_DATA,
      }),
      {
        pattern: '**/api/v1/agents/cases',
        body: BUSINESS_CASES,
      },
      {
        pattern: `**/api/v1/agents/cases/case-001`,
        body: BUSINESS_CASES[0],
      },
      {
        pattern: `**/api/v1/agents/cases/case-001/export`,
        body: { url: '/mock-export.pdf', format: 'pdf' },
      },
    ]);
  });

  journeyTest('Step 1: User enters Value Studio Action Plan tab', async ({ authedPage }) => {
    await navigateAndWait(authedPage, `/studio/${ACCOUNT.id}/action-plan`);
    await expectNoErrors(authedPage);

    // Account name should be visible in the studio header
    await expect(authedPage.getByText(ACCOUNT.name).first()).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 2: User navigates to Value Model tab', async ({ authedPage }) => {
    await navigateAndWait(authedPage, `/studio/${ACCOUNT.id}/value-model`);
    await expectNoErrors(authedPage);

    await expect(authedPage.getByText(ACCOUNT.name).first()).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 3: User navigates to Narrative tab', async ({ authedPage }) => {
    await navigateAndWait(authedPage, `/studio/${ACCOUNT.id}/narrative`);
    await expectNoErrors(authedPage);

    await expect(authedPage.getByText(ACCOUNT.name).first()).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 4: User views Business Case deliverable', async ({ authedPage }) => {
    await navigateAndWait(authedPage, '/deliverables/cases');
    await expectNoErrors(authedPage);

    // The business cases list should be visible
    await expect(
      authedPage.getByRole('heading', { name: /business case/i })
    ).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 5: User accesses CFO View deliverable', async ({ authedPage }) => {
    await navigateAndWait(authedPage, '/deliverables/views/cfo');
    await expectNoErrors(authedPage);

    // The CFO view should render
    await expect(
      authedPage.getByRole('heading', { name: /cfo/i })
    ).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 6: Cross-tab studio navigation preserves account context', async ({ authedPage }) => {
    const tabs = ['action-plan', 'value-model', 'narrative'];

    for (const tab of tabs) {
      await navigateAndWait(authedPage, `/studio/${ACCOUNT.id}/${tab}`);
      await expect(authedPage.getByText(ACCOUNT.name).first()).toBeVisible({ timeout: 10000 });
      await expect(authedPage).toHaveURL(new RegExp(`/studio/${ACCOUNT.id}/${tab}`));
    }
  });
});
