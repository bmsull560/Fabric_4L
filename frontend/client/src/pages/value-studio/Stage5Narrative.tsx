/**
 * Value Studio — Stage 5: Narrative
 * Package the validated model into stakeholder-ready stories — same numbers, different emphasis
 */
import { useState } from "react";
import { FileText, Presentation, FileIcon, Mail, Download, Share2, ExternalLink } from "lucide-react";
import ValueStudioShell, {
  StudioPanel, DEMO_DEAL, buildStages,
} from "./ValueStudioShell";
import { cn } from "@/lib/utils";

// ── Types ──────────────────────────────────────────────────────────────────────

interface StakeholderVersion {
  id: string;
  label: string;
  emphasis: string;
  selected: boolean;
}

type NarrativeSection = "Context" | "Problem" | "Solution" | "Impact" | "Proof" | "Next Steps";

// ── Mock data ──────────────────────────────────────────────────────────────────

const STAKEHOLDERS: StakeholderVersion[] = [
  { id: "cfo", label: "CFO", emphasis: "ROI, payback period, NPV", selected: true },
  { id: "cro", label: "CRO", emphasis: "Revenue impact, win rate, ramp time", selected: false },
  { id: "coo", label: "COO", emphasis: "Productivity, adoption, efficiency", selected: false },
  { id: "rep", label: "Sales Rep", emphasis: "Day-to-day workflow improvements", selected: false },
  { id: "enablement", label: "Enablement Lead", emphasis: "Content, coaching, onboarding", selected: false },
];

const EXPORT_FORMATS = [
  { id: "pdf", label: "PDF", sub: "1-pager", icon: FileText },
  { id: "pptx", label: "PPTX", sub: "Slide deck", icon: Presentation },
  { id: "docx", label: "DOCX", sub: "Full memo", icon: FileIcon },
  { id: "email", label: "Email", sub: "Brief", icon: Mail },
];

const NARRATIVE_SECTIONS: NarrativeSection[] = ["Context", "Problem", "Solution", "Impact", "Proof", "Next Steps"];

const CONTEXT_TEXT = `Acme Corp's sales organization faces three compounding challenges that together reduce revenue capacity by an estimated 15%: slow rep ramp time (6 months vs. 3-month industry target), low content findability at point of need (6hrs/week lost per rep), and limited deal engagement visibility after handoff...`;

const QUICK_ACTIONS = [
  "Objection Brief —",
  "Realization Plan —",
  "Risk Summary —",
  "Competitive Framing —",
];

// ── Left Panel ─────────────────────────────────────────────────────────────────

function LeftPanel({
  stakeholders,
  setStakeholders,
}: {
  stakeholders: StakeholderVersion[];
  setStakeholders: (s: StakeholderVersion[]) => void;
}) {
  const select = (id: string) =>
    setStakeholders(stakeholders.map((s) => ({ ...s, selected: s.id === id })));

  return (
    <StudioPanel title="Stakeholder Version" subtitle="Same numbers · Different emphasis">
      <div className="flex flex-col gap-2">
        {stakeholders.map((s) => (
          <button
            key={s.id}
            onClick={() => select(s.id)}
            className={cn(
              "w-full text-left px-3 py-2.5 rounded-md border transition-all",
              s.selected
                ? "border-foreground bg-primary/10 text-primary"
                : "border-border hover:border-muted-foreground"
            )}
          >
            <div className="flex items-center gap-2">
              <div className={cn(
                "w-2 h-2 rounded-full shrink-0",
                s.selected ? "bg-background" : "bg-muted-foreground"
              )} />
              <span className="text-[12px] font-semibold">{s.label}</span>
            </div>
            <p className={cn("text-[10px] mt-0.5 ml-4", s.selected ? "text-background/70" : "text-muted-foreground")}>
              {s.emphasis}
            </p>
          </button>
        ))}
      </div>
    </StudioPanel>
  );
}

// ── Center Panel ───────────────────────────────────────────────────────────────

