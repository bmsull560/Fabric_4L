/**
 * Signup Page — Account Registration
 *
 * Uses shadcn login-04 block layout (card with form + image panel).
 *
 * Codemap coverage:
 *  Trace 1 — SSO buttons reuse the same OIDC initiateLogin flow as Login page
 *  Email/password signup uses backend registration endpoint when enabled.
 *
 * After successful signup the user is auto-logged-in (Skill §2: "Auto-login after signup").
 */

import { useEffect, useState, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';
import { sessionService } from '../services/sessionService';
import { useNavigation } from '@/hooks';
import { SignupForm } from '../components/login-form';
import { getSSOTenantSlug } from '../config/auth';
import { registerWithEmailPassword } from '../api/auth';
import { ApiError } from '../api/client';

function getSignupErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    const normalizedMessage = err.message.toLowerCase();
    const normalizedCode = err.errorCode.toLowerCase();

    if (
      err.statusCode === 409 ||
      normalizedCode.includes('duplicate') ||
      normalizedCode.includes('already_exists') ||
      normalizedMessage.includes('already exists') ||
      normalizedMessage.includes('already registered') ||
      normalizedMessage.includes('duplicate')
    ) {
      return 'An account with this email already exists. Please sign in instead.';
    }

    if (
      err.statusCode === 422 ||
      normalizedCode.includes('validation') ||
      normalizedMessage.includes('invalid email') ||
      normalizedMessage.includes('validation')
    ) {
      return 'Please check your email and password and try again.';
    }

    if (
      normalizedCode.includes('password') ||
      normalizedMessage.includes('password') ||
      normalizedMessage.includes('weak') ||
      normalizedMessage.includes('complex')
    ) {
      return 'Password does not meet security requirements. Use at least 8 characters with a mix of character types.';
    }

    return err.message || 'Registration failed. Please try again.';
  }

  return err instanceof Error ? err.message : 'Registration failed. Please try again.';
}

export default function Signup() {
  const { navigateTo } = useNavigation();
  const { isAuthenticated, isLoading, initiateLogin } = useAuthContext();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Skip signup if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigateTo('home');
    }
  }, [isAuthenticated, isLoading, navigateTo]);

  const handleSignup = useCallback(async (data: { email: string; password: string }) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await registerWithEmailPassword(data);

      const canAutoLogin = Boolean(response.access_token && response.user_id && response.email);

      if (canAutoLogin && response.access_token && response.user_id && response.email) {
        const tenantSlug = response.tenant_slug || 'default';
        sessionService.persistSession(
          response.access_token,
          {
            id: response.user_id,
            email: response.email,
            role: response.role || 'standard',
            tenantId: response.tenant_id || tenantSlug,
            tenantSlug,
          },
          response.tenant_id || tenantSlug
        );

        navigateTo('home');
        return;
      }

      // Deterministic fallback: send users to login with success state
      navigateTo('login', undefined, { query: { signup: 'success' } });
    } catch (err) {
      setError(getSignupErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }, [navigateTo]);

  /**
   * SSO provider → OIDC flow (same as Login page).
   * Signing up with SSO creates the account on the backend automatically
   * via the auto-provision step in oidc.py (Trace 2, line 322).
   */
  const handleSSOProvider = useCallback(async (provider: string) => {
    setIsSubmitting(true);
    setError(null);

    const tenantSlug = getSSOTenantSlug(provider);
    if (!tenantSlug) {
      setError(`SSO provider "${provider}" is not configured.`);
      setIsSubmitting(false);
      return;
    }

    try {
      await initiateLogin(tenantSlug);
    } catch (err) {
      setIsSubmitting(false);
      setError(err instanceof Error ? err.message : 'Could not connect to SSO provider. Try again or use email/password.');
    }
  }, [initiateLogin]);

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-muted p-6 md:p-10">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden="true" />
          <p className="text-muted-foreground" role="status">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-muted p-6 md:p-10">
      <div className="w-full max-w-sm">
        <SignupForm
          onSignup={handleSignup}
          onSSOProvider={handleSSOProvider}
          isLoading={isSubmitting}
          error={error}
        />
      </div>
    </div>
  );
}
