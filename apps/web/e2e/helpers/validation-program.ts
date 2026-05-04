import type { Page, Route } from '@playwright/test';
import { expect } from '@playwright/test';
import { expectNoErrors, navigateAndWait } from './journey-fixture';

export type ValidationTraceability = {
  id: string;
  suite: string;
  workflow: string;
  priority: 'P0 production gate' | 'P1 core workflow' | 'P2 important workflow';
};

// ── Deep-Test Utility Helpers ────────────────────────────────────────────────

export interface FormField {
  /** Locator strategy: 'label' | 'placeholder' | 'testid' | 'role' */
  by: 'label' | 'placeholder' | 'testid' | 'role';
  selector: string;
  value: string;
  /** For select/dropdown fields */
  type?: 'input' | 'select' | 'textarea';
}

/**
 * Fill a form and submit it, then assert a visible outcome.
 * Finds fields using accessible selectors and fills them.
 */
export async function expectFormSubmission(
  page: Page,
  fields: FormField[],
  submitButton: string | RegExp,
  expectedOutcome: string | RegExp,
  timeout = 10000,
): Promise<void> {
  for (const field of fields) {
    let locator;
    switch (field.by) {
      case 'label':
        locator = page.getByLabel(field.selector);
        break;
      case 'placeholder':
        locator = page.getByPlaceholder(field.selector);
        break;
      case 'testid':
        locator = page.getByTestId(field.selector);
        break;
      case 'role':
        locator = page.getByRole('textbox', { name: field.selector });
        break;
    }
    if (field.type === 'select') {
      await locator.selectOption(field.value);
    } else {
      await locator.fill(field.value);
    }
  }

  const btn = page.getByRole('button', { name: submitButton }).first();
  await expect(btn).toBeVisible({ timeout: 5000 });
  await btn.click();
  await expect(page.getByText(expectedOutcome).first()).toBeVisible({ timeout });
}

/**
 * Navigate to a path, perform a sequence of actions, and verify the outcome.
 */
export async function expectWorkflowStep(
  page: Page,
  path: string,
  actions: Array<{ click?: string | RegExp; fill?: { selector: string; value: string }; wait?: number }>,
  expectedOutcome: string | RegExp,
  timeout = 10000,
): Promise<void> {
  await navigateAndWait(page, path);
  await expectNoErrors(page);

  for (const action of actions) {
    if (action.wait) {
      await page.waitForTimeout(action.wait);
    }
    if (action.click) {
      const target = page.getByRole('button', { name: action.click })
        .or(page.getByRole('link', { name: action.click }))
        .or(page.getByRole('tab', { name: action.click }))
        .or(page.getByText(action.click))
        .first();
      await expect(target).toBeVisible({ timeout: 5000 });
      await target.click();
    }
    if (action.fill) {
      const input = page.getByPlaceholder(action.fill.selector)
        .or(page.getByLabel(action.fill.selector))
        .first();
      await input.fill(action.fill.value);
    }
  }

  await expect(page.getByText(expectedOutcome).first()).toBeVisible({ timeout });
}

/**
 * Assert that a named action button exists but is disabled.
 */
export async function expectDisabledAction(
  page: Page,
  actionName: string | RegExp,
  timeout = 5000,
): Promise<void> {
  const btn = page.getByRole('button', { name: actionName }).first();
  await expect(btn).toBeVisible({ timeout });
  await expect(btn).toBeDisabled();
}

/**
 * Assert that a named action button exists and is enabled.
 */
export async function expectEnabledAction(
  page: Page,
  actionName: string | RegExp,
  timeout = 5000,
): Promise<void> {
  const btn = page.getByRole('button', { name: actionName }).first();
  await expect(btn).toBeVisible({ timeout });
  await expect(btn).toBeEnabled();
}

/**
 * Intercept API calls matching a pattern and track whether they were made.
 * Returns a function that asserts the call was made.
 */
