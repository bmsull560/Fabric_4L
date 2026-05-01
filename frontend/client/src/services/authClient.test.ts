/**
 * AuthClient security tests
 *
 * Tests cover:
 * - Token generation and validation
 * - Session management
 * - Error handling
 * - Edge cases
 */

import { AuthClient, authClient } from './authClient';
import { AuthError, AuthErrorCategory } from '../schemas/auth';

import { vi, describe, it, expect, beforeEach, type Mock } from 'vitest';

// Mock window.fetch directly to bypass MSW for AuthClient unit tests
const fetchMock = vi.fn();
beforeAll(() => {
  window.fetch = fetchMock as unknown as typeof window.fetch;
});
afterAll(() => {
  // MSW will restore its patched fetch on next test setup
});

// Mock localStorage and sessionStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
const mockSessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};

Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });
Object.defineProperty(window, 'sessionStorage', { value: mockSessionStorage });

describe('AuthClient', () => {
  let client: AuthClient;

  beforeEach(() => {
    client = new AuthClient();
    vi.clearAllMocks();
  });

  describe('initiateLogin', () => {
    it('should initiate login and return authorization URL', async () => {
      const mockResponse = {
        authorization_url: 'https://idp.example.com/auth?client_id=test&state=abc123',
        state: 'abc123',
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await client.initiateLogin('tenant-123', 'https://localhost:3000/callback');

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

      try {
        await client.initiateLogin('tenant-123', 'https://localhost:3000/callback');
      } catch (error) {
        expect(error).toBeInstanceOf(AuthError);
        expect(error.category).toBe(AuthErrorCategory.AUTHENTICATION);
        expect(error.statusCode).toBe(401);
      }
    });

    it('should throw VALIDATION error on other errors', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'Server error' }),
      });

      try {
        await client.initiateLogin('tenant-123', 'https://localhost:3000/callback');
      } catch (error) {
        expect(error).toBeInstanceOf(AuthError);
        expect(error.category).toBe(AuthErrorCategory.VALIDATION);
      }
    });

    it('should throw MALFORMED_RESPONSE on invalid JSON', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      try {
        await client.initiateLogin('tenant-123', 'https://localhost:3000/callback');
      } catch (error) {
        expect(error).toBeInstanceOf(AuthError);
        expect(error.category).toBe(AuthErrorCategory.MALFORMED_RESPONSE);
      }
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
      const mockResponse = {
        access_token: 'jwt_token_here',
        token_type: 'Bearer',
        expires_in: 3600,
        user_id: 'user-123',
        email: 'user@example.com',
        role: 'analyst',
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await client.exchangeCodeForTokens('auth-code', 'state-value');

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
      mockLocalStorage.getItem.mockReturnValue(null);

      const session = client.getCurrentSession();

      expect(session).toBeNull();
    });

    it('should return null when only token exists (no user info)', () => {
      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'accessToken') return 'token';
        if (key === 'userInfo') return null;
        return null;
      });

      const session = client.getCurrentSession();

      expect(session).toBeNull();
    });

    it('should return valid session when both token and user exist', () => {
      const userInfo = {
        id: 'user-123',
        email: 'user@example.com',
        role: 'analyst',
        tenantId: 'tenant-123',
        tenantSlug: 'tenant',
      };

      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'accessToken') return 'valid_token';
        if (key === 'userInfo') return JSON.stringify(userInfo);
        return null;
      });

      const session = client.getCurrentSession();

      expect(session).toEqual(userInfo);
    });

    it('should clear session on invalid user JSON', () => {
      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'accessToken') return 'token';
        if (key === 'userInfo') return 'invalid json{';
        return null;
      });

      const session = client.getCurrentSession();

      expect(session).toBeNull();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('accessToken');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('userInfo');
    });

    it('should clear session on schema validation failure', () => {
      const invalidUser = {
        id: 'user-123',
        // Missing required fields
      };

      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'accessToken') return 'token';
        if (key === 'userInfo') return JSON.stringify(invalidUser);
        return null;
      });

      const session = client.getCurrentSession();

      expect(session).toBeNull();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('accessToken');
    });
  });

  describe('refreshToken', () => {
    it('should return false when no token exists', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const result = await client.refreshToken();

      expect(result).toBe(false);
    });

    it('should return true for valid unexpired token', async () => {
      const exp = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
      const payload = { exp };
      const base64Payload = btoa(JSON.stringify(payload));
      const token = `header.${base64Payload}.signature`;

      mockLocalStorage.getItem.mockReturnValue(token);

      const result = await client.refreshToken();

      expect(result).toBe(true);
    });

    it('should return false and clear session for expired token', async () => {
      const exp = Math.floor(Date.now() / 1000) - 60; // 1 minute ago
      const payload = { exp };
      const base64Payload = btoa(JSON.stringify(payload));
      const token = `header.${base64Payload}.signature`;

      mockLocalStorage.getItem.mockReturnValue(token);

      const result = await client.refreshToken();

      expect(result).toBe(false);
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('accessToken');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('userInfo');
    });

    it('should return false and clear session for token expiring within buffer', async () => {
      const exp = Math.floor(Date.now() / 1000) + 30; // 30 seconds from now (within 60s buffer)
      const payload = { exp };
      const base64Payload = btoa(JSON.stringify(payload));
      const token = `header.${base64Payload}.signature`;

      mockLocalStorage.getItem.mockReturnValue(token);

      const result = await client.refreshToken();

      expect(result).toBe(false);
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('accessToken');
    });

    it('should return false for malformed JWT', async () => {
      mockLocalStorage.getItem.mockReturnValue('not.a.valid.jwt');

      const result = await client.refreshToken();

      expect(result).toBe(false);
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('accessToken');
    });

    it('should return false for invalid JWT structure', async () => {
      mockLocalStorage.getItem.mockReturnValue('invalid-token');

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

      mockLocalStorage.getItem.mockReturnValue(token);

      const result = await client.refreshToken();

      expect(result).toBe(true);
    });
  });

  describe('persistSession', () => {
    it('should persist all session data to localStorage', () => {
      const token = 'jwt_token';
      const userInfo = {
        id: 'user-123',
        email: 'user@example.com',
        role: 'analyst',
        tenantId: 'tenant-123',
        tenantSlug: 'tenant',
      };
      const tenantId = 'tenant-123';

      client.persistSession(token, userInfo, tenantId);

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('accessToken', token);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'userInfo',
        JSON.stringify(userInfo),
      );
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('tenantId', tenantId);
    });
  });

  describe('clearSession', () => {
    it('should remove all session data from localStorage', () => {
      client.clearSession();

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('accessToken');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('userInfo');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('tenantId');
    });
  });

  describe('clearOidcState', () => {
    it('should remove OIDC state from sessionStorage', () => {
      client.clearOidcState();

      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('oidcState');
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('oidcTenantSlug');
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
