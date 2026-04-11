/**
 * Screen 2 — Extraction Engine Live Run
 * Design: Refined Enterprise SaaS
 */
import { useEffect, useState, useMemo } from "react";
import { ArrowLeft, CheckCircle2, Circle, Loader2, AlertCircle } from "lucide-react";
import { Link } from "wouter";
import { PageHeader } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import { useExtractionJob, TYPE_COLORS, TYPE_LABELS } from "@/hooks/useExtraction";
import { useJobStream } from "@/hooks/useJobStream";

// Types for log entries
type LogType = 'sys' | 'info' | 'warn' | 'extract' | 'map' | 'plain';
interface StreamLog {
  timestamp: string;
  level: string;
  message: string;
}
interface StreamEntity {
  type: string;
  name: string;
}

// Constants for log level mapping
const LOG_LEVEL_MAP: Record<string, LogType> = {
  'error': 'warn',
  'warning': 'warn',
  'warn': 'warn',
  'info': 'info',
  'debug': 'sys',
  'extract': 'extract',
  'map': 'map',
};

/** Map log level string to display type */
function mapLogType(level: string): LogType {
  return LOG_LEVEL_MAP[level?.toLowerCase()] || 'plain';
}

export default function ExtractionEngine() {
  // Get job ID from URL query param: /extraction-engine?jobId=xxx
  const searchParams = new URLSearchParams(window.location.search);
  const jobId = searchParams.get('jobId');

  const { data: job, isLoading, error: jobError } = useExtractionJob(jobId);
  const { progress: streamProgress, status: streamStatus, logs: streamLogs, entities: streamEntities, isConnected, error: streamError } = useJobStream(jobId);
  const [visibleLines, setVisibleLines] = useState(20);

  // Use streamed data when available, fall back to polled job data
  const liveProgress = streamProgress || job?.progress || 0;
  const liveStatus = streamStatus || job?.status || 'pending';

  // Memoize log transformation to prevent recalculation on every render
  const liveLogs = useMemo(() => {
    if (streamLogs && streamLogs.length > 0) {
      return streamLogs.map((log) => ({
        t: new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        type: mapLogType(log.level),
        text: log.message,
      }));
    }
    return job?.logs || [];
  }, [streamLogs, job?.logs]);

  // Memoize entity chip transformation
  const liveEntities = useMemo(() => {
    if (streamEntities && streamEntities.length > 0) {
      return streamEntities.map((e) => ({
        label: `${e.type}: ${e.name}`,
        color: TYPE_COLORS[e.type.toLowerCase()] || 'text-neutral-400',
      }));
    }
    return job?.entitiesFound || [];
  }, [streamEntities, job?.entitiesFound]);

  // Combined error state
  const error = jobError || streamError;

  // Auto-scroll logs as new ones arrive
  useEffect(() => {
    if (liveLogs.length > 0) {
      setVisibleLines(liveLogs.length);
    }
  }, [liveLogs.length]);

  // Loading state - skeleton loader for terminal panel
  if (isLoading) {
    return <ExtractionEngineSkeleton />;
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
  const logs = liveLogs;
  const chips = liveEntities;
  const isRunning = liveStatus === 'running' || liveStatus === 'pending';

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
          {isRunning && (
            <>
              <span className={`w-2 h-2 rounded-full animate-pulse ${isConnected ? 'bg-emerald-400' : 'bg-amber-400'}`}/>
              {isConnected && <span className="text-[10px] text-emerald-600">LIVE</span>}
            </>
          )}
          <span className={isRunning ? 'text-amber-600' : liveStatus === 'completed' ? 'text-emerald-600' : 'text-red-600'}>
            {liveStatus === 'running' ? 'Processing' : liveStatus}
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
            {chips.map((chip, index) => (
              <span key={`${chip.label}-${index}`} className={`shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold border ${chip.color}`}>
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

/** Skeleton loader for the extraction engine loading state */
function ExtractionEngineSkeleton() {
  return (
    <div className="flex flex-col h-full">
      {/* Sub-header skeleton */}
      <div className="flex items-center justify-between px-6 py-3 bg-white border-b border-neutral-200">
        <Skeleton className="h-4 w-32" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-20" />
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left panel skeleton */}
        <div className="w-[240px] shrink-0 p-5 border-r border-neutral-200 bg-white">
          <Skeleton className="h-6 w-40 mb-1" />
          <Skeleton className="h-4 w-56 mb-6" />
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-5 w-5 rounded-full shrink-0" />
                <div className="flex-1">
                  <Skeleton className="h-4 w-24 mb-1" />
                  <Skeleton className="h-3 w-32" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel - terminal skeleton */}
        <div className="flex-1 flex flex-col overflow-hidden bg-[#0d1117]">
          {/* Terminal header skeleton */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-[#161b22] border-b border-[#30363d]">
            <div className="flex items-center gap-2">
              <Skeleton className="w-3 h-3 rounded-full bg-red-500/50" />
              <Skeleton className="w-3 h-3 rounded-full bg-amber-400/50" />
              <Skeleton className="w-3 h-3 rounded-full bg-emerald-500/50" />
              <Skeleton className="ml-2 h-3 w-32 bg-neutral-700" />
            </div>
            <Skeleton className="h-3 w-12 bg-emerald-700/50" />
          </div>

          {/* Log lines skeleton */}
          <div className="flex-1 p-4 space-y-2">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="flex gap-2">
                <Skeleton className="h-3 w-16 shrink-0 bg-neutral-800" />
                <Skeleton className="h-3 w-12 shrink-0 bg-neutral-700" />
                <Skeleton className="h-3 w-96 bg-neutral-800" />
              </div>
            ))}
          </div>

          {/* Entity chips skeleton */}
          <div className="flex gap-2 px-4 py-3 border-t border-[#30363d] bg-[#161b22]">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-6 w-24 rounded-full bg-neutral-800" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
