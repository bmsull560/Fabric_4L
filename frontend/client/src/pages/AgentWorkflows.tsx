/**
 * Screen 8 — Agent Workflows Dashboard
 * Design: Refined Enterprise SaaS
 * Data Flow: React Query for server state, Zustand for UI state
 */
import { useState } from "react";
import { Bot, Clock, AlertTriangle, ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { useActiveWorkflows, useWorkflowHistory, type Workflow } from "@/hooks/useWorkflows";
import { PageHeader, MetricCard, DataTable, StatusBadge, Btn, SectionCard, Tabs } from "@/components/WfPrimitives";
import { QueryState } from "@/components/QueryState";

const ITEMS_PER_PAGE = 10;

// Pagination display range helper
function getDisplayRange(page: number, itemsPerPage: number, total: number): string {
  const start = page * itemsPerPage + 1;
  const end = Math.min((page + 1) * itemsPerPage, total);
  return `Showing ${start} - ${end} of ${total}`;
}

// Reusable pagination controls component
interface PaginationControlsProps {
  page: number;
  totalPages: number;
  hasMore: boolean;
  isLoading: boolean;
  displayRange: string;
  onPrevious: () => void;
  onNext: () => void;
  onRefresh: () => void;
}

function PaginationControls({
  page,
  totalPages,
  hasMore,
  isLoading,
  displayRange,
  onPrevious,
  onNext,
  onRefresh,
}: PaginationControlsProps) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-neutral-100 mt-2">
      <div className="flex items-center gap-2">
        <span className="text-xs text-neutral-500">{displayRange}</span>
        {hasMore && (
          <span className="text-[10px] text-blue-600 bg-blue-50 px-2 py-0.5 rounded">More available</span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Btn
          variant="ghost"
          onClick={onPrevious}
          disabled={page === 0 || isLoading}
          className="text-xs"
        >
          <ChevronLeft size={14} className="mr-1" /> Previous
        </Btn>
        <span className="text-xs text-neutral-400">
          Page {page + 1} of {totalPages || 1}
        </span>
        <Btn
          variant="ghost"
          onClick={onNext}
          disabled={!hasMore || isLoading || page >= totalPages - 1}
          className="text-xs"
        >
          Next <ChevronRight size={14} className="ml-1" />
        </Btn>
        <div className="w-px h-4 bg-neutral-200 mx-1" />
        <Btn
          variant="ghost"
          onClick={onRefresh}
          disabled={isLoading}
          className="text-xs"
        >
          <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
        </Btn>
      </div>
    </div>
  );
}

export default function AgentWorkflows() {
  const [activeTab, setActiveTab] = useState("Workflow Dashboard");
  
  // Pagination state
  const [activePage, setActivePage] = useState(0);
  const [historyPage, setHistoryPage] = useState(0);

  // Server state: React Query handles fetching, caching, loading, error
  const {
    data: activeData,
    isLoading: activeLoading,
    error: activeError,
    refetch: refetchActive,
  } = useActiveWorkflows({ 
    limit: ITEMS_PER_PAGE, 
    offset: activePage * ITEMS_PER_PAGE 
  });

  const {
    data: historyData,
    isLoading: historyLoading,
    error: historyError,
    refetch: refetchHistory,
  } = useWorkflowHistory({ 
    limit: ITEMS_PER_PAGE, 
    offset: historyPage * ITEMS_PER_PAGE 
  });

  // Extract items from paginated response
  const activeWorkflows = activeData?.items ?? [];
  const historyWorkflows = historyData?.items ?? [];
  
  const isLoading = activeLoading || historyLoading;
  const error = activeError || historyError;
  
  // Pagination helpers
  const activeTotalPages = activeData ? Math.ceil(activeData.total / ITEMS_PER_PAGE) : 0;
  const historyTotalPages = historyData ? Math.ceil(historyData.total / ITEMS_PER_PAGE) : 0;

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        breadcrumbs={["Agent Workflows", "Dashboard"]}
        title="Workflow Dashboard"
        subtitle="Monitor and manage AI agent workflows across all active analyses."
      />

      <Tabs
        tabs={["Workflow Dashboard", "Whitespace Analysis", "Business Cases"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      {/* KPI row */}
      <div className="flex gap-4 mb-6">
        <MetricCard
          label="Active Workflows"
          value={activeWorkflows.filter((w: Workflow) => w.status === 'running').length.toString()}
          trend={isLoading ? "Loading..." : "Running now"}
        />
        <MetricCard
          label="Completed Today"
          value={historyWorkflows.filter((w: Workflow) => w.status === 'completed').length.toString()}
          trend="+4 vs yesterday"
          trendUp
        />
        <MetricCard label="Avg. Completion Time" value="3.2m" trend="Target: <5m" />
        <MetricCard
          label="Human-in-Loop Pending"
          value={activeWorkflows.filter((w: Workflow) => w.status === 'pending').length.toString()}
          trend="Needs review"
        />
      </div>

      {/* Active agents */}
      <SectionCard title="Active Agents" className="mb-5">
        <div className="p-4 space-y-3">
          <QueryState
            isLoading={isLoading}
            error={error}
            isEmpty={activeWorkflows.length === 0}
            emptyMessage="No active workflows."
            emptySubMessage="Start a new analysis to see agents in action."
            loadingMessage="Loading workflows…"
          >
            {activeWorkflows.map((workflow: Workflow) => (
              <div
                key={workflow.id}
                className={`flex items-start gap-3 p-3 rounded-lg border ${
                  workflow.status === 'pending'
                    ? "bg-amber-50 border-amber-200"
                    : "bg-neutral-50 border-neutral-200"
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  workflow.status === 'pending' ? "bg-amber-100" : "bg-blue-100"
                }`}>
                  {workflow.status === 'pending'
                    ? <AlertTriangle size={14} className="text-amber-600"/>
                    : <Bot size={14} className="text-blue-600"/>
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[12px] font-bold text-neutral-900 font-mono">{workflow.id}</span>
                    <StatusBadge status={workflow.status}/>
                  </div>
                  <div className="text-[11px] text-neutral-600">
                    <span className="font-semibold">{workflow.name}</span>
                    {workflow.progress > 0 && (
                      <span className="ml-2">Progress: {workflow.progress}%</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <div className="flex items-center gap-1 text-[11px] text-neutral-400">
                    <Clock size={10}/>
                    {workflow.status}
                  </div>
                  <Btn variant="ghost" className="text-[11px]">View</Btn>
                </div>
              </div>
            ))}
          </QueryState>
          
          {/* Active Workflows Pagination */}
          {activeData && activeData.total > ITEMS_PER_PAGE && (
            <PaginationControls
              page={activePage}
              totalPages={activeTotalPages}
              hasMore={activeData.has_more}
              isLoading={activeLoading}
              displayRange={getDisplayRange(activePage, ITEMS_PER_PAGE, activeData.total)}
              onPrevious={() => setActivePage(p => Math.max(0, p - 1))}
              onNext={() => setActivePage(p => Math.min(activeTotalPages - 1, p + 1))}
              onRefresh={refetchActive}
            />
          )}
        </div>
      </SectionCard>

      {/* History */}
      <SectionCard title="Workflow History" noPad>
        <QueryState
          isLoading={historyLoading}
          error={historyError}
          isEmpty={historyWorkflows.length === 0}
          emptyMessage="No workflow history available."
        >
          <DataTable
            columns={["Job ID", "Name", "Status", "Progress", "Created", "Actions"]}
            rows={historyWorkflows.map((w: Workflow) => [
              <span className="font-mono text-[11px] text-neutral-600">{w.id}</span>,
              <span className="text-neutral-700 font-semibold">{w.name}</span>,
              <StatusBadge status={w.status}/>,
              <span className="text-neutral-500 text-[11px]">{w.progress}%</span>,
              <span className="text-neutral-400 text-[11px]">{w.createdAt ? new Date(w.createdAt).toLocaleDateString() : '-'}</span>,
              <div className="flex gap-2">
                <button className="text-blue-600 text-[11px] hover:underline">View</button>
              </div>,
            ])}
          />
        </QueryState>
        
        {/* Pagination Controls */}
        {historyData && historyData.total > ITEMS_PER_PAGE && (
          <PaginationControls
            page={historyPage}
            totalPages={historyTotalPages}
            hasMore={historyData.has_more}
            isLoading={historyLoading}
            displayRange={getDisplayRange(historyPage, ITEMS_PER_PAGE, historyData.total)}
            onPrevious={() => setHistoryPage(p => Math.max(0, p - 1))}
            onNext={() => setHistoryPage(p => Math.min(historyTotalPages - 1, p + 1))}
            onRefresh={refetchHistory}
          />
        )}
      </SectionCard>
    </div>
  );
}
