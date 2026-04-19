/**
 * Value Studio — Stage 4: Validation
 * Independent challenge of the model — the skeptical CFO check — all critical issues must resolve before publishing
 */
import { useState } from "react";
import ValueStudioShell, {
  StudioPanel, DEMO_DEAL, buildStages,
} from "./ValueStudioShell";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle, XCircle } from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────────

type Severity = "critical" | "warning" | "pass";

interface QualityGate {
  label: string;
  status: Severity;
  detail?: string;
}

interface Issue {
  id: number;
  severity: Severity;
  title: string;
  description: string;
  recommendation?: string;
  actions?: string[];
  primaryAction?: string;
  secondaryActions?: string[];
  resolutionOptions?: { label: string; sub?: string }[];
}

// ── Mock data ──────────────────────────────────────────────────────────────────

const QUALITY_GATES: QualityGate[] = [
  { label: "Context Complete", status: "pass" },
  { label: "Chains Complete", status: "pass" },
  { label: "Evidence (3 gaps)", status: "warning", detail: "3 gaps" },
  { label: "Financial Valid", status: "pass" },
  { label: "Double Count Detected", status: "critical" },
];

const ISSUES: Issue[] = [
  {
    id: 1,
    severity: "critical",
    title: "CRITICAL: DOUBLE COUNT DETECTED",
    description: `"Content search time savings" appears in both Chain 1 (Content Management) and Chain 2 (Digital Selling). Both chains claim **$400K annual impact** from reduced search time — this is the same population of reps performing the same activity.`,
    recommendation: "Allocate 60% to Content Management (primary driver) and 40% to Digital Selling (activation mechanism). This preserves both chains while eliminating the double count.",
    primaryAction: "Apply Recommended Fix",
    secondaryActions: ["Edit Manually", "Accept Risk"],
    resolutionOptions: [
      { label: "Merge into single $400K claim (primary driver)" },
      { label: "Keep both at reduced values", sub: "($240K / $160K split)" },
      { label: "Reject Digital Selling claim —", sub: "apply only to Content Mgmt" },
    ],
  },
  {
    id: 2,
    severity: "warning",
    title: "WARNING: UNREALISTIC ADOPTION TIMELINE",
    description: "90% adoption assumed by Month 6 for a 500-rep org. Benchmark data across 23 comparable rollouts suggests **60–70% is more realistic** at Month 6 for organizations of this size without dedicated change management.",
    primaryAction: "Adjust to 65% at Month 6",
    secondaryActions: ["Accept with Justification"],
  },
  {
    id: 3,
    severity: "warning",
    title: "WARNING: 3 ASSUMPTIONS NEED VALIDATION",
    actions: [
      "Content find rate improvement — currently estimated, not measured",
      "Manager coaching adoption rate — no baseline established",
      "Cross-sell uplift % — customer has not confirmed this figure",
    ],
    primaryAction: "Schedule Validation Call",
  },
];

const EVIDENCE_ASSESSMENT = [
  { label: "Content search time", rating: "STRONG", color: "text-green-600" },
  { label: "Rep ramp improvement", rating: "MODERATE", color: "text-yellow-600" },
  { label: "Deal visibility ROI", rating: "WEAK", color: "text-red-600" },
];

// ── Gate Icon ──────────────────────────────────────────────────────────────────

function GateIcon({ status }: { status: Severity }) {
  if (status === "pass") return <CheckCircle2 size={14} className="text-green-600 shrink-0" />;
  if (status === "warning") return <AlertCircle size={14} className="text-yellow-500 shrink-0" />;
  return <XCircle size={14} className="text-red-600 shrink-0" />;
}

// ── Left Panel ─────────────────────────────────────────────────────────────────

