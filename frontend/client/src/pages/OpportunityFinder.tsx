/**
 * OpportunityFinder — Value Opportunity Discovery
 *
 * Features:
 * - Discover value opportunities across accounts
 * - Filter by impact level, category, status
 * - AI-generated opportunity scoring
 * - Quick actions to create business cases
 * - Trend analysis and recommendations
 *
 * Route: /discover/opportunities
 * Integrates with: Layer 4 opportunity detection workflows
 */

import { useState, useMemo, useCallback } from "react";
import { useLocation } from "wouter";
import {
  Plus, Search, Filter, TrendingUp, Target, Zap, Building2,
  ArrowRight, Loader2, AlertCircle, Lightbulb, DollarSign,
  Users, Clock, ChevronDown, ChevronUp
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";
import { useOpportunities, type Opportunity } from "@/hooks/useOpportunities";

// ── Re-export types from hook for local usage ─────────────────────────────────

type OpportunityStatus = 'new' | 'investigating' | 'qualified' | 'converted' | 'dismissed';
type ImpactLevel = 'high' | 'medium' | 'low';
type SortField = 'aiScore' | 'value' | 'confidence' | 'discoveredAt';
type SortDirection = 'asc' | 'desc';

// ── Styling Constants ─────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<OpportunityStatus, {
  label: string;
  color: string;
  bgColor: string;
}> = {
  new: { label: 'New', color: 'text-blue-600', bgColor: 'bg-blue-50' },
  investigating: { label: 'Investigating', color: 'text-amber-600', bgColor: 'bg-amber-50' },
  qualified: { label: 'Qualified', color: 'text-emerald-600', bgColor: 'bg-emerald-50' },
  converted: { label: 'Converted', color: 'text-violet-600', bgColor: 'bg-violet-50' },
  dismissed: { label: 'Dismissed', color: 'text-muted-foreground', bgColor: 'bg-muted/30' },
};

const IMPACT_CONFIG: Record<ImpactLevel, {
  label: string;
  color: string;
  bgColor: string;
  icon: React.ReactNode;
}> = {
  high: {
    label: 'High Impact',
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50',
    icon: <TrendingUp size={14} />,
  },
  medium: {
    label: 'Medium Impact',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    icon: <Target size={14} />,
  },
  low: {
    label: 'Low Impact',
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/30',
    icon: <Zap size={14} />,
  },
};

const CATEGORY_COLORS: Record<string, string> = {
  'Cost Optimization': 'bg-blue-50 text-blue-700',
  'Upsell': 'bg-emerald-50 text-emerald-700',
  'Cross-sell': 'bg-violet-50 text-violet-700',
  'Expansion': 'bg-amber-50 text-amber-700',
  'Retention': 'bg-rose-50 text-rose-700',
};

// ── Sub-components ─────────────────────────────────────────────────────────

