/**
 * Auth Context — OIDC authentication state management
 *
 * Architecture: AuthContext → AuthClient (contract boundary) → HTTP API → IdP
 *
 * Token model:
 *   The access token lives exclusively in the httpOnly `vf_session` cookie set
 *   by the backend. This context never holds or exposes the token. It manages:
 *     - User identity metadata (id, email, role, tenant) from sessionStorage
 *     - Login / callback / logout / refresh flows via AuthClient
 *     - 401 redirect handling
 */

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useUserTierStore } from '@/stores/userTierStore';
import { useAccountContextStore } from '@/stores/accountContextStore';
import { createFeatureLogger } from '@/lib/telemetry';
import { authClient } from '../services/authClient';
import { sessionService } from '../services/sessionService';
import { type UserInfo, AuthError, AuthErrorCategory } from '../schemas/auth';

export type { UserInfo } from '../schemas/auth';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserInfo | null;
  /** @deprecated Token is in the httpOnly cookie; always null. */
  accessToken: null;

  initiateLogin: (tenantSlug: string) => Promise<void>;
  handleCallback: (code: string, state: string) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  /** Development-only bypass — undefined in production builds */
  devBypass?: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
const log = createFeatureLogger('auth-context');

type AuthState = 'idle' | 'loading' | 'authenticated' | 'error';

