/**
 * Accounts Page — CRM Account Management
 * 
 * Features:
 * - List all CRM accounts with filtering and search
 * - View account details including opportunities and activity
 * - Sync accounts from Salesforce/HubSpot
 * - View sync status and health
 */
import { useState, useMemo } from "react";
import { PageHeader, Btn, StatusBadge } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";
import {
  useAccounts,
  useAccountSyncStatus,
  useSyncAccounts,
  useRefreshAccount,
  useAccountFilterOptions,
  type Account,
  type CRMProvider,
  type SyncStatus,
} from "@/hooks/useAccounts";
import {
  Building2,
  Search,
  Filter,
  RefreshCw,
  Loader2,
  ChevronRight,
  Briefcase,
  Users,
  Globe,
  DollarSign,
  Activity,
  CheckCircle2,
  AlertCircle,
  Clock,
  Cloud,
  CloudOff,
  MoreHorizontal,
} from "lucide-react";

const PROVIDER_COLORS: Record<CRMProvider, { bg: string; text: string; border: string }> = {
  salesforce: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
  hubspot: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
};

const SYNC_STATUS_COLORS: Record<SyncStatus, "completed" | "processing" | "failed"> = {
  synced: "completed",
  pending: "processing",
  failed: "failed",
  stale: "processing",
};

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return "—";
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return date.toLocaleDateString();
}

interface AccountCardProps {
  account: Account;
  onRefresh?: (id: string) => void;
  isRefreshing?: boolean;
}

function AccountCard({ account, onRefresh, isRefreshing }: AccountCardProps) {
  const providerStyle = PROVIDER_COLORS[account.provider];
  const totalOpportunityValue = account.opportunities?.reduce(
    (sum, opp) => sum + (opp.value || 0),
    0
  ) || 0;

  return (
    <div className="bg-white border border-neutral-200 rounded-xl shadow-sm hover:shadow-md hover:border-neutral-300 transition-all cursor-pointer group">
      {/* Header */}
      <div className="px-5 pt-5 pb-4 border-b border-neutral-100">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-lg ${providerStyle.bg} border ${providerStyle.border} flex items-center justify-center`}>
              <Building2 size={14} className={providerStyle.text} />
            </div>
            <div>
              <h3 className="text-[13px] font-bold text-neutral-900 leading-tight">{account.name}</h3>
              <p className="text-[10px] text-neutral-400 mt-0.5">{account.domain}</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <span className={`px-2 py-0.5 text-[10px] font-medium rounded-full ${providerStyle.bg} ${providerStyle.text} border ${providerStyle.border}`}>
              {account.provider === "salesforce" ? "Salesforce" : "HubSpot"}
            </span>
            <StatusBadge status={SYNC_STATUS_COLORS[account.sync_status]} />
          </div>
        </div>
        <p className="text-[11px] text-neutral-500 leading-relaxed">
          {account.industry || "No industry"} • {account.headquarters || "No location"}
        </p>
      </div>

      {/* Stats */}
      <div className="px-5 py-3 grid grid-cols-4 gap-2 border-b border-neutral-100">
        {[
          { icon: <DollarSign size={11} />, label: "Pipeline", value: formatCurrency(totalOpportunityValue) },
          { icon: <Briefcase size={11} />, label: "Opportunities", value: account.opportunities?.length || 0 },
          { icon: <Users size={11} />, label: "Employees", value: account.employees?.toLocaleString() || "—" },
          { icon: <Globe size={11} />, label: "Revenue", value: formatCurrency(account.annual_revenue) },
        ].map(s => (
          <div key={s.label} className="text-center">
            <div className="flex items-center justify-center gap-1 text-neutral-400 mb-0.5">
              {s.icon}
            </div>
            <p className="text-[14px] font-bold text-neutral-800">{s.value}</p>
            <p className="text-[9px] text-neutral-400 uppercase tracking-wide">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-5 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[11px] text-neutral-400">
          <Clock size={12} />
          <span>Synced {formatDate(account.last_synced_at)}</span>
        </div>
        <div className="flex items-center gap-2">
          {onRefresh && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRefresh(account.id);
              }}
              disabled={isRefreshing}
              className="p-1.5 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-md transition-colors disabled:opacity-50"
              title="Refresh from CRM"
            >
              {isRefreshing ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            </button>
          )}
          <ChevronRight size={16} className="text-neutral-300" />
        </div>
      </div>
    </div>
  );
}

interface SyncStatusPanelProps {
  onSync: (provider?: CRMProvider) => void;
  isSyncing: boolean;
}

function SyncStatusPanel({ onSync, isSyncing }: SyncStatusPanelProps) {
  const { data: syncStatus, isLoading } = useAccountSyncStatus();

  if (isLoading) {
    return (
      <div className="bg-white border border-neutral-200 rounded-xl p-5">
        <Skeleton className="h-4 w-32 mb-4" />
        <div className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-neutral-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[13px] font-semibold text-neutral-800 flex items-center gap-2">
          <Cloud size={14} className="text-blue-500" />
          CRM Sync Status
        </h3>
        <Btn
          variant="primary"
          onClick={() => onSync()}
          disabled={isSyncing}
        >
          {isSyncing ? (
            <>
              <Loader2 size={12} className="animate-spin mr-1" />
              Syncing...
            </>
          ) : (
            <>
              <RefreshCw size={12} className="mr-1" />
              Sync All
            </>
          )}
        </Btn>
      </div>

      <div className="space-y-3">
        {syncStatus?.map((status) => (
          <div
            key={status.provider}
            className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-100"
          >
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                status.provider === "salesforce"
                  ? "bg-blue-100 text-blue-600"
                  : "bg-orange-100 text-orange-600"
              }`}>
                {status.provider === "salesforce" ? <Cloud size={14} /> : <Cloud size={14} />}
              </div>
              <div>
                <p className="text-[12px] font-medium text-neutral-800 capitalize">
                  {status.provider}
                </p>
                <p className="text-[10px] text-neutral-500">
                  {status.status === "running"
                    ? "Sync in progress..."
                    : status.last_successful_sync_at
                    ? `Last sync: ${formatDate(status.last_successful_sync_at)}`
                    : "Never synced"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {status.status === "failed" && (
                <span className="text-[10px] text-red-600 flex items-center gap-1">
                  <AlertCircle size={10} />
                  Failed
                </span>
              )}
              <button
                onClick={() => onSync(status.provider)}
                disabled={isSyncing || status.status === "running"}
                className="p-1.5 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-md transition-colors disabled:opacity-50"
                title={`Sync ${status.provider}`}
              >
                {isSyncing ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              </button>
            </div>
          </div>
        ))}

        {!syncStatus?.length && (
          <div className="text-center py-6 text-neutral-400">
            <CloudOff size={24} className="mx-auto mb-2 opacity-50" />
            <p className="text-[12px]">No CRM providers configured</p>
            <p className="text-[10px] mt-1">Set up integrations in Settings</p>
          </div>
        )}
      </div>
    </div>
  );
}