function OpportunityCard({
  opportunity,
  isExpanded,
  onToggle,
}: {
  opportunity: Opportunity;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const [, navigate] = useLocation();
  const status = STATUS_CONFIG[opportunity.status];
  const impact = IMPACT_CONFIG[opportunity.impact];

  return (
    <div className={cn(
      "bg-card border rounded-xl transition-all",
      isExpanded ? "border-neutral-300 shadow-sm" : "border-border hover:border-neutral-300"
    )}>
      <div
        className="p-4 cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-[14px] font-semibold text-foreground">
                {opportunity.title}
              </h3>
              <span className={cn(
                "text-[10px] font-medium px-2 py-0.5 rounded-full",
                CATEGORY_COLORS[opportunity.category] || 'bg-muted/30 text-muted-foreground'
              )}>
                {opportunity.category}
              </span>
            </div>
            <p className="text-[12px] text-muted-foreground mb-2 line-clamp-2">
              {opportunity.description}
            </p>
            <div className="flex items-center gap-3 text-[11px] text-muted-foreground/60">
              <span className="flex items-center gap-1">
                <Building2 size={11} />
                {opportunity.account}
              </span>
              <span className={cn("flex items-center gap-1", impact.color)}>
                {impact.icon}
                {impact.label}
              </span>
              <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", status.bgColor, status.color)}>
                {status.label}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 ml-4">
            <div className="text-right">
              <p className="text-[18px] font-bold text-emerald-600">{opportunity.estimatedValue}</p>
              <p className="text-[10px] text-muted-foreground/60">Est. Value</p>
            </div>
            <div className="text-right">
              <p className="text-[18px] font-bold text-foreground">{opportunity.aiScore}</p>
              <p className="text-[10px] text-muted-foreground/60">AI Score</p>
            </div>
            <button className="p-1 rounded hover:bg-muted/30">
              {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-border/50 pt-3">
          <div className="grid grid-cols-2 gap-4">
            {/* Insights */}
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
                <Lightbulb size={12} />
                AI Insights
              </h4>
              <ul className="space-y-1">
                {opportunity.insights.map((insight, idx) => (
                  <li key={idx} className="text-[11px] text-muted-foreground flex items-start gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                    {insight}
                  </li>
                ))}
              </ul>
            </div>

            {/* Recommended Actions */}
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
                <Target size={12} />
                Recommended Actions
              </h4>
              <ul className="space-y-1">
                {opportunity.recommendedActions.map((action, idx) => (
                  <li key={idx} className="text-[11px] text-muted-foreground flex items-start gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Sources & Actions */}
          <div className="flex items-center justify-between mt-4 pt-3 border-t border-border/50">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-muted-foreground/60">Sources:</span>
              {opportunity.sources.map((source, idx) => (
                <span
                  key={idx}
                  className="text-[10px] px-2 py-0.5 bg-muted/30 text-muted-foreground rounded"
                >
                  {source}
                </span>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <Btn
                variant="ghost"
                className="text-[11px]"
                onClick={() => navigate(`/accounts/${opportunity.accountId}`)}
              >
                View Account
              </Btn>
              <Btn
                variant="primary"
                className="text-[11px]"
                onClick={() => navigate(`/deliver/cases/new?opportunity=${opportunity.id}`)}
              >
                <Plus size={12} className="mr-1" />
                Create Case
              </Btn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function OpportunitySkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Skeleton className="h-5 w-64 mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-3 w-32" />
        </div>
        <div className="flex items-center gap-3">
          <Skeleton className="h-10 w-16" />
          <Skeleton className="h-10 w-12" />
        </div>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

function OpportunityFinderContent() {
  const [, navigate] = useLocation();
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<OpportunityStatus | 'all'>('all');
  const [impactFilter, setImpactFilter] = useState<ImpactLevel | 'all'>('all');
  const [sortField, setSortField] = useState<SortField>('aiScore');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Real API integration
  const { data: opportunitiesData, isLoading, error } = useOpportunities();
  const rawOpportunities = opportunitiesData?.opportunities ?? [];

  // Filter and sort opportunities
  const opportunities = useMemo(() => {
    let filtered = [...rawOpportunities];

    if (search) {
      const term = search.toLowerCase();
      filtered = filtered.filter(o =>
        o.title.toLowerCase().includes(term) ||
        o.account.toLowerCase().includes(term) ||
        o.description.toLowerCase().includes(term)
      );
    }

    if (categoryFilter !== 'all') {
      filtered = filtered.filter(o => o.category === categoryFilter);
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter(o => o.status === statusFilter);
    }

    if (impactFilter !== 'all') {
      filtered = filtered.filter(o => o.impact === impactFilter);
    }

    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'aiScore':
          comparison = a.aiScore - b.aiScore;
          break;
        case 'value':
          comparison = parseInt(a.estimatedValue.replace(/[$K]/g, '')) - parseInt(b.estimatedValue.replace(/[$K]/g, ''));
          break;
        case 'confidence':
          comparison = a.confidenceScore - b.confidenceScore;
          break;
        case 'discoveredAt':
          comparison = new Date(a.discoveredAt).getTime() - new Date(b.discoveredAt).getTime();
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [rawOpportunities, search, categoryFilter, statusFilter, impactFilter, sortField, sortDirection]);

  const stats = useMemo(() => {
    const total = opportunities.length;
    const highImpact = opportunities.filter(o => o.impact === 'high').length;
    const totalValue = opportunities.reduce((sum, o) => sum + parseInt(o.estimatedValue.replace(/[$K]/g, '')) * 1000, 0);
    const newOpps = opportunities.filter(o => o.status === 'new').length;
    return { total, highImpact, totalValue, newOpps };
  }, [opportunities]);

  const categories = useMemo(() => Array.from(new Set(rawOpportunities.map(o => o.category))), [rawOpportunities]);

  const handleSort = useCallback((field: SortField) => {
    setSortField(prev => {
      if (prev === field) {
        setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
        return prev;
      }
      setSortDirection('desc');
      return field;
    });
  }, []);

  const handleToggleExpand = useCallback((id: string) => {
    setExpandedId(prev => prev === id ? null : id);
  }, []);

  if (isLoading) {
    return (
      <div className="p-6 max-w-6xl">
        <div className="flex items-start justify-between mb-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-9 w-32" />
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map(i => <OpportunitySkeleton key={i} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-6xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-8 h-8 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-[14px] font-semibold text-red-800 mb-1">Failed to load opportunities</h3>
              <p className="text-[12px] text-red-600">{error instanceof Error ? error.message : 'Unknown error'}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Opportunity Finder"
          subtitle={`${stats.total} opportunities · ${stats.highImpact} high impact · ${stats.newOpps} new`}
        />
        <Btn variant="primary" onClick={() => navigate('/discover/opportunities/scan')}>
          <Zap size={14} className="mr-1" />
          Run AI Scan
        </Btn>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <DollarSign size={14} className="text-emerald-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Total Pipeline</span>
          </div>
          <p className="text-[22px] font-extrabold text-emerald-600">${(stats.totalValue / 1000000).toFixed(1)}M</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={14} className="text-emerald-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">High Impact</span>
          </div>
          <p className="text-[22px] font-extrabold text-foreground">{stats.highImpact}</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <Lightbulb size={14} className="text-blue-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">New This Week</span>
          </div>
          <p className="text-[22px] font-extrabold text-foreground">{stats.newOpps}</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <Target size={14} className="text-violet-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Avg AI Score</span>
          </div>
          <p className="text-[22px] font-extrabold text-foreground">
            {opportunities.length > 0 ? Math.round(opportunities.reduce((sum, o) => sum + o.aiScore, 0) / opportunities.length) : 0}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2 flex-1 max-w-sm">
          <Search size={14} className="text-muted-foreground/60" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search opportunities..."
            className="flex-1 text-[13px] bg-transparent outline-none text-muted-foreground"
          />
        </div>

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="text-[12px] px-3 py-2 border border-border rounded-lg bg-card outline-none"
        >
          <option value="all">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as OpportunityStatus | 'all')}
          className="text-[12px] px-3 py-2 border border-border rounded-lg bg-card outline-none"
        >
          <option value="all">All Status</option>
          <option value="new">New</option>
          <option value="investigating">Investigating</option>
          <option value="qualified">Qualified</option>
          <option value="converted">Converted</option>
        </select>

        <select
          value={impactFilter}
          onChange={(e) => setImpactFilter(e.target.value as ImpactLevel | 'all')}
          className="text-[12px] px-3 py-2 border border-border rounded-lg bg-card outline-none"
        >
          <option value="all">All Impact</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <div className="flex items-center gap-2 ml-auto">
          <span className="text-[12px] text-muted-foreground">Sort:</span>
          <select
            value={sortField}
            onChange={(e) => handleSort(e.target.value as SortField)}
            className="text-[12px] px-3 py-2 border border-border rounded-lg bg-card outline-none"
          >
            <option value="aiScore">AI Score</option>
            <option value="value">Value</option>
            <option value="confidence">Confidence</option>
            <option value="discoveredAt">Date</option>
          </select>
        </div>
      </div>

      {/* Opportunity List */}
      <div className="space-y-3">
        {opportunities.map(opportunity => (
          <OpportunityCard
            key={opportunity.id}
            opportunity={opportunity}
            isExpanded={expandedId === opportunity.id}
            onToggle={() => handleToggleExpand(opportunity.id)}
          />
        ))}
      </div>

      {opportunities.length === 0 && (
        <div className="text-center py-12 text-muted-foreground/60">
          <Lightbulb size={48} className="mx-auto mb-4 text-neutral-300" />
          <p className="text-[14px] font-medium">No opportunities found</p>
          <p className="text-[12px] mt-1">Adjust filters or run an AI scan to discover new opportunities</p>
        </div>
      )}
    </div>
  );
}

export default function OpportunityFinder() {
  return (
    <ErrorBoundary>
      <OpportunityFinderContent />
    </ErrorBoundary>
  );
}
