import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { expectNoErrors, navigateAndWait } from './journey-fixture';

export type ValidationTraceability = {
  id: string;
  suite: string;
  workflow: string;
  priority: 'P0 production gate' | 'P1 core workflow' | 'P2 important workflow';
};

export async function expectAnyVisible(
  page: Page,
  candidates: Array<string | RegExp>,
  description: string,
  timeout = 8000,
): Promise<void> {
  const failures: string[] = [];

  for (const candidate of candidates) {
    const locator = page
      .getByRole('heading', { name: candidate })
      .or(page.getByRole('button', { name: candidate }))
      .or(page.getByRole('link', { name: candidate }))
      .or(page.getByPlaceholder(candidate))
      .or(page.getByText(candidate))
      .first();

    try {
      await expect(locator).toBeVisible({ timeout });
      return;
    } catch (error) {
      failures.push(`${candidate}: ${error instanceof Error ? error.message.split('\n')[0] : String(error)}`);
    }
  }

  throw new Error(`Expected visible UI evidence for ${description} at ${page.url()}. Tried: ${failures.join(' | ')}`);
}

export async function expectRouteSupportsWorkflow(
  page: Page,
  path: string,
  candidates: Array<string | RegExp>,
  description: string,
): Promise<void> {
  await navigateAndWait(page, path);
  await expectNoErrors(page);
  await expectAnyVisible(page, candidates, description);
}

export async function expectTenantContext(page: Page, expectedTenantId = 'tenant-e2e-001'): Promise<void> {
  const tenantId = await page.evaluate(() => localStorage.getItem('tenantId'));
  expect(tenantId).toBe(expectedTenantId);
}

export async function expectNoCrossTenantLeakage(page: Page): Promise<void> {
  await expect(page.getByText(/tenant-other|other tenant|globex confidential|cross-tenant/i).first()).not.toBeVisible({ timeout: 3000 });
}

export async function attemptOptionalAction(page: Page, actionName: RegExp): Promise<boolean> {
  const action = page.getByRole('button', { name: actionName }).or(page.getByRole('link', { name: actionName })).first();
  try {
    if (await action.isVisible({ timeout: 2000 })) {
      await action.click();
      return true;
    }
  } catch {
    return false;
  }
  return false;
}
