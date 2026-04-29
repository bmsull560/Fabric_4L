/**
 * Ingestion Jobs Page
 * Design: Refined Enterprise SaaS matching the wireframe
 *
 * Layout:
 *   - Page header with title, Refresh, and + New Job buttons
 *   - Filter controls (Status, Source, Date Range)
 *   - Job queue table (left, wide)
 *   - Actions panel with Run All, Pause (right top)
 *   - Job detail panel (right mid)
 *   - Logs/Output panel (right bottom)
 */
import { useState, useMemo, useCallback } from 'react';
import { useLocation } from 'wouter';
import { RefreshCw, Plus, Play, Pause, ChevronLeft, ChevronRight, AlertCircle, Info } from 'lucide-react';
import { PageHeader, Btn } from '@/components/WfPrimitives';
import { DataTable, type DataTableColumn } from '@/components/ui/fabric/DataTable';
import { StatusBadge } from '@/components/ui/fabric/StatusBadge';
import { useIngestionJobsStore, type JobStatusFilter } from '@/stores/ingestionJobsStore';
import {
  useIngestionJobList,
  useIngestionJobDetail,
  useJobComplianceLogs,
  useCancelJob,
  useRetryJob,
  type JobListFilters,
  type IngestionJob,
} from '@/hooks/useIngestion';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const STATUS_OPTIONS: { value: JobStatusFilter; label: string }[] = [
  { value: 'all', label: 'All Status' },
  { value: 'pending', label: 'Pending' },
  { value: 'processing', label: 'Processing' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
];

const PAGE_SIZE = 15;

const STAGE_STATUS_COLORS = {
  COMPLETED: 'text-emerald-600',
  FAILED: 'text-destructive',
  RUNNING: 'text-amber-600',
  DEFAULT: 'text-muted-foreground',
} as const;

const JOB_ID_TRUNCATE_TABLE = 8;
const JOB_ID_TRUNCATE_DETAIL = 16;

function truncateId(id: string, length: number): string {
  if (!id || id.length <= length) return id ?? '—';
  return `${id.slice(0, length)}...`;
}

const JOB_STATUS_VARIANTS: Record<string, 'default' | 'secondary' | 'outline' | 'destructive' | 'success' | 'warning' | 'info' | 'pending'> = {
  completed: 'success',
  processing: 'warning',
  pending: 'pending',
  failed: 'destructive',
};

export default function IngestionJobs() {
  // UI state from Zustand store
  const { selectedJobId, setSelectedJobId, filters, setStatusFilter, setDateFrom, setDateTo, resetFilters } =
    useIngestionJobsStore();

  // Local pagination state
  const [page, setPage] = useState(1);

  // Build API filters
  const apiFilters: JobListFilters = useMemo(
    () => ({
      status: filters.status === 'all' ? undefined : [filters.status.toUpperCase()],
      dateFrom: filters.dateFrom || undefined,
      dateTo: filters.dateTo || undefined,
      sortBy: 'created_at',
      sortOrder: 'desc',
      page,
      limit: PAGE_SIZE,
    }),
    [filters, page]
  );

  // Data fetching
  const { data: listData, isLoading: listLoading, error: listError, refetch } = useIngestionJobList(apiFilters);
  const { data: detailData, isLoading: detailLoading } = useIngestionJobDetail(selectedJobId);
  const { data: logsData, isLoading: logsLoading } = useJobComplianceLogs(selectedJobId);

  // Mutations
  const cancelJob = useCancelJob();
  const retryJob = useRetryJob();

  const jobs = listData?.jobs ?? [];
  const pagination = listData?.pagination ?? { page: 1, limit: PAGE_SIZE, total: 0, totalPages: 1 };

  const [, setLocation] = useLocation();

  // Handlers
  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleNewJob = useCallback(() => {
    setLocation('/home');
  }, [setLocation]);

  const handleRowClick = useCallback((job: IngestionJob) => {
    setSelectedJobId(job.id === selectedJobId ? null : job.id);
  }, [selectedJobId, setSelectedJobId]);

  const handleCancelJob = useCallback(async () => {
    if (!selectedJobId || cancelJob.isPending) return;
    try {
      await cancelJob.mutateAsync(selectedJobId);
    } catch {
      // Error is handled by mutation state and displayed in UI
    }
  }, [selectedJobId, cancelJob]);

  const handleRetryJob = useCallback(async () => {
    if (!selectedJobId || retryJob.isPending) return;
    try {
      await retryJob.mutateAsync(selectedJobId);
    } catch {
      // Error is handled by mutation state and displayed in UI
    }
  }, [selectedJobId, retryJob]);

  // Table columns definition using fabric DataTable format
  const columns: DataTableColumn<IngestionJob>[] = [
    { key: 'id', header: 'Job ID', render: (job) => (
      <span className="font-mono text-[11px] text-muted-foreground">
        {truncateId(job.id, JOB_ID_TRUNCATE_TABLE)}
      </span>
    )},
    { key: 'domain', header: 'Domain', render: (job) => (
      <span className="font-medium text-foreground truncate max-w-[150px]" title={job.domain}>
        {job.domain}
      </span>
    )},
    { key: 'status', header: 'Status', render: (job) => (
      <StatusBadge variant={JOB_STATUS_VARIANTS[job.status] ?? 'default'}>
        {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
      </StatusBadge>
    )},
    { key: 'progress', header: 'Progress', render: (job) => (
      <div className="flex items-center gap-2">
        <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all"
            style={{ width: `${job.progress}%` }}
          />
        </div>
        <span className="text-[11px] text-muted-foreground">{job.progress}%</span>
      </div>
    )},
    { key: 'createdAt', header: 'Created', render: (job) => (
      <span className="text-[11px] text-muted-foreground">
        {new Date(job.createdAt).toLocaleDateString()}
      </span>
    )},
  ];

  return (
    <TooltipProvider>
    <div className="p-6 h-full flex flex-col">
      {/* Page Header */}
      <PageHeader
        title="Ingestion Jobs"
        subtitle="Monitor and manage data ingestion pipeline"
        actions={
          <div className="flex items-center gap-2">
            <Btn variant="ghost" onClick={handleRefresh} disabled={listLoading}>
              <RefreshCw size={13} className={listLoading ? 'animate-spin' : ''} />
              Refresh
            </Btn>
            <Btn variant="primary" onClick={handleNewJob}>
              <Plus size={13} />
              New Job
            </Btn>
          </div>
        }
      />

      {/* Main Content Grid */}
      <div className="flex-1 grid grid-cols-[1fr_320px] gap-4 min-h-0">
        {/* Left Column: Filters + Job Queue */}
        <div className="flex flex-col gap-4 min-h-0">
          {/* Filter Controls */}
          <div className="bg-card border border-border rounded-lg p-3 flex items-center gap-3 flex-wrap">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Filter Controls</span>
            <div className="flex items-center gap-2">
              <label className="text-[11px] text-muted-foreground">Status:</label>
              <select
                value={filters.status}
                onChange={(e) => {
                  setStatusFilter(e.target.value as JobStatusFilter);
                  setPage(1);
                }}
                className="text-[12px] border border-border rounded px-2 py-1 bg-background"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-[11px] text-muted-foreground">From:</label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => {
                  setDateFrom(e.target.value);
                  setPage(1);
                }}
                className="text-[12px] border border-border rounded px-2 py-1 bg-background"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-[11px] text-muted-foreground">To:</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => {
                  setDateTo(e.target.value);
                  setPage(1);
                }}
                className="text-[12px] border border-border rounded px-2 py-1 bg-background"
              />
            </div>
            {(filters.status !== 'all' || filters.dateFrom || filters.dateTo) && (
              <button
                onClick={() => {
                  resetFilters();
                  setPage(1);
                }}
                className="text-[11px] text-primary hover:underline ml-auto"
              >
                Reset filters
              </button>
            )}
          </div>

          {/* Job Queue Table */}
          <div className="bg-card border border-border rounded-lg flex-1 flex flex-col min-h-0 overflow-hidden">
            <div className="px-4 pt-3 pb-2 border-b border-border flex items-center justify-between">
              <span className="text-[13px] font-bold text-foreground">Job Queue</span>
              <span className="text-[11px] text-muted-foreground">
                {pagination.total} total jobs
              </span>
            </div>
            <div className="flex-1 overflow-auto">
              {listError ? (
                <div className="p-8 text-center">
                  <AlertCircle size={24} className="text-destructive mx-auto mb-2" />
                  <p className="text-[12px] text-muted-foreground mb-2">Failed to load jobs</p>
                  <button
                    onClick={handleRefresh}
                    className="text-[12px] text-primary hover:underline"
                  >
                    Try again
                  </button>
                </div>
              ) : (
                <DataTable
                  data={jobs}
                  columns={columns}
                  keyExtractor={(job) => job.id}
                  onRowClick={handleRowClick}
                  selectedKey={selectedJobId ?? undefined}
                  emptyMessage={listLoading ? '' : (filters.status !== 'all' || filters.dateFrom || filters.dateTo)
                    ? 'No jobs match your filters'
                    : 'No jobs found — create a new job to get started'
                  }
                />
              )}
              {listLoading && (
                <div className="p-4 space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-8 w-full" />
                  ))}
                </div>
              )}
            </div>
            {/* Pagination */}
            <div className="px-4 py-2 border-t border-border flex items-center justify-between">
              <span className="text-[11px] text-muted-foreground">
                Page {pagination.page} of {pagination.totalPages}
              </span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1 || listLoading}
                  className="p-1 rounded hover:bg-muted disabled:opacity-50"
                >
                  <ChevronLeft size={14} />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(pagination.totalPages, p + 1))}
                  disabled={page >= pagination.totalPages || listLoading}
                  className="p-1 rounded hover:bg-muted disabled:opacity-50"
                >
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Actions + Job Detail + Logs */}
        <div className="flex flex-col gap-4 min-h-0">
          {/* Actions Panel */}
          <div className="bg-card border border-border rounded-lg p-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-2">
              Actions
            </span>
            <div className="flex items-center gap-2">
              {/* Batch operations coming soon - disabled pending backend support */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Btn variant="outline" className="flex-1" disabled>
                    <Play size={13} />
                    Run All
                  </Btn>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p className="text-[11px]">Batch Run All — coming in future release</p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Btn variant="outline" className="flex-1" disabled>
                    <Pause size={13} />
                    Pause
                  </Btn>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p className="text-[11px]">Batch Pause — coming in future release</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>

          {/* Job Detail Panel */}
          <div className="bg-card border border-border rounded-lg flex-1 flex flex-col min-h-0">
            <div className="px-4 pt-3 pb-2 border-b border-border">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Job Detail</span>
            </div>
            <div className="flex-1 overflow-auto p-4">
              {!selectedJobId ? (
                <p data-testid="job-detail-empty-state" className="text-[12px] text-muted-foreground text-center py-8">
                  Select a job from the queue to view details
                </p>
              ) : detailLoading ? (
                <div className="space-y-3" data-testid="job-detail-loading-state">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-4 w-2/3" />
                </div>
              ) : detailData ? (
                <div className="space-y-3 text-[12px]">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">ID:</span>
                    <span className="font-mono text-[11px]">{truncateId(detailData.id, JOB_ID_TRUNCATE_DETAIL)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status:</span>
                    <StatusBadge variant={JOB_STATUS_VARIANTS[detailData.status] ?? 'default'}>
                      {detailData.status.charAt(0).toUpperCase() + detailData.status.slice(1)}
                    </StatusBadge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Priority:</span>
                    <span>{detailData.priority}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Domain:</span>
                    <span className="truncate max-w-[150px]" title={detailData.domain}>
                      {detailData.domain}
                    </span>
                  </div>
                  <div className="border-t border-border pt-2 mt-2">
                    <span className="text-[10px] font-semibold uppercase text-muted-foreground block mb-1">
                      Progress
                    </span>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${detailData.progress?.percentComplete ?? 0}%` }}
                        />
                      </div>
                      <span className="text-[11px]">{detailData.progress?.percentComplete ?? 0}%</span>
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      {detailData.progress?.processedPages ?? 0} / {detailData.progress?.totalPages ?? '?'} pages
                    </div>
                  </div>
                  {detailData.stages && detailData.stages.length > 0 && (
                    <div className="border-t border-border pt-2">
                      <span className="text-[10px] font-semibold uppercase text-muted-foreground block mb-1">
                        Stages
                      </span>
                      <div className="space-y-1">
                        {detailData.stages.map((stage, i) => (
                          <div key={i} className="flex items-center justify-between text-[11px]">
                            <span className="truncate">{stage.stage}</span>
                            <span
                              className={
                                STAGE_STATUS_COLORS[stage.status as keyof typeof STAGE_STATUS_COLORS] ??
                                STAGE_STATUS_COLORS.DEFAULT
                              }
                            >
                              {stage.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {detailData.errors && detailData.errors.length > 0 && (
                    <div className="border-t border-border pt-2">
                      <span className="text-[10px] font-semibold uppercase text-destructive block mb-1">
                        Errors ({detailData.errors.length})
                      </span>
                      <div className="space-y-1 max-h-24 overflow-auto">
                        {detailData.errors.map((err) => (
                          <div key={err.id} className="text-[11px] text-destructive p-1 bg-destructive/5 rounded">
                            <div className="font-semibold">{err.errorCode}</div>
                            <div className="truncate">{err.errorMessage}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* Action Buttons */}
                  <div className="border-t border-border pt-3 flex gap-2">
                    {detailData.status === 'failed' && (
                      <Btn variant="primary" className="flex-1" onClick={handleRetryJob} disabled={retryJob.isPending}>
                        {retryJob.isPending ? 'Retrying...' : 'Retry Job'}
                      </Btn>
                    )}
                    {(detailData.status === 'pending' || detailData.status === 'processing') && (
                      <Btn
                        variant="danger"
                        className="flex-1"
                        onClick={handleCancelJob}
                        disabled={cancelJob.isPending}
                      >
                        {cancelJob.isPending ? 'Cancelling...' : 'Cancel Job'}
                      </Btn>
                    )}
                  </div>
                  {/* Mutation Error Display */}
                  {(retryJob.error || cancelJob.error) && (
                    <div className="mt-2 p-2 bg-destructive/10 border border-destructive/20 rounded text-[11px] text-destructive">
                      <div className="flex items-start gap-1.5">
                        <AlertCircle size={12} className="mt-0.5 shrink-0" />
                        <div>
                          <p className="font-semibold">Action failed</p>
                          <p className="text-destructive/80">
                            {retryJob.error?.message || cancelJob.error?.message || 'Please try again'}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-[12px] text-muted-foreground text-center py-8">Job not found</p>
              )}
            </div>
          </div>

          {/* Logs / Output Panel */}
          <div className="bg-card border border-border rounded-lg h-48 flex flex-col">
            <div className="px-4 pt-3 pb-2 border-b border-border">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Logs / Output
              </span>
            </div>
            <div className="flex-1 overflow-auto p-3">
              {!selectedJobId ? (
                <p className="text-[11px] text-muted-foreground text-center py-4">
                  Select a job to view logs
                </p>
              ) : logsLoading ? (
                <div className="space-y-2" data-testid="job-logs-loading-state">
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              ) : logsData && logsData.length > 0 ? (
                <div className="space-y-1" data-testid="job-logs-list-state">
                  {logsData.map((log) => (
                    <div key={log.id} className="text-[11px] border-b border-border/50 pb-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={
                            log.severity === 'ERROR'
                              ? 'text-destructive font-semibold'
                              : log.severity === 'WARNING'
                              ? 'text-amber-600'
                              : 'text-muted-foreground'
                          }
                        >
                          {log.severity}
                        </span>
                        <span className="text-muted-foreground">
                          {new Date(log.createdAt).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-foreground truncate" title={log.eventType}>
                        {log.eventType}
                      </div>
                      {log.requestUrl && (
                        <div className="text-muted-foreground truncate text-[10px]" title={log.requestUrl}>
                          {log.requestUrl}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p data-testid="job-logs-empty-state" className="text-[11px] text-muted-foreground text-center py-4">No logs available</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
    </TooltipProvider>
  );
}
