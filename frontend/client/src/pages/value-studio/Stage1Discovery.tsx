/**
 * Value Studio — Stage 1: Discovery
 * Build the business context for your value model — must reach ≥70% context score to advance
 */
import { useState } from "react";
import {
  Upload, Link2, FileText, Clipboard,
  Plus, CheckCircle2, Circle, Zap,
  ChevronDown, ChevronRight
} from "lucide-react";
import ValueStudioShell, {
  StudioPanel, DEMO_DEAL, buildStages,
} from "./ValueStudioShell";
import { cn } from "@/lib/utils";

// ── Mock data ──────────────────────────────────────────────────────────────────

const UPLOADED_SOURCES = [
  { id: 1, label: "Discovery Call Transcript", status: "ok" },
  { id: 2, label: "CRM Opportunity Record", status: "ok" },
  { id: 3, label: "Prospect Website Export", status: "ok" },
];

const PAIN_POINTS = [
  { id: 1, score: 8, text: "Reps spend 6hrs/week searching for content", category: "Cost Reduction", color: "bg-red-500" },
  { id: 2, score: 6, text: "New reps take 6 months to fully ramp", category: "Productivity", color: "bg-yellow-400" },
  { id: 3, score: 9, text: "No visibility into deal engagement after send", category: "Revenue Risk", color: "bg-red-500" },
  { id: 4, score: 5, text: "Inconsistent messaging across the field", category: "Quality", color: "bg-muted-foreground" },
  { id: 5, score: 7, text: "Manager coaching time is untracked and ad hoc", category: "Productivity", color: "bg-yellow-400" },
];

const STAKEHOLDERS = [
  { role: "CRO", name: "Pat Williams", authority: "Decider", confirmed: true },
  { role: "Enablement", name: "Sam Chen", authority: "Influencer", confirmed: true },
];

const INITIATIVES = [
  { quarter: "Q1", text: "Consolidate vendor tech stack — decision by Jan 15" },
  { quarter: "Q2", text: "Roll out pilot to Enterprise West (100 reps)" },
  { quarter: "Q3", text: "Scale to full org — 500 reps, all regions" },
];

const AI_SUGGESTIONS = [
  "Slow new rep ramp time",
  "Content findability at point of need",
  "Inconsistent sales messaging",
  "Low coaching visibility for managers",
];

const EXTRACTED_QUOTES = [
  { text: '"Faster time to close is our top initiative this quarter"', source: "Discovery Call Transcript — Revenue Uplift" },
  { text: '"We lose reps after 8 months because onboarding is too slow"', source: "CRM Notes — Productivity / Retention" },
];

// ── Sub-components ─────────────────────────────────────────────────────────────

function SourceButton({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <button className="w-full flex items-center gap-2 px-3 py-2 text-[12px] font-medium border border-border rounded-md hover:bg-muted transition-colors text-left">
      <span className="text-muted-foreground">{icon}</span>
      {label}
    </button>
  );
}

function PainPointRow({ pp }: { pp: typeof PAIN_POINTS[0] }) {
  return (
    <div className="flex items-start gap-2 py-2 border-b border-border last:border-0">
      <span className={cn("w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0 mt-0.5", pp.color)}>
        {pp.score}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-[12px] text-foreground leading-snug">{pp.text}</p>
        <p className="text-[10px] text-muted-foreground mt-0.5">→ {pp.category}</p>
      </div>
    </div>
  );
}

// ── Left Panel ─────────────────────────────────────────────────────────────────