function CenterPanel({ activeSection, setActiveSection }: {
  activeSection: NarrativeSection;
  setActiveSection: (s: NarrativeSection) => void;
}) {
  return (
    <>
      {/* Executive Summary */}
      <StudioPanel title="Executive Summary — CFO Version">
        <p className="text-[13px] font-semibold text-foreground mb-1">
          Acme Corp can achieve $1.9M in net value over 3 years by consolidating sales enablement onto Allego's revenue platform.
        </p>
        <p className="text-[12px] text-muted-foreground mb-3 leading-relaxed">
          The investment yields a 412% 3-year ROI with an 8-month payback period and $1.67M NPV — well within the CFO's typical benchmark of 18-month payback for SaaS platforms.
        </p>

        {/* Key figures */}
        <div className="grid grid-cols-3 gap-3 mb-3">
          {[
            { label: "3-Year ROI", value: "412%" },
            { label: "Payback", value: "8 months" },
            { label: "3-Year NPV", value: "$1.67M" },
          ].map((m) => (
            <div key={m.label} className="border border-border rounded-md p-2.5 text-center">
              <p className="text-[10px] text-muted-foreground mb-0.5">{m.label}</p>
              <p className="text-[18px] font-bold text-foreground">{m.value}</p>
            </div>
          ))}
        </div>

        {/* Assumptions */}
        <div className="mb-3">
          <p className="text-[11px] font-semibold text-foreground mb-1.5">Assumptions</p>
          <ul className="space-y-1">
            {[
              "Based on 500-rep deployment over 18 months",
              "8-month S-curve adoption profile",
              "Customer-stated baselines where available",
            ].map((a) => (
              <li key={a} className="flex items-start gap-1.5 text-[12px] text-muted-foreground">
                <span className="mt-1 w-1 h-1 rounded-full bg-muted-foreground shrink-0" />
                {a}
              </li>
            ))}
          </ul>
        </div>

        <div className="border-t border-border pt-3">
          <p className="text-[11px] font-semibold text-foreground mb-1">Decision Required</p>
          <p className="text-[12px] text-muted-foreground">Approve pilot program by Q1 kickoff (January 15)</p>
        </div>

        <div className="flex items-center gap-3 mt-3">
          <button className="text-[11px] text-primary hover:underline">Edit inline</button>
          <span className="text-border">|</span>
          <button className="text-[11px] text-muted-foreground hover:underline">Track changes</button>
        </div>
      </StudioPanel>

      {/* Full Narrative Section Editor */}
      <StudioPanel title="Full Narrative — Section Editor">
        <div className="flex items-center gap-1.5 mb-3 flex-wrap">
          {NARRATIVE_SECTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setActiveSection(s)}
              className={cn(
                "h-6 px-3 text-[11px] font-medium rounded-full border transition-colors",
                activeSection === s
                  ? "bg-primary/10 text-primary border-foreground"
                  : "border-border text-muted-foreground hover:bg-muted"
              )}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="min-h-[80px] p-3 border border-border rounded-md bg-muted/30 text-[12px] text-foreground leading-relaxed">
          {activeSection === "Context" ? CONTEXT_TEXT : (
            <span className="text-muted-foreground italic">
              {activeSection} section — click to edit inline...
            </span>
          )}
        </div>
      </StudioPanel>
    </>
  );
}

// ── Right Panel ────────────────────────────────────────────────────────────────

