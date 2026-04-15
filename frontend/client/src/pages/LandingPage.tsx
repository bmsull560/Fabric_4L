/**
 * LandingPage — Public Marketing/Login Page
 * 
 * Unauthenticated entry point with "Source to Boardroom" hero
 * and sign-in form. Design matches screenshot 2.
 */

import { useState } from 'react';
import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, LogIn, AlertCircle, Sparkles, ArrowRight } from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';

export default function LandingPage() {
  const [, navigate] = useLocation();
  const { isAuthenticated, isLoading, initiateLogin, handleCallback, devBypass } = useAuthContext();
  
  const [tenantSlug, setTenantSlug] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for callback params on mount
  const search = window.location.search;
  const params = new URLSearchParams(search);
  const code = params.get('code');
  const state = params.get('state');
  const isCallback = code && state;

  // Handle callback flow
  const handleCallbackFlow = async (code: string, state: string) => {
    setIsLoggingIn(true);
    setError(null);

    try {
      const success = await handleCallback(code, state);
      if (success) {
        navigate('/home');
      } else {
        setError('Authentication failed. Please try again.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setIsLoggingIn(false);
    }
  };

  // Handle initial callback if present
  if (isCallback && !isLoggingIn && !error) {
    handleCallbackFlow(code, state);
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Completing authentication...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Redirect if already authenticated
  if (isAuthenticated && !isLoading) {
    navigate('/home');
    return null;
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!tenantSlug.trim()) {
      setError('Please enter a tenant identifier');
      return;
    }

    setIsLoggingIn(true);
    setError(null);

    try {
      await initiateLogin(tenantSlug.trim());
      // Page will redirect to IdP
    } catch (err) {
      setIsLoggingIn(false);
      setError(err instanceof Error ? err.message : 'Failed to initiate login');
    }
  };

  const handleDevBypass = () => {
    devBypass?.();
    navigate('/home');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Navigation */}
      <nav className="w-full px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight">VALUE FABRIC</span>
        </div>
        <div className="flex items-center gap-6 text-xs font-medium tracking-wider text-slate-600">
          <a href="#platform" className="hover:text-blue-600 transition-colors">PLATFORM</a>
          <a href="#expertise" className="hover:text-blue-600 transition-colors">EXPERTISE</a>
          <Button 
            variant="outline" 
            size="sm" 
            className="text-xs tracking-wider"
            onClick={() => navigate('/login')}
          >
            SIGN IN
          </Button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* Left Column — Hero */}
        <div className="space-y-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-100/50 rounded-full text-[10px] font-semibold tracking-widest text-blue-700">
            <span className="w-1.5 h-1.5 bg-blue-600 rounded-full"></span>
            ENTERPRISE INTELLIGENCE
          </div>
          
          <h1 className="text-5xl lg:text-6xl font-bold leading-tight tracking-tight text-slate-900">
            Value Fabric:<br />
            <span className="text-blue-600">Source to</span><br />
            <span className="text-blue-600">Boardroom.</span>
          </h1>
          
          <p className="text-lg text-slate-600 max-w-md leading-relaxed">
            Transform scattered enterprise data into AI-generated business cases with full provenance and precision.
          </p>

          {/* Pipeline Steps */}
          <div className="flex items-center gap-4 pt-4">
            {[
              { num: '01', label: 'INGESTION', desc: 'Multi-source unstructured sync' },
              { num: '02', label: 'EXTRACTION', desc: 'Ontology-guided parsing' },
              { num: '03', label: 'GRAPH', desc: 'Semantic relationship mapping' },
              { num: '04', label: 'WORKFLOW', desc: 'Auditable case generation' },
            ].map((step, i) => (
              <div key={step.num} className="flex flex-col gap-1">
                <div className="text-[10px] font-bold text-blue-600 tracking-wider">{step.num} {step.label}</div>
                <div className="text-[9px] text-slate-500 leading-tight max-w-[80px]">{step.desc}</div>
                {i < 3 && <div className="hidden lg:block absolute ml-[90px] mt-4 w-4 h-px bg-slate-300" />}
              </div>
            ))}
          </div>
        </div>

        {/* Right Column — Sign In Card */}
        <div className="flex justify-center lg:justify-end">
          <Card className="w-full max-w-md shadow-xl border-0 bg-white/80 backdrop-blur">
            <CardHeader className="space-y-2 pb-4">
              <CardTitle className="text-2xl font-semibold">Welcome back</CardTitle>
              <CardDescription className="text-sm text-slate-500">
                Enter your credentials to continue
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive" className="text-xs">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Google Sign In */}
              <Button 
                variant="outline" 
                className="w-full h-11 font-medium"
                onClick={() => setError('Google OAuth not configured in development')}
              >
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
              </Button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-slate-200" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-slate-400">OR</span>
                </div>
              </div>

              {/* Tenant Login Form */}
              <form onSubmit={handleLogin} className="space-y-3">
                <div className="space-y-1.5">
                  <Label htmlFor="tenant" className="text-[11px] font-semibold tracking-wider text-slate-600 uppercase">
                    Email Address
                  </Label>
                  <Input
                    id="tenant"
                    type="text"
                    placeholder="name@value-fabric.com"
                    value={tenantSlug}
                    onChange={(e) => setTenantSlug(e.target.value)}
                    disabled={isLoggingIn}
                    className="h-11"
                  />
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-[11px] font-semibold tracking-wider text-slate-600 uppercase">
                      Password
                    </Label>
                    <a href="#" className="text-[10px] text-blue-600 hover:underline">
                      Forgot?
                    </a>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    disabled={isLoggingIn}
                    className="h-11"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input type="checkbox" id="remember" className="rounded border-slate-300" />
                  <Label htmlFor="remember" className="text-[11px] text-slate-500 font-normal">
                    Remember device
                  </Label>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-11 bg-blue-600 hover:bg-blue-700 text-white font-medium tracking-wider"
                  disabled={isLoggingIn || !tenantSlug.trim()}
                >
                  {isLoggingIn ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    <>
                      Sign in to Value Fabric
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              </form>

              {/* Development Bypass Button */}
              {import.meta.env.DEV && (
                <div className="pt-4 border-t border-slate-100">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full text-[10px] text-slate-400 hover:text-amber-600"
                    onClick={handleDevBypass}
                  >
                    <Sparkles className="mr-1 h-3 w-3" />
                    Development Bypass (No Credentials)
                  </Button>
                </div>
              )}

              <div className="text-center text-[11px] text-slate-400">
                Don't have an account?{' '}
                <a href="#" className="text-blue-600 hover:underline font-medium">
                  Sign up
                </a>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Footer */}
      <footer className="fixed bottom-0 w-full px-6 py-4 flex items-center justify-between text-[10px] text-slate-400">
        <div className="flex items-center gap-2">
          <span>© 2024 VALUE FABRIC</span>
          <span className="w-1 h-1 bg-slate-300 rounded-full" />
          <span>V2.4.0</span>
        </div>
        <div className="flex items-center gap-6">
          <a href="#" className="hover:text-slate-600">Privacy</a>
          <a href="#" className="hover:text-slate-600">Terms</a>
          <a href="#" className="hover:text-slate-600">Security</a>
          <div className="flex items-center gap-1">
            <span className="w-4 h-4 rounded-full bg-slate-200" />
            <span>EN-US</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
