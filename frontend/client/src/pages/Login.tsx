/**
 * Login Page — OIDC Authentication Entry Point
 *
 * Uses shadcn login-04 block layout (card with form + image panel).
 *
 * Codemap coverage:
 *  Trace 1 — Frontend Login Initiation: SSO buttons → AuthContext.initiateLogin()
 *  Trace 2 — OIDC Callback: code+state → handleCallback() → JWT + role
 *  Trace 3 — Role Normalization: handled by AuthContext → userTierStore
 *
 * Flow:
 * 1a. Email/password — dev bypass in dev, placeholder for production auth
 * 1b. SSO button → initiateLogin(tenantSlug) → IdP redirect (Trace 1)
 * 2.  /login/callback → handleCallback(code, state) → JWT exchange (Trace 2)
 * 3.  Role sync → userTierStore.setUserRole() (Trace 3)
 * 4.  Redirect to stored destination or /home
 */

import { useEffect, useState, useCallback } from 'react';
import { useLocation, useSearch } from 'wouter';
import { Loader2 } from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';
import { LoginForm } from '../components/login-form';
import { SSO_PROVIDER_TENANT, getSSOTenantSlug } from '../config/auth';

export default function Login() {
  const [, navigate] = useLocation();
  const search = useSearch();
  const {
    isAuthenticated, isLoading,
    initiateLogin, handleCallback, devBypass,
  } = useAuthContext();

  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // ── Trace 2: OIDC Callback handling ──────────────────────────────────────
  useEffect(() => {
    const params = new URLSearchParams(search);
    const code = params.get('code');
    const state = params.get('state');
    const redirect = params.get('redirect');
    const signup = params.get('signup');

    // Show success message after signup redirect
    if (signup === 'success') {
      setSuccessMessage('Account created successfully. Please sign in.');
      // Clean up URL
      navigate('/login', { replace: true });
    }

    // Preserve intended destination before IdP redirect
    if (redirect && !code) {
      sessionStorage.setItem('postLoginRedirect', redirect);
    }

    if (code && state) {
      handleCallbackFlow(code, state);
    }
  }, [search, navigate]);

  // Skip login if already authenticated (Skill §3: "Skip login if session valid")
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      const redirect = sessionStorage.getItem('postLoginRedirect');
      sessionStorage.removeItem('postLoginRedirect');
      navigate(redirect || '/home');
    }
  }, [isAuthenticated, isLoading, navigate]);

  /**
   * Trace 2: Exchange authorization code for JWT.
   * AuthContext.handleCallback validates CSRF state against sessionStorage,
   * calls AuthClient.exchangeCodeForTokens, persists session, and syncs role.
   */
  const handleCallbackFlow = async (code: string, state: string) => {
    setIsLoggingIn(true);
    setError(null);

    try {
      const success = await handleCallback(code, state);
      if (success) {
        const redirect = sessionStorage.getItem('postLoginRedirect');
        sessionStorage.removeItem('postLoginRedirect');
        navigate(redirect || '/home');
      } else {
        setError('Authentication failed. Please try again.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setIsLoggingIn(false);
    }
  };

  /**
   * Email/password handler.
   * In dev mode: uses devBypass for instant auth.
   * In production: placeholder until backend email/password endpoint exists.
   */
  const handleLogin = useCallback(async (_email: string, _password: string) => {
    setIsLoggingIn(true);
    setError(null);

    try {
      if (import.meta.env.DEV && devBypass) {
        devBypass();
        navigate('/home');
      } else {
        setError('Email/password login is not yet configured. Use SSO or contact your admin.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoggingIn(false);
    }
  }, [devBypass, navigate]);

  /**
   * Trace 1: SSO button → OIDC redirect.
   * Maps provider key ("google" | "microsoft") to a tenant slug, then calls
   * AuthContext.initiateLogin(tenantSlug) which:
   *   1c. Calls AuthClient.initiateLogin() → fetch /auth/oidc/{tenant}/login
   *   1e. Stores CSRF state in sessionStorage
   *   1f. Redirects browser to IdP authorization URL
   */
  const handleSSOProvider = useCallback(async (provider: string) => {
    setIsLoggingIn(true);
    setError(null);

    const tenantSlug = getSSOTenantSlug(provider);
    if (!tenantSlug) {
      setError(`SSO provider "${provider}" is not configured.`);
      setIsLoggingIn(false);
      return;
    }

    try {
      await initiateLogin(tenantSlug);
      // Browser will redirect to IdP — page unloads here
    } catch (err) {
      setIsLoggingIn(false);
      if (err instanceof Error && err.message.toLowerCase().includes('not found')) {
        setError(`SSO provider not found. Please contact your administrator.`);
      } else {
        setError(err instanceof Error ? err.message : 'Could not connect to SSO provider. Try again or use email/password.');
      }
    }
  }, [initiateLogin]);

  const handleDevBypass = useCallback(() => {
    devBypass?.();
    navigate('/home');
  }, [devBypass, navigate]);

  // Show loading state while checking auth or handling callback
  if (isLoading || isLoggingIn) {
    return (
      <div className="flex min-h-svh flex-col items-center justify-center bg-muted p-6 md:p-10">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden="true" />
          <p className="text-muted-foreground" role="status">
            {isLoggingIn ? 'Authenticating...' : 'Loading...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-muted p-6 md:p-10">
      <div className="w-full max-w-sm md:max-w-4xl">
        <LoginForm
          onLogin={handleLogin}
          onSSOProvider={handleSSOProvider}
          onDevBypass={handleDevBypass}
          isLoading={isLoggingIn}
          error={error}
          successMessage={successMessage}
        />
      </div>
    </div>
  );
}
