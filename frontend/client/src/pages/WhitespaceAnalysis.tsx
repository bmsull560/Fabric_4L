/**
 * WhitespaceAnalysis — Account Penetration & Whitespace
 *
 * Features:
 * - Visualize product/solution penetration across accounts
 * - Identify whitespace opportunities by product line
 * - Account-level matrix view
 * - Filter by account size, industry, region
 * - Export whitespace reports
 *
 * Route: /discover/white-space
 */

import { useState, useMemo } from "react";
import { useLocation } from "wouter";
import {
  Search, Filter, Grid3X3, Download, ChevronRight, Check,
  Minus, Square, Building2, BarChart3, PieChart, ArrowRight,
  Loader2, AlertCircle
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";

// ── Types ───────────────────────────────────────────────────────────────────

type PenetrationStatus = 'adopted' | 'partial' | 'opportunity' | 'not_applicable';
type ViewMode = 'matrix' | 'summary';

interface ProductLine {
  id: string;
  name: string;
  category: string;
  avgDealSize: string;
}

interface AccountWhitespace {
  accountId: string;
  accountName: string;
  industry: string;
  region: string;
  arr: string;
  penetration: Record<string, PenetrationStatus>;
  totalWhitespace: string;
  penetrationRate: number;
}

// ── Mock Data ─────────────────────────────────────────────────────────────────

const PRODUCT_LINES: ProductLine[] = [
  { id: 'p1', name: 'Core Platform', category: 'Foundation', avgDealSize: '$50K' },
  { id: 'p2', name: 'Advanced Analytics', category: 'Intelligence', avgDealSize: '$25K' },
  { id: 'p3', name: 'AI Assistant', category: 'Intelligence', avgDealSize: '$15K' },
  { id: 'p4', name: 'Security Module', category: 'Compliance', avgDealSize: '$35K' },
  { id: 'p5', name: 'API Gateway', category: 'Integration', avgDealSize: '$20K' },
  { id: 'p6', name: 'Mobile SDK', category: 'Integration', avgDealSize: '$10K' },
  { id: 'p7', name: 'Premium Support', category: 'Services', avgDealSize: '$30K' },
  { id: 'p8', name: 'Training Package', category: 'Services', avgDealSize: '$12K' },
];

const ACCOUNTS: AccountWhitespace[] = [
  {
    accountId: 'acc-1',
    accountName: 'Acme Corporation',
    industry: 'Manufacturing',
    region: 'North America',
    arr: '$450K',
    penetration: { p1: 'adopted', p2: 'adopted', p3: 'partial', p4: 'opportunity', p5: 'opportunity', p6: 'not_applicable', p7: 'adopted', p8: 'opportunity' },
    totalWhitespace: '$77K',
    penetrationRate: 56,
  },
  {
    accountId: 'acc-2',
    accountName: 'Globex Industries',
    industry: 'Technology',
    region: 'EMEA',
    arr: '$280K',
    penetration: { p1: 'adopted', p2: 'opportunity', p3: 'opportunity', p4: 'opportunity', p5: 'adopted', p6: 'partial', p7: 'not_applicable', p8: 'opportunity' },
    totalWhitespace: '$102K',
    penetrationRate: 38,
  },
  {
    accountId: 'acc-3',
    accountName: 'Initech LLC',
    industry: 'Finance',
    region: 'North America',
    arr: '$620K',
    penetration: { p1: 'adopted', p2: 'adopted', p3: 'adopted', p4: 'partial', p5: 'adopted', p6: 'adopted', p7: 'adopted', p8: 'adopted' },
    totalWhitespace: '$17K',
    penetrationRate: 95,
  },
  {
    accountId: 'acc-4',
    accountName: 'Massive Dynamic',
    industry: 'Technology',
    region: 'APAC',
    arr: '$180K',
    penetration: { p1: 'adopted', p2: 'opportunity', p3: 'not_applicable', p4: 'opportunity', p5: 'opportunity', p6: 'opportunity', p7: 'opportunity', p8: 'opportunity' },
    totalWhitespace: '$122K',
    penetrationRate: 25,
  },
  {
    accountId: 'acc-5',
    accountName: 'Stark Industries',
    industry: 'Manufacturing',
    region: 'North America',
    arr: '$890K',
    penetration: { p1: 'adopted', p2: 'adopted', p3: 'adopted', p4: 'adopted', p5: 'adopted', p6: 'partial', p7: 'adopted', p8: 'partial' },
    totalWhitespace: '$42K',
    penetrationRate: 85,
  },
];

// ── Styling Constants ─────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<PenetrationStatus, {
  icon: React.ReactNode;
  bgColor: string;
  borderColor: string;
  label: string;
}> = {
  adopted: {
    icon: <Check size={12} />,
    bgColor: 'bg-emerald-100',
    borderColor: 'border-emerald-300',
    label: 'Adopted',
  },
  partial: {
    icon: <Minus size={12} />,
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-300',
    label: 'Partial',
  },
  opportunity: {
    icon: <Square size={12} />,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-300',
    label: 'Whitespace',
  },
  not_applicable: {
    icon: null,
    bgColor: 'bg-muted/30',
    borderColor: 'border-border',
    label: 'N/A',
  },
};

