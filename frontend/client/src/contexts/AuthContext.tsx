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
import { authClient, AuthClient } from '../services/authClient';
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
  devBypass?: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

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
    const initAuth = () => {
      const session = authClient.getCurrentSession();
      const storedToken = localStorage.getItem('accessToken');

      if (storedToken && session) {
        setAuthState({
          state: 'authenticated',
          user: session,
          accessToken: storedToken,
          error: null,
        });

        // Synchronize restored role with userTierStore
        useUserTierStore.getState().setUserRole(session.role);
      } else {
        // Clear any partial/invalid data
        authClient.clearSession();
        setAuthState({
          state: 'idle',
          user: null,
          accessToken: null,
          error: null,
        });
      }

      setIsLoading(false);
    };

    initAuth();
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
      const callbackUrl = `${window.location.origin}/login/callback`;
      const result = await authClient.initiateLogin(tenantSlug, callbackUrl);

      // Store state for verification on callback
      sessionStorage.setItem('oidcState', result.state);
      sessionStorage.setItem('oidcTenantSlug', tenantSlug);

      // Redirect to IdP (this will unload the page)
      window.location.href = result.authorization_url;
    } catch (error) {
      setIsLoading(false);
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
      // Verify state matches what we stored
      const storedState = sessionStorage.getItem('oidcState');
      if (state !== storedState) {
        throw new AuthError(
          'Invalid state parameter - possible CSRF attack',
          AuthErrorCategory.AUTHENTICATION
        );
      }

      // Use AuthClient for contract-validated token exchange
      const tokenResponse = await authClient.exchangeCodeForTokens(code, state);

      const tenantSlug = sessionStorage.getItem('oidcTenantSlug') || 'default';

      // Build validated user info
      const userInfo: UserInfo = {
        id: tokenResponse.user_id,
        email: tokenResponse.email,
        role: tokenResponse.role,
        tenantId: tenantSlug,
        tenantSlug,
      };

      // Persist session via AuthClient
      authClient.persistSession(tokenResponse.access_token, userInfo, tenantSlug);

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
      authClient.clearOidcState();

      return true;
    } catch (error) {
      // Clean up on failure
      authClient.clearOidcState();
      sessionStorage.removeItem('postLoginRedirect');

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
    authClient.clearSession();
    authClient.clearOidcState();

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
    window.location.href = '/login';
  }, []);

  /**
   * Token refresh — delegates to AuthClient
   */
  const refreshToken = useCallback(async (): Promise<boolean> => {
    const isValid = await authClient.refreshToken();

    if (!isValid) {
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
   * Development bypass — creates mock auth state without credentials
   * Only available in development mode
   */
  const devBypass = useCallback(() => {
    if (!import.meta.env.DEV) {
      console.warn('devBypass only available in development mode');
      return;
    }

    const mockUser: UserInfo = {
      id: 'dev-user-001',
      email: 'dev@value-fabric.com',
      role: 'admin',
      tenantId: 'dev-tenant',
      tenantSlug: 'development',
    };

    // Create a mock JWT token (valid structure but not verified)
    // Use base64url encoding (RFC 7519) instead of standard base64
    const base64url = (str: string): string => {
      return btoa(str)
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
    };

    const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' +
      base64url(JSON.stringify({
        sub: mockUser.id,
        email: mockUser.email,
        role: mockUser.role,
        exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour expiry
      })) +
      '.mock-signature';

    authClient.persistSession(mockToken, mockUser, mockUser.tenantSlug);

    setAuthState({
      state: 'authenticated',
      user: mockUser,
      accessToken: mockToken,
      error: null,
    });

    useUserTierStore.getState().setUserRole(mockUser.role);

    console.log('[DEV] Authentication bypassed — logged in as', mockUser.email);
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
    devBypass: import.meta.env.DEV ? devBypass : undefined,
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