export async function expectApiCallMade(
  page: Page,
  pattern: string,
  method?: string,
): Promise<() => void> {
  let callMade = false;
  let requestUrl = '';

  await page.route(pattern, async (route: Route) => {
    if (!method || route.request().method() === method.toUpperCase()) {
      callMade = true;
      requestUrl = route.request().url();
    }
    await route.fallback();
  });

  return () => {
    expect(callMade, `Expected API call to ${pattern} (${method ?? 'any'}) but none was made. Last URL: ${requestUrl}`).toBe(true);
  };
}

/**
 * Assert that a visible audit event or status text appears after an action.
 */
export async function expectAuditEvent(
  page: Page,
  eventPattern: string | RegExp,
  timeout = 8000,
): Promise<void> {
  await expect(
    page.getByText(eventPattern).first(),
  ).toBeVisible({ timeout });
}

/**
 * Register sequential mock responses for the same endpoint pattern.
 * Each call returns the next response in the array.
 */
export async function mockSequentialResponses(
  page: Page,
  pattern: string,
  responses: Array<{ status?: number; body: unknown; delay?: number }>,
): Promise<void> {
  let callIndex = 0;
  await page.route(pattern, async (route: Route) => {
    const resp = responses[Math.min(callIndex, responses.length - 1)];
    callIndex++;
    if (resp.delay) {
      await new Promise((resolve) => setTimeout(resolve, resp.delay));
    }
    await route.fulfill({
      status: resp.status ?? 200,
      contentType: 'application/json',
      body: JSON.stringify(resp.body),
    });
  });
}

/**
 * Assert that specific text is NOT visible (negative assertion for security tests).
 */
export async function expectNotVisible(
  page: Page,
  text: string | RegExp,
  timeout = 3000,
): Promise<void> {
  await expect(page.getByText(text).first()).not.toBeVisible({ timeout });
}

/**
 * Switch user role mid-test and reload to take effect.
 */
export async function switchToReadOnlyUser(page: Page): Promise<void> {
  await page.evaluate(() => {
    const storeKey = 'user-tier-storage';
    const storeState = {
      state: { currentTier: 'standard', isAdvancedModeEnabled: false, userRole: 'read_only' },
      version: 0,
    };
    localStorage.setItem(storeKey, JSON.stringify(storeState));
    const userInfoRaw = localStorage.getItem('userInfo');
    if (userInfoRaw) {
      try {
        const userInfo = JSON.parse(userInfoRaw);
        userInfo.role = 'read_only';
        localStorage.setItem('userInfo', JSON.stringify(userInfo));
      } catch { /* ignore */ }
    }
  });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
}

export async function expectAnyVisible(
  page: Page,
  candidates: Array<string | RegExp>,
  description: string,
  timeout = 3000,
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

export async function expectTenantContext(
  page: Page,
  expectedTenantId = 'tenant-e2e-001',
): Promise<void> {
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

export function requireBackendOrThrow(testName: string): void {
  if (!process.env.PLAYWRIGHT_BACKEND_URL) {
    throw new Error(
      `PLAYWRIGHT_BACKEND_URL is required for ${testName}. ` +
      'Run this suite in the backend-integrated project against seeded validation data.',
    );
  }
}

export async function expectButtonStateIfVisible(
  page: Page,
  buttonName: RegExp,
  state: 'enabled' | 'disabled',
): Promise<void> {
  const button = page.getByRole('button', { name: buttonName }).first();
  if (await button.isVisible({ timeout: 3000 }).catch(() => false)) {
    if (state === 'enabled') {
      await expect(button).toBeEnabled();
    } else {
      await expect(button).toBeDisabled();
    }
  }
}

export async function expectFieldValueIfVisible(
  page: Page,
  labelOrPlaceholder: RegExp,
  expected: string,
): Promise<void> {
  const field = page
    .getByLabel(labelOrPlaceholder)
    .or(page.getByPlaceholder(labelOrPlaceholder))
    .first();

  if (await field.isVisible({ timeout: 3000 }).catch(() => false)) {
    await expect(field).toHaveValue(expected);
  }
}
