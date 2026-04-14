/**
 * Login Page — OIDC Authentication Entry Point
 * 
 * Flow:
 * 1. User enters/selects tenant slug
 * 2. Clicks "Sign In" → calls /auth/oidc/{tenant}/login
 * 3. Backend returns authorization_url with PKCE parameters
 * 4. Redirect browser to IdP (Google, Azure AD, Okta, etc.)
 * 5. IdP redirects back to /login/callback with code+state
 * 6. Frontend exchanges code for JWT via backend callback
 * 7. Store JWT, redirect to /home
 */

import { useEffect, useState } from 'react';
import { useLocation, useSearch } from 'wouter';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, LogIn, AlertCircle } from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';
import { useI18n } from "@/i18n";

export default function Login() {
  const { t } = useI18n();
  const [, navigate] = useLocation();
  const search = useSearch();
  const { isAuthenticated, isLoading, initiateLogin, handleCallback } = useAuthContext();
  
  const [tenantSlug, setTenantSlug] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if we're handling a callback (URL has code and state)
  useEffect(() => {
    const params = new URLSearchParams(search);
    const code = params.get('code');
    const state = params.get('state');

    if (code && state) {
      // Handle OIDC callback
      handleCallbackFlow(code, state);
    }
  }, [search]);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate('/home');
    }
  }, [isAuthenticated, isLoading, navigate]);

  const handleCallbackFlow = async (code: string, state: string) => {
    setIsLoggingIn(true);
    setError(null);

    try {
      const success = await handleCallback(code, state);
      if (success) {
        navigate('/home');
      } else {
        setError(t("login.errors.authFailed"));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("login.errors.authFailedGeneric"));
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!tenantSlug.trim()) {
      setError(t("login.errors.tenantRequired"));
      return;
    }

    setIsLoggingIn(true);
    setError(null);

    try {
      await initiateLogin(tenantSlug.trim());
      // Page will redirect to IdP, no need to handle success here
    } catch (err) {
      setIsLoggingIn(false);
      setError(err instanceof Error ? err.message : t("login.errors.initiateFailed"));
    }
  };

  // Show loading state while checking auth or handling callback
  if (isLoading || isLoggingIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/50">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">
              {isLoggingIn ? t("login.authenticating") : t("login.loading")}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">{t("login.signIn")}</CardTitle>
          <CardDescription>
            {t("login.cardDescription")}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="tenant">{t("login.tenantLabel")}</Label>
              <Input
                id="tenant"
                type="text"
                placeholder={t("login.tenantPlaceholder")}
                value={tenantSlug}
                onChange={(e) => setTenantSlug(e.target.value)}
                disabled={isLoggingIn}
                autoFocus
              />
              <p className="text-sm text-muted-foreground">
                {t("login.tenantHelp")}
              </p>
            </div>

            <Button 
              type="submit" 
              className="w-full"
              disabled={isLoggingIn || !tenantSlug.trim()}
            >
              {isLoggingIn ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t("login.submitting")}
                </>
              ) : (
                <>
                  <LogIn className="mr-2 h-4 w-4" />
                  {t("login.submit")}
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            <p>{t("login.footer")}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