// ── Sub-components ─────────────────────────────────────────────────────────

function PenetrationCell({ status, onClick }: { status: PenetrationStatus; onClick?: () => void }) {
  const config = STATUS_CONFIG[status];
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full h-10 flex items-center justify-center rounded border transition-all hover:scale-105",
        config.bgColor,
        config.borderColor,
        status === 'opportunity' && "hover:bg-blue-100 cursor-pointer"
      )}
      title={config.label}
    >
      {config.icon}
    </button>
  );
}

function MatrixView({
  accounts,
  products,
  onAccountClick,
}: {
  accounts: AccountWhitespace[];
  products: ProductLine[];
  onAccountClick: (accountId: string) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="sticky left-0 bg-card z-10 p-3 text-left text-[11px] font-semibold text-muted-foreground border-b border-border min-w-[200px]">
              Account
            </th>
            <th className="p-3 text-left text-[11px] font-semibold text-muted-foreground border-b border-border">
              Industry
            </th>
            <th className="p-3 text-left text-[11px] font-semibold text-muted-foreground border-b border-border">
              ARR
            </th>
            {products.map(product => (
              <th key={product.id} className="p-2 text-center text-[10px] font-medium text-muted-foreground border-b border-border min-w-[60px]">
                <div className="rotate-180 [writing-mode:vertical-lr] whitespace-nowrap">
                  {product.name}
                </div>
              </th>
            ))}
            <th className="p-3 text-right text-[11px] font-semibold text-muted-foreground border-b border-border">
              Penetration
            </th>
            <th className="p-3 text-right text-[11px] font-semibold text-muted-foreground border-b border-border">
              Whitespace
            </th>
          </tr>
        </thead>
        <tbody>
          {accounts.map(account => (
            <tr
              key={account.accountId}
              className="hover:bg-muted/20 cursor-pointer"
              onClick={() => onAccountClick(account.accountId)}
            >
              <td className="sticky left-0 bg-card p-3 border-b border-border/50">
                <div className="font-medium text-[13px] text-foreground">{account.accountName}</div>
                <div className="text-[10px] text-muted-foreground/60">{account.region}</div>
              </td>
              <td className="p-3 border-b border-border/50 text-[12px] text-muted-foreground">
                {account.industry}
              </td>
              <td className="p-3 border-b border-border/50 text-[12px] font-medium text-muted-foreground">
                {account.arr}
              </td>
              {products.map(product => (
                <td key={product.id} className="p-1 border-b border-border/50">
                  <PenetrationCell
                    status={account.penetration[product.id] || 'not_applicable'}
                  />
                </td>
              ))}
              <td className="p-3 border-b border-border/50 text-right">
                <div className="text-[14px] font-bold text-foreground">{account.penetrationRate}%</div>
                <div className="w-16 h-1.5 bg-neutral-200 rounded-full mt-1 ml-auto overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full",
                      account.penetrationRate >= 80 ? "bg-emerald-500" :
                      account.penetrationRate >= 50 ? "bg-amber-500" : "bg-blue-500"
                    )}
                    style={{ width: `${account.penetrationRate}%` }}
                  />
                </div>
              </td>
              <td className="p-3 border-b border-border/50 text-right">
                <span className="text-[14px] font-bold text-emerald-600">{account.totalWhitespace}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SummaryView({
  accounts,
  products,
}: {
  accounts: AccountWhitespace[];
  products: ProductLine[];
}) {
  // Calculate product-level stats
  const productStats = useMemo(() => {
    return products.map(product => {
      const adopted = accounts.filter(a => a.penetration[product.id] === 'adopted').length;
      const partial = accounts.filter(a => a.penetration[product.id] === 'partial').length;
      const opportunity = accounts.filter(a => a.penetration[product.id] === 'opportunity').length;
      const total = accounts.filter(a => a.penetration[product.id] !== 'not_applicable').length;
      const penetrationRate = total > 0 ? Math.round((adopted / total) * 100) : 0;

      return {
        ...product,
        adopted,
        partial,
        opportunity,
        total,
        penetrationRate,
      };
    });
  }, [accounts, products]);

  // Calculate industry stats
  const industryStats = useMemo(() => {
    const industries = Array.from(new Set(accounts.map(a => a.industry)));
    return industries.map(industry => {
      const industryAccounts = accounts.filter(a => a.industry === industry);
      const avgPenetration = Math.round(
        industryAccounts.reduce((sum, a) => sum + a.penetrationRate, 0) / industryAccounts.length
      );
      const totalWhitespace = industryAccounts.reduce((sum, a) => {
        const value = parseInt(a.totalWhitespace.replace(/[$K]/g, '')) * 1000;
        return sum + value;
      }, 0);

      return {
        industry,
        accountCount: industryAccounts.length,
        avgPenetration,
        totalWhitespace: `$${(totalWhitespace / 1000000).toFixed(1)}M`,
      };
    });
  }, [accounts]);

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Product Penetration */}
      <div className="bg-card border border-border rounded-xl p-4">
        <h3 className="text-[14px] font-semibold text-foreground mb-4 flex items-center gap-2">
          <BarChart3 size={16} className="text-blue-500" />
          Product Penetration
        </h3>
        <div className="space-y-3">
          {productStats.map(stat => (
            <div key={stat.id} className="flex items-center gap-3">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[12px] font-medium text-muted-foreground">{stat.name}</span>
                  <span className="text-[12px] text-muted-foreground">{stat.penetrationRate}%</span>
                </div>
                <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all"
                    style={{ width: `${stat.penetrationRate}%` }}
                  />
                </div>
                <div className="flex items-center gap-3 mt-1 text-[10px] text-muted-foreground/60">
                  <span className="text-emerald-600">{stat.adopted} adopted</span>
                  <span className="text-amber-600">{stat.partial} partial</span>
                  <span className="text-blue-600">{stat.opportunity} whitespace</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Industry Breakdown */}
      <div className="bg-card border border-border rounded-xl p-4">
        <h3 className="text-[14px] font-semibold text-foreground mb-4 flex items-center gap-2">
          <PieChart size={16} className="text-violet-500" />
          By Industry
        </h3>
        <div className="space-y-3">
          {industryStats.map(stat => (
            <div key={stat.industry} className="flex items-center justify-between p-2 bg-muted/20 rounded-lg">
              <div>
                <span className="text-[12px] font-medium text-muted-foreground">{stat.industry}</span>
                <span className="text-[10px] text-muted-foreground/60 ml-2">{stat.accountCount} accounts</span>
              </div>
              <div className="text-right">
                <div className="text-[12px] font-medium text-foreground">{stat.avgPenetration}% penetration</div>
                <div className="text-[10px] text-emerald-600">{stat.totalWhitespace} whitespace</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function WhitespaceSkeleton() {
  return (
    <div className="p-6 max-w-6xl">
      <Skeleton className="h-8 w-48 mb-6" />
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

function WhitespaceAnalysisContent() {
  const [, navigate] = useLocation();
  const [search, setSearch] = useState("");
  const [industryFilter, setIndustryFilter] = useState<string>('all');
  const [regionFilter, setRegionFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('matrix');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const filteredAccounts = useMemo(() => {
    let filtered = [...ACCOUNTS];

    if (search) {
      const term = search.toLowerCase();
      filtered = filtered.filter(a =>
        a.accountName.toLowerCase().includes(term) ||
        a.industry.toLowerCase().includes(term)
      );
    }

    if (industryFilter !== 'all') {
      filtered = filtered.filter(a => a.industry === industryFilter);
    }

    if (regionFilter !== 'all') {
      filtered = filtered.filter(a => a.region === regionFilter);
    }

    return filtered;
  }, [search, industryFilter, regionFilter]);

  const industries = useMemo(() => Array.from(new Set(ACCOUNTS.map(a => a.industry))), []);
  const regions = useMemo(() => Array.from(new Set(ACCOUNTS.map(a => a.region))), []);

  const stats = useMemo(() => {
    const totalAccounts = filteredAccounts.length;
    const totalWhitespace = filteredAccounts.reduce((sum, a) => {
      const value = parseInt(a.totalWhitespace.replace(/[$K]/g, '')) * 1000;
      return sum + value;
    }, 0);
    const avgPenetration = totalAccounts > 0
      ? Math.round(filteredAccounts.reduce((sum, a) => sum + a.penetrationRate, 0) / totalAccounts)
      : 0;
    const highPenetration = filteredAccounts.filter(a => a.penetrationRate >= 80).length;

    return { totalAccounts, totalWhitespace, avgPenetration, highPenetration };
  }, [filteredAccounts]);

  if (isLoading) {
    return <WhitespaceSkeleton />;
  }

  if (error) {
    return (
      <div className="p-6 max-w-6xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-8 h-8 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-[14px] font-semibold text-red-800 mb-1">Failed to load whitespace analysis</h3>
              <p className="text-[12px] text-red-600">{error.message}</p>
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
          title="Whitespace Analysis"
          subtitle={`${stats.totalAccounts} accounts · ${stats.avgPenetration}% avg penetration · $${(stats.totalWhitespace / 1000000).toFixed(1)}M whitespace`}
        />
        <Btn variant="outline" onClick={() => alert('Export functionality coming soon')}>
          <Download size={14} className="mr-1" />
          Export Report
        </Btn>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Total Accounts</p>
          <p className="text-[22px] font-extrabold text-foreground">{stats.totalAccounts}</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Total Whitespace</p>
          <p className="text-[22px] font-extrabold text-emerald-600">${(stats.totalWhitespace / 1000000).toFixed(1)}M</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Avg Penetration</p>
          <p className="text-[22px] font-extrabold text-blue-600">{stats.avgPenetration}%</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">High Penetration</p>
          <p className="text-[22px] font-extrabold text-violet-600">{stats.highPenetration}</p>
        </div>
      </div>

      {/* Filters & View Toggle */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2">
            <Search size={14} className="text-muted-foreground/60" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search accounts..."
              className="text-[13px] bg-transparent outline-none text-muted-foreground w-48"
            />
          </div>

          <select
            value={industryFilter}
            onChange={(e) => setIndustryFilter(e.target.value)}
            className="text-[12px] px-3 py-2 border border-border rounded-lg bg-card outline-none"
          >
            <option value="all">All Industries</option>
            {industries.map(ind => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>

          <select
            value={regionFilter}
            onChange={(e) => setRegionFilter(e.target.value)}
            className="text-[12px] px-3 py-2 border border-border rounded-lg bg-card outline-none"
          >
            <option value="all">All Regions</option>
            {regions.map(reg => (
              <option key={reg} value={reg}>{reg}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1 bg-muted/30 rounded-lg p-1">
          <button
            onClick={() => setViewMode('matrix')}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] font-medium transition-all",
              viewMode === 'matrix'
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-muted-foreground"
            )}
          >
            <Grid3X3 size={14} />
            Matrix
          </button>
          <button
            onClick={() => setViewMode('summary')}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] font-medium transition-all",
              viewMode === 'summary'
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-muted-foreground"
            )}
          >
            <BarChart3 size={14} />
            Summary
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        {viewMode === 'matrix' ? (
          <MatrixView
            accounts={filteredAccounts}
            products={PRODUCT_LINES}
            onAccountClick={(id) => navigate(`/accounts/${id}`)}
          />
        ) : (
          <div className="p-4">
            <SummaryView accounts={filteredAccounts} products={PRODUCT_LINES} />
          </div>
        )}
      </div>

      {filteredAccounts.length === 0 && (
        <div className="text-center py-12 text-muted-foreground/60">
          <Building2 size={48} className="mx-auto mb-4 text-neutral-300" />
          <p className="text-[14px] font-medium">No accounts match your filters</p>
          <p className="text-[12px] mt-1">Adjust filters to see whitespace analysis</p>
        </div>
      )}
    </div>
  );
}

export default function WhitespaceAnalysis() {
  return (
    <ErrorBoundary>
      <WhitespaceAnalysisContent />
    </ErrorBoundary>
  );
}