interface AuthStateMachine {
  state: AuthState;
  user: UserInfo | null;
  error: AuthError | null;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authState, setAuthState] = useState<AuthStateMachine>({
    state: 'idle',
    user: null,
    error: null,
  });
  const [isLoading, setIsLoading] = useState(true);

  // Restore session metadata from sessionStorage on mount
  useEffect(() => {
    const meta = sessionService.getSessionMeta();
    if (meta) {
      setAuthState({ state: 'authenticated', user: meta.user, error: null });
      useUserTierStore.getState().setUserRole(meta.user.role);
    } else {
      setAuthState({ state: 'idle', user: null, error: null });
    }
    setIsLoading(false);
  }, []);

  const initiateLogin = useCallback(async (tenantSlug: string) => {
    setIsLoading(true);
    setAuthState(prev => ({ ...prev, state: 'loading' }));

    try {
      const callbackUrl = sessionService.getCallbackUrl();
      const result = await authClient.initiateLogin(tenantSlug, callbackUrl);

      const postLoginRedirect = sessionService.consumePostLoginRedirect() ?? undefined;
      sessionService.persistOidcFlowState({ state: result.state, tenantSlug, postLoginRedirect });

      sessionService.redirectTo(result.authorization_url);
    } catch (error) {
      setIsLoading(false);
      log.error('Login initiation failed', {
        tenantId: tenantSlug,
        authPhase: 'initiate-login',
        error: error instanceof Error ? error.message : String(error),
      });
      setAuthState(prev => ({
        ...prev,
        state: 'error',
        error: error instanceof AuthError
          ? error
          : new AuthError(String(error), AuthErrorCategory.AUTHENTICATION),
      }));
      throw error;
    }
  }, []);

  const handleCallback = useCallback(async (code: string, state: string): Promise<boolean> => {
    setAuthState(prev => ({ ...prev, state: 'loading' }));

    try {
      const oidcFlow = sessionService.getOidcFlowState();
      if (!oidcFlow || state !== oidcFlow.state) {
        throw new AuthError(
          'Invalid state parameter - possible CSRF attack',
          AuthErrorCategory.AUTHENTICATION
        );
      }

      const tokenResponse = await authClient.exchangeCodeForTokens(code, state);
      const tenantSlug = oidcFlow.tenantSlug || 'default';

      const userInfo: UserInfo = {
        id: tokenResponse.user_id,
        email: tokenResponse.email,
        role: tokenResponse.role,
        tenantId: tenantSlug,
        tenantSlug,
      };

      // Persist only non-secret metadata; token is in the httpOnly cookie
      sessionService.persistSessionMeta(userInfo, tenantSlug);

      setAuthState({ state: 'authenticated', user: userInfo, error: null });
      useUserTierStore.getState().setUserRole(tokenResponse.role);
      sessionService.clearOidcState();

      return true;
    } catch (error) {
      sessionService.clearOidcState();

      let authError: AuthError;
      if (error instanceof AuthError) {
        authError = error;
      } else {
        const msg = String(error).toLowerCase();
        if (msg.includes('expired') || msg.includes('timeout')) {
          authError = new AuthError('Session expired. Please try logging in again.', AuthErrorCategory.SESSION_EXPIRED);
        } else if (msg.includes('state') || msg.includes('csrf')) {
          authError = new AuthError('Invalid session state. Please try logging in again.', AuthErrorCategory.AUTHENTICATION);
        } else if (msg.includes('provider') || msg.includes('oidc')) {
          authError = new AuthError('SSO provider error. Please contact your administrator.', AuthErrorCategory.SSO_PROVIDER_ERROR);
        } else {
          const clean = error ? String(error).trim() : '';
          authError = new AuthError(
            clean && clean !== 'undefined' && clean !== 'null'
              ? clean
              : 'Authentication failed. Please try again.',
            AuthErrorCategory.AUTHENTICATION
          );
        }
      }

      log.error('Callback authentication failed', {
        authPhase: 'callback',
        errorCode: authError.category,
        message: authError.message,
      });

      setAuthState({ state: 'error', user: null, error: authError });
      return false;
    }
  }, []);

  /**
   * Logout: clears local metadata and calls the backend to expire the cookie.
   */
  const logout = useCallback(async () => {
    await authClient.logout();

    setAuthState({ state: 'idle', user: null, error: null });

    const tierStore = useUserTierStore.getState();
    tierStore.setTier('standard');
    tierStore.disableAdvancedMode();

    sessionService.redirectToLogin();
  }, []);

  /**
   * Refresh: calls the backend to rotate the session cookie.
   * On 401 the session is cleared and the user is considered logged out.
   */
  const refreshToken = useCallback(async (): Promise<boolean> => {
    const valid = await authClient.refreshToken();

    if (valid) {
      const meta = sessionService.getSessionMeta();
      if (meta) {
        setAuthState({ state: 'authenticated', user: meta.user, error: null });
        useUserTierStore.getState().setUserRole(meta.user.role);
      }
    } else {
      setAuthState({ state: 'idle', user: null, error: null });
    }

    return valid;
  }, []);

  /**
   * Development bypass — instant mock authentication for local testing.
   * Blocked in production by NODE_ENV and VITE_APP_ENV checks.
   */
  const devBypass = useCallback(() => {
    const nodeEnv = process.env.NODE_ENV;
    const appEnv = (import.meta.env?.VITE_APP_ENV ?? import.meta.env?.APP_ENV ?? nodeEnv) as string | undefined;
    const bypassFlag = (import.meta.env?.VITE_AUTH_BYPASS ?? 'false') as string;

    const isProductionLike = nodeEnv === 'production' || appEnv === 'production' || appEnv === 'prod';
    const isBypassExplicitlyEnabled = bypassFlag === 'true' || bypassFlag === '1';

    if (isProductionLike) {
      log.error('Auth bypass blocked in production environment', { authPhase: 'dev-bypass', nodeEnv, appEnv });
      throw new AuthError('Auth bypass is disabled in production.', AuthErrorCategory.AUTHENTICATION);
    }

    const isDevLike = nodeEnv === 'development' || nodeEnv === 'test';
    if (!isDevLike && !isBypassExplicitlyEnabled) {
      log.warn('devBypass is only available in development/test mode unless VITE_AUTH_BYPASS is explicitly enabled', {
        authPhase: 'dev-bypass',
        nodeEnv,
        bypassFlag,
      });
      return;
    }

    const mockUser: UserInfo = {
      id: 'sarah-chen-001',
      email: 'sarah.chen@axiomrobotics.com',
      role: 'admin',
      tenantId: 'demo-acme',
      tenantSlug: 'acme',
    };

    sessionService.persistSessionMeta(mockUser, 'demo-acme');
    setAuthState({ state: 'authenticated', user: mockUser, error: null });
    useUserTierStore.getState().setUserRole('admin');
    useAccountContextStore.getState().setSelectedAccountId('axiom-robotics');
  }, []);

  const value: AuthContextType = {
    isAuthenticated: authState.state === 'authenticated',
    isLoading,
    user: authState.user,
    accessToken: null,
    initiateLogin,
    handleCallback,
    logout,
    refreshToken,
    // Expose devBypass in non-production builds (dev + test).
    // The function itself enforces the production guard at call time.
    devBypass: import.meta.env.PROD ? undefined : devBypass,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}
