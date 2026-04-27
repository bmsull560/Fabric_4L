/**
 * Value Studio — Stage 2: Mapping
 * Connect product capabilities to customer pain through use cases — builds the value chains
 */
import { useState } from "react";
import {
  CheckCircle2, ChevronDown, ChevronRight, ChevronUp,
  Zap, Search, Cpu, BookOpen, FileText, MessageSquare,
  Monitor, Mic, Play
} from "lucide-react";
import ValueStudioShell, {
  StudioPanel, DEMO_DEAL, buildStages,
} from "./ValueStudioShell";
import { cn } from "@/lib/utils";
import { Btn, SearchInput } from "@/components/WfPrimitives";

// ── Mock data ──────────────────────────────────────────────────────────────────

const PAIN_POINTS = [
  { id: 1, score: 8, text: "Reps spend 6hrs/week on content search", mapped: true, color: "bg-red-500" },
  { id: 2, score: 6, text: "New reps take 6 months to ramp", mapped: true, color: "bg-yellow-400" },
  { id: 3, score: 9, text: "No visibility into deal engagement", mapped: false, color: "bg-red-500" },
  { id: 4, score: 5, text: "Inconsistent messaging across field", mapped: false, color: "bg-muted-foreground" },
];

const CAPABILITY_PALETTE = [
  {
    category: "Practical AI",
    icon: <Cpu size={13} className="text-purple-500" />,
    items: ["AI Agents", "Intelligent Coaching", "Smart Recommendations"],
  },
  {
    category: "Learning",
    icon: <BookOpen size={13} className="text-blue-500" />,
    items: ["Onboarding Journeys", "Skill Reinforcement", "Certifications"],
  },
  {
    category: "Content",
    icon: <FileText size={13} className="text-green-500" />,
    items: ["Content Management", "Just-in-Time Delivery", "Search & Find"],
  },
  {
    category: "Conversation Intelligence",
    icon: <MessageSquare size={13} className="text-orange-500" />,
    items: ["Call Recording", "Deal Analysis", "Win/Loss Patterns"],
  },
  {
    category: "Digital Selling",
    icon: <Monitor size={13} className="text-cyan-500" />,
    items: ["Digital Sales Rooms", "Buyer Engagement", "Content Tracking"],
  },
  {
    category: "AI Role Play",
    icon: <Play size={13} className="text-pink-500" />,
    items: ["Practice Scenarios", "Objection Handling"],
  },
];

// ── Value Chain ────────────────────────────────────────────────────────────────

interface ChainStep {
  label: string;
  value: string;
  aiSuggested?: boolean;
}

interface ValueChain {
  id: number;
  painText: string;
  impact?: string;
  status: "expanded" | "collapsed" | "building";
  steps?: {
    pain: ChainStep;
    useCase: ChainStep;
    capability: ChainStep;
    outcome: ChainStep;
    metric: ChainStep;
  };
}

const CHAINS: ValueChain[] = [
  {
    id: 1,
    painText: "Reps spend 6hrs/week on content search",
    status: "expanded",
    steps: {
      pain: { label: "Pain", value: "Reps spend 6hrs/week searching for content" },
      useCase: { label: "Use Case", value: "Just-in-time content delivery in seller workflow", aiSuggested: true },
      capability: { label: "Capability", value: "Sales Content Management + Smart Search" },
      outcome: { label: "Outcome", value: "75% reduction in content search time" },
      metric: { label: "Metric", value: "Hours saved/rep/week · Baseline: 6 → Target: 1.5" },
    },
  },
  {
    id: 2,
    painText: "New rep ramp time",
    impact: "$1.2M / yr",
    status: "collapsed",
    steps: {
      pain: { label: "Pain", value: "New rep ramp time" },
      useCase: { label: "Use Case", value: "Guided Onboarding Journeys" },
      capability: { label: "Capability", value: "Learning + AI Coaching" },
      outcome: { label: "Outcome", value: "4.2 → 3 month ramp" },
      metric: { label: "Metric", value: "$1.2M / yr" },
    },
  },
  {
    id: 3,
    painText: "No visibility into deal engagement after send",
    status: "building",
  },
];

// ── Sub-components ─────────────────────────────────────────────────────────────

function ChainStepBox({ step }: { step: ChainStep }) {
  return (
    <div className="bg-background border border-border rounded-md p-3 min-w-0">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">{step.label}</p>
      <p className="text-[12px] text-foreground leading-snug">{step.value}</p>
      {step.aiSuggested && (
        <div className="flex items-center gap-1 mt-1.5">
          <Zap size={9} className="text-primary" />
          <span className="text-[10px] text-primary font-medium">AI suggested</span>
        </div>
      )}
    </div>
  );
}

