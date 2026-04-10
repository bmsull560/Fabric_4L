/**
 * Screen 2 — Extraction Engine Live Run
 * Design: Refined Enterprise SaaS
 */
import { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, Circle, Loader2, AlertCircle } from "lucide-react";
import { Link, useRoute } from "wouter";
import { PageHeader } from "@/components/WfPrimitives";
import { useExtractionJob, TYPE_COLORS, TYPE_LABELS } from "@/hooks/useExtraction";

export default function ExtractionEngine() {
  // Get job ID from URL query param: /extraction-engine?jobId=xxx
  const [match, params] = useRoute('/extraction-engine');
  const searchParams = new URLSearchParams(window.location.search);
  const jobId = searchParams.get('jobId');

  const { data: job, isLoading, error } = useExtractionJob(jobId);
  const [visibleLines, setVisibleLines] = useState(20);

  // Auto-scroll logs as new ones arrive
  useEffect(() => {
    if (job?.logs) {
      setVisibleLines(job.logs.length);
    }
  }, [job?.logs?.length]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-full items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-3" />
        <span className="text-sm text-neutral-600">Loading extraction job...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col h-full items-center justify-center">
        <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
        <span className="text-sm text-red-600">{(error as Error).message || 'Failed to load job'}</span>
        <Link href="/command-center">
          <span className="text-sm text-blue-600 mt-2 hover:underline">Back to Command Center</span>
        </Link>
      </div>
    );
  }

  // Empty state - no job ID
  if (!jobId) {
    return (
      <div className="flex flex-col h-full items-center justify-center">
        <span className="text-sm text-neutral-600">No job specified</span>
        <Link href="/command-center">
          <span className="text-sm text-blue-600 mt-2 hover:underline">Start a new extraction</span>
        </Link>
      </div>
    );
  }

  const steps = job?.steps || [];
  const logs = job?.logs || [];
  const chips = job?.entitiesFound || [];
  const isRunning = job?.status === 'running' || job?.status === 'pending';

  return (
    <div className="flex flex-col h-full">
      {/* Sub-header */}
      <div className="flex items-center justify-between px-6 py-3 bg-white border-b border-neutral-200">
        <Link href="/command-center">
          <span className="flex items-center gap-1.5 text-[12px] text-neutral-500 hover:text-neutral-800 transition-colors">
            <ArrowLeft size={13}/> Back to Command Center
          </span>
        </Link>
        <div className="flex items-center gap-2 text-[12px] text-neutral-500">
          {isRunning && <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"/>}
          <span className={isRunning ? 'text-amber-600' : job?.status === 'completed' ? 'text-emerald-600' : 'text-red-600'}>
            {job?.status === 'running' ? 'Processing' : job?.status}
          </span>
          <span className="font-semibold text-neutral-800">{job?.domain}</span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — pipeline steps */}
        <div className="w-[240px] shrink-0 p-5 border-r border-neutral-200 bg-white overflow-y-auto">
          <PageHeader title="Extraction Engine" subtitle="Mapping structural ontology to value fabric." />
          <div className="space-y-4 mt-4">
            {steps.map(step => (
              <div key={step.id} className="flex gap-3">
                <div className="flex flex-col items-center">
                  {step.done ? (
                    <CheckCircle2 size={18} className="text-emerald-500 shrink-0"/>
                  ) : step.active ? (
                    <Loader2 size={18} className="text-blue-600 shrink-0 animate-spin"/>
                  ) : (
                    <Circle size={18} className="text-neutral-300 shrink-0"/>
                  )}
                  {step.id < 4 && <div className="w-px flex-1 bg-neutral-200 mt-1 min-h-[20px]"/>}
                </div>
                <div className="pb-4">
                  <div className={`text-[13px] font-semibold ${step.done ? "text-neutral-800" : step.active ? "text-neutral-900" : "text-neutral-400"}`}>
                    {step.label}
                  </div>
                  {step.sub && <div className="text-[11px] text-neutral-500 mt-0.5">{step.sub}</div>}
                  {step.active && step.pct !== undefined && (
                    <div className="mt-2">
                      <div className="h-1.5 bg-neutral-100 rounded-full overflow-hidden w-full">
                        <div
                          className="h-full bg-blue-600 rounded-full progress-fill"
                          style={{ width: `${step.pct}%` }}
                        />
                      </div>
                      <div className="text-[10px] text-neutral-400 mt-1 text-right">{step.pct}%</div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-neutral-100 flex justify-between text-[11px] text-neutral-500">
            <span>Job ID:</span>
            <span className="font-mono font-semibold text-neutral-800">{jobId?.slice(0, 8)}...</span>
          </div>
        </div>

        {/* Right panel — terminal log */}
        <div className="flex-1 flex flex-col overflow-hidden bg-[#0d1117]">
          {/* Terminal header */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-[#161b22] border-b border-[#30363d]">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500"/>
              <span className="w-3 h-3 rounded-full bg-amber-400"/>
              <span className="w-3 h-3 rounded-full bg-emerald-500"/>
              <span className="ml-2 text-[11px] text-neutral-400 font-mono">extraction_stream.log</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"/>
              LIVE
            </div>
          </div>

          {/* Log lines */}
          <div className="flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-relaxed space-y-0.5">
            {logs.length === 0 && (
              <div className="text-neutral-500">No logs available yet...</div>
            )}
            {logs.slice(0, visibleLines).map((line, i) => (
              <div key={i} className="flex gap-2">
                <span className="text-neutral-600 shrink-0 w-[68px]">
                  {line.t ? `[${line.t}]` : ""}
                </span>
                <span className={`shrink-0 font-semibold ${TYPE_COLORS[line.type]}`}>
                  {TYPE_LABELS[line.type]}
                </span>
                <span className="text-[#c9d1d9]">
                  {line.text}
                  {line.link && (
                    <span className="text-cyan-400 ml-1">{line.link}</span>
                  )}
                  {line.conf && (
                    <span className="text-neutral-500 ml-1">(Conf: {line.conf})</span>
                  )}
                  {line.extra && (
                    <span className={`ml-1 ${line.extraColor}`}>{line.extra}</span>
                  )}
                </span>
              </div>
            ))}
            {logs.length > 0 && isRunning && (
              <div className="flex gap-2">
                <span className="text-neutral-600 w-[68px]">[{new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]</span>
                <span className="text-neutral-400">Processing...</span>
                <span className="cursor-blink"/>
              </div>
            )}
          </div>

          {/* Entity chips */}
          <div className="flex gap-2 px-4 py-3 border-t border-[#30363d] bg-[#161b22] overflow-x-auto">
            {chips.length === 0 && (
              <span className="text-[10px] text-neutral-500">No entities extracted yet...</span>
            )}
            {chips.map(chip => (
              <span key={chip.label} className={`shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold border ${chip.color}`}>
                <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70"/>
                {chip.label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
