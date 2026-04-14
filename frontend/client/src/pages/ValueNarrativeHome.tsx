/**
 * ValueNarrativeHome — Main landing page composing the narrative hero
 * with the existing ingestion dashboard content.
 *
 * Layout:
 *   1. Dark hero section (ValueNarrativeHero) — narrative creation CTA
 *   2. Light dashboard section — KPIs + recent maps + activity feed
 *      (reuses existing CommandCenter patterns)
 */
import { Clock, CheckCircle2, AlertCircle, Loader2, Zap } from "lucide-react";
import { useRecentIngestionJobs, useIngestionStats, type IngestionJob } from "@/hooks/useIngestion";
import { MetricCard, DataTable, StatusBadge } from "@/components/WfPrimitives";
import ValueNarrativeHero from "@/components/ValueNarrativeHero";

export default function ValueNarrativeHome() {
  const { data: recentJobs = [], isLoading: jobsLoading } = useRecentIngestionJobs(5);
  const {
    data: kpiData = { totalDomains: 0, pagesSynthesized: 0, sourcesAnalyzed: 0, avgProcessingTime: 0 },
  } = useIngestionStats();

  return (
    <div className="min-h-full">
      {/* ── Hero section (dark) ──────────────────────────────────────────── */}
      <ValueNarrativeHero />

      {/* ── Dashboard section (light) ────────────────────────────────────── */}
      <div className="p-6 max-w-5xl mx-auto">
        {/* KPI row */}
        <div className="flex gap-4 mb-6">
          <MetricCard
            label="Total Processed Nodes"
            value={kpiData.totalDomains.toLocaleString()}
            trend="+12%"
            trendUp
          />
          <MetricCard
            label="Verified Relationships"
            value={kpiData.pagesSynthesized.toLocaleString()}
            trend="+5%"
            trendUp
          />
          <MetricCard
            label="Sources Analyzed"
            value={kpiData.sourcesAnalyzed.toString()}
            trend="Active"
          />
        </div>

        {/* Two-column lower section */}
        <div className="grid grid-cols-3 gap-4">
          {/* Recent maps table — spans 2 cols */}
          <div className="col-span-2 bg-white border border-neutral-200 rounded-lg shadow-sm">
            <div className="px-4 pt-4 pb-3 border-b border-neutral-100 flex items-center justify-between">
              <h2 className="text-[14px] font-bold text-neutral-800">Recent Maps</h2>
              <button className="text-[11px] text-blue-600 hover:underline">View all</button>
            </div>
            <DataTable
              columns={["Domain", "Pages", "Status", "Updated"]}
              rows={recentJobs.map((job) => [
                <span key={`d-${job.id}`} className="flex items-center gap-2">
                  <span className="text-neutral-300 text-[14px]">🏢</span>
                  <span className="font-medium text-neutral-800">{job.domain}</span>
                </span>,
                <span key={`p-${job.id}`} className="text-neutral-600">{job.pagesProcessed || 0}</span>,
                <StatusBadge key={`s-${job.id}`} status={job.status} />,
                <span key={`u-${job.id}`} className="text-neutral-400 text-[11px]">
                  {job.updatedAt ? new Date(job.updatedAt).toLocaleDateString() : "-"}
                </span>,
              ])}
            />
          </div>

          {/* Activity feed — 1 col */}
          <div className="bg-white border border-neutral-200 rounded-lg shadow-sm">
            <div className="px-4 pt-4 pb-3 border-b border-neutral-100 flex items-center gap-2">
              <Clock size={13} className="text-neutral-400" />
              <h2 className="text-[13px] font-bold text-neutral-800">Recent Activity</h2>
            </div>
            <div className="divide-y divide-neutral-100">
              {recentJobs.slice(0, 4).map((job: IngestionJob) => (
                <div key={job.id} className="px-4 py-3 flex items-start gap-2.5">
                  <span className="mt-0.5 shrink-0">
                    {job.status === "completed" ? (
                      <CheckCircle2 size={13} className="text-emerald-500" />
                    ) : job.status === "processing" ? (
                      <Loader2 size={13} className="text-blue-500 animate-spin" />
                    ) : job.status === "failed" ? (
                      <AlertCircle size={13} className="text-red-400" />
                    ) : (
                      <Zap size={13} className="text-violet-500" />
                    )}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] text-neutral-700 leading-snug">
                      {job.domain} — {job.status} ({job.progress}%)
                    </p>
                    <p className="text-[10px] text-neutral-400 mt-0.5">
                      {job.updatedAt ? new Date(job.updatedAt).toLocaleDateString() : "Just now"}
                    </p>
                  </div>
                </div>
              ))}
              {recentJobs.length === 0 && !jobsLoading && (
                <div className="px-4 py-8 text-center text-neutral-400 text-[11px]">
                  No recent activity
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
