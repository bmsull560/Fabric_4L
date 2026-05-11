/**
 * Journey 19 Notifications Persistence Backend-Integrated
 *
 * Proves notification create/read/reload uses the live Layer 4 notifications API, not static mocks.
 *
 * Tag: @backend
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import { expectNoErrors } from '../helpers/journey-fixture';
import { requireBackendOrThrow } from '../helpers/validation-program';

journeyTest.describe('@backend Notifications Persistence Backend-Integrated', () => {
  journeyTest.setTimeout(90000);

  journeyTest.beforeEach(async () => {
    requireBackendOrThrow('notification persistence workflow');
  });

  journeyTest('J19-NOTIFICATIONS-PERSISTENCE: create, mark read, and reload state persists', async ({ authedPage }) => {
    const title = `Persisted notification ${Date.now()}`;
    const message = `Notification read state survives reload ${Date.now()}`;

    await authedPage.goto('/notifications', { waitUntil: 'domcontentloaded' });
    await expectNoErrors(authedPage);

    await authedPage.getByLabel(/notification title/i).fill(title);
    await authedPage.getByLabel(/type/i).fill('manual_validation');
    await authedPage.getByLabel(/^message$/i).fill(message);
    await authedPage.getByRole('button', { name: /^create notification$/i }).click();

    const notificationCard = authedPage.locator('section[aria-label="Persisted notifications"]').filter({ hasText: title }).first();
    await expect(notificationCard.getByText(message).first()).toBeVisible({ timeout: 15000 });
    await expect(notificationCard.getByText(/pending/i).first()).toBeVisible();

    await notificationCard.getByRole('button', { name: /mark read/i }).click();
    await expect(notificationCard.getByText(/read/i).first()).toBeVisible({ timeout: 15000 });

    await authedPage.reload({ waitUntil: 'domcontentloaded' });
    await expectNoErrors(authedPage);

    const reloadedCard = authedPage.locator('section[aria-label="Persisted notifications"]').filter({ hasText: title }).first();
    await expect(reloadedCard.getByText(message).first()).toBeVisible({ timeout: 15000 });
    await expect(reloadedCard.getByText(/read/i).first()).toBeVisible({ timeout: 15000 });
  });
});
