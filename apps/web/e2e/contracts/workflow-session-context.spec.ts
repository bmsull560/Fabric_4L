import { test, expect } from '../fixtures/contract-test';
import { seedAuthState, setUserTier } from '../fixtures';

test.describe('Workflow session context', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthState(page);
    await setUserTier(page, 'advanced');
  });

  test('mid-flow reload retains meaningful state', async ({ page }) => {
    await page.goto('/drivers/acc-123/trees?caseId=case-123&entityId=ent-11');
    await expect(page).toHaveURL(/\/drivers\/acc-123\/trees\?caseId=case-123&entityId=ent-11/);

    await page.reload();
    await expect(page).toHaveURL(/\/drivers\/acc-123\/trees\?caseId=case-123&entityId=ent-11/);
  });

  test('cross-route navigation keeps resumable context', async ({ page }) => {
    await page.goto('/hypothesis/acc-123/hypothesis?caseId=case-99');
    await page.goto('/calculator/acc-123/roi');

    await page.getByRole('link', { name: /resume last workflow/i }).click();
    await expect(page).toHaveURL(/\/calculator\/acc-123\/roi/);
  });
});
