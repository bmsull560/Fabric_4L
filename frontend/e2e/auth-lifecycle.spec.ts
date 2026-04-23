/**
 * Authentication Lifecycle E2E Tests
 *
 * Tests cover:
 * - OIDC login flow initiation
 * - Login page validation
 * - Session persistence
 * - Logout flow
 * - Protected route access
 * - Token expiration handling
 */

import { test, expect } from '@playwright/test';

test.describe('Authentication Lifecycle', () => {
  test.describe('Login Page', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/login');
    });

    test('should display login form with tenant input', async ({ page }) => {
      await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
      await expect(page.getByLabel(/tenant/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
    });

    test('should validate empty tenant submission', async ({ page }) => {
      await page.getByRole('button', { name: /sign in/i }).click();
      await expect(page.getByText(/tenant is required/i)).toBeVisible();
    });

    test('should validate invalid tenant format', async ({ page }) => {
      await page.getByLabel(/tenant/i).fill('Invalid Tenant Name!');
      await page.getByRole('button', { name: /sign in/i }).click();
      await expect(page.getByText(/invalid tenant format/i)).toBeVisible();
    });

    test('should show loading state during login initiation', async ({ page }) => {
      // Mock slow API response
      await page.route('**/auth/oidc/**/login', async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 500));
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            authorization_url: 'https://example.com/auth',
            state: 'test-state',
          }),
        });
      });

      await page.getByLabel(/tenant/i).fill('valid-tenant');
      await page.getByRole('button', { name: /sign in/i }).click();

      await expect(page.getByRole('button', { name: /sign in/i })).toBeDisabled();
      await expect(page.getByText(/loading/i)).toBeVisible();
    });

    test('should display error on login initiation failure', async ({ page }) => {
      await page.route('**/auth/oidc/**/login', (route) => {
        route.fulfill({
          status: 404,
          body: JSON.stringify({ detail: 'Tenant not found' }),
        });
      });

      await page.getByLabel(/tenant/i).fill('nonexistent-tenant');
      await page.getByRole('button', { name: /sign in/i }).click();

      await expect(page.getByText(/tenant not found/i)).toBeVisible();
    });

    test('should store state in sessionStorage before redirect', async ({ page }) => {
      await page.route('**/auth/oidc/**/login', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify({
            authorization_url: 'https://example.com/auth',
            state: 'test-state-123',
          }),
        });
      });

      await page.getByLabel(/tenant/i).fill('test-tenant');

      // Setup redirect interception
      let redirectUrl: string | null = null;
      await page.route('https://example.com/auth', (route) => {
        redirectUrl = route.request().url();
        route.abort(); // Prevent actual redirect
      });

      await page.getByRole('button', { name: /sign in/i }).click();

      // Check sessionStorage
      const state = await page.evaluate(() => sessionStorage.getItem('oidcState'));
      const tenantSlug = await page.evaluate(() =>
        sessionStorage.getItem('oidcTenantSlug'),
      );

      expect(state).toBe('test-state-123');
      expect(tenantSlug).toBe('test-tenant');
    });
  });

  test.describe('OIDC Callback', () => {
    test('should handle successful callback', async ({ page }) => {
      // Setup sessionStorage before callback
      await page.goto('/login');
      await page.evaluate(() => {
        sessionStorage.setItem('oidcState', 'valid-state');
        sessionStorage.setItem('oidcTenantSlug', 'test-tenant');
      });

      // Mock successful token exchange
      await page.route('**/auth/oidc/callback**', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify({
            access_token: 'test-jwt-token',
            token_type: 'Bearer',
            expires_in: 3600,
            user_id: 'user-123',
            email: 'test@example.com',
            role: 'analyst',
          }),
        });
      });

      await page.goto('/login/callback?code=auth-code&state=valid-state');

      // Should redirect to home or stored redirect
      await expect(page).toHaveURL(/^(?!.*\/login).*$/);

      // Verify session persisted
      const token = await page.evaluate(() => localStorage.getItem('accessToken'));
      expect(token).toBe('test-jwt-token');
    });

    test('should detect CSRF attack with mismatched state', async ({ page }) => {
      await page.goto('/login');
      await page.evaluate(() => {
        sessionStorage.setItem('oidcState', 'expected-state');
        sessionStorage.setItem('oidcTenantSlug', 'test-tenant');
      });

      // Attempt callback with wrong state (simulating CSRF)
      await page.goto('/login/callback?code=auth-code&state=attacker-state');

      await expect(page.getByText(/invalid state parameter/i)).toBeVisible();
      await expect(page.getByText(/possible csrf attack/i)).toBeVisible();
    });

    test('should handle token exchange failure', async ({ page }) => {
      await page.goto('/login');
      await page.evaluate(() => {
        sessionStorage.setItem('oidcState', 'valid-state');
        sessionStorage.setItem('oidcTenantSlug', 'test-tenant');
      });

      await page.route('**/auth/oidc/callback**', (route) => {
        route.fulfill({
          status: 400,
          body: JSON.stringify({ detail: 'Invalid authorization code' }),
        });
      });

      await page.goto('/login/callback?code=invalid-code&state=valid-state');

      await expect(page.getByText(/authentication failed/i)).toBeVisible();

      // Verify session cleared
      const token = await page.evaluate(() => localStorage.getItem('accessToken'));
      expect(token).toBeNull();
    });

    test('should handle expired session', async ({ page }) => {
      await page.goto('/login');
      await page.evaluate(() => {
        sessionStorage.setItem('oidcState', 'valid-state');
        sessionStorage.setItem('oidcTenantSlug', 'test-tenant');
      });

      await page.route('**/auth/oidc/callback**', (route) => {
        route.fulfill({
          status: 400,
          body: JSON.stringify({ detail: 'OIDC session expired' }),
        });
      });

      await page.goto('/login/callback?code=auth-code&state=valid-state');

      await expect(page.getByText(/session expired/i)).toBeVisible();
      await expect(page.getByText(/please try logging in again/i)).toBeVisible();
    });
  });

  test.describe('Session Management', () => {
    test('should persist session across page reloads', async ({ page }) => {
      // Setup authenticated session
      await page.goto('/login');
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'valid-jwt-token');
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'analyst',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
        localStorage.setItem('tenantId', 'tenant-123');
      });

      // Reload page
      await page.goto('/');

      // Should be authenticated (not redirected to login)
      await expect(page).not.toHaveURL(/\/login/);

      // User info should be loaded
      await expect(page.getByText(/test@example.com/i)).toBeVisible();
    });

    test('should clear session on logout', async ({ page }) => {
      // Setup authenticated session
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'valid-jwt-token');
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'analyst',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
      });

      // Click logout
      await page.getByRole('button', { name: /logout/i }).click();

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/);

      // Session should be cleared
      const token = await page.evaluate(() => localStorage.getItem('accessToken'));
      const userInfo = await page.evaluate(() => localStorage.getItem('userInfo'));

      expect(token).toBeNull();
      expect(userInfo).toBeNull();
    });

    test('should detect and clear expired session on load', async ({ page }) => {
      // Create expired JWT (exp in past)
      const expiredPayload = {
        exp: Math.floor(Date.now() / 1000) - 3600, // 1 hour ago
        iat: Math.floor(Date.now() / 1000) - 7200,
        sub: 'user-123',
        tenant_id: 'tenant-123',
      };
      const expiredToken = `header.${btoa(JSON.stringify(expiredPayload))}.signature`;

      await page.goto('/');
      await page.evaluate((token) => {
        localStorage.setItem('accessToken', token);
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'analyst',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
      }, expiredToken);

      // Reload to trigger expiration check
      await page.reload();

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/);

      // Session should be cleared
      const token = await page.evaluate(() => localStorage.getItem('accessToken'));
      expect(token).toBeNull();
    });

    test('should refresh valid token on page load', async ({ page }) => {
      // Create valid JWT (exp in future)
      const validPayload = {
        exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
        iat: Math.floor(Date.now() / 1000),
        sub: 'user-123',
        tenant_id: 'tenant-123',
      };
      const validToken = `header.${btoa(JSON.stringify(validPayload))}.signature`;

      await page.goto('/');
      await page.evaluate((token) => {
        localStorage.setItem('accessToken', token);
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'analyst',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
      }, validToken);

      // Reload to trigger refresh check
      await page.reload();

      // Should stay on current page (authenticated)
      await expect(page).not.toHaveURL(/\/login/);
    });
  });

  test.describe('Protected Routes', () => {
    test('should redirect unauthenticated users to login', async ({ page }) => {
      await page.goto('/admin/users');

      // Should redirect to login with return URL
      await expect(page).toHaveURL(/\/login/);
    });

    test('should allow authenticated users to access protected routes', async ({ page }) => {
      // Setup authenticated session
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'valid-jwt-token');
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'tenant_admin',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
      });

      // Try to access protected route
      await page.goto('/admin/users');

      // Should not redirect to login
      await expect(page).not.toHaveURL(/\/login/);
    });

    test('should redirect after login to originally requested page', async ({ page }) => {
      // Try to access protected route without auth
      await page.goto('/admin/users');

      // Should be redirected to login with return URL
      await expect(page).toHaveURL(/\/login/);

      // Setup successful login
      await page.route('**/auth/oidc/**/login', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify({
            authorization_url: 'https://example.com/auth',
            state: 'test-state',
          }),
        });
      });

      await page.getByLabel(/tenant/i).fill('test-tenant');

      // The redirect should preserve the return URL
      await page.evaluate(() => {
        sessionStorage.setItem('postLoginRedirect', '/admin/users');
      });

      // After successful callback, should redirect to original page
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'valid-jwt-token');
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'tenant_admin',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
      });

      await page.goto('/admin/users');
      await expect(page).toHaveURL('/admin/users');
    });
  });

  test.describe('Security Headers', () => {
    test('should include authorization header on API requests', async ({ page }) => {
      // Setup auth
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'test-jwt-token');
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'analyst',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
      });

      // Intercept API request
      let requestHeaders: Record<string, string> = {};
      await page.route('**/api/**', (route) => {
        requestHeaders = route.request().headers();
        route.fulfill({
          status: 200,
          body: JSON.stringify({ data: [] }),
        });
      });

      // Trigger API call
      await page.goto('/');
      await page.getByRole('button', { name: /search/i }).click();

      // Verify Authorization header
      expect(requestHeaders['authorization']).toBe('Bearer test-jwt-token');
    });

    test('should handle 401 API responses by redirecting to login', async ({ page }) => {
      // Setup auth
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'expired-jwt-token');
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'analyst',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
      });

      // Mock 401 response
      await page.route('**/api/**', (route) => {
        route.fulfill({
          status: 401,
          body: JSON.stringify({ detail: 'Token has expired' }),
        });
      });

      // Trigger API call
      await page.getByRole('button', { name: /search/i }).click();

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/);
    });
  });

  test.describe('Role-Based UI', () => {
    test('should show admin navigation for admin users', async ({ page }) => {
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'valid-jwt-token');
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'tenant_admin',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
      });

      await page.reload();

      // Admin navigation should be visible
      await expect(page.getByRole('link', { name: /admin/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /users/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /api keys/i })).toBeVisible();
    });

    test('should hide admin navigation for analyst users', async ({ page }) => {
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'valid-jwt-token');
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'analyst',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
      });

      await page.reload();

      // Admin navigation should not be visible
      await expect(page.getByRole('link', { name: /admin/i })).not.toBeVisible();
      await expect(page.getByRole('link', { name: /users/i })).not.toBeVisible();
    });

    test('should show tier badge for advanced mode users', async ({ page }) => {
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'valid-jwt-token');
        localStorage.setItem(
          'userInfo',
          JSON.stringify({
            id: 'user-123',
            email: 'test@example.com',
            role: 'analyst',
            tenantId: 'tenant-123',
            tenantSlug: 'test-tenant',
          }),
        );
        // Enable advanced mode
        localStorage.setItem('userTier', JSON.stringify({ tier: 'advanced' }));
      });

      await page.reload();

      // Advanced tier badge should be visible
      await expect(page.getByText(/advanced/i)).toBeVisible();
    });
  });
});
