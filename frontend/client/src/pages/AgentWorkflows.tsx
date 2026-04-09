/**
 * Screen 8 — Agent Workflows Dashboard
 * Design: Refined Enterprise SaaS
 */
import { useState } from "react";
import { Bot, Clock, AlertTriangle, CheckCircle2, Play, Pause } from "lucide-react";
import { PageHeader, MetricCard, DataTable, StatusBadge, Btn, SectionCard, Tabs } from "@/components/WfPrimitives";

const ACTIVE_AGENTS = [
  {
    id: "WhitespaceAnalyzer-v2.1",
    target: "GlobalFin Corp",
    step: "Step 3/6: Value Tree Projection",
    elapsed: "1m 24s",
    status: "running" as const,
  },
  {
    id: "BusinessCaseGenerator-v3.0",
    target: "TechCorp Inc",
    step: "Step 5/6: ROI Calculation",
    elapsed: "3m 07s",
    status: "running" as const,
  },
  {
    id: "NarrativeSynthesis-v2.3",
    target: "MegaBank Ltd",
    step: "Awaiting human review: Confidence below threshold",
    elapsed: "Paused",
    status: "paused" as const,
    needsReview: true,
  },
];

const HISTORY = [
  { id: "WA-2241", type: "Whitespace Analysis",  account: "Acme Corp",   status: "completed" as const, duration: "2m 14s", ts: "09:41" },
  { id: "BC-1892", type: "Business Case",         account: "Globex IO",   status: "completed" as const, duration: "4m 03s", ts: "09:38" },
  { id: "NS-0731", type: "Narrative Synthesis",   account: "Initech",     status: "failed" as const,    duration: "1m 55s", ts: "09:35" },
  { id: "WA-2240", type: "Whitespace Analysis",   account: "MegaBank",    status: "completed" as const, duration: "2m 48s", ts: "09:30" },
];

export default function AgentWorkflows() {
  const [activeTab, setActiveTab] = useState("Workflow Dashboard");

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
        <MetricCard label="Active Workflows"       value="3"    trend="Running now" />
        <MetricCard label="Completed Today"        value="12"   trend="+4 vs yesterday" trendUp />
        <MetricCard label="Avg. Completion Time"   value="3.2m" trend="Target: <5m" />
        <MetricCard label="Human-in-Loop Pending"  value="2"    trend="Needs review" />
      </div>

      {/* Active agents */}
      <SectionCard title="Active Agents" className="mb-5">
        <div className="p-4 space-y-3">
          {ACTIVE_AGENTS.map(agent => (
            <div
              key={agent.id}
              className={`flex items-start gap-3 p-3 rounded-lg border ${
                agent.needsReview
                  ? "bg-amber-50 border-amber-200"
                  : "bg-neutral-50 border-neutral-200"
              }`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                agent.needsReview ? "bg-amber-100" : "bg-blue-100"
              }`}>
                {agent.needsReview
                  ? <AlertTriangle size={14} className="text-amber-600"/>
                  : <Bot size={14} className="text-blue-600"/>
                }
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-[12px] font-bold text-neutral-900 font-mono">{agent.id}</span>
                  <StatusBadge status={agent.status}/>
                </div>
                <div className="text-[11px] text-neutral-600">
                  Analyzing: <span className="font-semibold">{agent.target}</span>
                  {" · "}{agent.step}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <div className="flex items-center gap-1 text-[11px] text-neutral-400">
                  <Clock size={10}/>
                  {agent.elapsed}
                </div>
                {agent.needsReview
                  ? <Btn variant="primary" className="text-[11px]">Review</Btn>
                  : <Btn variant="ghost" className="text-[11px]">View</Btn>
                }
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      {/* History */}
      <SectionCard title="Workflow History" noPad>
        <DataTable
          columns={["Job ID", "Type", "Account", "Status", "Duration", "Time", "Actions"]}
          rows={HISTORY.map(h => [
            <span className="font-mono text-[11px] text-neutral-600">{h.id}</span>,
            <span className="text-neutral-700">{h.type}</span>,
            <span className="font-semibold text-neutral-800">{h.account}</span>,
            <StatusBadge status={h.status}/>,
            <span className="text-neutral-500 text-[11px]">{h.duration}</span>,
            <span className="text-neutral-400 text-[11px]">{h.ts}</span>,
            <div className="flex gap-2">
              <a href="#" className="text-blue-600 text-[11px] hover:underline">View</a>
            </div>,
          ])}
        />
      </SectionCard>
    </div>
  );
}
