/**
 * AuthClient tests
 *
 * Covers the cookie-based session model:
 * - Token is never stored in localStorage or returned to JS
 * - Session metadata (user info, tenantId) lives in sessionStorage
 * - refreshToken() calls the backend; clears metadata on 401
 * - logout() calls the backend and clears local metadata
 * - devBypass is blocked in production
 */

import { AuthClient } from './authClient';
import { AuthError, AuthErrorCategory } from '../schemas/auth';
import {
  applySessionServiceTestEnvironment,
  authFixtures,
} from '@/test/authSessionTestUtils';
import { sessionService } from './sessionService';

import { vi, describe, it, expect, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';

const fetchMock = vi.fn();
const originalFetch = window.fetch;
beforeAll(() => { window.fetch = fetchMock as unknown as typeof window.fetch; });
afterAll(() => { window.fetch = originalFetch; });

describe('AuthClient', () => {
  let client: AuthClient;
  let env: ReturnType<typeof applySessionServiceTestEnvironment>;

  beforeEach(() => {
    client = new AuthClient();
    vi.clearAllMocks();
    env = applySessionServiceTestEnvironment();
  });

  afterEach(() => {
    env.reset();
  });

  // ── initiateLogin ──────────────────────────────────────────────────────────

  describe('initiateLogin', () => {
    it('returns authorization URL and state', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          authorization_url: 'https://idp.example.com/auth?client_id=test&state=abc123',
          state: 'abc123',
        }),
      });

      const result = await client.initiateLogin('tenant-123', 'https://localhost:3000/callback');

      expect(result.authorization_url).toContain('idp.example.com');
      expect(result.state).toBe('abc123');
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/auth/oidc/tenant-123/login'),
        expect.objectContaining({ credentials: 'include' })
      );
    });

    it('throws NETWORK error on fetch failure', async () => {
      fetchMock.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        client.initiateLogin('tenant-123', 'https://localhost:3000/callback')
      ).rejects.toThrow(AuthError);
    });

    it('throws AUTHENTICATION error on 401', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Invalid tenant' }),
      });

      await expect(
        client.initiateLogin('tenant-123', 'https://localhost:3000/callback')
      ).rejects.toMatchObject({ category: AuthErrorCategory.AUTHENTICATION, statusCode: 401 });
    });



    it('blocks unsafe tenant slug input with an operator-safe validation message', async () => {
      await expect(
        client.initiateLogin('<script>alert(1)</script>', 'https://localhost:3000/callback')
      ).rejects.toMatchObject({
        category: AuthErrorCategory.VALIDATION,
        message: 'Tenant slug contains unsafe characters. Contact your administrator.',
      });
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it('encodes redirect URI', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ authorization_url: 'https://example.com', state: 'state' }),
      });

      const redirectUri = 'https://localhost:3000/callback?param=value';
      await client.initiateLogin('tenant-123', redirectUri);

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(encodeURIComponent(redirectUri)),
        expect.anything()
      );
    });
  });

  // ── exchangeCodeForTokens ──────────────────────────────────────────────────

  describe('exchangeCodeForTokens', () => {
    it('returns user metadata; does NOT include access_token in response body', async () => {
      // Backend now omits access_token from JSON body (cookie-only delivery)
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          token_type: 'Bearer',
          expires_in: 3600,
          user_id: 'user-123',
          email: 'user@example.com',
          role: 'analyst',
        }),
      });

      const result = await client.exchangeCodeForTokens('auth-code', 'state-value');

      expect(result.user_id).toBe('user-123');
      expect(result.email).toBe('user@example.com');
      // access_token is optional in the schema; must not be present in this response
      expect((result as Record<string, unknown>).access_token).toBeUndefined();
    });

    it('sends credentials: include so the session cookie is set', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          token_type: 'Bearer',
          expires_in: 3600,
          user_id: 'user-123',
          email: 'user@example.com',
          role: 'analyst',
        }),
      });

      await client.exchangeCodeForTokens('code', 'state');

      expect(fetchMock).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ credentials: 'include' })
      );
    });
  });

  // ── Session metadata storage — no localStorage token persistence ──────────

  describe('token storage', () => {
    it('session metadata persistence does NOT write tokens to localStorage', () => {
      const user = authFixtures.user({ role: 'analyst', tenantSlug: 'tenant' });
      sessionService.persistSessionMeta(user, 'tenant-123');

      // localStorage must remain empty — token is in the httpOnly cookie
      expect(localStorage.getItem('accessToken')).toBeNull();
      expect(localStorage.getItem('vf.auth.session')).toBeNull();
      expect(localStorage.getItem('userInfo')).toBeNull();
    });

    it('getAccessToken always returns null', () => {
      const user = authFixtures.user();
      sessionService.persistSessionMeta(user, 'tenant-123');

      expect(sessionService.getAccessToken()).toBeNull();
    });

    it('getCurrentSession returns user from sessionStorage metadata', () => {
      const user = authFixtures.user({ role: 'analyst', tenantSlug: 'tenant' });
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: user.tenantId })
      );

      const session = client.getCurrentSession();

      expect(session).toMatchObject({ id: user.id, email: user.email });
    });

    it('getCurrentSession returns null when no metadata exists', () => {
      expect(client.getCurrentSession()).toBeNull();
    });
  });

  // ── refreshToken ───────────────────────────────────────────────────────────

  describe('refreshToken', () => {
    it('calls POST /auth/refresh with credentials: include', async () => {
      Object.defineProperty(document, 'cookie', {
        value: 'vf_csrf_token=csrf-refresh-token',
        configurable: true,
      });
      // Seed session metadata so the tenantId guard passes
      const user = authFixtures.user({ role: 'analyst', tenantSlug: 'acme' });
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: user.tenantId })
      );
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          token_type: 'Bearer',
          expires_in: 3600,
          user_id: user.id,
          email: user.email,
          role: user.role,
        }),
      });

      const result = await client.refreshToken();

      expect(result).toBe(true);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/auth/oidc/refresh'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          headers: expect.objectContaining({ 'X-CSRF-Token': 'csrf-refresh-token' }),
        })
      );
    });

    it('returns false and clears metadata on 401', async () => {
      const user = authFixtures.user();
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: user.tenantId })
      );

      fetchMock.mockResolvedValueOnce({ ok: false, status: 401 });

      const result = await client.refreshToken();

      expect(result).toBe(false);
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();
    });

    it('returns false and clears metadata on 403', async () => {
      const user = authFixtures.user();
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: user.tenantId })
      );

      fetchMock.mockResolvedValueOnce({ ok: false, status: 403 });

      const result = await client.refreshToken();

      expect(result).toBe(false);
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();
    });

    it('returns true on network error (keeps existing metadata)', async () => {
      const user = authFixtures.user();
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: user.tenantId })
      );

      fetchMock.mockRejectedValueOnce(new Error('Network error'));

      const result = await client.refreshToken();

      // Network error should not log the user out
      expect(result).toBe(true);
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).not.toBeNull();
    });

    it('returns false and clears session when existing metadata has no tenantId', async () => {
      // Simulate corrupted session metadata with missing tenantId
      const user = authFixtures.user();
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: '' })
      );

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: user.id,
          email: user.email,
          role: user.role,
          expires_in: 3600,
          token_type: 'Bearer',
        }),
      });

      const result = await client.refreshToken();

      // Missing tenantId in existing metadata → treat as invalid session
      expect(result).toBe(false);
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();
    });

    it('throws AuthError(MALFORMED_RESPONSE) when 200 response body is not parseable JSON', async () => {
      const user = authFixtures.user({ role: 'analyst', tenantSlug: 'acme' });
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: user.tenantId })
      );

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.reject(new SyntaxError('Unexpected token')),
      });

      await expect(client.refreshToken()).rejects.toMatchObject({
        category: 'MALFORMED_RESPONSE',
      });
    });
  });

  // ── logout ─────────────────────────────────────────────────────────────────

  describe('logout', () => {
    it('calls POST /auth/logout and clears local metadata', async () => {
      Object.defineProperty(document, 'cookie', {
        value: 'vf_csrf_token=csrf-logout-token',
        configurable: true,
      });
      const user = authFixtures.user();
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: user.tenantId })
      );

      fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ detail: 'Logged out' }) });

      await client.logout();

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/auth/oidc/logout'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          headers: expect.objectContaining({ 'X-CSRF-Token': 'csrf-logout-token' }),
        })
      );
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();
    });

    it('clears local metadata even when the network call fails', async () => {
      const user = authFixtures.user();
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: user.tenantId })
      );

      fetchMock.mockRejectedValueOnce(new Error('Network error'));

      await client.logout();

      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();
    });
  });

  // ── clearSession / clearOidcState ──────────────────────────────────────────

  describe('clearSession', () => {
    it('removes session metadata from sessionStorage', () => {
      const user = authFixtures.user();
      env.sessionStorage.setItem(
        'vf.auth.session.meta',
        JSON.stringify({ user, tenantId: user.tenantId })
      );

      client.clearSession();

      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();
    });
  });

  describe('clearOidcState', () => {
    it('removes OIDC state from sessionStorage', () => {
      const flow = authFixtures.oidcFlow({ postLoginRedirect: '/home' });
      env.sessionStorage.setItem('vf.auth.oidc', JSON.stringify(flow));
      env.sessionStorage.setItem('oidcState', flow.state);
      env.sessionStorage.setItem('oidcTenantSlug', flow.tenantSlug);

      client.clearOidcState();

      expect(env.sessionStorage.getItem('vf.auth.oidc')).toBeNull();
      expect(env.sessionStorage.getItem('oidcState')).toBeNull();
      expect(env.sessionStorage.getItem('oidcTenantSlug')).toBeNull();
    });
  });
});

// ── AuthError ──────────────────────────────────────────────────────────────

describe('AuthError', () => {
  it('creates error with category and message', () => {
    const error = new AuthError('Test message', AuthErrorCategory.NETWORK);

    expect(error.message).toBe('Test message');
    expect(error.category).toBe(AuthErrorCategory.NETWORK);
    expect(error.name).toBe('AuthError');
  });

  it('includes status code when provided', () => {
    const error = new AuthError('Unauthorized', AuthErrorCategory.AUTHENTICATION, 401);

    expect(error.statusCode).toBe(401);
  });
});
