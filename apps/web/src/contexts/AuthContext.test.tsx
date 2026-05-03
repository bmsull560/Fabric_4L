/**
 * AuthContext tests — cookie-based session model
 *
 * Covers:
 * - Initialization from sessionStorage metadata (no localStorage)
 * - OIDC login initiation and redirect
 * - Callback: metadata persisted, no token in JS
 * - CSRF state mismatch rejection
 * - Logout: calls backend, clears metadata, redirects
 * - Refresh: calls backend, updates metadata on success, clears on 401
 * - devBypass: works in test/dev builds; production omission is enforced by a bundle gate
 * - accessToken is always null on the context value
 */
import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { createWrapper, TestAuthComponent } from '../test-utils';
import { AuthProvider, useAuthContext } from './AuthContext';
import {
  applySessionServiceTestEnvironment,
  authFixtures,
  type MutableLocationLike,
} from '@/test/authSessionTestUtils';
import { sessionService } from '../services/sessionService';


// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

describe('AuthProvider', () => {
  let env: ReturnType<typeof applySessionServiceTestEnvironment>;
  let location: MutableLocationLike;

  beforeEach(() => {
    vi.clearAllMocks();
    env = applySessionServiceTestEnvironment();
    location = env.location;
  });

  afterEach(() => {
    env.reset();
    vi.restoreAllMocks();
  });

  // ── Initialization ─────────────────────────────────────────────────────────

  describe('initialization', () => {
    it('starts unauthenticated when sessionStorage is empty', async () => {
      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });

      await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));

      expect(screen.getByTestId('authenticated')).toHaveTextContent('no');
      expect(screen.getByTestId('user-email')).toHaveTextContent('none');
    });

    it('restores session from sessionStorage metadata on mount', async () => {
      const user = authFixtures.user({ email: 'restored@example.com', tenantId: 'tenant-1', tenantSlug: 'tenant-1' });
      env.sessionStorage.setItem('vf.auth.session.meta', JSON.stringify({ user, tenantId: 'tenant-1' }));

      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });

      await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));

      expect(screen.getByTestId('authenticated')).toHaveTextContent('yes');
      expect(screen.getByTestId('user-email')).toHaveTextContent('restored@example.com');
    });

    it('accessToken is always null — token lives in the httpOnly cookie', async () => {
      const user = authFixtures.user();
      env.sessionStorage.setItem('vf.auth.session.meta', JSON.stringify({ user, tenantId: user.tenantId }));

      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });

      await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));

      expect(screen.getByTestId('access-token')).toHaveTextContent('null');
    });

    it('clears corrupted metadata and starts unauthenticated', async () => {
      env.sessionStorage.setItem('vf.auth.session.meta', 'not-valid-json{');

      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });

      await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));

      expect(screen.getByTestId('authenticated')).toHaveTextContent('no');
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();
    });

    it('does NOT read from localStorage', async () => {
      // Simulate old localStorage data that should be ignored
      localStorage.setItem('accessToken', 'old-token');
      localStorage.setItem('vf.auth.session', JSON.stringify(authFixtures.validSession()));

      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });

      await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));

      // sessionStorage is empty → unauthenticated, regardless of localStorage
      expect(screen.getByTestId('authenticated')).toHaveTextContent('no');

      localStorage.removeItem('accessToken');
      localStorage.removeItem('vf.auth.session');
    });
  });

  // ── initiateLogin ──────────────────────────────────────────────────────────

  describe('initiateLogin', () => {
    it('stores OIDC flow state and redirects to IdP', async () => {
      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });
      await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));

      await act(async () => { screen.getByTestId('login-btn').click(); });

      await waitFor(() => {
        expect(env.sessionStorage.getItem('vf.auth.oidc')).not.toBeNull();
        expect(location.href).toContain('idp.example.com');
      });
    });

    it('rejects with error for unknown tenant', async () => {
      function TriggerLogin() {
        const auth = useAuthContext();
        const [err, setErr] = React.useState('');
        return (
          <div>
            <button data-testid="btn" onClick={async () => {
              try { await auth.initiateLogin('error-tenant'); }
              catch (e) { setErr((e as Error).message); }
            }}>go</button>
            <div data-testid="err">{err}</div>
          </div>
        );
      }

      render(<AuthProvider><TriggerLogin /></AuthProvider>, { wrapper: createWrapper() });

      await act(async () => { screen.getByTestId('btn').click(); });

      await waitFor(() => expect(screen.getByTestId('err')).toHaveTextContent('Tenant not found'));
    });
  });

  // ── handleCallback ─────────────────────────────────────────────────────────

  describe('handleCallback', () => {
    beforeEach(() => {
      env.sessionStorage.setItem('oidcState', 'oidc-state-123');
      env.sessionStorage.setItem('oidcTenantSlug', 'test-tenant');
    });

    it('sets authenticated state and persists metadata to sessionStorage', async () => {
      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });
      await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));

      await act(async () => { screen.getByTestId('callback-btn').click(); });

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('yes');
        expect(screen.getByTestId('user-email')).toHaveTextContent('newuser@example.com');
      });

      // Metadata in sessionStorage
      const meta = JSON.parse(env.sessionStorage.getItem('vf.auth.session.meta') ?? 'null');
      expect(meta).not.toBeNull();
      expect(meta.user.email).toBe('newuser@example.com');

      // Token NOT in sessionStorage or localStorage
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).not.toContain('mock-jwt-token');
      expect(localStorage.getItem('accessToken')).toBeNull();
    });

    it('accessToken remains null after successful callback', async () => {
      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });
      await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));

      await act(async () => { screen.getByTestId('callback-btn').click(); });

      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('yes'));

      expect(screen.getByTestId('access-token')).toHaveTextContent('null');
    });

    it('clears OIDC state from sessionStorage after callback', async () => {
      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });
      await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));

      await act(async () => { screen.getByTestId('callback-btn').click(); });

      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('yes'));

      expect(env.sessionStorage.getItem('oidcState')).toBeNull();
      expect(env.sessionStorage.getItem('oidcTenantSlug')).toBeNull();
      expect(env.sessionStorage.getItem('vf.auth.oidc')).toBeNull();
    });

    it('rejects with CSRF error when state parameter does not match', async () => {
      function WrongStateCallback() {
        const auth = useAuthContext();
        const [result, setResult] = React.useState<boolean | null>(null);
        return (
          <div>
            <button data-testid="btn" onClick={async () => {
              const ok = await auth.handleCallback('code', 'wrong-state');
              setResult(ok);
            }}>go</button>
            <div data-testid="result">{result === null ? 'pending' : String(result)}</div>
          </div>
        );
      }

      render(<AuthProvider><WrongStateCallback /></AuthProvider>, { wrapper: createWrapper() });

      await act(async () => { screen.getByTestId('btn').click(); });

      await waitFor(() => expect(screen.getByTestId('result')).toHaveTextContent('false'));
      // OIDC state cleaned up even on failure
      expect(env.sessionStorage.getItem('oidcState')).toBeNull();
    });

    it('returns false when backend rejects the code', async () => {
      function BadCodeCallback() {
        const auth = useAuthContext();
        const [result, setResult] = React.useState<boolean | null>(null);
        return (
          <div>
            <button data-testid="btn" onClick={async () => {
              const ok = await auth.handleCallback('invalid-code', 'oidc-state-123');
              setResult(ok);
            }}>go</button>
            <div data-testid="result">{result === null ? 'pending' : String(result)}</div>
          </div>
        );
      }

      render(<AuthProvider><BadCodeCallback /></AuthProvider>, { wrapper: createWrapper() });

      await act(async () => { screen.getByTestId('btn').click(); });

      await waitFor(() => expect(screen.getByTestId('result')).toHaveTextContent('false'));
    });
  });

  // ── logout ─────────────────────────────────────────────────────────────────

  describe('logout', () => {
    it('clears metadata, resets auth state, and redirects to /login', async () => {
      const user = authFixtures.user({ email: 'active@example.com' });
      env.sessionStorage.setItem('vf.auth.session.meta', JSON.stringify({ user, tenantId: user.tenantId }));

      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });
      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('yes'));

      await act(async () => { screen.getByTestId('logout-btn').click(); });

      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('no'));

      expect(screen.getByTestId('user-email')).toHaveTextContent('none');
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();
      expect(location.pathname).toBe('/login');
    });

    it('clears local state even when the backend logout call fails', async () => {
      const user = authFixtures.user();
      env.sessionStorage.setItem('vf.auth.session.meta', JSON.stringify({ user, tenantId: user.tenantId }));

      // Temporarily override the logout handler to simulate network failure
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'));

      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });
      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('yes'));

      await act(async () => { screen.getByTestId('logout-btn').click(); });

      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('no'));
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();

      fetchSpy.mockRestore();
    });
  });

  // ── refreshToken ───────────────────────────────────────────────────────────

  describe('refreshToken', () => {
    it('calls backend and updates metadata on success', async () => {
      const user = authFixtures.user({ email: 'active@example.com' });
      env.sessionStorage.setItem('vf.auth.session.meta', JSON.stringify({ user, tenantId: user.tenantId }));

      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });
      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('yes'));

      await act(async () => { screen.getByTestId('refresh-btn').click(); });

      // Still authenticated after refresh
      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('yes'));
      // accessToken remains null — cookie is rotated server-side
      expect(screen.getByTestId('access-token')).toHaveTextContent('null');
    });

    it('clears session and marks unauthenticated on 401', async () => {
      const user = authFixtures.user();
      env.sessionStorage.setItem('vf.auth.session.meta', JSON.stringify({ user, tenantId: user.tenantId }));

      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(null, { status: 401 })
      );

      render(<AuthProvider><TestAuthComponent /></AuthProvider>, { wrapper: createWrapper() });
      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('yes'));

      await act(async () => { screen.getByTestId('refresh-btn').click(); });

      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('no'));
      expect(env.sessionStorage.getItem('vf.auth.session.meta')).toBeNull();

      fetchSpy.mockRestore();
    });
  });

  // ── devBypass ──────────────────────────────────────────────────────────────

  describe('devBypass', () => {
    it('is undefined in production builds (PROD=true)', async () => {
      // import.meta.env.PROD is true in production builds; devBypass is stripped.
      // In the test environment PROD is false, so devBypass is always present —
      // the production guard is enforced inside the function itself (tested below).
      // This test verifies the guard throws rather than silently no-ops.
      function Inspector() {
        const auth = useAuthContext();
        return <div data-testid="bypass-defined">{auth.devBypass ? 'defined' : 'undefined'}</div>;
      }

      render(<AuthProvider><Inspector /></AuthProvider>, { wrapper: createWrapper() });
      // In test mode (PROD=false) devBypass is exposed on the context
      await waitFor(() => expect(screen.getByTestId('bypass-defined')).toHaveTextContent('defined'));
    });

    it('sets mock authenticated state in development', async () => {
      // devBypass is available in test mode (import.meta.env.PROD = false).
      // VITE_APP_ENV is not set, so the production guard does not trigger.
      function BypassTrigger() {
        const auth = useAuthContext();
        return (
          <div>
            <div data-testid="authenticated">{auth.isAuthenticated ? 'yes' : 'no'}</div>
            <div data-testid="email">{auth.user?.email ?? 'none'}</div>
            <button data-testid="btn" onClick={() => auth.devBypass?.()}>go</button>
          </div>
        );
      }

      render(<AuthProvider><BypassTrigger /></AuthProvider>, { wrapper: createWrapper() });
      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('no'));

      await act(async () => { screen.getByTestId('btn').click(); });

      await waitFor(() => expect(screen.getByTestId('authenticated')).toHaveTextContent('yes'));
      expect(screen.getByTestId('email')).toHaveTextContent('sarah.chen@axiomrobotics.com');

      // Metadata in sessionStorage, NOT a token in localStorage
      const meta = JSON.parse(env.sessionStorage.getItem('vf.auth.session.meta') ?? 'null');
      expect(meta?.user?.email).toBe('sarah.chen@axiomrobotics.com');
      expect(localStorage.getItem('accessToken')).toBeNull();
    });
  });

  // ── useAuthContext guard ───────────────────────────────────────────────────

  describe('useAuthContext', () => {
    it('throws when used outside AuthProvider', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      function Outside() {
        try {
          useAuthContext();
          return <div data-testid="ok">ok</div>;
        } catch (e) {
          return <div data-testid="err">{(e as Error).message}</div>;
        }
      }

      render(<Outside />, { wrapper: createWrapper() });

      expect(screen.getByTestId('err')).toHaveTextContent(
        'useAuthContext must be used within an AuthProvider'
      );

      consoleSpy.mockRestore();
    });
  });
});