function RightPanel({ selectedFormat, setSelectedFormat }: {
  selectedFormat: string;
  setSelectedFormat: (f: string) => void;
}) {
  return (
    <>
      <StudioPanel title="Export Formats">
        <div className="flex flex-col gap-2 mb-3">
          {EXPORT_FORMATS.map((f) => {
            const Icon = f.icon;
            return (
              <button
                key={f.id}
                onClick={() => setSelectedFormat(f.id)}
                className={cn(
                  "flex items-center gap-2.5 px-3 py-2 rounded-md border text-left transition-all",
                  selectedFormat === f.id
                    ? "border-foreground bg-foreground/5"
                    : "border-border hover:border-muted-foreground"
                )}
              >
                <Icon size={14} className="shrink-0 text-muted-foreground" />
                <div>
                  <span className="text-[12px] font-semibold text-foreground">{f.label}</span>
                  <span className="text-[11px] text-muted-foreground ml-1.5">{f.sub}</span>
                </div>
                {selectedFormat === f.id && (
                  <span className="ml-auto text-[10px] font-semibold text-foreground">Selected</span>
                )}
              </button>
            );
          })}
        </div>
        <button className="w-full h-8 bg-primary/10 text-primary text-[12px] font-semibold rounded-md hover:opacity-90 transition-opacity flex items-center justify-center gap-2">
          <Download size={13} /> Download PDF
        </button>
      </StudioPanel>

      {/* Document Preview */}
      <StudioPanel title="Document Preview">
        <div className="border border-border rounded-md overflow-hidden bg-white">
          <div className="h-4 bg-foreground" />
          <div className="p-3 space-y-1.5">
            <div className="h-2 bg-foreground rounded w-4/5" />
            <div className="h-1.5 bg-muted rounded w-3/5" />
            <div className="h-1.5 bg-muted rounded w-2/3" />
            <div className="grid grid-cols-3 gap-2 mt-2">
              {["412%", "8mo", "$1.67M"].map((v) => (
                <div key={v} className="border border-border rounded p-1.5 text-center">
                  <p className="text-[10px] font-bold text-foreground">{v}</p>
                </div>
              ))}
            </div>
            <div className="h-1.5 bg-muted rounded w-full" />
            <div className="h-1.5 bg-muted rounded w-4/5" />
            <div className="h-4 bg-foreground rounded mt-2" />
          </div>
        </div>
      </StudioPanel>

      {/* Quick Actions */}
      <StudioPanel title="Quick Actions">
        <div className="flex flex-col gap-1.5 mb-3">
          {QUICK_ACTIONS.map((a) => (
            <button
              key={a}
              className="flex items-center justify-between px-2.5 py-2 border border-border rounded-md text-[12px] text-muted-foreground hover:bg-muted transition-colors"
            >
              {a}
              <ExternalLink size={11} className="shrink-0" />
            </button>
          ))}
        </div>
        <button className="w-full h-8 border border-foreground text-foreground text-[12px] font-semibold rounded-md hover:bg-muted transition-colors flex items-center justify-center gap-2">
          <Share2 size={13} /> Share for Stakeholder Review
        </button>
      </StudioPanel>
    </>
  );
}

// ── Status Bar ─────────────────────────────────────────────────────────────────

function StatusBar() {
  return (
    <>
      <span className="h-6 px-2.5 bg-green-600 text-white text-[11px] font-semibold rounded flex items-center">
        Narrative complete
      </span>
      <span>Stakeholder versions: 5</span>
      <span>Formats: 4</span>
      <button className="flex items-center gap-1 text-[11px] font-medium hover:underline">
        <Share2 size={11} /> Share ▾
      </button>
    </>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function Stage5Narrative() {
  const [stakeholders, setStakeholders] = useState(STAKEHOLDERS);
  const [activeSection, setActiveSection] = useState<NarrativeSection>("Context");
  const [selectedFormat, setSelectedFormat] = useState("pdf");

  return (
    <ValueStudioShell
      stageId={5}
      title="Narrative"
      subtitle="Package the validated model into stakeholder-ready stories — same numbers, different emphasis"
      deal={DEMO_DEAL}
      stages={buildStages(5)}
      prevLabel="Validation"
      prevPath="/model/value-studio/validation"
      nextLabel="Continue to Tracking"
      nextPath="/model/value-studio/tracking"
      extraActions={
        <button className="h-8 px-3 border border-border text-[12px] font-medium rounded-md hover:bg-muted transition-colors flex items-center gap-1.5">
          <Share2 size={13} /> Share for Review
        </button>
      }
      leftPanel={<LeftPanel stakeholders={stakeholders} setStakeholders={setStakeholders} />}
      centerPanel={<CenterPanel activeSection={activeSection} setActiveSection={setActiveSection} />}
      rightPanel={<RightPanel selectedFormat={selectedFormat} setSelectedFormat={setSelectedFormat} />}
      statusBar={<StatusBar />}
    />
  );
}