function LeftPanel({ activeIssue }: { activeIssue: number }) {
  const passed = QUALITY_GATES.filter((g) => g.status === "pass").length;
  const blocking = QUALITY_GATES.filter((g) => g.status === "critical").length;

  return (
    <StudioPanel title="Quality Gates">
      <div className="flex flex-col gap-2">
        {QUALITY_GATES.map((gate) => (
          <div
            key={gate.label}
            className={cn(
              "flex items-center gap-2 px-2.5 py-2 rounded-md border text-[12px]",
              gate.status === "critical"
                ? "border-red-200 bg-red-50 text-red-800"
                : gate.status === "warning"
                ? "border-yellow-200 bg-yellow-50 text-yellow-800"
                : "border-green-200 bg-green-50 text-green-800"
            )}
          >
            <GateIcon status={gate.status} />
            <span className="font-medium">{gate.label}</span>
          </div>
        ))}
      </div>
      <p className="mt-4 text-[11px] text-muted-foreground">
        {QUALITY_GATES.length} gates · {passed} passed · {blocking} blocking
      </p>
    </StudioPanel>
  );
}

// ── Issue Card ─────────────────────────────────────────────────────────────────

function IssueCard({
  issue,
  active,
  onSelect,
}: {
  issue: Issue;
  active: boolean;
  onSelect: () => void;
}) {
  const severityLabel = issue.severity === "critical" ? "🔴 CRITICAL" : "🟡 WARNING";
  const severityColor =
    issue.severity === "critical"
      ? "text-red-700 font-bold"
      : "text-yellow-700 font-semibold";

  return (
    <div
      onClick={onSelect}
      className={cn(
        "border rounded-lg p-4 cursor-pointer transition-all",
        active ? "border-foreground shadow-sm" : "border-border hover:border-muted-foreground"
      )}
    >
      <p className={cn("text-[11px] uppercase tracking-wider mb-2", severityColor)}>
        Issue #{issue.id} — {severityLabel}: {issue.title.replace(/^(CRITICAL|WARNING): /, "")}
      </p>

      {issue.description && (
        <p className="text-[12px] text-foreground mb-3 leading-relaxed">
          {issue.description.split(/(\*\*.*?\*\*)/).map((part, i) => {
            if (part.startsWith("**") && part.endsWith("**")) {
              return <strong key={i}>{part.slice(2, -2)}</strong>;
            }
            return <span key={i}>{part}</span>;
          })}
        </p>
      )}

      {issue.recommendation && (
        <div className="mb-3 p-2.5 bg-muted rounded-md">
          <p className="text-[11px] font-semibold text-foreground mb-0.5">Recommendation</p>
          <p className="text-[12px] text-muted-foreground">{issue.recommendation}</p>
        </div>
      )}

      {issue.actions && (
        <div className="flex flex-col gap-1.5 mb-3">
          {issue.actions.map((a) => (
            <div key={a} className="px-3 py-2 border border-border rounded-md text-[12px] text-muted-foreground">
              {a}
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 flex-wrap">
        {issue.primaryAction && (
          <button className="h-7 px-4 bg-foreground text-background text-[11px] font-semibold rounded-md hover:opacity-90 transition-opacity">
            {issue.primaryAction}
          </button>
        )}
        {issue.secondaryActions?.map((a) => (
          <button
            key={a}
            className="h-7 px-3 border border-border text-[11px] font-medium rounded-md hover:bg-muted transition-colors"
          >
            {a}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Center Panel ───────────────────────────────────────────────────────────────

function CenterPanel({
  activeIssue,
  setActiveIssue,
}: {
  activeIssue: number;
  setActiveIssue: (id: number) => void;
}) {
  return (
    <StudioPanel title="Integrity Report">
      <div className="flex flex-col gap-4">
        {ISSUES.map((issue) => (
          <IssueCard
            key={issue.id}
            issue={issue}
            active={activeIssue === issue.id}
            onSelect={() => setActiveIssue(issue.id)}
          />
        ))}
      </div>
    </StudioPanel>
  );
}

// ── Right Panel ────────────────────────────────────────────────────────────────

function RightPanel({ activeIssue }: { activeIssue: number }) {
  const issue = ISSUES.find((i) => i.id === activeIssue);
  const [selected, setSelected] = useState(0);

  return (
    <StudioPanel title="Resolution Workspace">
      {issue ? (
        <>
          <p className="text-[11px] text-muted-foreground mb-3">
            Resolving: Issue #{issue.id} — {issue.title.replace(/^(CRITICAL|WARNING): /, "")}
          </p>

          {issue.resolutionOptions && (
            <>
              <p className="text-[11px] font-semibold text-foreground mb-2">Choose Resolution</p>
              <div className="flex flex-col gap-2 mb-4">
                {issue.resolutionOptions.map((opt, idx) => (
                  <label
                    key={idx}
                    className="flex items-start gap-2 cursor-pointer"
                    onClick={() => setSelected(idx)}
                  >
                    <div className={cn(
                      "mt-0.5 w-3.5 h-3.5 rounded-full border-2 shrink-0",
                      selected === idx ? "border-foreground bg-foreground" : "border-muted-foreground"
                    )} />
                    <span className="text-[12px] text-foreground">
                      {opt.label}
                      {opt.sub && <span className="text-muted-foreground"> {opt.sub}</span>}
                    </span>
                  </label>
                ))}
              </div>
              <button className="w-full h-8 bg-foreground text-background text-[12px] font-semibold rounded-md hover:opacity-90 transition-opacity mb-4">
                Apply Fix
              </button>
            </>
          )}

          {activeIssue === 1 && (
            <>
              <p className="text-[11px] font-semibold text-foreground mb-2">Evidence Assessment</p>
              <div className="flex flex-col gap-1.5">
                {EVIDENCE_ASSESSMENT.map((e) => (
                  <div key={e.label} className="flex items-center justify-between text-[12px]">
                    <span className="text-muted-foreground">{e.label}</span>
                    <span className={cn("font-bold", e.color)}>{e.rating}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      ) : (
        <p className="text-[12px] text-muted-foreground">Select an issue to resolve it.</p>
      )}
    </StudioPanel>
  );
}

// ── Status Bar ─────────────────────────────────────────────────────────────────

function StatusBar() {
  return (
    <>
      <span className="flex items-center gap-1.5 text-red-700 font-medium">
        <XCircle size={12} className="text-red-600" /> 1 CRITICAL must resolve
      </span>
      <span className="flex items-center gap-1.5 text-yellow-700">
        <AlertCircle size={12} className="text-yellow-500" /> 2 WARNINGS
      </span>
      <span className="h-6 px-2.5 bg-green-600 text-white text-[11px] font-semibold rounded flex items-center gap-1">
        <CheckCircle2 size={11} /> 2 GATES passed
      </span>
      <button className="text-[11px] text-muted-foreground hover:underline">
        Publish Anyway (requires justification)
      </button>
    </>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function Stage4Validation() {
  const [activeIssue, setActiveIssue] = useState(1);

  return (
    <ValueStudioShell
      stageId={4}
      title="Validation"
      subtitle="Independent challenge of the model — the skeptical CFO check — all critical issues must resolve before publishing"
      deal={DEMO_DEAL}
      stages={buildStages(4)}
      prevLabel="Modeling"
      prevPath="/model/value-studio/modeling"
      nextLabel="Continue to Narrative"
      nextPath="/model/value-studio/narrative"
      extraActions={
        <button className="h-8 px-3 border border-border text-[12px] font-medium rounded-md hover:bg-muted transition-colors">
          Run Review Again
        </button>
      }
      leftPanel={<LeftPanel activeIssue={activeIssue} />}
      centerPanel={<CenterPanel activeIssue={activeIssue} setActiveIssue={setActiveIssue} />}
      rightPanel={<RightPanel activeIssue={activeIssue} />}
      statusBar={<StatusBar />}
    />
  );
}
