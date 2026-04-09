/**
 * Screen 2 — Extraction Engine Live Run
 * Design: Refined Enterprise SaaS
 */
import { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, Circle, Loader2 } from "lucide-react";
import { Link } from "wouter";
import { PageHeader } from "@/components/WfPrimitives";

const STEPS = [
  { id: 1, label: "Crawling",         sub: "Acquired 4,209 nodes from domain.", done: true },
  { id: 2, label: "NER Extraction",   sub: "Identifying entities, capabilities, and outcomes.", active: true, pct: 68 },
  { id: 3, label: "Semantic Mapping", sub: "", done: false },
  { id: 4, label: "Fabric Assembly",  sub: "", done: false },
];

const LOG_LINES = [
  { t: null,         type: "sys",     text: "Initializing NLP models…",                                                           extra: "[OK]",    extraColor: "text-emerald-400" },
  { t: null,         type: "sys",     text: "Loading target domain: example.com" },
  { t: "09:41:02",   type: "info",    text: "Crawling phase complete. 4,209 valid pages parsed." },
  { t: "09:41:05",   type: "warn",    text: "Skipping deeply nested node /assets/legacy…" },
  { t: "09:41:12",   type: "info",    text: "Initiating Named Entity Recognition (Spacy/RoBERTa)" },
  { t: "09:41:14",   type: "extract", text: "Parsed Node 102: Capability →", link: "Single Sign-On",       conf: "0.94" },
  { t: "09:41:15",   type: "extract", text: "Parsed Node 103: Outcome →",    link: "Churn Reduction",      conf: "0.88" },
  { t: "09:41:16",   type: "map",     text: "Linking Capability(102) to Outcome(103)" },
  { t: "09:41:18",   type: "extract", text: "Parsed Node 144: Capability →", link: "RBAC",                 conf: "0.97" },
  { t: "09:41:20",   type: "extract", text: "Parsed Node 145: Capability →", link: "Audit Logging",        conf: "0.91" },
  { t: "09:41:22",   type: "extract", text: "Parsed Node 149: Outcome →",    link: "Compliance Automation",conf: "0.85" },
  { t: "09:41:25",   type: "map",     text: "Linking Capability(144, 145) to Outcome(149)" },
  { t: "09:41:28",   type: "extract", text: "Parsed Node 210: Outcome →",    link: "Cost Savings",         conf: "0.92" },
  { t: "09:41:29",   type: "extract", text: "Parsed Node 212: Capability →", link: "Automated Provisioning",conf:"0.89" },
  { t: "09:41:31",   type: "plain",   text: "Scanning batch 4/10" },
];

const TYPE_COLORS: Record<string, string> = {
  sys:     "text-neutral-400",
  info:    "text-cyan-400",
  warn:    "text-amber-400",
  extract: "text-neutral-300",
  map:     "text-neutral-300",
  plain:   "text-neutral-400",
};
const TYPE_LABELS: Record<string, string> = {
  sys: "[SYS]", info: "[INFO]", warn: "[WARN]", extract: "[EXTRACT]", map: "[MAP]", plain: "",
};

const CHIPS = [
  { label: "Outcome: Churn Reduction",       color: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  { label: "Capability: RBAC",               color: "bg-violet-900/40 text-violet-300 border-violet-700" },
  { label: "Capability: Audit Logging",      color: "bg-violet-900/40 text-violet-300 border-violet-700" },
  { label: "Outcome: Compliance Automation", color: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  { label: "Outcome: Cost Savings",          color: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  { label: "Capability: Automated Provisioning", color: "bg-violet-900/40 text-violet-300 border-violet-700" },
];

export default function ExtractionEngine() {
  const [visibleLines, setVisibleLines] = useState(8);

  useEffect(() => {
    const t = setInterval(() => {
      setVisibleLines(v => Math.min(v + 1, LOG_LINES.length));
    }, 600);
    return () => clearInterval(t);
  }, []);

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
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"/>
          Processing domain: <span className="font-semibold text-neutral-800">example.com</span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — pipeline steps */}
        <div className="w-[240px] shrink-0 p-5 border-r border-neutral-200 bg-white overflow-y-auto">
          <PageHeader title="Extraction Engine" subtitle="Mapping structural ontology to value fabric." />
          <div className="space-y-4 mt-4">
            {STEPS.map(step => (
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
            <span>Estimated time left:</span>
            <span className="font-mono font-semibold text-neutral-800">01:42</span>
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
            {LOG_LINES.slice(0, visibleLines).map((line, i) => (
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
            {visibleLines >= LOG_LINES.length && (
              <div className="flex gap-2">
                <span className="text-neutral-600 w-[68px]">[09:41:31]</span>
                <span className="text-neutral-400">Scanning batch 4/10</span>
                <span className="cursor-blink"/>
              </div>
            )}
          </div>

          {/* Entity chips */}
          <div className="flex gap-2 px-4 py-3 border-t border-[#30363d] bg-[#161b22] overflow-x-auto">
            {CHIPS.map(chip => (
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
