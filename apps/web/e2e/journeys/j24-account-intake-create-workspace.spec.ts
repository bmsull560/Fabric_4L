import { journeyTest, expect } from '../helpers/journey-fixture';

journeyTest.describe('Account intake modal create-account smoke', () => {
  journeyTest('ACCOUNT-INTAKE-001: create account navigates to intelligence workspace without refresh', async ({ authedPage, addMocks }) => {
    const createdAccountId = 'acc-intake-001';

    await addMocks([
      {
        pattern: '**/api/accounts',
        method: 'POST',
        status: 201,
        body: {
          id: createdAccountId,
          provider: 'manual',
          provider_record_id: 'manual-smoke-account',
          name: 'Smoke Account',
          stage: 'prospect',
          sync_status: 'pending',
          created_at: '2026-05-07T00:00:00Z',
          updated_at: '2026-05-07T00:00:00Z',
          source_attribution: 'Pending sync from manual',
          provider_badge: 'Manual',
          opportunities: [],
          contacts: [],
        },
      },
      {
        pattern: `**/api/workspace-cases/account/${createdAccountId}`,
        method: 'POST',
        status: 200,
        body: { case_id: 'case-smoke-001' },
      },
      {
        pattern: '**/api/workspace-cases/*/tabs/intake',
        method: 'PUT',
        status: 200,
        body: { ok: true },
      },
    ]);

    await authedPage.goto('/accounts', { waitUntil: 'domcontentloaded' });
    await authedPage.getByRole('button', { name: /new value case/i }).first().click();
    await authedPage.getByPlaceholder(/search or enter company name/i).fill('Smoke Account');
    await authedPage.getByRole('button', { name: /launch intelligence/i }).click();

    await expect(authedPage).toHaveURL(new RegExp(`/intelligence/${createdAccountId}/signals`));
    await expect(authedPage.locator('body')).toContainText(/signals|intelligence/i);
  });
});
