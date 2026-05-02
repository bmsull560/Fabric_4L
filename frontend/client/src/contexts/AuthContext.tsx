/**
 * Auth Context — Contract-Based OIDC Authentication State Management
 *
 * Architecture: AuthContext → AuthClient (contract boundary) → HTTP API → IdP
 *
 * Manages:
 * - JWT token storage (memory + localStorage for refresh)
 * - User info (id, email, role, tenant)
 * - Login/logout flows via AuthClient
 * - Token refresh via AuthClient
 * - 401 redirect handling
 */

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useUserTierStore } from '@/stores/userTierStore';
import { createFeatureLogger } from '@/lib/telemetry';
import { authClient } from '../services/authClient';
import { sessionService } from '../services/sessionService';
import { type UserInfo, AuthError, AuthErrorCategory } from '../schemas/auth';

// Re-export UserInfo for backward compatibility
export type { UserInfo } from '../schemas/auth';

interface AuthContextType {
  // State
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserInfo | null;
  accessToken: string | null;

  // Actions
  initiateLogin: (tenantSlug: string) => Promise<void>;
  handleCallback: (code: string, state: string) => Promise<boolean>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  /** Development-only bypass for testing authenticated flows */
  devBypass?: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
const log = createFeatureLogger('auth-context');

// Auth state machine states
type AuthState = 'idle' | 'loading' | 'authenticated' | 'error';

interface AuthStateMachine {
  state: AuthState;
  user: UserInfo | null;
  accessToken: string | null;
  error: AuthError | null;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Use state machine pattern for clear transitions
  const [authState, setAuthState] = useState<AuthStateMachine>({
    state: 'idle',
    user: null,
    accessToken: null,
    error: null,
  });
  const [isLoading, setIsLoading] = useState(true); // Separate loading for UI

  // Initialize auth state from storage on mount
  useEffect(() => {
    const initAuth = async () => {
      const snapshot = sessionService.getSessionSnapshot();

      if (snapshot) {
        const isValid = sessionService.isSessionValid(snapshot);
        if (isValid) {
          setAuthState({
            state: 'authenticated',
            user: snapshot.user,
            accessToken: snapshot.accessToken,
            error: null,
          });
          // Synchronize restored role with userTierStore
          useUserTierStore.getState().setUserRole(snapshot.user.role);
        } else {
          sessionService.clearSession();
          setAuthState({
            state: 'idle',
            user: null,
            accessToken: null,
            error: null,
          });
        }
      } else {
        sessionService.clearSession();
        setAuthState({
          state: 'idle',
          user: null,
          accessToken: null,
          error: null,
        });
      }

      setIsLoading(false);
    };

    void initAuth();
  }, []);

  /**
   * Step 1: Initiate OIDC login flow
   * Delegates to AuthClient for contract-validated exchange
   */
  const initiateLogin = useCallback(async (tenantSlug: string) => {
    // Set loading state synchronously before async operations
    setIsLoading(true);
    setAuthState(prev => ({ ...prev, state: 'loading' }));

    try {
      const callbackUrl = sessionService.getCallbackUrl();
      const result = await authClient.initiateLogin(tenantSlug, callbackUrl);

      const postLoginRedirect = sessionService.consumePostLoginRedirect() ?? undefined;
      sessionService.persistOidcFlowState({
        state: result.state,
        tenantSlug,
        postLoginRedirect,
      });

      // Redirect to IdP (this will unload the page)
      sessionService.redirectTo(result.authorization_url);
    } catch (error) {
      setIsLoading(false);
      log.error('Login initiation failed', {
        tenantId: tenantSlug,
        authPhase: 'initiate-login',
        route: typeof window !== 'undefined' ? window.location.pathname : undefined,
        error: error instanceof Error ? error.message : String(error),
      });
      setAuthState(prev => ({
        ...prev,
        state: 'error',
        error: error instanceof AuthError ? error : new AuthError(
          String(error),
          AuthErrorCategory.AUTHENTICATION
        ),
      }));
      throw error;
    }
  }, []);

  /**
   * Step 2: Handle OIDC callback
   * Delegates token exchange to AuthClient with schema validation
   */
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

      // Use AuthClient for contract-validated token exchange
      const tokenResponse = await authClient.exchangeCodeForTokens(code, state);

      const tenantSlug = oidcFlow.tenantSlug || 'default';

      // Build validated user info
      const userInfo: UserInfo = {
        id: tokenResponse.user_id,
        email: tokenResponse.email,
        role: tokenResponse.role,
        tenantId: tenantSlug,
        tenantSlug,
      };

      // Persist session via AuthClient
      sessionService.persistSession(tokenResponse.access_token, userInfo, tenantSlug);

