/**
 * LandingPage — VALYNT-style Marketing/Registration Page
 * 
 * Split-screen design with light registration panel and dark value visualization.
 * Uses platform design tokens for consistent theming.
 */

import { useState } from 'react';
import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, Shield, Database, FileText, BarChart3 } from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';

// Platform Logo Component
const ValyntLogo = () => (
  <div className="flex items-center gap-2">
    <div className="w-6 h-6 bg-primary rounded-md flex items-center justify-center">
      <svg viewBox="0 0 24 24" className="w-4 h-4 text-primary-foreground" fill="currentColor">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    </div>
    <span className="font-semibold text-sm tracking-tight">VALYNT</span>
  </div>
);

// Google Icon
const GoogleIcon = () => (
  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
  </svg>
);

// Microsoft Icon
const MicrosoftIcon = () => (
  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
    <path d="M0 0h11.5v11.5H0V0zm12.5 0H24v11.5H12.5V0zM0 12.5h11.5V24H0V12.5zm12.5 0H24V24H12.5V12.5z" />
  </svg>
);

// Value Visualization for Right Panel
const ValueVisualization = () => (
  <div className="relative w-full max-w-md mx-auto">
    {/* Data Source Icons */}
    <div className="flex justify-center gap-6 mb-8">
      <div className="flex flex-col items-center gap-2">
        <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
          <Database className="w-5 h-5 text-white/70" />
        </div>
        <span className="text-[10px] text-white/50 uppercase tracking-wider">CRM</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
          <FileText className="w-5 h-5 text-white/70" />
        </div>
        <span className="text-[10px] text-white/50 uppercase tracking-wider">Transcripts</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-white/70" />
        </div>
        <span className="text-[10px] text-white/50 uppercase tracking-wider">Benchmarks</span>
      </div>
    </div>

    {/* Main Value Circle */}
    <div className="relative flex items-center justify-center">
      {/* Outer ring */}
      <div className="absolute w-64 h-64 rounded-full border border-white/10" />
      
      {/* Value Display */}
      <div className="relative z-10 text-center">
        <p className="text-[10px] text-white/50 uppercase tracking-widest mb-2">Annual Value</p>
        <p className="text-4xl font-bold text-white tracking-tight">$2.4M</p>
        <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span className="text-[10px] font-medium text-emerald-400">Confidence: 82%</span>
        </div>
      </div>
    </div>

    {/* Value Pillars */}
    <div className="mt-10 flex justify-center gap-8">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-violet-400" />
        <span className="text-[10px] text-white/60 uppercase tracking-wider">Revenue Uplift</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-white/60" />
        <span className="text-[10px] text-white/60 uppercase tracking-wider">Cost Savings</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-amber-400" />
        <span className="text-[10px] text-white/60 uppercase tracking-wider">Risk Reduction</span>
      </div>
    </div>

    {/* Connection Lines (decorative) */}
    <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 300">
      <path
        d="M120 80 Q 200 150 200 200"
        stroke="rgba(139, 92, 246, 0.4)"
        strokeWidth="2"
        strokeDasharray="4 4"
        fill="none"
      />
      <path
        d="M280 80 Q 200 150 200 200"
        stroke="rgba(245, 158, 11, 0.4)"
        strokeWidth="2"
        strokeDasharray="4 4"
        fill="none"
      />
    </svg>
  </div>
);

