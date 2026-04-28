/**
 * Auth Helpers for Playwright Contract Tests
 *
 * Seeds the browser's localStorage with a valid authenticated session
 * so that RouteGuard (AuthContext) considers the user logged in.
 *
 * Contract: AuthContext.initAuth() checks:
 *   1. localStorage.getItem('accessToken') — must be truthy
 *   2. authClient.getCurrentSession() — reads 'userInfo' from localStorage
 *      and validates against UserInfoSchema (id, email, role, tenantId, tenantSlug)
 *
 * IMPORTANT: page.evaluate() can only access localStorage when the page
 * is on a same-origin URL (not about:blank). All helpers navigate first
 * if the page hasn't been loaded yet.
 */
import { Page } from '@playwright/test';

export interface TestUserInfo {
  id: string;
  email: string;
  role: string;
  tenantId: string;
  tenantSlug: string;
}

/**
 * Default test user — admin role for maximum access in contract tests.
 * Individual tests override tier via setUserTier() after this.
 */
export const DEFAULT_TEST_USER: TestUserInfo = {
  id: 'test-user-e2e',
  email: 'e2e@valuefabric.test',
  role: 'admin',
  tenantId: 'tenant-e2e-001',
  tenantSlug: 'e2e-test',
};

/**
 * Ensure the page is on a same-origin URL so localStorage is accessible.
 * If the page is on about:blank or a different origin, navigates to '/'.
 */
async function ensureSameOrigin(page: Page): Promise<void> {
  const url = page.url();
  if (url === 'about:blank' || url === '' || url === 'chrome://newtab/') {
    await page.goto('/login', { waitUntil: 'commit' });
  }
}

/**
 * Seed authenticated session in localStorage.
 * Must be called before any route navigation that requires auth.
 *
 * @param page - Playwright page object
 * @param user - Optional user info override (defaults to admin test user)
 */
export async function seedAuthState(
  page: Page,
  user: TestUserInfo = DEFAULT_TEST_USER
): Promise<void> {
  await ensureSameOrigin(page);

  await page.evaluate((u) => {
    localStorage.setItem('accessToken', 'e2e-test-token-valid');
    localStorage.setItem('userInfo', JSON.stringify(u));
    localStorage.setItem('tenantId', u.tenantId);
  }, user);
}

/**
 * Clear authenticated session from localStorage.
 */
export async function clearAuthState(page: Page): Promise<void> {
  try {
    await page.evaluate(() => {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('userInfo');
      localStorage.removeItem('tenantId');
    });
  } catch {
    // Page may already be closed or on about:blank — safe to ignore
  }
}