function Accounts() {
  const [filters, setFilters] = useState({
    provider: "all" as CRMProvider | "all",
    sync_status: "all" as SyncStatus | "all",
    industry: undefined as string | undefined,
    search: "",
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error } = useAccounts(filters);
  const { data: filterOptions } = useAccountFilterOptions();
  const syncMutation = useSyncAccounts();
  const refreshMutation = useRefreshAccount();

  const accounts = data?.accounts || [];
  const total = data?.total || 0;

  const handleSync = (provider?: CRMProvider) => {
    syncMutation.mutate({ provider });
  };

  const handleRefresh = (accountId: string) => {
    refreshMutation.mutate(accountId);
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-[1400px] mx-auto px-6 py-8">
        {/* Header */}
        <PageHeader
          title="Accounts"
          subtitle={`${total} accounts from CRM`}
          actions={
            <Btn
              variant="primary"
              onClick={() => handleSync()}
              disabled={syncMutation.isPending}
            >
              {syncMutation.isPending ? (
                <>
                  <Loader2 size={14} className="animate-spin mr-2" />
                  Syncing...
                </>
              ) : (
                <>
                  <RefreshCw size={14} className="mr-2" />
                  Sync All
                </>
              )}
            </Btn>
          }
        />

        <div className="grid grid-cols-12 gap-6 mt-6">
          {/* Sidebar */}
          <div className="col-span-3 space-y-4">
            <SyncStatusPanel
              onSync={handleSync}
              isSyncing={syncMutation.isPending}
            />

            {/* Filters */}
            <div className="bg-white border border-neutral-200 rounded-xl p-5">
              <h3 className="text-[13px] font-semibold text-neutral-800 mb-4 flex items-center gap-2">
                <Filter size={14} className="text-neutral-400" />
                Filters
              </h3>

              {/* Provider Filter */}
              <div className="mb-4">
                <label className="text-[11px] font-medium text-neutral-600 mb-2 block">
                  Provider
                </label>
                <select
                  value={filters.provider}
                  onChange={(e) => setFilters({ ...filters, provider: e.target.value as CRMProvider | "all" })}
                  className="w-full text-[12px] px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  <option value="all">All Providers</option>
                  <option value="salesforce">Salesforce</option>
                  <option value="hubspot">HubSpot</option>
                </select>
              </div>

              {/* Sync Status Filter */}
              <div className="mb-4">
                <label className="text-[11px] font-medium text-neutral-600 mb-2 block">
                  Sync Status
                </label>
                <select
                  value={filters.sync_status}
                  onChange={(e) => setFilters({ ...filters, sync_status: e.target.value as SyncStatus | "all" })}
                  className="w-full text-[12px] px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  <option value="all">All Statuses</option>
                  <option value="synced">Synced</option>
                  <option value="pending">Pending</option>
                  <option value="failed">Failed</option>
                  <option value="stale">Stale</option>
                </select>
              </div>

              {/* Industry Filter */}
              {filterOptions?.industries && filterOptions.industries.length > 0 && (
                <div>
                  <label className="text-[11px] font-medium text-neutral-600 mb-2 block">
                    Industry
                  </label>
                  <select
                    value={filters.industry || "all"}
                    onChange={(e) => setFilters({ ...filters, industry: e.target.value === "all" ? undefined : e.target.value })}
                    className="w-full text-[12px] px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  >
                    <option value="all">All Industries</option>
                    {filterOptions.industries.map((ind) => (
                      <option key={ind} value={ind}>{ind}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="col-span-9">
            {/* Search Bar */}
            <div className="mb-4">
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
                <input
                  type="text"
                  placeholder="Search accounts by name, domain, or owner..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value, page: 1 })}
                  className="w-full pl-10 pr-4 py-2.5 bg-white border border-neutral-200 rounded-xl text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Accounts Grid */}
            {isLoading ? (
              <div className="grid grid-cols-2 gap-4">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-48 w-full rounded-xl" />
                ))}
              </div>
            ) : error ? (
              <div className="bg-white border border-red-200 rounded-xl p-8 text-center">
                <AlertCircle size={32} className="mx-auto mb-3 text-red-500" />
                <h3 className="text-[14px] font-semibold text-neutral-800 mb-1">Failed to load accounts</h3>
                <p className="text-[12px] text-neutral-500">{error.message}</p>
              </div>
            ) : accounts.length === 0 ? (
              <div className="bg-white border border-neutral-200 rounded-xl p-12 text-center">
                <Building2 size={48} className="mx-auto mb-4 text-neutral-300" />
                <h3 className="text-[16px] font-semibold text-neutral-800 mb-2">No accounts found</h3>
                <p className="text-[13px] text-neutral-500 mb-4">
                  {filters.search || filters.provider !== "all" || filters.sync_status !== "all"
                    ? "Try adjusting your filters"
                    : "Sync accounts from your CRM to get started"}
                </p>
                {!filters.search && filters.provider === "all" && filters.sync_status === "all" && (
                  <Btn
                    variant="primary"
                    onClick={() => handleSync()}
                    disabled={syncMutation.isPending}
                  >
                    {syncMutation.isPending ? (
                      <>
                        <Loader2 size={14} className="animate-spin mr-2" />
                        Syncing...
                      </>
                    ) : (
                      <>
                        <RefreshCw size={14} className="mr-2" />
                        Sync from CRM
                      </>
                    )}
                  </Btn>
                )}
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-4">
                  {accounts.map((account) => (
                    <AccountCard
                      key={account.id}
                      account={account}
                      onRefresh={handleRefresh}
                      isRefreshing={refreshMutation.isPending && refreshMutation.variables === account.id}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {total > filters.page_size && (
                  <div className="mt-6 flex items-center justify-between">
                    <p className="text-[12px] text-neutral-500">
                      Showing {(filters.page - 1) * filters.page_size + 1} to{" "}
                      {Math.min(filters.page * filters.page_size, total)} of {total} accounts
                    </p>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setFilters({ ...filters, page: filters.page - 1 })}
                        disabled={filters.page <= 1}
                        className="px-3 py-1.5 text-[12px] bg-white border border-neutral-200 rounded-lg hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
                        disabled={filters.page * filters.page_size >= total}
                        className="px-3 py-1.5 text-[12px] bg-white border border-neutral-200 rounded-lg hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AccountsPage() {
  return (
    <ErrorBoundary>
      <Accounts />
    </ErrorBoundary>
  );
}
