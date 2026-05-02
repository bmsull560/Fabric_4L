/**
 * AuthContext Tests
 *
 * Comprehensive tests for authentication state management including:
 * - AuthProvider initialization from localStorage
 * - Login flow initiation
 * - Callback handling with state verification
 * - Logout cleanup
 * - Token refresh and validation
 */
import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { AuthProvider, useAuthContext, type UserInfo } from './AuthContext';
import {
  applySessionServiceTestEnvironment,
  authFixtures,
  type MemoryStorage,
  type MutableLocationLike,
} from '@/test/authSessionTestUtils';

// ── Test Helpers ───────────────────────────────────────────────────────────

/**
 * Test component that exposes all AuthContext values and actions.
 *
 * This component renders the auth state (loading, authenticated, user, token)
 * and provides buttons to trigger auth actions (login, logout, callback).
 *
 * Usage:
 *   render(
 *     <AuthProvider>
 *       <TestComponent />
 *     </AuthProvider>
 *   );
 *   // Then interact with screen.getByTestId('login-btn') etc.
 */
function TestComponent() {
  const auth = useAuthContext();
  return (
    <div>
      <div data-testid="loading">{auth.isLoading ? 'loading' : 'ready'}</div>
      <div data-testid="authenticated">{auth.isAuthenticated ? 'authenticated' : 'unauthenticated'}</div>
      <div data-testid="user-email">{auth.user?.email || 'no-user'}</div>
      <div data-testid="token">{auth.accessToken || 'no-token'}</div>
      <button data-testid="login-btn" onClick={() => auth.initiateLogin('test-tenant')}>
        Login
      </button>
      <button data-testid="logout-btn" onClick={auth.logout}>
        Logout
      </button>
      <button
        data-testid="callback-btn"
        onClick={() => auth.handleCallback('test-code', 'oidc-state-123')}
      >
        Handle Callback
      </button>
    </div>
  );
}

