/**
 * BusinessCaseList — Case Management List View
 *
 * Features:
 * - List all business cases with key metrics
 * - Filter by status (draft, active, archived)
 * - Search by name or company
 * - Sort by value, confidence, date
 * - Create new case action
 * - Archive cases
 *
 * Route: /deliver/cases (list view)
 * Integrates with: useBusinessCases, useCreateBusinessCase, useArchiveBusinessCase
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Plus, Search, Filter, Archive, ArrowUpRight, Clock,
  CheckCircle2, TrendingUp, Users, Building2, Loader2, AlertCircle
} from "lucide-react";
import { useNavigation, useRoutePrefetch } from "@/hooks";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { EmptyState } from "@/components/states";
import { Skeleton } from "@/components/ui/skeleton";
import { VirtualList } from "@/components/ui/virtual-list";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import ErrorBoundary from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";
import {
  useBusinessCases,
  useCreateBusinessCase,
  useArchiveBusinessCase,
  type BusinessCaseListItem,
  type BusinessCaseFilters,
} from "@/hooks/useBusinessCases";

// ── Types ───────────────────────────────────────────────────────────────────

type SortField = 'name' | 'company' | 'totalValue' | 'confidence' | 'updatedAt';
type SortDirection = 'asc' | 'desc';

// ── Styling Constants ─────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<BusinessCaseListItem['status'], {
  label: string;
  color: string;
  bgColor: string;
  icon: React.ReactNode;
}> = {
  draft: {
    label: "Draft",
    color: "text-muted-foreground",
    bgColor: "bg-muted/30",
    icon: <Clock size={12} />,
  },
  active: {
    label: "Active",
    color: "text-emerald-600",
    bgColor: "bg-emerald-50",
    icon: <CheckCircle2 size={12} />,
  },
  archived: {
    label: "Archived",
    color: "text-muted-foreground",
    bgColor: "bg-muted/30",
    icon: <Archive size={12} />,
  },
};

// ── Helper Functions ────────────────────────────────────────────────────────

function parseCurrency(value: string): number {
  const num = value.replace(/[$,MK]/g, '');
  const multiplier = value.includes('M') ? 1000000 : value.includes('K') ? 1000 : 1;
  return parseFloat(num) * multiplier;
}

// ── Sub-components ─────────────────────────────────────────────────────────

function CaseCard({
  caseItem,
  onArchive,
  isArchiving,
}: {
  caseItem: BusinessCaseListItem;
  onArchive: (id: string) => void;
  isArchiving: boolean;
}) {
  const { navigateTo } = useNavigation();
  const { prefetchBusinessCaseDetail } = useRoutePrefetch();
  const status = STATUS_CONFIG[caseItem.status];

  return (
    <div
      className="bg-card border border-border rounded-xl p-4 hover:border-neutral-300 transition-colors group"
      onMouseEnter={() => prefetchBusinessCaseDetail(caseItem.id)}
      onFocus={() => prefetchBusinessCaseDetail(caseItem.id)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-[14px] font-semibold text-foreground truncate">
              {caseItem.name}
            </h3>
            <span className={cn(
              "inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full",
              status.bgColor, status.color
            )}>
              {status.icon} {status.label}
            </span>
          </div>
          <div className="flex items-center gap-2 text-[12px] text-muted-foreground">
            <Building2 size={12} />
            <span>{caseItem.company}</span>
            <span className="text-neutral-300">·</span>
            <Users size={12} />
            <span>{caseItem.useCaseCount} use cases</span>
          </div>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => navigateTo('business-case-detail', { caseId: caseItem.id })}
            className="p-1.5 rounded hover:bg-muted/30 text-muted-foreground/60 hover:text-muted-foreground"
            title="View details"
            aria-label="View details"
          >
            <ArrowUpRight size={14} />
          </button>
          {caseItem.status !== 'archived' && (
            <button
              onClick={() => onArchive(caseItem.id)}
              disabled={isArchiving}
              className="p-1.5 rounded hover:bg-red-50 text-muted-foreground/60 hover:text-red-500 disabled:opacity-50"
              title="Archive"
              aria-label="Archive"
            >
              <Archive size={14} />
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mt-4">
        <div className="bg-muted/20 rounded-lg p-2">
          <p className="text-[10px] text-muted-foreground/60 uppercase tracking-wider">Total Value</p>
          <p className="text-[16px] font-bold text-emerald-600">{caseItem.totalValue}</p>
        </div>
        <div className="bg-muted/20 rounded-lg p-2">
          <p className="text-[10px] text-muted-foreground/60 uppercase tracking-wider">Confidence</p>
          <p className="text-[16px] font-bold text-muted-foreground">{caseItem.confidence}%</p>
        </div>
        <div className="bg-muted/20 rounded-lg p-2">
          <p className="text-[10px] text-muted-foreground/60 uppercase tracking-wider">Updated</p>
          <p className="text-[12px] font-medium text-muted-foreground">
            {new Date(caseItem.updatedAt).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  );
}

function CaseListSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map(i => (
        <div key={i} className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <Skeleton className="h-5 w-48 mb-2" />
              <Skeleton className="h-4 w-32" />
            </div>
            <Skeleton className="h-8 w-8 rounded" />
          </div>
          <div className="grid grid-cols-3 gap-3 mt-4">
            {[1, 2, 3].map(j => (
              <Skeleton key={j} className="h-14 rounded-lg" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

function BusinessCaseListContent() {
  const { navigateTo } = useNavigation();
  const { prefetchBusinessCaseDetail } = useRoutePrefetch();
  const [searchParams, setSearchParams] = useSearchParams();

  // Validation helpers for URL params (used only during initialization)
  const validateStatus = (val: string | null): BusinessCaseFilters['status'] => {
    if (!val) return 'all';
    const validStatuses: BusinessCaseFilters['status'][] = ['all', 'active', 'draft', 'archived'];
    return validStatuses.includes(val as BusinessCaseFilters['status']) ? val as BusinessCaseFilters['status'] : 'all';
  };

  const validateSortField = (val: string | null): SortField => {
    if (!val) return 'updatedAt';
    const validFields: SortField[] = ['name', 'company', 'totalValue', 'confidence', 'updatedAt'];
    return validFields.includes(val as SortField) ? val as SortField : 'updatedAt';
  };

  const validateSortDirection = (val: string | null): SortDirection => {
    if (!val) return 'desc';
    return val === 'asc' || val === 'desc' ? val : 'desc';
  };

  // Initialize state from URL search params with validation
  const [search, setSearch] = useState(searchParams.get('search') || "");
  const [statusFilter, setStatusFilter] = useState<BusinessCaseFilters['status']>(
    validateStatus(searchParams.get('status'))
  );
  const [sortField, setSortField] = useState<SortField>(
    validateSortField(searchParams.get('sort'))
  );
  const [sortDirection, setSortDirection] = useState<SortDirection>(
    validateSortDirection(searchParams.get('dir'))
  );
  const [showNewCaseModal, setShowNewCaseModal] = useState(false);
  const [newCaseName, setNewCaseName] = useState("");
  const [newCaseCompany, setNewCaseCompany] = useState("");

  // Sync filter state to URL
  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (statusFilter && statusFilter !== 'all') params.set('status', statusFilter);
    if (sortField && sortField !== 'updatedAt') params.set('sort', sortField);
    if (sortDirection && sortDirection !== 'desc') params.set('dir', sortDirection);
    setSearchParams(params, { replace: true });
  }, [search, statusFilter, sortField, sortDirection, setSearchParams]);

  const { data: cases = [], isLoading, error, refetch } = useBusinessCases({
    status: statusFilter,
    search: search || undefined,
  });

  const createMutation = useCreateBusinessCase();
  const archiveMutation = useArchiveBusinessCase();

  const sortedCases = useMemo(() => {
    const sorted = [...cases];
    sorted.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'company':
          comparison = a.company.localeCompare(b.company);
          break;
        case 'totalValue':
          comparison = parseCurrency(a.totalValue) - parseCurrency(b.totalValue);
          break;
        case 'confidence':
          comparison = a.confidence - b.confidence;
          break;
        case 'updatedAt':
          comparison = new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime();
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });
    return sorted;
  }, [cases, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const handleCreateCase = () => {
    if (!newCaseName.trim() || !newCaseCompany.trim()) return;
    
    createMutation.mutate(
      { name: newCaseName.trim(), company: newCaseCompany.trim() },
      {
        onSuccess: (data) => {
          setShowNewCaseModal(false);
          setNewCaseName("");
          setNewCaseCompany("");
          navigateTo('business-case-detail', { caseId: data.workflow_id });
        },
      }
    );
  };

  const handleArchive = (id: string) => {
    if (confirm('Are you sure you want to archive this business case?')) {
      archiveMutation.mutate(id);
    }
  };

  const stats = useMemo(() => {
    const total = cases.length;
    const active = cases.filter(c => c.status === 'active').length;
    const draft = cases.filter(c => c.status === 'draft').length;
    const totalValue = cases.reduce((sum, c) => sum + parseCurrency(c.totalValue), 0);
    return { total, active, draft, totalValue };
  }, [cases]);

  if (isLoading) {
    return (
      <div className="p-6 max-w-6xl">
        <div className="flex items-start justify-between mb-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-9 w-32" />
        </div>
        <CaseListSkeleton />
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
              <h3 className="text-[14px] font-semibold text-red-800 mb-1">Failed to load business cases</h3>
              <p className="text-[12px] text-red-600">{error instanceof Error ? error.message : "An unexpected error occurred"}</p>
              <button
                onClick={() => refetch()}
                className="mt-4 flex items-center gap-1.5 px-3 py-1.5 bg-red-100 text-red-700 text-[12px] font-medium rounded-lg hover:bg-red-200"
              >
                Try again
              </button>
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
          title="Business Cases"
          subtitle={`${stats.total} cases · ${stats.active} active · ${stats.draft} drafts`}
        />
        <Btn variant="primary" onClick={() => setShowNewCaseModal(true)}>
          <Plus size={14} className="mr-1" />
          New Case
        </Btn>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={14} className="text-emerald-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Total Value</span>
          </div>
          <p className="text-[22px] font-extrabold text-emerald-600">${(stats.totalValue / 1000000).toFixed(1)}M</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 size={14} className="text-emerald-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Active</span>
          </div>
          <p className="text-[22px] font-extrabold text-foreground">{stats.active}</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <Clock size={14} className="text-muted-foreground/60" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Drafts</span>
          </div>
          <p className="text-[22px] font-extrabold text-foreground">{stats.draft}</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <Building2 size={14} className="text-blue-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Companies</span>
          </div>
          <p className="text-[22px] font-extrabold text-foreground">{new Set(cases.map(c => c.company)).size}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2 flex-1 max-w-sm">
          <Search size={14} className="text-muted-foreground/60" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search cases or companies..."
            className="flex-1 text-[13px] bg-transparent outline-none text-muted-foreground"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={14} className="text-muted-foreground/60" />
          <Select
            value={statusFilter}
            onValueChange={(value) => setStatusFilter(value as BusinessCaseFilters['status'])}
          >
            <SelectTrigger className="text-[12px] h-9 w-[130px] bg-card border-border">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[12px] text-muted-foreground">Sort by:</span>
          <Select
            value={sortField}
            onValueChange={(value) => handleSort(value as SortField)}
          >
            <SelectTrigger className="text-[12px] h-9 w-[140px] bg-card border-border">
              <SelectValue placeholder="Last Updated" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="updatedAt">Last Updated</SelectItem>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="company">Company</SelectItem>
              <SelectItem value="totalValue">Value</SelectItem>
              <SelectItem value="confidence">Confidence</SelectItem>
            </SelectContent>
          </Select>
          <button
            onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
            className="text-[12px] px-2 py-2 border border-border rounded-lg hover:bg-muted/20"
            aria-label={`Sort ${sortDirection === 'asc' ? 'descending' : 'ascending'}`}
          >
            {sortDirection === 'asc' ? '↑' : '↓'}
          </button>
        </div>
      </div>

      {/* Case List */}
      {sortedCases.length > 0 && (
        <div className="h-[600px]">
          <VirtualList
            items={sortedCases}
            estimateSize={120}
            overscan={3}
            renderItem={(caseItem) => (
              <CaseCard
                caseItem={caseItem}
                onArchive={handleArchive}
                isArchiving={archiveMutation.isPending}
              />
            )}
          />
        </div>
      )}

      {sortedCases.length === 0 && (
        <EmptyState
          icon={Building2}
          title="No business cases found"
          description="Create your first case to get started"
          action={
            <Btn variant="primary" onClick={() => setShowNewCaseModal(true)}>
              <Plus size={14} className="mr-1" />
              Create Case
            </Btn>
          }
        />
      )}

      {/* New Case Modal */}
      <Dialog open={showNewCaseModal} onOpenChange={setShowNewCaseModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create New Business Case</DialogTitle>
            <DialogDescription>
              Enter the case name and company to create a new business case.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label htmlFor="new-case-name" className="block text-[12px] font-medium text-muted-foreground mb-1">
                Case Name
              </label>
              <input
                id="new-case-name"
                type="text"
                value={newCaseName}
                onChange={(e) => setNewCaseName(e.target.value)}
                placeholder="e.g., Q2 Expansion Analysis"
                className="w-full px-3 py-2 border border-border rounded-lg text-[13px] outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <div>
              <label htmlFor="new-case-company" className="block text-[12px] font-medium text-muted-foreground mb-1">
                Company
              </label>
              <input
                id="new-case-company"
                type="text"
                value={newCaseCompany}
                onChange={(e) => setNewCaseCompany(e.target.value)}
                placeholder="e.g., Acme Corporation"
                className="w-full px-3 py-2 border border-border rounded-lg text-[13px] outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </div>
          <DialogFooter>
            <Btn
              variant="ghost"
              onClick={() => {
                setShowNewCaseModal(false);
                setNewCaseName("");
                setNewCaseCompany("");
              }}
            >
              Cancel
            </Btn>
            <Btn
              variant="primary"
              disabled={createMutation.isPending || !newCaseName.trim() || !newCaseCompany.trim()}
              onClick={handleCreateCase}
            >
              {createMutation.isPending ? (
                <Loader2 size={14} className="animate-spin mr-1" />
              ) : (
                <Plus size={14} className="mr-1" />
              )}
              Create
            </Btn>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function BusinessCaseList() {
  return (
    <ErrorBoundary>
      <BusinessCaseListContent />
    </ErrorBoundary>
  );
}
