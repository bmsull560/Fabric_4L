/**
 * Home — Personalized Dashboard
 * Design: Refined Enterprise SaaS
 *
 * Displays a real-time overview of the value fabric pipeline:
 * - Pipeline summary (accounts, readiness, coverage)
 * - Active workflows
 * - System health status
 * - Ingestion stats
 * - Top accounts by deal readiness
 *
 * Connected hooks:
 * - usePipelineSummary (L4 Intelligence)
 * - useActiveWorkflows (L4 Agents)
 * - useSystemHealth (Platform)
 * - useHealthAlerts (Platform)
 * - useIngestionStats (L1 Ingestion)
 */
import { Link } from "wouter";
import {
  Activity, Users, Zap, AlertTriangle, CheckCircle2,
  ArrowRight, BarChart3, Database, Bot, Shield
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { SectionCard, Btn } from "@/components/WfPrimitives";
import { usePipelineSummary } from "@/hooks/useIntelligence";
import { useActiveWorkflows, type Workflow } from "@/hooks/useWorkflows";
import { useSystemHealth, useHealthAlerts } from "@/hooks/useHealthMonitor";
import { useIngestionStats } from "@/hooks/useIngestion";
import { cn } from "@/lib/utils";

// ── Helpers ──────────────────────────────────────────────────────────────────────────────
function statusColor(status: string) {
  switch (status) {
    case "healthy": return "text-emerald-600";
    case "degraded": return "text-amber-600";
    case "unhealthy": return "text-red-600";
    default: return "text-neutral-500";
  }
}

function workflowStatusBadge(status: Workflow["status"]) {
  const map: Record<string, string> = {
    running: "bg-blue-100 text-blue-800",
    pending: "bg-amber-100 text-amber-800",
    completed: "bg-emerald-100 text-emerald-800",
    failed: "bg-red-100 text-red-800",
    cancelled: "bg-neutral-100 text-neutral-700",
  };
  return (
    <span className={cn("px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase", map[status] || map.pending)}>
      {status}
    </span>
  );
}

// ── Stat Card ────────────────────────────────────────────────────────────────────────────
function StatCard({ icon: Icon, label, value, sub, color }: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="p-4 bg-white border border-neutral-100 rounded-xl">
      <div className="flex items-center gap-2 mb-2">
        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", color || "bg-blue-50")}>
          <Icon size={16} className={color?.includes("red") ? "text-red-600" : color?.includes("amber") ? "text-amber-600" : color?.includes("emerald") ? "text-emerald-600" : "text-blue-600"} />
        </div>
        <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-[24px] font-extrabold text-neutral-900">{value}</div>
      {sub && <div className="text-[11px] text-neutral-500 mt-0.5">{sub}</div>}
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────────────────
export default function Home() {
  const { data: pipeline, isLoading: pipelineLoading } = usePipelineSummary();
  const { data: workflows, isLoading: workflowsLoading } = useActiveWorkflows({ limit: 5, status: "running" });
  const { data: health, isLoading: healthLoading } = useSystemHealth();
  const { data: alerts } = useHealthAlerts();
  const { data: ingestion, isLoading: ingestionLoading } = useIngestionStats();

  const activeAlerts = alerts?.filter(a => !a.resolved_at) ?? [];
  const isLoading = pipelineLoading || workflowsLoading || healthLoading || ingestionLoading;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-[24px] font-extrabold text-neutral-900">Value Fabric Dashboard</h1>
        <p className="text-[13px] text-neutral-500 mt-1">
          Real-time overview of your intelligence pipeline, workflows, and system health.
        </p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {isLoading ? (
          [1, 2, 3, 4].map(i => <Skeleton key={i} className="h-[100px] rounded-xl" />)
        ) : (
          <>
            <StatCard
              icon={Users}
              label="Accounts"
              value={pipeline?.total_accounts ?? 0}
              sub={`Avg readiness: ${pipeline?.avg_deal_readiness ? Math.round(pipeline.avg_deal_readiness * 100) : 0}%`}
              color="bg-blue-50"
            />
            <StatCard
              icon={Bot}
              label="Active Workflows"
              value={workflows?.items?.length ?? 0}
              sub={`${workflows?.total ?? 0} total in queue`}
              color="bg-violet-50"
            />
            <StatCard
              icon={Database}
              label="Pages Ingested"
              value={ingestion?.pagesSynthesized ?? 0}
              sub={`${ingestion?.totalDomains ?? 0} domains tracked`}
              color="bg-emerald-50"
            />
            <StatCard
              icon={activeAlerts.length > 0 ? AlertTriangle : Shield}
              label="System Health"
              value={health?.overall_status ?? "unknown"}
              sub={activeAlerts.length > 0 ? `${activeAlerts.length} active alert${activeAlerts.length > 1 ? "s" : ""}` : "All systems operational"}
              color={activeAlerts.length > 0 ? "bg-amber-50" : "bg-emerald-50"}
            />
          </>
        )}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-3 gap-4">
        {/* Left: Top Accounts + Coverage */}
        <div className="col-span-2 space-y-4">
          {/* Top Accounts */}
          <SectionCard>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-[14px] font-bold text-neutral-800">Top Accounts by Deal Readiness</h2>
              <Link href="/accounts" className="text-[11px] text-blue-600 hover:underline flex items-center gap-1">
                View all <ArrowRight size={10} />
              </Link>
            </div>
            {pipelineLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map(i => <Skeleton key={i} className="h-12" />)}
              </div>
            ) : pipeline?.top_accounts && pipeline.top_accounts.length > 0 ? (
              <div className="space-y-2">
                {pipeline.top_accounts.slice(0, 5).map(account => (
                  <Link
                    key={account.account_id}
                    href={`/accounts/${account.account_id}`}
                    className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-100 hover:border-blue-200 transition-colors cursor-pointer"
                  >
                    <div className="flex-1">
                      <div className="text-[13px] font-semibold text-neutral-800">{account.account_name}</div>
                      <div className="text-[11px] text-neutral-500">{account.label}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-neutral-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${Math.round(account.readiness_score * 100)}%` }}
                        />
                      </div>
                      <span className="text-[12px] font-bold text-neutral-700 w-10 text-right">
                        {Math.round(account.readiness_score * 100)}%
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-[12px] text-neutral-400 text-center py-6">
                No account data available yet. Start by enriching accounts.
              </div>
            )}
          </SectionCard>

          {/* Coverage Metrics */}
          {pipeline?.coverage_metrics && (
            <SectionCard>
              <h2 className="text-[14px] font-bold text-neutral-800 mb-3">Pipeline Coverage</h2>
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: "Enriched", value: pipeline.coverage_metrics.enriched_pct },
                  { label: "Hypotheses", value: pipeline.coverage_metrics.with_hypotheses_pct },
                  { label: "Narratives", value: pipeline.coverage_metrics.with_narratives_pct },
                  { label: "ROI Models", value: pipeline.coverage_metrics.with_roi_pct },
                ].map(metric => (
                  <div key={metric.label} className="text-center">
                    <div className="text-[20px] font-extrabold text-neutral-800">
                      {Math.round((metric.value ?? 0) * 100)}%
                    </div>
                    <div className="text-[11px] text-neutral-500">{metric.label}</div>
                    <div className="mt-1.5 h-1.5 bg-neutral-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.round((metric.value ?? 0) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </SectionCard>
          )}
        </div>

        {/* Right: Workflows + Health */}
        <div className="space-y-4">
          {/* Active Workflows */}
          <SectionCard>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-[14px] font-bold text-neutral-800">Active Workflows</h2>
              <Link href="/intelligence/workflows" className="text-[11px] text-blue-600 hover:underline flex items-center gap-1">
                All <ArrowRight size={10} />
              </Link>
            </div>
            {workflowsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map(i => <Skeleton key={i} className="h-10" />)}
              </div>
            ) : workflows?.items && workflows.items.length > 0 ? (
              <div className="space-y-2">
                {workflows.items.slice(0, 5).map((wf: Workflow) => (
                  <div key={wf.id} className="flex items-center gap-2 p-2 bg-neutral-50 rounded-md border border-neutral-100">
                    <Activity size={12} className="text-blue-500 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-[11px] font-semibold text-neutral-800 truncate">{wf.name}</div>
                      <div className="w-full h-1 bg-neutral-200 rounded-full mt-1">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${wf.progress}%` }} />
                      </div>
                    </div>
                    {workflowStatusBadge(wf.status)}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-[12px] text-neutral-400 text-center py-4">
                No active workflows.
              </div>
            )}
          </SectionCard>

          {/* System Health */}
          <SectionCard>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-[14px] font-bold text-neutral-800">System Health</h2>
              <Link href="/admin/health" className="text-[11px] text-blue-600 hover:underline flex items-center gap-1">
                Details <ArrowRight size={10} />
              </Link>
            </div>
            {healthLoading ? (
              <Skeleton className="h-16" />
            ) : health ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={14} className={statusColor(health.overall_status)} />
                  <span className={cn("text-[13px] font-semibold capitalize", statusColor(health.overall_status))}>
                    {health.overall_status}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-center">
                  <div>
                    <div className="text-[16px] font-bold text-emerald-600">{health.summary.healthy}</div>
                    <div className="text-[9px] text-neutral-500">Healthy</div>
                  </div>
                  <div>
                    <div className="text-[16px] font-bold text-amber-600">{health.summary.degraded}</div>
                    <div className="text-[9px] text-neutral-500">Degraded</div>
                  </div>
                  <div>
                    <div className="text-[16px] font-bold text-red-600">{health.summary.unhealthy}</div>
                    <div className="text-[9px] text-neutral-500">Down</div>
                  </div>
                  <div>
                    <div className="text-[16px] font-bold text-neutral-500">{health.summary.total}</div>
                    <div className="text-[9px] text-neutral-500">Total</div>
                  </div>
                </div>
                {activeAlerts.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-neutral-100">
                    <div className="text-[10px] font-bold uppercase text-amber-600 mb-1">Active Alerts</div>
                    {activeAlerts.slice(0, 3).map(alert => (
                      <div key={alert.id} className="flex items-start gap-1.5 text-[11px] text-neutral-700 mb-1">
                        <AlertTriangle size={10} className="text-amber-500 mt-0.5 shrink-0" />
                        <span className="truncate">{alert.message}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-[12px] text-neutral-400 text-center py-4">
                Health data unavailable.
              </div>
            )}
          </SectionCard>

          {/* Quick Links */}
          <SectionCard>
            <h2 className="text-[14px] font-bold text-neutral-800 mb-3">Quick Actions</h2>
            <div className="space-y-1.5">
              {[
                { href: "/command-center", icon: Database, label: "Ingest New Domain" },
                { href: "/intelligence/workspace", icon: Zap, label: "Intelligence Workspace" },
                { href: "/deliverables/studio", icon: BarChart3, label: "Value Studio" },
                { href: "/context/ontology/entities", icon: Activity, label: "Entity Browser" },
              ].map(link => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="flex items-center gap-2.5 p-2 rounded-md hover:bg-neutral-50 transition-colors cursor-pointer"
                >
                  <link.icon size={14} className="text-neutral-400" />
                  <span className="text-[12px] font-medium text-neutral-700">{link.label}</span>
                  <ArrowRight size={10} className="ml-auto text-neutral-300" />
                </Link>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
