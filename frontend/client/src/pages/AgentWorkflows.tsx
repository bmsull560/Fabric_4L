/**
 * Screen 8 — Agent Workflows Dashboard
 * Design: Refined Enterprise SaaS
 * Data Flow: React Query for server state, Zustand for UI state
 */
import { useState } from "react";
import { Bot, Clock, AlertTriangle, Loader2 } from "lucide-react";
import { useActiveWorkflows, useWorkflowHistory, type Workflow } from "@/hooks/useWorkflows";
import { PageHeader, MetricCard, DataTable, StatusBadge, Btn, SectionCard, Tabs } from "@/components/WfPrimitives";

export default function AgentWorkflows() {
  const [activeTab, setActiveTab] = useState("Workflow Dashboard");

  // Server state: React Query handles fetching, caching, loading, error
  const {
    data: activeWorkflows = [],
    isLoading: activeLoading,
    error: activeError,
    refetch: refetchActive,
  } = useActiveWorkflows();

  const {
    data: workflows = [],
    isLoading: historyLoading,
    error: historyError,
  } = useWorkflowHistory();

  const isLoading = activeLoading || historyLoading;
  const error = activeError || historyError;

  const errorMessage = error
    ? (error as any).response?.data?.detail || (error as Error).message
    : null;

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

      {/* Error display */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-red-600" />
            <span className="text-red-700 text-sm">{errorMessage}</span>
            <Btn variant="ghost" className="text-[11px] ml-auto" onClick={() => refetchActive()}>Retry</Btn>
          </div>
        </div>
      )}

      {/* KPI row */}
      <div className="flex gap-4 mb-6">
        <MetricCard
          label="Active Workflows"
          value={activeWorkflows.filter((w: Workflow) => w.status === 'running').length.toString()}
          trend={isLoading ? "Loading..." : "Running now"}
        />
        <MetricCard
          label="Completed Today"
          value={workflows.filter((w: Workflow) => w.status === 'completed').length.toString()}
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
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 size={24} className="animate-spin text-blue-600" />
              <span className="ml-2 text-neutral-500">Loading workflows...</span>
            </div>
          ) : activeWorkflows.length === 0 ? (
            <div className="text-center p-8 text-neutral-500">
              No active workflows. Start a new analysis to see agents in action.
            </div>
          ) : (
            activeWorkflows.map((workflow: Workflow) => (
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
            ))
          )}
        </div>
      </SectionCard>

      {/* History */}
      <SectionCard title="Workflow History" noPad>
        <DataTable
          columns={["Job ID", "Name", "Status", "Progress", "Created", "Actions"]}
          rows={workflows.map((w: Workflow) => [
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
        {workflows.length === 0 && !isLoading && (
          <div className="text-center p-8 text-neutral-500">
            No workflow history available.
          </div>
        )}
      </SectionCard>
    </div>
  );
}
