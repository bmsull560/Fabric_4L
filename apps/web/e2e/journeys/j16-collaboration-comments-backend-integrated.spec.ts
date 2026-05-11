/**
 * Journey 16 Collaboration Comments Backend-Integrated
 *
 * Proves comment create/reload uses the live Layer 4 comments API, not static mocks.
 *
 * Tag: @backend
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import { expectNoErrors } from '../helpers/journey-fixture';
import { requireBackendOrThrow } from '../helpers/validation-program';

journeyTest.describe('@backend Collaboration Comments Backend-Integrated', () => {
  journeyTest.setTimeout(90000);

  journeyTest.beforeEach(async () => {
    requireBackendOrThrow('collaboration comment persistence workflow');
  });

  journeyTest('J16-COMMENTS-PERSISTENCE: comment create and reload visibility persists', async ({ authedPage }) => {
    const subjectId = `case-${Date.now()}`;
    const body = `Persisted collaboration comment ${Date.now()}`;

    await authedPage.goto('/collaboration/comments', { waitUntil: 'domcontentloaded' });
    await expectNoErrors(authedPage);

    await authedPage.getByLabel(/subject type/i).fill('business_case');
    await authedPage.getByLabel(/subject id/i).fill(subjectId);
    await authedPage.getByLabel(/^comment$/i).fill(body);
    await authedPage.getByRole('button', { name: /^post comment$/i }).click();

    await expect(authedPage.getByText(body).first()).toBeVisible({ timeout: 15000 });
    await expect(authedPage.getByText(new RegExp(`business_case:${subjectId}`, 'i')).first()).toBeVisible();

    await authedPage.reload({ waitUntil: 'domcontentloaded' });
    await expectNoErrors(authedPage);
    await expect(authedPage.getByText(body).first()).toBeVisible({ timeout: 15000 });
  });
});
