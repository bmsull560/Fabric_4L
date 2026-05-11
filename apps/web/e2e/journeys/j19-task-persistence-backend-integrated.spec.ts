/**
 * Journey 19 Task Persistence Backend-Integrated
 *
 * Proves task create/update/reload uses the live Layer 4 task API, not static mocks.
 *
 * Tag: @backend
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import { expectNoErrors } from '../helpers/journey-fixture';
import { requireBackendOrThrow } from '../helpers/validation-program';

journeyTest.describe('@backend Task Persistence Backend-Integrated', () => {
  journeyTest.setTimeout(90000);

  journeyTest.beforeEach(async () => {
    requireBackendOrThrow('task persistence workflow');
  });

  journeyTest('J19-TASK-PERSISTENCE: task create, complete, and reload state persists', async ({ authedPage }) => {
    const title = `Persisted task ${Date.now()}`;

    await authedPage.goto('/tasks', { waitUntil: 'domcontentloaded' });
    await expectNoErrors(authedPage);

    await authedPage.getByLabel(/task title/i).fill(title);
    await authedPage.getByLabel(/owner/i).fill('Avery Stone');
    await authedPage.getByLabel(/stage/i).fill('evidence');
    await authedPage.getByRole('button', { name: /^create task$/i }).click();

    const createdTask = authedPage.getByText(title).first();
    await expect(createdTask).toBeVisible({ timeout: 15000 });
    await expect(authedPage.getByText(/owner:\s*avery stone/i).first()).toBeVisible();

    const taskCard = authedPage.locator('section[aria-label="Persisted tasks"]').filter({ hasText: title }).first();
    await taskCard.getByRole('button', { name: /mark complete/i }).click();
    await expect(taskCard.getByText(/completed/i).first()).toBeVisible({ timeout: 15000 });

    await authedPage.reload({ waitUntil: 'domcontentloaded' });
    await expectNoErrors(authedPage);
    await expect(authedPage.getByText(title).first()).toBeVisible({ timeout: 15000 });
    await expect(authedPage.getByText(/completed/i).first()).toBeVisible({ timeout: 15000 });
  });
});
