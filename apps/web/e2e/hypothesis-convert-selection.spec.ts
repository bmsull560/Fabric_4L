import { journeyTest, expect, navigateAndWait } from './helpers/journey-fixture';
import { mockAccountData } from './helpers/api-harness';
import { TEST_ACCOUNTS } from './fixtures/account-helpers';

const ACCOUNT = TEST_ACCOUNTS.meridian;


journeyTest('hypothesis convert lands on selected tree/model and persists', async ({ authedPage, addMocks }) => {
  await addMocks([
    ...mockAccountData(ACCOUNT.id, {
      account: { id: ACCOUNT.id, name: ACCOUNT.name, industry: ACCOUNT.industry, tier: ACCOUNT.tier },
    }),
    {
      pattern: `**/api/v1/agents/v1/hypotheses/account/${ACCOUNT.id}**`,
      body: {
        hypotheses: [
          {
            id: 'hyp-1', account_id: ACCOUNT.id, product_id: 'prd-1', signal_id: 'sig-1',
            hypothesis_text: 'Validated hypothesis', confidence: 0.88, status: 'validated',
            evidence_ids: [], created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z'
          }
        ], total: 1
      }
    },
    {
      method: 'POST',
      pattern: '**/api/v1/agents/v1/hypotheses/*/convert',
      body: {
        hypothesis_id: 'hyp-1', account_id: ACCOUNT.id, tenant_id: 'tenant-1', evidence_ids: [],
        value_model_id: 'vm-123', tree_id: 'tree-456', status: 'converted'
      }
    }
  ]);

  await navigateAndWait(authedPage, `/intelligence/${ACCOUNT.id}/hypotheses`);
  await authedPage.getByText('Validated hypothesis').click();
  await authedPage.getByRole('button', { name: /convert to driver tree/i }).click();

  await expect(authedPage).toHaveURL(new RegExp(`/drivers/${ACCOUNT.id}/evidence\\?`));
  await navigateAndWait(authedPage, `/calculator/${ACCOUNT.id}/roi`);
  await expect(authedPage.getByText(/Selected tree: tree-456 · Selected model: vm-123/i)).toBeVisible();

  await authedPage.reload();
  await expect(authedPage.getByText(/Selected tree: tree-456 · Selected model: vm-123/i)).toBeVisible();
});