      // Update auth state machine
      setAuthState({
        state: 'authenticated',
        user: userInfo,
        accessToken: tokenResponse.access_token,
        error: null,
      });

      // Synchronize role with userTierStore
      useUserTierStore.getState().setUserRole(tokenResponse.role);

      // Clean up session storage
      sessionService.clearOidcState();

      return true;
    } catch (error) {
      sessionService.clearOidcState();

      // Categorize error for better UX
      let authError: AuthError;
      if (error instanceof AuthError) {
        authError = error;
      } else {
        const errorMessage = String(error).toLowerCase();
        if (errorMessage.includes('expired') || errorMessage.includes('timeout')) {
          authError = new AuthError(
            'Session expired. Please try logging in again.',
            AuthErrorCategory.SESSION_EXPIRED
          );
        } else if (errorMessage.includes('state') || errorMessage.includes('csrf')) {
          authError = new AuthError(
            'Invalid session state. Please try logging in again.',
            AuthErrorCategory.AUTHENTICATION
          );
        } else if (errorMessage.includes('provider') || errorMessage.includes('oidc')) {
          authError = new AuthError(
            'SSO provider error. Please contact your administrator.',
            AuthErrorCategory.SSO_PROVIDER_ERROR
          );
        } else {
          const message = error ? String(error).trim() : '';
          authError = new AuthError(
            message && message !== 'undefined' && message !== 'null'
              ? message
              : 'Authentication failed. Please try again.',
            AuthErrorCategory.AUTHENTICATION
          );
        }
      }

      log.error('Callback authentication failed', {
        route: typeof window !== 'undefined' ? window.location.pathname : undefined,
        authPhase: 'callback',
        traceId: authError.statusCode ? String(authError.statusCode) : null,
        errorCode: authError.category,
        message: authError.message,
      });

      setAuthState({
        state: 'error',
        user: null,
        accessToken: null,
        error: authError,
      });

      return false;
    }
  }, []);

  /**
   * Logout — clear all auth state via AuthClient
   */
  const logout = useCallback(() => {
    sessionService.clearSession();
    sessionService.clearOidcState();

    setAuthState({
      state: 'idle',
      user: null,
      accessToken: null,
      error: null,
    });

    // Reset userTierStore to default state
    const tierStore = useUserTierStore.getState();
    tierStore.setTier('standard');
    tierStore.disableAdvancedMode();

    // Redirect to login
    sessionService.redirectToLogin();
  }, []);

  /**
   * Token refresh — delegates to AuthClient
   */
  const refreshToken = useCallback(async (): Promise<boolean> => {
    const snapshot = sessionService.getSessionSnapshot();
    const isValid = sessionService.isSessionValid(snapshot);

    if (isValid) {
      const restoredSnapshot = sessionService.getSessionSnapshot();
      if (restoredSnapshot) {
        setAuthState({
          state: 'authenticated',
          user: restoredSnapshot.user,
          accessToken: restoredSnapshot.accessToken,
          error: null,
        });
        useUserTierStore.getState().setUserRole(restoredSnapshot.user.role);
      }
    } else {
      // Session expired or invalid, clear state
      setAuthState({
        state: 'idle',
        user: null,
        accessToken: null,
        error: null,
      });
    }

    return isValid;
  }, []);

  /**
   * Development bypass — allows instant authentication for testing
   * Only available in development environment
   */
  const devBypass = useCallback(() => {
    if (process.env.NODE_ENV !== 'development') {
      log.warn('devBypass is only available in development mode', {
        authPhase: 'dev-bypass',
      });
      return;
    }
    // Set mock authenticated state for development testing
    const mockUser: UserInfo = {
      id: 'dev-user-123',
      email: 'dev@example.com',
      role: 'admin',
      tenantId: 'dev-tenant',
      tenantSlug: 'dev',
    };
    // Generate a valid JWT-format token so refreshToken() doesn't clear it
    const payload = {
      exp: Math.floor(Date.now() / 1000) + 3600,
      iat: Math.floor(Date.now() / 1000),
      sub: mockUser.id,
      tenant_id: mockUser.tenantId,
    };
    const mockToken = `header.${btoa(JSON.stringify(payload))}.signature`;
    sessionService.persistSession(mockToken, mockUser, 'dev-tenant');
    setAuthState({
      state: 'authenticated',
      user: mockUser,
      accessToken: mockToken,
      error: null,
    });
    // Synchronize role with userTierStore
    useUserTierStore.getState().setUserRole('admin');
  }, []);

  const value: AuthContextType = {
    isAuthenticated: authState.state === 'authenticated',
    isLoading,
    user: authState.user,
    accessToken: authState.accessToken,
    initiateLogin,
    handleCallback,
    logout,
    refreshToken,
    devBypass: process.env.NODE_ENV === 'development' ? devBypass : undefined,
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