function LeftPanel() {
  return (
    <>
      <StudioPanel title="Your Sources">
        <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">
          Add discovery materials — AI extracts entities and populates the canvas with confidence scores.
        </p>
        <div className="flex flex-col gap-2 mb-4">
          <SourceButton icon={<Upload size={12} />} label="Upload notes / transcript" />
          <SourceButton icon={<Link2 size={12} />} label="Connect CRM" />
          <SourceButton icon={<FileText size={12} />} label="Import ontology map" />
          <SourceButton icon={<Clipboard size={12} />} label="Paste call transcript" />
        </div>
        <div className="border-t border-border pt-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">Uploaded</p>
          <div className="flex flex-col gap-1.5">
            {UPLOADED_SOURCES.map((s) => (
              <div key={s.id} className="flex items-center gap-2 text-[11px]">
                <CheckCircle2 size={11} className="text-green-500 shrink-0" />
                <span className="text-foreground">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </StudioPanel>
    </>
  );
}

// ── Center Panel ───────────────────────────────────────────────────────────────

function CenterPanel() {
  const [stakeholders, setStakeholders] = useState(STAKEHOLDERS);

  return (
    <>
      {/* Customer Profile */}
      <StudioPanel title="Customer Profile">
        <div className="grid grid-cols-2 gap-x-6 gap-y-3">
          {[
            { label: "Company", value: "Acme Corp" },
            { label: "Industry", value: "Technology / SaaS" },
            { label: "Employees", value: "2,400" },
            { label: "Revenue", value: "$180M" },
            { label: "HQ", value: "Austin, TX" },
            { label: "Urgency", value: "Q1 decision" },
          ].map((f) => (
            <div key={f.label}>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-0.5">{f.label}</p>
              <p className="text-[13px] text-foreground font-medium">{f.value}</p>
            </div>
          ))}
        </div>
      </StudioPanel>

      {/* Stakeholder Map */}
      <StudioPanel
        title="Stakeholder Map"
        action={
          <button className="flex items-center gap-1 text-[11px] font-medium text-primary hover:underline">
            <Plus size={11} /> Add Stakeholder
          </button>
        }
      >
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-border">
              {["Role", "Name", "Authority", "Status"].map((h) => (
                <th key={h} className="text-left py-1.5 pr-4 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stakeholders.map((s, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                <td className="py-2 pr-4 font-medium">{s.role}</td>
                <td className="py-2 pr-4">{s.name}</td>
                <td className="py-2 pr-4 text-muted-foreground">{s.authority}</td>
                <td className="py-2">
                  {s.confirmed
                    ? <CheckCircle2 size={13} className="text-green-500" />
                    : <Circle size={13} className="text-muted-foreground" />}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </StudioPanel>

      {/* Pain Point Registry */}
      <StudioPanel
        title="Pain Point Registry"
        action={
          <button className="flex items-center gap-1 text-[11px] font-medium text-primary hover:underline">
            <Plus size={11} /> Add Pain
          </button>
        }
      >
        <div>
          {PAIN_POINTS.map((pp) => (
            <PainPointRow key={pp.id} pp={pp} />
          ))}
        </div>
      </StudioPanel>

      {/* Initiatives & Timeline */}
      <StudioPanel title="Initiatives & Timeline">
        <div className="flex flex-col gap-2">
          {INITIATIVES.map((item) => (
            <div key={item.quarter} className="flex items-start gap-3 text-[12px]">
              <span className="text-[10px] font-bold text-muted-foreground w-6 shrink-0 mt-0.5">{item.quarter}</span>
              <span className="text-foreground">{item.text}</span>
            </div>
          ))}
        </div>
      </StudioPanel>
    </>
  );
}

// ── Right Panel ────────────────────────────────────────────────────────────────

function RightPanel() {
  const [accepted, setAccepted] = useState<number[]>([]);

  return (
    <>
      <StudioPanel title="AI Assist">
        <p className="text-[11px] text-muted-foreground mb-2 leading-relaxed">
          Suggested pain points based on <strong>Technology / SaaS</strong> companies of this size:
        </p>
        <div className="flex flex-col gap-1.5 mb-4">
          {AI_SUGGESTIONS.map((s, i) => (
            <div key={i} className="flex items-center gap-2 text-[12px]">
              <Zap size={10} className="text-primary shrink-0" />
              <span className="text-foreground">{s}</span>
            </div>
          ))}
        </div>
      </StudioPanel>

      <StudioPanel title="Extracted from Sources">
        <div className="flex flex-col gap-3">
          {EXTRACTED_QUOTES.map((q, i) => (
            <div key={i} className="bg-muted/50 rounded-md p-3">
              <p className="text-[12px] text-foreground italic leading-snug mb-1">{q.text}</p>
              <p className="text-[10px] text-muted-foreground">{q.source}</p>
            </div>
          ))}
          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] font-semibold text-foreground">Confidence: 85%</span>
            <div className="flex gap-1.5">
              <button className="h-6 px-2.5 text-[11px] font-semibold bg-foreground text-background rounded hover:bg-foreground/90">Accept</button>
              <button className="h-6 px-2.5 text-[11px] border border-border rounded hover:bg-muted">Edit</button>
            </div>
          </div>
        </div>
      </StudioPanel>

      <StudioPanel title="Process Inventory">
        <div className="flex flex-col gap-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-3 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </StudioPanel>
    </>
  );
}

// ── Status Bar ─────────────────────────────────────────────────────────────────

function StatusBar() {
  return (
    <>
      <div className="flex items-center gap-1.5">
        <span className="h-6 px-2.5 bg-foreground text-background text-[11px] font-semibold rounded flex items-center">
          Context Score: 82%
        </span>
      </div>
      <span>Stakeholders: 3/3</span>
      <span>Pain Points: 5</span>
      <span>Sources: 2</span>
      <span className="text-yellow-600 font-medium">Must reach ≥70% to advance</span>
    </>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function Stage1Discovery() {
  return (
    <ValueStudioShell
      stageId={1}
      title="Discovery"
      subtitle="Build the business context for your value model — must reach ≥70% context score to advance"
      deal={DEMO_DEAL}
      stages={buildStages(1)}
      nextLabel="Continue to Mapping"
      nextPath="/model/value-studio/mapping"
      secondaryAction={{ label: "Import", onClick: () => {} }}
      leftPanel={<LeftPanel />}
      centerPanel={<CenterPanel />}
      rightPanel={<RightPanel />}
      statusBar={<StatusBar />}
    />
  );
}