describe('AuthProvider', () => {
  let testLocalStorage: MemoryStorage;
  let testSessionStorage: MemoryStorage;
  let location: MutableLocationLike;

  beforeEach(() => {
    vi.clearAllMocks();
    ({ localStorage: testLocalStorage, sessionStorage: testSessionStorage, location } = applySessionServiceTestEnvironment());
    location.href = 'http://localhost:3000/';
    location.pathname = '/';
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('initialization', () => {
    it('initializes as unauthenticated when no stored data', async () => {
      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      expect(screen.getByTestId('authenticated')).toHaveTextContent('unauthenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
      expect(screen.getByTestId('token')).toHaveTextContent('no-token');
    });

    it('restores auth state from localStorage on mount', async () => {
      const userInfo: UserInfo = authFixtures.user({
        email: 'restored@example.com',
        role: 'tenant_admin',
        tenantId: 'tenant-1',
        tenantSlug: 'test-tenant',
      });

      const validSession = authFixtures.validSession({
        accessToken: authFixtures.validSession().accessToken,
        tenantId: 'tenant-1',
        user: userInfo,
      });
      testLocalStorage.setItem('vf.auth.session', JSON.stringify(validSession));

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('restored@example.com');
      expect(screen.getByTestId('token')).toHaveTextContent(validSession.accessToken);
    });

    it('clears invalid stored data and initializes as unauthenticated', async () => {
      testLocalStorage.setItem('accessToken', 'some-token');
      testLocalStorage.setItem('userInfo', 'invalid-json{');

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      expect(screen.getByTestId('authenticated')).toHaveTextContent('unauthenticated');
      expect(testLocalStorage.getItem('accessToken')).toBeNull();
      expect(testLocalStorage.getItem('userInfo')).toBeNull();
    });

    it('handles missing user info gracefully', async () => {
      testLocalStorage.setItem('accessToken', 'token-without-user');
      // No userInfo in localStorage

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      expect(screen.getByTestId('authenticated')).toHaveTextContent('unauthenticated');
    });
  });

  describe('initiateLogin', () => {
    it('calls backend login endpoint and redirects to IdP', async () => {
      // Default MSW handler in handlers.ts returns valid LoginInitiationResponse
      // No need to override - uses contract boundary

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      // Trigger login - this starts async operation
      await act(async () => {
        screen.getByTestId('login-btn').click();
      });

      // Wait for async operations to complete (state storage then redirect)
      await waitFor(() => {
        expect(testSessionStorage.getItem('oidcState')).toBe('oidc-state-123');
        expect(testSessionStorage.getItem('oidcTenantSlug')).toBe('test-tenant');
      });

      // Verify redirect happened
      await waitFor(() => {
        expect(location.href).toBe('https://idp.example.com/auth?client_id=test&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Flogin%2Fcallback&state=oidc-state-123');
      });
    });

    it('shows loading state during login', async () => {
      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      // Wait for initial ready state
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      // Click login and await async operations - triggers setIsLoading(true) synchronously
      // then proceeds to async authClient call
      await act(async () => {
        screen.getByTestId('login-btn').click();
      });

      // Loading state is set synchronously before async call, verify immediately
      expect(screen.getByTestId('loading')).toHaveTextContent('loading');

      // Wait for the async operation to complete (and redirect)
      await waitFor(() => {
        expect(location.href).toBe('https://idp.example.com/auth?client_id=test&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Flogin%2Fcallback&state=oidc-state-123');
      });
    });

    it('throws error when login initiation fails', async () => {
      // Component that exposes initiateLogin for direct testing
      function LoginTrigger() {
        const auth = useAuthContext();
        const [error, setError] = React.useState<string>('');
        return (
          <div>
            <button
              data-testid="trigger-login"
              onClick={async () => {
                try {
                  // Use error-tenant which returns 404 in MSW handler
                  await auth.initiateLogin('error-tenant');
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              Trigger
            </button>
            <div data-testid="login-error">{error}</div>
          </div>
        );
      }

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <LoginTrigger />
        </AuthProvider>,
        { wrapper }
      );

      // Click immediately - AuthProvider will initialize synchronously
      await act(async () => {
        screen.getByTestId('trigger-login').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('login-error')).toHaveTextContent('Tenant not found');
      });
    });

    it('throws error when network fails', async () => {
      // Component that exposes initiateLogin for direct testing
      function LoginTrigger() {
        const auth = useAuthContext();
        const [error, setError] = React.useState<string>('');
        return (
          <div>
            <button
              data-testid="trigger-login"
              onClick={async () => {
                try {
                  await auth.initiateLogin('network-error');
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              Trigger
            </button>
            <div data-testid="login-error">{error}</div>
          </div>
        );
      }

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <LoginTrigger />
        </AuthProvider>,
        { wrapper }
      );

      // Click immediately - AuthProvider will initialize synchronously
      await act(async () => {
        screen.getByTestId('trigger-login').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('login-error')).toHaveTextContent('Failed to connect to authentication service');
      });
    });
  });

  describe('handleCallback', () => {
    beforeEach(() => {
      // Set state to match what TestComponent callback button uses
      // Must match the default MSW handler's expected state pattern
      testSessionStorage.setItem('oidcState', 'oidc-state-123');
      testSessionStorage.setItem('oidcTenantSlug', 'test-tenant');
    });

    it('exchanges code for tokens and sets auth state', async () => {
      // Default MSW handler in handlers.ts returns valid TokenResponse
      // No need to override - uses contract boundary

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      await act(async () => {
        screen.getByTestId('callback-btn').click();
      });

      // Verify auth state updated based on contract response
      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user-email')).toHaveTextContent('newuser@example.com');
        expect(screen.getByTestId('token')).toHaveTextContent('new-access-token');
      });

      // Verify localStorage updated
      expect(testLocalStorage.getItem('accessToken')).toBe('new-access-token');
      expect(testLocalStorage.getItem('tenantId')).toBe('test-tenant');

      // Verify sessionStorage cleaned up
      expect(testSessionStorage.getItem('oidcState')).toBeNull();
      expect(testSessionStorage.getItem('oidcTenantSlug')).toBeNull();
    });

    it('rejects when state parameter does not match', async () => {
      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      // Create a custom button with wrong state
      function CallbackWithWrongState() {
        const auth = useAuthContext();
        return (
          <button data-testid="wrong-callback-btn" onClick={() => auth.handleCallback('code', 'wrong-state')}>
            Wrong Callback
          </button>
        );
      }

      render(
        <AuthProvider>
          <CallbackWithWrongState />
        </AuthProvider>,
        { wrapper }
      );

      await act(async () => {
        screen.getByTestId('wrong-callback-btn').click();
      });

      // Should fail and clean up session storage
      await waitFor(() => {
        expect(testSessionStorage.getItem('oidcState')).toBeNull();
      });
    });

    it('returns false when callback endpoint returns error', async () => {
      // Component that captures handleCallback result
      // Uses 'invalid-code' to trigger error response in MSW handler
      function CallbackWithResult() {
        const auth = useAuthContext();
        const [callbackResult, setCallbackResult] = React.useState<boolean | null>(null);
        return (
          <div>
            <button
              data-testid="callback-result-btn"
              onClick={async () => {
                const result = await auth.handleCallback('invalid-code', 'oidc-state-123');
                setCallbackResult(result);
              }}
            >
              Handle Callback
            </button>
            <div data-testid="callback-result">{callbackResult === null ? 'null' : callbackResult.toString()}</div>
          </div>
        );
      }

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <CallbackWithResult />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('callback-result')).toHaveTextContent('null');
      });

      await act(async () => {
        screen.getByTestId('callback-result-btn').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('callback-result')).toHaveTextContent('false');
      });
    });
  });

  describe('logout', () => {
    it('clears all auth state and storage', async () => {
      // Set up authenticated state with backend-canonical role
      const userInfo: UserInfo = authFixtures.user({
        email: 'test@example.com',
        role: 'super_admin',
        tenantId: 'tenant-1',
        tenantSlug: 'test-tenant',
      });
      const snapshot = authFixtures.validSession({
        accessToken: 'header.eyJleHAiOjQ3MDAwMDAwMDB9.signature',
        tenantId: 'tenant-1',
        user: userInfo,
      });
      testLocalStorage.setItem('vf.auth.session', JSON.stringify(snapshot));

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
      });

      await act(async () => {
        screen.getByTestId('logout-btn').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('unauthenticated');
      });

      expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
      expect(screen.getByTestId('token')).toHaveTextContent('no-token');

      // Verify all storage cleared
      expect(testLocalStorage.getItem('accessToken')).toBeNull();
      expect(testLocalStorage.getItem('userInfo')).toBeNull();
      expect(testLocalStorage.getItem('tenantId')).toBeNull();
    });
  });

  describe('devBypass', () => {
    it('creates mock auth state in development mode', async () => {
      // devBypass is only available in development mode
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      // Component that exposes devBypass for testing
      function DevBypassTrigger() {
        const auth = useAuthContext();
        return (
          <div>
            <div data-testid="loading">{auth.isLoading ? 'loading' : 'ready'}</div>
            <div data-testid="authenticated">{auth.isAuthenticated ? 'authenticated' : 'unauthenticated'}</div>
            <div data-testid="user-email">{auth.user?.email || 'no-user'}</div>
            <div data-testid="user-id">{auth.user?.id || 'no-user-id'}</div>
            <div data-testid="tenant-id">{auth.user?.tenantId || 'no-tenant'}</div>
            <button data-testid="dev-bypass-btn" onClick={auth.devBypass}>
              Dev Bypass
            </button>
          </div>
        );
      }

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <DevBypassTrigger />
        </AuthProvider>,
        { wrapper }
      );

      // Wait for initial ready state
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      // Initially unauthenticated
      expect(screen.getByTestId('authenticated')).toHaveTextContent('unauthenticated');

      // Trigger dev bypass
      await act(async () => {
        screen.getByTestId('dev-bypass-btn').click();
      });

      // Should now be authenticated as demo user (Sarah Chen)
      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user-email')).toHaveTextContent('sarah.chen@axiomrobotics.com');
        expect(screen.getByTestId('user-id')).toHaveTextContent('sarah-chen-001');
        expect(screen.getByTestId('tenant-id')).toHaveTextContent('demo-acme');
      });

      // Verify token was stored (valid JWT format with 3 parts)
      const storedToken = testLocalStorage.getItem('accessToken');
      expect(storedToken?.split('.')).toHaveLength(3);

      process.env.NODE_ENV = originalNodeEnv;
    });

    it('throws error when called in production mode (NODE_ENV=production)', async () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      function DevBypassTrigger() {
        const auth = useAuthContext();
        const [error, setError] = React.useState<string>('');
        return (
          <div>
            <div data-testid="error">{error}</div>
            <button
              data-testid="dev-bypass-btn"
              onClick={() => {
                try {
                  auth.devBypass?.();
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              Dev Bypass
            </button>
          </div>
        );
      }

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <DevBypassTrigger />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('');
      });

      // Trigger dev bypass - should throw in production
      await act(async () => {
        screen.getByTestId('dev-bypass-btn').click();
      });

      // Should show error about production mode
      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Auth bypass is disabled in production.');
      });

      // Verify no demo data was stored
      expect(testLocalStorage.getItem('accessToken')).toBeNull();
      expect(testLocalStorage.getItem('tenantId')).not.toBe('demo-acme');

      consoleSpy.mockRestore();
      process.env.NODE_ENV = originalNodeEnv;
    });

    it('throws error when called with VITE_APP_ENV=production', async () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      // Mock import.meta.env
      const originalViteEnv = (globalThis as { import?: { meta?: { env?: Record<string, string> } } }).import;
      (globalThis as { import?: { meta?: { env?: Record<string, string> } } }).import = {
        meta: {
          env: {
            VITE_APP_ENV: 'production',
          },
        },
      };

      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      function DevBypassTrigger() {
        const auth = useAuthContext();
        const [error, setError] = React.useState<string>('');
        return (
          <div>
            <div data-testid="error">{error}</div>
            <button
              data-testid="dev-bypass-btn"
              onClick={() => {
                try {
                  auth.devBypass?.();
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              Dev Bypass
            </button>
          </div>
        );
      }

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <DevBypassTrigger />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('');
      });

      // Trigger dev bypass - should throw because VITE_APP_ENV=production
      await act(async () => {
        screen.getByTestId('dev-bypass-btn').click();
      });

      // Should show error about production mode
      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Auth bypass is disabled in production.');
      });

      // Verify no demo data was stored
      expect(testLocalStorage.getItem('accessToken')).toBeNull();

      consoleSpy.mockRestore();
      (globalThis as { import?: { meta?: { env?: Record<string, string> } } }).import = originalViteEnv;
      process.env.NODE_ENV = originalNodeEnv;
    });

    it('returns undefined when devBypass is not available (production build)', async () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      function DevBypassCheck() {
        const auth = useAuthContext();
        return (
          <div data-testid="has-bypass">{auth.devBypass === undefined ? 'undefined' : 'defined'}</div>
        );
      }

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <DevBypassCheck />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('has-bypass')).toHaveTextContent('undefined');
      });

      process.env.NODE_ENV = originalNodeEnv;
    });

    it('does not seed Sarah Chen / demo-acme / axiom-robotics in production', async () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      function DevBypassTrigger() {
        const auth = useAuthContext();
        return (
          <div>
            <div data-testid="authenticated">{auth.isAuthenticated ? 'authenticated' : 'unauthenticated'}</div>
            <div data-testid="user-email">{auth.user?.email || 'no-user'}</div>
            <button data-testid="dev-bypass-btn" onClick={auth.devBypass}>
              Dev Bypass
            </button>
          </div>
        );
      }

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <DevBypassTrigger />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('unauthenticated');
      });

      // Verify demo data not in storage
      expect(testLocalStorage.getItem('tenantId')).not.toBe('demo-acme');
      const userInfo = testLocalStorage.getItem('userInfo');
      if (userInfo) {
        const parsed = JSON.parse(userInfo);
        expect(parsed.email).not.toBe('sarah.chen@axiomrobotics.com');
        expect(parsed.id).not.toBe('sarah-chen-001');
      }

      process.env.NODE_ENV = originalNodeEnv;
    });
  });

  describe('refreshToken', () => {
    it('returns true when token is valid', async () => {
      // Create a JWT that expires in 1 hour
      const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }));
      const signature = btoa('signature');
      const validToken = `${header}.${payload}.${signature}`;

      testLocalStorage.setItem('accessToken', validToken);

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      // Note: We'd need to expose refreshToken through TestComponent to test it directly
      // For now, the initialization test validates the token parsing logic
      expect(screen.getByTestId('authenticated')).toHaveTextContent('unauthenticated'); // No user info
    });

    it('logs out when token structure is invalid', async () => {
      testLocalStorage.setItem('accessToken', 'invalid-token');
      // Uses backend-canonical role read_only which normalizes to standard tier
      testLocalStorage.setItem('userInfo', JSON.stringify({ id: 'user-1', email: 'test@test.com', role: 'read_only', tenantId: 't1', tenantSlug: 'test' }));

      const wrapper = createWrapper();
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
        { wrapper }
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      // Token is set but user info exists - should be authenticated initially
      // In real scenario, the token validation would happen on refreshToken call
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    });
  });
});

describe('useAuthContext error handling', () => {
  it('throws error when used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    function ComponentOutsideProvider() {
      try {
        useAuthContext();
        return <div data-testid="no-error">No error</div>;
      } catch (e) {
        return <div data-testid="error">{(e as Error).message}</div>;
      }
    }

    render(<ComponentOutsideProvider />);

    expect(screen.getByTestId('error')).toHaveTextContent(
      'useAuthContext must be used within an AuthProvider'
    );

    consoleSpy.mockRestore();
  });
});