function ExpandedChain({ chain }: { chain: ValueChain }) {
  if (!chain.steps) return null;
  const steps = [chain.steps.pain, chain.steps.useCase, chain.steps.capability, chain.steps.outcome, chain.steps.metric];
  return (
    <div className="border border-border rounded-lg p-4 bg-primary/5">
      <p className="text-[11px] font-semibold text-primary mb-3 uppercase tracking-wider">
        Value Chain — Chain {chain.id} (Expanded)
      </p>
      <div className="flex items-stretch gap-2">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-2 flex-1 min-w-0">
            <ChainStepBox step={step} />
            {i < steps.length - 1 && (
              <ChevronRight size={12} className="text-muted-foreground shrink-0" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CollapsedChain({ chain }: { chain: ValueChain }) {
  return (
    <div className="border border-border rounded-lg px-4 py-3 flex items-center justify-between hover:bg-muted/30 cursor-pointer">
      <div className="flex items-center gap-3">
        <p className="text-[12px] font-semibold uppercase tracking-wider text-muted-foreground">
          Value Chain — Chain {chain.id} (Collapsed)
        </p>
        <span className="text-[12px] text-muted-foreground">
          {chain.steps?.pain.value} → {chain.steps?.useCase.value} → {chain.steps?.outcome.value}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-[12px] font-semibold text-foreground">{chain.impact}</span>
        <CheckCircle2 size={13} className="text-green-500" />
      </div>
    </div>
  );
}

function BuildingChain({ chain }: { chain: ValueChain }) {
  return (
    <div className="border border-border rounded-lg p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-3">
        Value Chain — Chain {chain.id} (Building)
      </p>
      <div className="border border-border rounded-md p-3 mb-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">Pain</p>
        <p className="text-[12px] text-foreground">{chain.painText}</p>
      </div>
      <div className="border border-border rounded-md p-3 mb-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">Use Case</p>
        <p className="text-[12px] text-muted-foreground">Drop a capability from the palette →</p>
      </div>
      <div className="border-2 border-dashed border-border rounded-md p-4 flex items-center justify-center">
        <p className="text-[12px] text-muted-foreground">Drag capability here to continue</p>
      </div>
    </div>
  );
}

// ── Left Panel ─────────────────────────────────────────────────────────────────

function LeftPanel() {
  return (
    <StudioPanel title="Pain Points (from Discovery)">
      <div className="flex flex-col gap-0">
        {PAIN_POINTS.map((pp) => (
          <div key={pp.id} className="flex items-start gap-2 py-2.5 border-b border-border last:border-0">
            <span className={cn("w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0 mt-0.5", pp.color)}>
              {pp.score}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-[12px] text-foreground leading-snug">{pp.text}</p>
            </div>
            {pp.mapped && <CheckCircle2 size={12} className="text-green-500 shrink-0 mt-0.5" />}
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
        <span className="text-[11px] text-muted-foreground">Unmapped: 2</span>
        <span className="h-6 px-2.5 bg-primary/10 text-primary text-[11px] font-semibold rounded flex items-center">Mapped: 2</span>
      </div>
    </StudioPanel>
  );
}

// ── Center Panel ───────────────────────────────────────────────────────────────

function CenterPanel() {
  return (
    <>
      {CHAINS.map((chain) => (
        <div key={chain.id}>
          {chain.status === "expanded" && <ExpandedChain chain={chain} />}
          {chain.status === "collapsed" && <CollapsedChain chain={chain} />}
          {chain.status === "building" && <BuildingChain chain={chain} />}
        </div>
      ))}
    </>
  );
}

// ── Right Panel ────────────────────────────────────────────────────────────────

function CapabilityPalette() {
  const [expanded, setExpanded] = useState<string[]>(["Practical AI", "Learning", "Content"]);
  const [search, setSearch] = useState("");

  const toggle = (cat: string) =>
    setExpanded((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );

  const filtered = CAPABILITY_PALETTE.map((cat) => ({
    ...cat,
    items: cat.items.filter((item) =>
      item.toLowerCase().includes(search.toLowerCase())
    ),
  })).filter((cat) => cat.items.length > 0 || search === "");

  return (
    <StudioPanel title="Capability Palette">
      <div className="mb-3">
        <SearchInput
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search capabilities..."
        />
      </div>
      <div className="flex flex-col gap-0 overflow-y-auto max-h-[500px]">
        {filtered.map((cat) => (
          <div key={cat.category}>
            <button
              onClick={() => toggle(cat.category)}
              className="w-full flex items-center justify-between py-2 text-[12px] font-semibold text-foreground hover:text-primary transition-colors"
            >
              <div className="flex items-center gap-2">
                {cat.icon}
                {cat.category}
              </div>
              {expanded.includes(cat.category) ? (
                <ChevronDown size={12} />
              ) : (
                <ChevronRight size={12} />
              )}
            </button>
            {expanded.includes(cat.category) && (
              <div className="flex flex-col gap-0 pl-5 mb-1">
                {cat.items.map((item) => (
                  <div
                    key={item}
                    draggable
                    className="py-1.5 text-[12px] text-muted-foreground hover:text-foreground cursor-grab border-b border-border/50 last:border-0 transition-colors"
                  >
                    {item}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </StudioPanel>
  );
}

// ── Status Bar ─────────────────────────────────────────────────────────────────

function StatusBar() {
  return (
    <>
      <span className="h-6 px-2.5 bg-foreground text-background text-[11px] font-semibold rounded flex items-center">Chains: 3</span>
      <span>Bridge gaps: 1</span>
      <span className="text-primary font-medium">AI suggestions: 5</span>
      <Btn variant="ghost" className="h-6 px-2 text-primary hover:underline">Auto-map all</Btn>
    </>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function Stage2Mapping() {
  return (
    <ValueStudioShell
      stageId={2}
      title="Mapping"
      subtitle="Connect product capabilities to customer pain through use cases — builds the value chains"
      deal={DEMO_DEAL}
      stages={buildStages(2)}
      prevLabel="Discovery"
      prevPath="/model/value-studio/discovery"
      nextLabel="Continue to Modeling"
      nextPath="/model/value-studio/modeling"
      secondaryAction={{ label: "Auto-map All Pains", onClick: () => {} }}
      leftPanel={<LeftPanel />}
      centerPanel={<CenterPanel />}
      rightPanel={<CapabilityPalette />}
      statusBar={<StatusBar />}
    />
  );
}