export default function LandingPage() {
  const [, navigate] = useLocation();
  const { isAuthenticated, isLoading, initiateLogin, handleCallback, devBypass } = useAuthContext();

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for callback params on mount
  const search = window.location.search;
  const params = new URLSearchParams(search);
  const code = params.get('code');
  const state = params.get('state');
  const isCallback = code && state;

  // Handle callback flow
  const handleCallbackFlow = async (code: string, state: string) => {
    setIsSubmitting(true);
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
      setIsSubmitting(false);
    }
  };

  // Handle initial callback if present
  if (isCallback && !isSubmitting && !error) {
    handleCallbackFlow(code, state);
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Completing authentication...</p>
        </div>
      </div>
    );
  }

  // Redirect if already authenticated
  if (isAuthenticated && !isLoading) {
    navigate('/home');
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.email.trim() || !formData.password.trim()) {
      setError('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    // For now, simulate registration and redirect to login
    setTimeout(() => {
      setIsSubmitting(false);
      navigate('/login');
    }, 1500);
  };

  const handleDevBypass = () => {
    devBypass?.();
    navigate('/home');
  };

  const updateField = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* LEFT PANEL — Registration Form */}
      <div className="flex-1 flex flex-col bg-background px-6 py-8 lg:px-12 lg:py-10">
        {/* Header */}
        <div className="mb-10">
          <p className="text-[10px] font-semibold tracking-widest text-muted-foreground uppercase mb-4">
            Value Intelligence Platform
          </p>
          <ValyntLogo />
        </div>

        {/* Hero Text */}
        <div className="max-w-md mb-8">
          <h1 className="text-3xl lg:text-4xl font-bold text-foreground leading-tight tracking-tight mb-4">
            Reveal the economic value hidden in your business.
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Access a unified system that transforms data, conversations, and signals into quantified ROI, validated assumptions, and executive-ready outcomes.
          </p>
        </div>

        {/* Registration Form */}
        <div className="max-w-md flex-1">
          <h2 className="text-base font-semibold text-foreground mb-4">
            Create your value workspace
          </h2>

          {/* SSO Buttons */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <Button
              variant="outline"
              className="h-10 text-sm font-normal"
              onClick={() => setError('Google OAuth not configured in development')}
            >
              <GoogleIcon />
              <span className="ml-2">Google</span>
            </Button>
            <Button
              variant="outline"
              className="h-10 text-sm font-normal"
              onClick={() => setError('Microsoft OAuth not configured in development')}
            >
              <MicrosoftIcon />
              <span className="ml-2">Microsoft</span>
            </Button>
          </div>

          {/* Divider */}
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-background px-2 text-[10px] uppercase tracking-wider text-muted-foreground">
                Or continue with email
              </span>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive" className="text-xs">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="firstName" className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
                  First Name
                </Label>
                <Input
                  id="firstName"
                  type="text"
                  placeholder="Jane"
                  value={formData.firstName}
                  onChange={(e) => updateField('firstName', e.target.value)}
                  disabled={isSubmitting}
                  className="h-10 bg-secondary/50 border-0"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="lastName" className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
                  Last Name
                </Label>
                <Input
                  id="lastName"
                  type="text"
                  placeholder="Doe"
                  value={formData.lastName}
                  onChange={(e) => updateField('lastName', e.target.value)}
                  disabled={isSubmitting}
                  className="h-10 bg-secondary/50 border-0"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
                Work Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="jane@enterprise.com"
                value={formData.email}
                onChange={(e) => updateField('email', e.target.value)}
                disabled={isSubmitting}
                className="h-10 bg-secondary/50 border-0"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => updateField('password', e.target.value)}
                disabled={isSubmitting}
                className="h-10 bg-secondary/50 border-0"
              />
            </div>

            <Button
              type="submit"
              className="w-full h-10 bg-foreground text-background hover:bg-foreground/90 font-medium"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  Create Account
                  <svg className="ml-2 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </>
              )}
            </Button>
          </form>

          {/* Development Bypass */}
          {import.meta.env.DEV && (
            <div className="mt-4 pt-4 border-t border-border">
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-[10px] text-muted-foreground hover:text-primary"
                onClick={handleDevBypass}
              >
                Development Bypass
              </Button>
            </div>
          )}

          {/* Footer Text */}
          <p className="mt-6 text-[11px] text-muted-foreground leading-relaxed">
            Built for Sales, Value Engineers, and Finance leaders. Powered by agentic value modeling and real-time validation. Designed for boardroom confidence, not dashboards.
          </p>

          <p className="mt-4 text-[10px] text-muted-foreground">
            Trusted by revenue and finance teams scaling from $10M → $1B+
          </p>
        </div>

        {/* Bottom Links */}
        <div className="mt-auto pt-8 flex items-center justify-between text-[10px] text-muted-foreground">
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-foreground transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-foreground transition-colors">Privacy Policy</a>
          </div>
          <p>
            Already have an account?{' '}
            <a href="/login" className="text-foreground font-medium hover:underline" onClick={(e) => { e.preventDefault(); navigate('/login'); }}>
              Sign In
            </a>
          </p>
        </div>
      </div>

      {/* RIGHT PANEL — Value Visualization */}
      <div className="hidden lg:flex flex-1 bg-slate-900 flex-col items-center justify-center px-12 py-10 relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-800/50 via-slate-900 to-slate-950" />
        
        {/* Content */}
        <div className="relative z-10 w-full max-w-lg">
          {/* Header */}
          <div className="text-center mb-12">
            <h2 className="text-2xl font-semibold text-white leading-tight mb-3">
              Build a defensible business case—automatically.
            </h2>
            <p className="text-sm text-white/60 leading-relaxed">
              From discovery to boardroom approval, Valynt transforms inputs into quantified, evidence-backed value.
            </p>
          </div>

          {/* Value Visualization */}
          <ValueVisualization />

          {/* Trust Badge */}
          <div className="mt-12 flex items-start gap-3 px-4 py-3 rounded-lg bg-white/5 border border-white/10">
            <Shield className="w-5 h-5 text-white/50 flex-shrink-0 mt-0.5" />
            <p className="text-[11px] text-white/50 leading-relaxed">
              Every projection is linked back to source data and validated assumptions for total auditability.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
