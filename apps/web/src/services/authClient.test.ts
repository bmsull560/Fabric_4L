/**
 * AuthClient security tests
 *
 * Tests cover:
 * - Token generation and validation
 * - Session management
 * - Error handling
 * - Edge cases
 */

import { AuthClient } from './authClient';
import { AuthError, AuthErrorCategory } from '../schemas/auth';
import {
  applySessionServiceTestEnvironment,
  authFixtures,
  type MemoryStorage,
} from '@/test/authSessionTestUtils';

import { vi, describe, it, expect, beforeEach, afterEach, beforeAll, afterAll } from "vitest";

// Mock window.fetch directly to bypass MSW for AuthClient unit tests
const fetchMock = vi.fn();
const originalFetch = window.fetch;
beforeAll(() => {
  window.fetch = fetchMock as unknown as typeof window.fetch;
});
afterAll(() => {
  window.fetch = originalFetch;
});

describe('AuthClient', () => {
  let client: AuthClient;
  let testLocalStorage: MemoryStorage;
  let testSessionStorage: MemoryStorage;

  beforeEach(() => {
    client = new AuthClient();
    vi.clearAllMocks();
    ({ localStorage: testLocalStorage, sessionStorage: testSessionStorage } = applySessionServiceTestEnvironment());
  });

  describe('initiateLogin', () => {
    it('should initiate login and return authorization URL', async () => {
      // Arrange: Mock successful OIDC initiation response
      const mockResponse = {
        authorization_url: 'https://idp.example.com/auth?client_id=test&state=abc123',
        state: 'abc123',
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      // Act: Initiate login flow
      const result = await client.initiateLogin('tenant-123', 'https://localhost:3000/callback');

      // Assert: Verify response contains expected auth data
      expect(result.authorization_url).toBe(mockResponse.authorization_url);
      expect(result.state).toBe(mockResponse.state);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/auth/oidc/tenant-123/login'),
      );
    });

    it('should throw NETWORK error on fetch failure', async () => {
      fetchMock.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        client.initiateLogin('tenant-123', 'https://localhost:3000/callback'),
      ).rejects.toThrow(AuthError);
    });

    it('should throw AUTHENTICATION error on 401', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Invalid tenant' }),
      });

      await expect(
        client.initiateLogin('tenant-123', 'https://localhost:3000/callback'),
      ).rejects.toMatchObject({
        category: AuthErrorCategory.AUTHENTICATION,
        statusCode: 401,
      });
    });

    it('should throw VALIDATION error on other errors', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'Server error' }),
      });

      await expect(
        client.initiateLogin('tenant-123', 'https://localhost:3000/callback'),
      ).rejects.toMatchObject({
        category: AuthErrorCategory.VALIDATION,
      });
    });

    it('should throw MALFORMED_RESPONSE on invalid JSON', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      await expect(
        client.initiateLogin('tenant-123', 'https://localhost:3000/callback'),
      ).rejects.toMatchObject({
        category: AuthErrorCategory.MALFORMED_RESPONSE,
      });
    });

    it('should encode redirect URI properly', async () => {
      const redirectUri = 'https://localhost:3000/callback?param=value';
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ authorization_url: 'https://example.com', state: 'state' }),
      });

      await client.initiateLogin('tenant-123', redirectUri);

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(encodeURIComponent(redirectUri)),
      );
    });
  });

  describe('exchangeCodeForTokens', () => {
    it('should exchange code for tokens successfully', async () => {
      // Arrange: Mock successful token exchange response
      const mockResponse = {
        access_token: 'jwt_token_here',
        token_type: 'Bearer',
        expires_in: 3600,
        user_id: 'user-123',
        email: 'user@example.com',
        role: 'analyst' as const,
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      // Act: Exchange authorization code for tokens
      const result = await client.exchangeCodeForTokens('auth-code', 'state-value');

      // Assert: Verify token data and URL parameters
      expect(result.access_token).toBe(mockResponse.access_token);
      expect(result.user_id).toBe(mockResponse.user_id);
      expect(result.email).toBe(mockResponse.email);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('code=auth-code'),
      );
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('state=state-value'),
      );
    });

    it('should encode special characters in code and state', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'token',
          token_type: 'Bearer',
          expires_in: 3600,
          user_id: 'user',
          email: 'test@example.com',
          role: 'analyst',
        }),
      });

      await client.exchangeCodeForTokens('code with spaces&symbols=', 'state/value');

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(encodeURIComponent('code with spaces&symbols=')),
      );
    });
  });

  describe('getCurrentSession', () => {
    it('should return null when no session exists', () => {
      const session = client.getCurrentSession();

      expect(session).toBeNull();
    });

    it('should return null when only token exists (no user info)', () => {
      testLocalStorage.setItem('accessToken', 'token');

      const session = client.getCurrentSession();

      expect(session).toBeNull();
    });

    it('should return valid session when both token and user exist', () => {
      const userInfo = authFixtures.user({ role: 'analyst', tenantSlug: 'tenant' });
      testLocalStorage.setItem('accessToken', authFixtures.validSession().accessToken);
      testLocalStorage.setItem('userInfo', JSON.stringify(userInfo));
      testLocalStorage.setItem('tenantId', userInfo.tenantId);

      // Act: Retrieve the current session
      const session = client.getCurrentSession();

      expect(session).toEqual(userInfo);
    });

    it('should clear session on invalid user JSON', () => {
      testLocalStorage.setItem('accessToken', authFixtures.validSession().accessToken);
      testLocalStorage.setItem('userInfo', authFixtures.malformedUserPayload());
      testLocalStorage.setItem('tenantId', 'tenant-123');

      // Act: Attempt to retrieve session
      const session = client.getCurrentSession();

      // Assert: Session should be null and storage cleared
      expect(session).toBeNull();
      expect(testLocalStorage.getItem('accessToken')).toBeNull();
      expect(testLocalStorage.getItem('userInfo')).toBeNull();
    });

    it('should clear session on schema validation failure', () => {
      testLocalStorage.setItem('accessToken', authFixtures.validSession().accessToken);
      testLocalStorage.setItem('userInfo', JSON.stringify({ id: 'user-123' }));
      testLocalStorage.setItem('tenantId', 'tenant-123');

      // Act: Attempt to get session with invalid data
      const session = client.getCurrentSession();

      // Assert: Session should be cleared and null returned
      expect(session).toBeNull();
      expect(testLocalStorage.getItem('accessToken')).toBeNull();
    });
  });

  describe('refreshToken', () => {
    it('should return false when no token exists', async () => {
      const result = await client.refreshToken();

      expect(result).toBe(false);
    });

    it('should return true for valid unexpired token', async () => {
      const snapshot = authFixtures.validSession();
      testLocalStorage.setItem('vf.auth.session', JSON.stringify(snapshot));

      const result = await client.refreshToken();

      expect(result).toBe(true);
    });

    it('should return false and clear session for expired token', async () => {
      testLocalStorage.setItem('vf.auth.session', JSON.stringify(authFixtures.expiredSession()));

      const result = await client.refreshToken();

      expect(result).toBe(false);
      expect(testLocalStorage.getItem('vf.auth.session')).toBeNull();
    });

    it('should return false and clear session for token expiring within buffer', async () => {
      const exp = Math.floor(Date.now() / 1000) + 30; // 30 seconds from now (within 60s buffer)
      const payload = { exp };
      const base64Payload = btoa(JSON.stringify(payload));
      const token = `header.${base64Payload}.signature`;
      testLocalStorage.setItem(
        'vf.auth.session',
        JSON.stringify(authFixtures.validSession({ accessToken: token }))
      );

      const result = await client.refreshToken();

      expect(result).toBe(false);
      expect(testLocalStorage.getItem('vf.auth.session')).toBeNull();
    });

    it('should return false for malformed JWT', async () => {
      testLocalStorage.setItem(
        'vf.auth.session',
        JSON.stringify(authFixtures.validSession({ accessToken: 'not.a.valid.jwt' }))
      );

      const result = await client.refreshToken();

      expect(result).toBe(false);
      expect(testLocalStorage.getItem('vf.auth.session')).toBeNull();
    });

    it('should return false for invalid JWT structure', async () => {
      testLocalStorage.setItem(
        'vf.auth.session',
        JSON.stringify(authFixtures.validSession({ accessToken: 'invalid-token' }))
      );

      const result = await client.refreshToken();

      expect(result).toBe(false);
    });

    it('should handle base64url encoding correctly', async () => {
      // Token with URL-safe base64 characters
      const payload = { exp: Math.floor(Date.now() / 1000) + 3600 };
      const base64Payload = Buffer.from(JSON.stringify(payload))
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
      const token = `header.${base64Payload}.signature`;
      testLocalStorage.setItem(
        'vf.auth.session',
        JSON.stringify(authFixtures.validSession({ accessToken: token }))
      );

      const result = await client.refreshToken();

      expect(result).toBe(true);
    });
  });

  describe('persistSession', () => {
    it('should persist all session data to localStorage', () => {
      // Arrange: Prepare session data
      const token = 'jwt_token';
      const userInfo = authFixtures.user({ role: 'analyst', tenantSlug: 'tenant' });
      const tenantId = 'tenant-123';

      // Act: Persist the session
      client.persistSession(token, userInfo, tenantId);

      expect(testLocalStorage.getItem('accessToken')).toBe(token);
      expect(testLocalStorage.getItem('userInfo')).toBe(JSON.stringify(userInfo));
      expect(testLocalStorage.getItem('tenantId')).toBe(tenantId);
      expect(testLocalStorage.getItem('vf.auth.session')).not.toBeNull();
    });
  });

  describe('clearSession', () => {
    it('should remove all session data from localStorage', () => {
      const snapshot = authFixtures.validSession();
      testLocalStorage.setItem('vf.auth.session', JSON.stringify(snapshot));
      testLocalStorage.setItem('accessToken', snapshot.accessToken);
      testLocalStorage.setItem('userInfo', JSON.stringify(snapshot.user));
      testLocalStorage.setItem('tenantId', snapshot.tenantId);

      client.clearSession();

      expect(testLocalStorage.getItem('vf.auth.session')).toBeNull();
      expect(testLocalStorage.getItem('accessToken')).toBeNull();
      expect(testLocalStorage.getItem('userInfo')).toBeNull();
      expect(testLocalStorage.getItem('tenantId')).toBeNull();
    });
  });

  describe('clearOidcState', () => {
    it('should remove OIDC state from sessionStorage', () => {
      const flow = authFixtures.oidcFlow({ postLoginRedirect: '/home' });
      testSessionStorage.setItem('vf.auth.oidc', JSON.stringify(flow));
      testSessionStorage.setItem('oidcState', flow.state);
      testSessionStorage.setItem('oidcTenantSlug', flow.tenantSlug);

      client.clearOidcState();

      expect(testSessionStorage.getItem('vf.auth.oidc')).toBeNull();
      expect(testSessionStorage.getItem('oidcState')).toBeNull();
      expect(testSessionStorage.getItem('oidcTenantSlug')).toBeNull();
    });
  });
});

describe('AuthError', () => {
  it('should create error with category and message', () => {
    const error = new AuthError('Test message', AuthErrorCategory.NETWORK);

    expect(error.message).toBe('Test message');
    expect(error.category).toBe(AuthErrorCategory.NETWORK);
    expect(error.name).toBe('AuthError');
  });

  it('should include status code when provided', () => {
    const error = new AuthError('Unauthorized', AuthErrorCategory.AUTHENTICATION, 401);

    expect(error.statusCode).toBe(401);
  });
});
