import { journeyTest, expect, navigateAndWait } from './helpers/journey-fixture';

const ACCOUNT_ID = 'acc-signal-review';
const CASE_ID = 'case-signal-review';

journeyTest('signal review persists after reload and triggers downstream refetches', async ({ authedPage }) => {
  let reviewStatus: 'unreviewed' | 'approved' | 'rejected' = 'unreviewed';
  let reviewedBy: string | undefined;
  let reviewedAt: string | undefined;
  let hypothesisFetches = 0;

  await authedPage.route('**/api/v1/agents/v1/analysis/cases/canonical?account_id=*', async (route) => {
    await route.fulfill({ json: { case_id: CASE_ID } });
  });

  await authedPage.route(`**/api/v1/agents/v1/analysis/cases/${CASE_ID}/workspace/signals`, async (route) => {
    await route.fulfill({ json: { signals: [{ id: 'sig-1', name: 'Signal 1', category: 'Cost', confidence: 82, impact: 'High', review_status: reviewStatus, reviewed_by: reviewedBy, reviewed_at: reviewedAt }] } });
  });

  await authedPage.route('**/api/v1/agents/v1/hypotheses/**', async (route) => {
    hypothesisFetches += 1;
    await route.fulfill({ json: { hypotheses: [], total: 0 } });
  });

  await authedPage.route('**/api/v1/agents/v1/signals/sig-1/review', async (route) => {
    const body = route.request().postDataJSON() as { review_status: 'approved' | 'rejected' };
    reviewStatus = body.review_status;
    reviewedBy = 'reviewer-123';
    reviewedAt = '2026-05-07T12:00:00Z';
    await route.fulfill({ json: { signal_id: 'sig-1', account_id: ACCOUNT_ID, review_status: reviewStatus, reviewed_by: reviewedBy, reviewed_at: reviewedAt } });
  });

  await navigateAndWait(authedPage, `/intelligence/${ACCOUNT_ID}/signals`);
  await authedPage.getByText('Signal 1').click();
  await authedPage.getByRole('button', { name: /approve/i }).click();

  await expect(authedPage.getByText(/Review: approved by reviewer-123/i)).toBeVisible();

  await authedPage.reload();
  await authedPage.getByText('Signal 1').click();
  await expect(authedPage.getByText(/Review: approved by reviewer-123/i)).toBeVisible();
  expect(hypothesisFetches).toBeGreaterThan(0);
});
