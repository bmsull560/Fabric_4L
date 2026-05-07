import { journeyTest, expect } from '../helpers/journey-fixture';
import { expectRouteSupportsWorkflow } from '../helpers/validation-program';
import { SYNTHETIC_TENANT } from '../fixtures/synthetic-tenant-data';

journeyTest.describe('Journey 24: Account → Signals → Evidence → Driver → Calculator → Business Case', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      {
        pattern: `**/api/v1/accounts/${SYNTHETIC_TENANT.accountId}/signals**`,
        body: { signals: SYNTHETIC_TENANT.signals },
      },
      {
        pattern: `**/api/v1/agents/workspace/${SYNTHETIC_TENANT.accountId}/evidence**`,
        body: { evidence: SYNTHETIC_TENANT.evidence },
      },
      {
        pattern: `**/api/v1/drivers/${SYNTHETIC_TENANT.accountId}**`,
        body: { drivers: [SYNTHETIC_TENANT.driver] },
      },
      {
        pattern: `**/api/v1/calculator/${SYNTHETIC_TENANT.accountId}/roi**`,
        body: SYNTHETIC_TENANT.calculator,
      },
      {
        pattern: `**/api/v1/business-case/${SYNTHETIC_TENANT.accountId}**`,
        body: SYNTHETIC_TENANT.businessCase,
      },
    ]);
  });

  journeyTest('validates the key clickpath in deterministic CI data mode', async ({ authedPage }) => {
    const accountId = SYNTHETIC_TENANT.accountId;

    await expectRouteSupportsWorkflow(authedPage, `/accounts/${accountId}`, [/account/i, /prospect|workspace|lifecycle/i], 'account workspace');
    await expectRouteSupportsWorkflow(authedPage, `/intelligence/${accountId}/signals`, [/signal/i, /confidence|priority|insight/i], 'signals');
    await expectRouteSupportsWorkflow(authedPage, `/drivers/${accountId}/evidence`, [/evidence/i, /driver/i, /source|confidence/i], 'driver evidence');
    await expectRouteSupportsWorkflow(authedPage, `/drivers/${accountId}`, [/driver/i, /value|benchmark|impact/i], 'driver summary');
    await expectRouteSupportsWorkflow(authedPage, `/calculator/${accountId}/roi`, [/roi calculator|scenario|payback/i], 'calculator');
    await expectRouteSupportsWorkflow(authedPage, `/value-case/${accountId}`, [/business case|value case|executive summary/i], 'business case');

    await expect(authedPage.getByText(/business case|value case/i).first()).toBeVisible({ timeout: 10000 });
  });
});
