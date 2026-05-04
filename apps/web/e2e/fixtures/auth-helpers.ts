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
 * Generate a valid JWT-format token for E2E tests.
 * refreshToken() validates JWT structure (header.payload.signature)
 * and checks expiry, so test tokens must conform.
 */
function generateTestToken(userId: string, tenantId: string): string {
  const payload = {
    exp: Math.floor(Date.now() / 1000) + 86400, // 24 hours from now
    iat: Math.floor(Date.now() / 1000),
    sub: userId,
    tenant_id: tenantId,
  };
  const base64Payload = btoa(JSON.stringify(payload));
  return `header.${base64Payload}.signature`;
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
    // Generate a valid JWT-format token so refreshToken() doesn't clear it
    const payload = {
      exp: Math.floor(Date.now() / 1000) + 86400, // 24 hours from now
      iat: Math.floor(Date.now() / 1000),
      sub: u.id,
      tenant_id: u.tenantId,
    };
    const base64Payload = btoa(JSON.stringify(payload));
    const token = `header.${base64Payload}.signature`;

    localStorage.setItem('accessToken', token);
    localStorage.setItem('userInfo', JSON.stringify(u));
    localStorage.setItem('tenantId', u.tenantId);

    // Current auth uses cookie-backed sessions with non-secret metadata in
    // sessionStorage. Keep the legacy localStorage keys above for older E2E
    // helpers, but seed the canonical session metadata key so AuthProvider and
    // ProtectedRoute treat the journey page as authenticated.
    sessionStorage.setItem('vf.auth.session.meta', JSON.stringify({ user: u, tenantId: u.tenantId }));
  }, user);

  // AuthProvider reads sessionStorage on mount. If ensureSameOrigin loaded the
  // app at /login before storage was seeded, reload once so the provider observes
  // the seeded session instead of retaining the unauthenticated initial state.
  await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => undefined);
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
      sessionStorage.removeItem('vf.auth.session.meta');
    });
  } catch {
    // Page may already be closed or on about:blank — safe to ignore
  }
}
