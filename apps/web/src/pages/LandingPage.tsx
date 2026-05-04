/**
 * LandingPage — VALYNT-style Marketing/Registration Page
 * 
 * Split-screen design with light registration panel and dark value visualization.
 * Uses platform design tokens for consistent theming.
 */

import { Button } from '@/components/ui/button';
import { Shield, Database, FileText, BarChart3, ArrowRight } from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';
import { useNavigation } from '@/hooks';

// Platform Logo Component
const ValyntLogo = () => (
  <div className="flex items-center gap-2">
    <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
      <svg viewBox="0 0 24 24" className="w-5 h-5 text-primary-foreground" fill="currentColor">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    </div>
    <span className="font-semibold text-lg tracking-tight">VALYNT</span>
  </div>
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
  const { navigateTo } = useNavigation();
  const auth = useAuthContext();
  const { isAuthenticated, isLoading } = auth;

  // Redirect if already authenticated
  if (isAuthenticated && !isLoading) {
    navigateTo('home');
    return null;
  }

  const handleDevBypass = () => {
    if (import.meta.env.DEV || import.meta.env.MODE === 'test') {
      auth.devBypass?.();
      navigateTo('home');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col lg:flex-row overflow-auto">
      {/* LEFT PANEL — Marketing & CTAs */}
      <div className="flex-1 flex flex-col bg-background px-6 py-8 lg:px-12 lg:py-10">
        {/* Header */}
        <div className="mb-10">
          <p className="text-[10px] font-semibold tracking-widest text-muted-foreground uppercase mb-4">
            Value Intelligence Platform
          </p>
          <ValyntLogo />
        </div>

        {/* Hero Text */}
        <div className="max-w-md mb-10">
          <h1 className="text-3xl lg:text-4xl font-bold text-foreground leading-tight tracking-tight mb-4">
            Reveal the economic value hidden in your business.
          </h1>
          <p className="text-base text-muted-foreground leading-relaxed mb-6">
            Access a unified system that transforms data, conversations, and signals into quantified ROI, validated assumptions, and executive-ready outcomes.
          </p>
          <p className="text-sm text-muted-foreground">
            Built for Sales, Value Engineers, and Finance leaders scaling from $10M to $1B+.
          </p>
        </div>

        {/* Primary CTAs */}
        <div className="max-w-md flex-1">
          <div className="space-y-3">
            {/* Primary: Get Started */}
            <Button
              size="lg"
              className="w-full h-12 bg-foreground text-background hover:bg-foreground/90 font-semibold text-base"
              onClick={() => navigateTo('signup')}
            >
              Get Started
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>

            {/* Secondary: Sign In */}
            <Button
              size="lg"
              variant="outline"
              className="w-full h-12 font-medium text-base"
              onClick={() => navigateTo('login')}
            >
              Sign In
            </Button>
          </div>

          {/* Supporting text */}
          <p className="mt-6 text-sm text-muted-foreground text-center">
            Free to get started. No credit card required.
          </p>

          {/* Feature bullets */}
          <div className="mt-8 space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
              <p className="text-sm text-muted-foreground">
                <span className="text-foreground font-medium">Connect your CRM</span> — Salesforce, HubSpot, and more
              </p>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
              <p className="text-sm text-muted-foreground">
                <span className="text-foreground font-medium">Analyze conversations</span> — Calls, emails, and transcripts
              </p>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
              <p className="text-sm text-muted-foreground">
                <span className="text-foreground font-medium">Build business cases</span> — Quantified ROI with confidence scores
              </p>
            </div>
          </div>

          {/* Development Bypass */}
          {import.meta.env.DEV && (
            <div className="mt-8 pt-4 border-t border-border">
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
        </div>

        {/* Bottom Links */}
        <div className="mt-auto pt-8 flex items-center justify-between text-[10px] text-muted-foreground">
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-foreground transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-foreground transition-colors">Privacy Policy</a>
          </div>
          <p>© 2025 Valynt</p>
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
