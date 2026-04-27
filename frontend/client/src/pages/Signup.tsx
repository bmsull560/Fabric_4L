/**
 * Signup Page — Account Registration
 *
 * Uses shadcn login-04 block layout (card with form + image panel).
 *
 * Codemap coverage:
 *  Trace 1 — SSO buttons reuse the same OIDC initiateLogin flow as Login page
 *  Email/password signup: placeholder until backend supports registration endpoint
 *
 * After successful signup the user is auto-logged-in (Skill §2: "Auto-login after signup").
 */

import { useEffect, useState, useCallback } from 'react';
import { useLocation } from 'wouter';
import { Loader2 } from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';
import { SignupForm } from '../components/login-form';
import { getSSOTenantSlug } from '../config/auth';

export default function Signup() {
  const [, navigate] = useLocation();
  const { isAuthenticated, isLoading, initiateLogin, devBypass } = useAuthContext();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Skip signup if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate('/home');
    }
  }, [isAuthenticated, isLoading, navigate]);

  const handleSignup = useCallback(async (_data: { email: string; password: string }) => {
    setIsSubmitting(true);
    setError(null);

    try {
      // TODO: Wire to real signup endpoint when backend supports it.
      // Auto-login after signup (Skill §2)
      if (import.meta.env.DEV && devBypass) {
        devBypass();
        navigate('/home');
      } else {
        // Redirect to login with success indicator in query string
        navigate('/login?signup=success');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
      setIsSubmitting(false);
    }
  }, [devBypass, navigate]);

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
