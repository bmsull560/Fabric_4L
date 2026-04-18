/**
 * SourceConfiguration — Data Source Management
 *
 * Features:
 * - Configure and manage data source connections
 * - Connection health monitoring
 * - Field mapping configuration
 * - Sync schedule management
 * - Test connection functionality
 *
 * Route: /discover/sources
 * Integrates with: Layer 1 (Ingestion) APIs
 */

import { useState, useMemo } from "react";
import {
  Plus, Search, Settings, CheckCircle2, XCircle, AlertTriangle,
  Clock, RefreshCw, Database, Globe, FileText, Cloud, Server,
  ChevronRight, Loader2, Save, TestTube, Trash2, Edit3, Plug,
  AlertCircle
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";

// ── Types ───────────────────────────────────────────────────────────────────

type SourceType = 'crm' | 'database' | 'file' | 'api' | 'cloud_storage';
type ConnectionStatus = 'connected' | 'disconnected' | 'error' | 'testing';
type SyncFrequency = 'realtime' | 'hourly' | 'daily' | 'weekly' | 'manual';

interface DataSource {
  id: string;
  name: string;
  type: SourceType;
  status: ConnectionStatus;
  endpoint?: string;
  lastSyncAt?: string;
  nextSyncAt?: string;
  syncFrequency: SyncFrequency;
  recordCount?: number;
  healthScore: number;
  errorMessage?: string;
  fieldMappings: FieldMapping[];
}

interface FieldMapping {
  sourceField: string;
  targetField: string;
  transformation?: string;
  isRequired: boolean;
}

// ── Mock Data ─────────────────────────────────────────────────────────────────

const MOCK_SOURCES: DataSource[] = [
  {
    id: 'src-1',
    name: 'Salesforce CRM',
    type: 'crm',
    status: 'connected',
    endpoint: 'https://acme.my.salesforce.com',
    lastSyncAt: '2024-01-15T09:30:00Z',
    nextSyncAt: '2024-01-15T10:30:00Z',
    syncFrequency: 'hourly',
    recordCount: 15420,
    healthScore: 98,
    fieldMappings: [
      { sourceField: 'Account.Name', targetField: 'account_name', isRequired: true },
      { sourceField: 'Account.ARR__c', targetField: 'annual_recurring_revenue', isRequired: true },
      { sourceField: 'Contact.Email', targetField: 'contact_email', isRequired: false },
    ],
  },
  {
    id: 'src-2',
    name: 'PostgreSQL Billing DB',
    type: 'database',
    status: 'connected',
    endpoint: 'postgres://billing-db.internal:5432',
    lastSyncAt: '2024-01-15T08:00:00Z',
    nextSyncAt: '2024-01-16T08:00:00Z',
    syncFrequency: 'daily',
    recordCount: 89234,
    healthScore: 95,
    fieldMappings: [
      { sourceField: 'invoices.total', targetField: 'invoice_amount', isRequired: true },
      { sourceField: 'invoices.status', targetField: 'payment_status', isRequired: true },
    ],
  },
  {
    id: 'src-3',
    name: 'HubSpot Marketing',
    type: 'crm',
    status: 'error',
    endpoint: 'https://api.hubapi.com',
    syncFrequency: 'hourly',
    healthScore: 0,
    errorMessage: 'API token expired. Please re-authenticate.',
    fieldMappings: [
      { sourceField: 'contacts.email', targetField: 'contact_email', isRequired: true },
    ],
  },
  {
    id: 'src-4',
    name: 'AWS S3 Data Lake',
    type: 'cloud_storage',
    status: 'connected',
    endpoint: 's3://acme-data-lake/raw/',
    lastSyncAt: '2024-01-14T23:00:00Z',
    nextSyncAt: '2024-01-15T23:00:00Z',
    syncFrequency: 'daily',
    recordCount: 456000,
    healthScore: 92,
    fieldMappings: [],
  },
  {
    id: 'src-5',
    name: 'REST API - Product Usage',
    type: 'api',
    status: 'disconnected',
    endpoint: 'https://api.acme.com/v1/usage',
    syncFrequency: 'realtime',
    healthScore: 0,
    fieldMappings: [
      { sourceField: 'event_type', targetField: 'activity_type', isRequired: true },
      { sourceField: 'timestamp', targetField: 'event_timestamp', isRequired: true },
    ],
  },
];

// ── Styling Constants ─────────────────────────────────────────────────────────

const TYPE_CONFIG: Record<SourceType, {
  icon: React.ReactNode;
  label: string;
  bgColor: string;
}> = {
  crm: { icon: <Globe size={16} />, label: 'CRM', bgColor: 'bg-blue-50 text-blue-600' },
  database: { icon: <Database size={16} />, label: 'Database', bgColor: 'bg-violet-50 text-violet-600' },
  file: { icon: <FileText size={16} />, label: 'File', bgColor: 'bg-amber-50 text-amber-600' },
  api: { icon: <Server size={16} />, label: 'API', bgColor: 'bg-emerald-50 text-emerald-600' },
  cloud_storage: { icon: <Cloud size={16} />, label: 'Cloud', bgColor: 'bg-cyan-50 text-cyan-600' },
};

const STATUS_CONFIG: Record<ConnectionStatus, {
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  label: string;
}> = {
  connected: {
    icon: <CheckCircle2 size={14} />,
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50',
    label: 'Connected',
  },
  disconnected: {
    icon: <XCircle size={14} />,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/30',
    label: 'Disconnected',
  },
  error: {
    icon: <AlertTriangle size={14} />,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    label: 'Error',
  },
  testing: {
    icon: <Loader2 size={14} className="animate-spin" />,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    label: 'Testing...',
  },
};

const FREQUENCY_LABELS: Record<SyncFrequency, string> = {
  realtime: 'Real-time',
  hourly: 'Hourly',
  daily: 'Daily',
  weekly: 'Weekly',
  manual: 'Manual',
};

// ── Sub-components ─────────────────────────────────────────────────────────

function SourceCard({
  source,
  isExpanded,
  onToggle,
  onTest,
  onDelete,
  isTesting,
}: {
  source: DataSource;
  isExpanded: boolean;
  onToggle: () => void;
  onTest: () => void;
  onDelete: () => void;
  isTesting: boolean;
}) {
  const type = TYPE_CONFIG[source.type];
  const status = STATUS_CONFIG[isTesting ? 'testing' : source.status];

  return (
    <div className={cn(
      "bg-card border rounded-xl transition-all",
      isExpanded ? "border-neutral-300 shadow-sm" : "border-border hover:border-neutral-300"
    )}>
      <div className="p-4" onClick={onToggle}>
        <div className="flex items-center gap-4">
          {/* Type Icon */}
          <div className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center shrink-0",
            type.bgColor
          )}>
            {type.icon}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <h3 className="text-[14px] font-semibold text-foreground">{source.name}</h3>
              <span className={cn(
                "inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full",
                status.bgColor, status.color
              )}>
                {status.icon} {status.label}
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground/60 truncate">{source.endpoint || 'No endpoint configured'}</p>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-6 text-right shrink-0">
            {source.recordCount !== undefined && (
              <div>
                <p className="text-[14px] font-bold text-foreground">{source.recordCount.toLocaleString()}</p>
                <p className="text-[10px] text-muted-foreground/60">records</p>
              </div>
            )}
            <div>
              <p className={cn(
                "text-[14px] font-bold",
                source.healthScore >= 90 ? "text-emerald-600" :
                source.healthScore >= 70 ? "text-amber-600" : "text-red-600"
              )}>
                {source.healthScore}%
              </p>
              <p className="text-[10px] text-muted-foreground/60">health</p>
            </div>
            <div>
              <p className="text-[12px] font-medium text-muted-foreground">{FREQUENCY_LABELS[source.syncFrequency]}</p>
              <p className="text-[10px] text-muted-foreground/60">sync</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => { e.stopPropagation(); onTest(); }}
              disabled={isTesting}
              className="p-2 rounded hover:bg-muted/30 text-muted-foreground/60 hover:text-muted-foreground disabled:opacity-50"
              title="Test connection"
            >
              <TestTube size={14} />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              className="p-2 rounded hover:bg-red-50 text-muted-foreground/60 hover:text-red-500"
              title="Delete source"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>

        {/* Error Message */}
        {source.status === 'error' && source.errorMessage && (
          <div className="mt-3 p-2 bg-red-50 border border-red-100 rounded-lg text-[11px] text-red-600 flex items-start gap-2">
            <AlertTriangle size={12} className="shrink-0 mt-0.5" />
            {source.errorMessage}
          </div>
        )}
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-border/50 pt-3">
          {/* Sync Info */}
          <div className="flex items-center gap-6 mb-4 text-[11px] text-muted-foreground">
            {source.lastSyncAt && (
              <span className="flex items-center gap-1">
                <Clock size={12} />
                Last sync: {new Date(source.lastSyncAt).toLocaleString()}
              </span>
            )}
            {source.nextSyncAt && (
              <span className="flex items-center gap-1">
                <RefreshCw size={12} />
                Next sync: {new Date(source.nextSyncAt).toLocaleString()}
              </span>
            )}
          </div>

          {/* Field Mappings */}
          {source.fieldMappings.length > 0 && (
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Field Mappings ({source.fieldMappings.length})
              </h4>
              <div className="bg-muted/20 rounded-lg border border-border overflow-hidden">
                <table className="w-full text-[11px]">
                  <thead className="bg-muted/30">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-muted-foreground">Source Field</th>
                      <th className="px-3 py-2 text-center font-medium text-muted-foreground">→</th>
                      <th className="px-3 py-2 text-left font-medium text-muted-foreground">Target Field</th>
                      <th className="px-3 py-2 text-center font-medium text-muted-foreground">Required</th>
                    </tr>
                  </thead>
                  <tbody>
                    {source.fieldMappings.map((mapping, idx) => (
                      <tr key={idx} className="border-t border-border">
                        <td className="px-3 py-2 font-mono text-muted-foreground">{mapping.sourceField}</td>
                        <td className="px-3 py-2 text-center text-muted-foreground/60">→</td>
                        <td className="px-3 py-2 font-mono text-muted-foreground">{mapping.targetField}</td>
                        <td className="px-3 py-2 text-center">
                          {mapping.isRequired ? (
                            <span className="text-emerald-600">●</span>
                          ) : (
                            <span className="text-neutral-300">○</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 mt-4">
            <Btn variant="ghost" className="text-[11px]">
              <Edit3 size={12} className="mr-1" />
              Edit Configuration
            </Btn>
            <Btn variant="outline" className="text-[11px]">
              <Settings size={12} className="mr-1" />
              Advanced Settings
            </Btn>
          </div>
        </div>
      )}
    </div>
  );
}

function SourceSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="flex items-center gap-4">
        <Skeleton className="w-10 h-10 rounded-lg" />
        <div className="flex-1">
          <Skeleton className="h-5 w-48 mb-1" />
          <Skeleton className="h-3 w-64" />
        </div>
        <div className="flex items-center gap-6">
          <Skeleton className="h-10 w-20" />
          <Skeleton className="h-10 w-16" />
          <Skeleton className="h-10 w-20" />
        </div>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

function SourceConfigurationContent() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<SourceType | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<ConnectionStatus | 'all'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const filteredSources = useMemo(() => {
    let filtered = [...MOCK_SOURCES];

    if (search) {
      const term = search.toLowerCase();
      filtered = filtered.filter(s =>
        s.name.toLowerCase().includes(term) ||
        s.endpoint?.toLowerCase().includes(term)
      );
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter(s => s.type === typeFilter);
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter(s => s.status === statusFilter);
    }

    return filtered;
  }, [search, typeFilter, statusFilter]);

  const stats = useMemo(() => {
    const total = filteredSources.length;
    const connected = filteredSources.filter(s => s.status === 'connected').length;
    const error = filteredSources.filter(s => s.status === 'error').length;
    const totalRecords = filteredSources.reduce((sum, s) => sum + (s.recordCount || 0), 0);
    return { total, connected, error, totalRecords };
  }, [filteredSources]);

  const handleTest = (sourceId: string) => {
    setTestingId(sourceId);
    // Simulate test
    setTimeout(() => setTestingId(null), 2000);
  };

  const handleDelete = (sourceId: string) => {
    if (confirm('Are you sure you want to delete this data source?')) {
      alert('Delete functionality coming soon');
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-6xl">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="space-y-4">
          {[1, 2, 3].map(i => <SourceSkeleton key={i} />)}
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
              <h3 className="text-[14px] font-semibold text-red-800 mb-1">Failed to load sources</h3>
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
          title="Source Configuration"
          subtitle={`${stats.total} sources · ${stats.connected} connected · ${stats.error} errors`}
        />
        <Btn variant="primary" onClick={() => alert('Add source functionality coming soon')}>
          <Plus size={14} className="mr-1" />
          Add Source
        </Btn>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <Database size={14} className="text-blue-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Total Sources</span>
          </div>
          <p className="text-[22px] font-extrabold text-foreground">{stats.total}</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <Plug size={14} className="text-emerald-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Connected</span>
          </div>
          <p className="text-[22px] font-extrabold text-emerald-600">{stats.connected}</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={14} className="text-red-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Errors</span>
          </div>
          <p className="text-[22px] font-extrabold text-red-600">{stats.error}</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <FileText size={14} className="text-violet-500" />
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold">Total Records</span>
          </div>
          <p className="text-[22px] font-extrabold text-violet-600">{(stats.totalRecords / 1000000).toFixed(1)}M</p>
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
            placeholder="Search sources..."
            className="flex-1 text-[13px] bg-transparent outline-none text-muted-foreground"
          />
        </div>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as SourceType | 'all')}
          className="text-[12px] px-3 py-2 border border-border rounded-lg bg-card outline-none"
        >
          <option value="all">All Types</option>
          <option value="crm">CRM</option>
          <option value="database">Database</option>
          <option value="api">API</option>
          <option value="cloud_storage">Cloud Storage</option>
          <option value="file">File</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as ConnectionStatus | 'all')}
          className="text-[12px] px-3 py-2 border border-border rounded-lg bg-card outline-none"
        >
          <option value="all">All Status</option>
          <option value="connected">Connected</option>
          <option value="disconnected">Disconnected</option>
          <option value="error">Error</option>
        </select>
      </div>

      {/* Source List */}
      <div className="space-y-3">
        {filteredSources.map(source => (
          <SourceCard
            key={source.id}
            source={source}
            isExpanded={expandedId === source.id}
            onToggle={() => setExpandedId(expandedId === source.id ? null : source.id)}
            onTest={() => handleTest(source.id)}
            onDelete={() => handleDelete(source.id)}
            isTesting={testingId === source.id}
          />
        ))}
      </div>

      {filteredSources.length === 0 && (
        <div className="text-center py-12 text-muted-foreground/60">
          <Database size={48} className="mx-auto mb-4 text-neutral-300" />
          <p className="text-[14px] font-medium">No sources found</p>
          <p className="text-[12px] mt-1">Add a data source to start ingesting data</p>
          <Btn variant="primary" className="mt-4" onClick={() => alert('Add source functionality coming soon')}>
            <Plus size={14} className="mr-1" />
            Add First Source
          </Btn>
        </div>
      )}
    </div>
  );
}

export default function SourceConfiguration() {
  return (
    <ErrorBoundary>
      <SourceConfigurationContent />
    </ErrorBoundary>
  );
}
