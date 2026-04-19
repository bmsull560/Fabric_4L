/**
 * Value Studio — Stage 6: Tracking
 * Measure actual outcomes against the model — close the loop between promised and realized value
 */
import { useState, useEffect, useRef } from "react";
import { Plus, Download, TrendingUp, TrendingDown, Minus } from "lucide-react";
import ValueStudioShell, {
  StudioPanel, DEMO_DEAL, buildStages,
} from "./ValueStudioShell";
import { cn } from "@/lib/utils";

// ── Mock data ──────────────────────────────────────────────────────────────────

const KPI_ITEMS = [
  {
    label: "Revenue Uplift",
    promised: "$1.1M / Yr 3",
    actual: "$495K",
    delta: "-55%",
    pct: 45,
    trend: "down" as const,
    note: "On track — Q3/Q4 data not yet collected",
    color: "bg-yellow-400",
  },
  {
    label: "Cost Savings",
    promised: "$840K / Yr 2",
    actual: "$521K",
    delta: "-38%",
    pct: 62,
    trend: "up" as const,
    note: "Ahead of pace at Month 8",
    color: "bg-green-500",
  },
  {
    label: "Rep Ramp Time",
    promised: "3 months",
    actual: "4.2 months",
    delta: "+1.2 mo",
    pct: 55,
    trend: "down" as const,
    note: "Below target — manager coaching delayed",
    color: "bg-orange-400",
  },
  {
    label: "Content Find Time",
    promised: "< 5 min",
    actual: "8 min",
    delta: "+3 min",
    pct: 63,
    trend: "down" as const,
    note: "Search tool adoption at 71%",
    color: "bg-orange-400",
  },
];

const QUARTERLY_DATA = [
  { quarter: "Q1", promised: "$50K", actual: "$42K", pct: 84, status: "On track" },
];

const MILESTONES_Q1 = [
  { label: "Platform configured and live", done: true },
  { label: "Content library migrated (1,400 assets)", done: true },
  { label: "100 reps onboarded (Enterprise West)", done: true },
  { label: "Manager training program launched", done: false },
];

const MILESTONES_Q2 = [
  { label: "Scale to 300 reps (Enterprise East)", done: false },
  { label: "Launch AI coaching program", done: false },
  { label: "First QBR — value review with CRO", done: false },
];

const EXPANSION_ITEMS = [
  { label: "AI Role Play", status: "Not activated", value: "$200K add'l value", cta: "Model Expansion Value" },
  { label: "Digital Selling Rooms", status: "Pilot — 10 reps", value: "$150K add'l value", cta: "Expand to Full Org" },
];

// ── Adoption Curve Chart ───────────────────────────────────────────────────────

function AdoptionCurveChart() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const padL = 40, padR = 20, padT = 10, padB = 30;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;

    // Grid lines
    ctx.strokeStyle = "#f3f4f6";
    ctx.lineWidth = 1;
    [0, 25, 50, 75, 100].forEach((pct) => {
      const y = padT + chartH - (pct / 100) * chartH;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(W - padR, y);
      ctx.stroke();
    });

    // Y axis labels
    ctx.fillStyle = "#9ca3af";
    ctx.font = "9px system-ui";
    ctx.textAlign = "right";
    [0, 25, 50, 75, 100].forEach((pct) => {
      const y = padT + chartH - (pct / 100) * chartH;
      ctx.fillText(`${pct}%`, padL - 4, y + 3);
    });

    const months = 18;
    const toX = (m: number) => padL + (m / months) * chartW;
    const toY = (pct: number) => padT + chartH - (pct / 100) * chartH;

    // Promised S-curve (dashed gray)
    ctx.strokeStyle = "#9ca3af";
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    for (let m = 0; m <= months; m++) {
      const t = m / months;
      const sigmoid = 1 / (1 + Math.exp(-10 * (t - 0.5)));
      const x = toX(m);
      const y = toY(sigmoid * 100);
      m === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Actual curve (solid black) — only up to month 8
    const actualMonths = 8;
    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let m = 0; m <= actualMonths; m++) {
      const t = m / months;
      // Slightly lagging S-curve
      const sigmoid = 1 / (1 + Math.exp(-10 * (t - 0.6)));
      const x = toX(m);
      const y = toY(sigmoid * 100);
      m === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Current position dot
    const currentM = actualMonths;
    const currentT = currentM / months;
    const currentSigmoid = 1 / (1 + Math.exp(-10 * (currentT - 0.6)));
    const dotX = toX(currentM);
    const dotY = toY(currentSigmoid * 100);
    ctx.fillStyle = "#111827";
    ctx.beginPath();
    ctx.arc(dotX, dotY, 6, 0, Math.PI * 2);
    ctx.fill();

    // Gap annotation
    const gapX = toX(actualMonths);
    const promisedY = toY((1 / (1 + Math.exp(-10 * (currentT - 0.5)))) * 100);
    ctx.strokeStyle = "#f59e0b";
    ctx.lineWidth = 2;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(gapX, dotY);
    ctx.lineTo(gapX, promisedY);
    ctx.stroke();
    ctx.setLineDash([]);

    // X-axis labels
    ctx.fillStyle = "#9ca3af";
    ctx.font = "9px system-ui";
    ctx.textAlign = "center";
    [0, 3, 6, 9, 12, 15, 18].forEach((m) => {
      ctx.fillText(`M${m}`, toX(m), H - 8);
    });

    // "Months post-launch" label
    ctx.fillStyle = "#9ca3af";
    ctx.font = "9px system-ui";
    ctx.textAlign = "right";
    ctx.fillText("Months post-launch", W - padR, padT + 8);
  }, []);

  return <canvas ref={canvasRef} width={860} height={200} className="w-full" />;
}

// ── Left Panel ─────────────────────────────────────────────────────────────────

function LeftPanel() {
  return (
    <StudioPanel title="KPI Dashboard">
      <div className="flex flex-col gap-4">
        {KPI_ITEMS.map((kpi) => {
          const TrendIcon = kpi.trend === "up" ? TrendingUp : kpi.trend === "down" ? TrendingDown : Minus;
          const trendColor = kpi.trend === "up" ? "text-green-600" : kpi.trend === "down" ? "text-orange-600" : "text-muted-foreground";
          return (
            <div key={kpi.label} className="pb-3 border-b border-border last:border-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{kpi.label}</span>
                <span className={cn("flex items-center gap-0.5 text-[11px] font-bold", trendColor)}>
                  <TrendIcon size={11} /> {kpi.delta}
                </span>
              </div>
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-[13px] font-bold text-foreground">{kpi.actual}</span>
                <span className="text-[10px] text-muted-foreground">vs {kpi.promised}</span>
              </div>
              <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden mb-1">
                <div className={cn("h-full rounded-full", kpi.color)} style={{ width: `${kpi.pct}%` }} />
              </div>
              <p className="text-[10px] text-muted-foreground">{kpi.note}</p>
            </div>
          );
        })}
      </div>
    </StudioPanel>
  );
}

// ── Center Panel ───────────────────────────────────────────────────────────────

function CenterPanel() {
  return (
    <>
      {/* Promised vs Actual Quarterly */}
      <StudioPanel title="Promised vs Actual — Quarterly">
        <table className="w-full text-[12px] mb-3">
          <thead>
            <tr className="border-b border-border">
              {["Quarter", "Promised", "Actual", "vs Pace"].map((h) => (
                <th key={h} className="text-left py-2 pr-4 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {QUARTERLY_DATA.map((row) => (
              <tr key={row.quarter} className="border-b border-border last:border-0">
                <td className="py-2.5 pr-4 font-semibold">{row.quarter}</td>
                <td className="py-2.5 pr-4 text-muted-foreground">{row.promised}</td>
                <td className="py-2.5 pr-4 font-semibold">{row.actual}</td>
                <td className="py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-green-500 rounded-full" style={{ width: `${row.pct}%` }} />
                    </div>
                    <span className="text-green-600 font-semibold text-[11px]">{row.pct}%</span>
                    <span className="text-green-600 text-[11px]">On track ↑</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-[12px] font-semibold text-foreground">Overall: 87% of pace</p>
      </StudioPanel>

      {/* Adoption Curve */}
      <StudioPanel title="Adoption Curve — Promised vs Actual">
        <AdoptionCurveChart />
        <div className="flex items-center gap-3 mt-2 flex-wrap">
          <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className="inline-block w-6 border-t-2 border-dashed border-muted-foreground" /> Promised
          </span>
          <span className="flex items-center gap-1.5 text-[11px] text-foreground">
            <span className="inline-block w-6 border-t-2 border-foreground" /> Actual
          </span>
          <span className="flex items-center gap-1.5 text-[11px] text-yellow-600">
            <span className="inline-block w-3 border-l-2 border-dashed border-yellow-500 h-3" /> Gap: -12pp at Month 8
          </span>
        </div>
      </StudioPanel>

      {/* Expansion Opportunities */}
      <StudioPanel title="Expansion Opportunities">
        <div className="flex flex-col gap-2">
          {EXPANSION_ITEMS.map((item) => (
            <div key={item.label} className="flex items-center justify-between p-3 border border-border rounded-md">
              <div>
                <p className="text-[12px] font-semibold text-foreground">{item.label}</p>
                <p className="text-[11px]">
                  <span className="text-muted-foreground">{item.status} · </span>
                  <span className="text-green-600 font-medium">{item.value}</span>
                </p>
              </div>
              <button className="h-7 px-3 border border-border text-[11px] font-medium rounded-md hover:bg-muted transition-colors whitespace-nowrap">
                {item.cta}
              </button>
            </div>
          ))}
        </div>
      </StudioPanel>
    </>
  );
}

// ── Right Panel ────────────────────────────────────────────────────────────────

function RightPanel() {
  return (
    <>
      <StudioPanel title="Milestones & Actions">
        <div className="mb-4">
          <p className="text-[11px] font-bold uppercase tracking-wider text-foreground mb-2">Q1 2026</p>
          <div className="flex flex-col gap-1.5">
            {MILESTONES_Q1.map((m) => (
              <div key={m.label} className="flex items-start gap-2">
                <div className={cn(
                  "mt-0.5 w-3.5 h-3.5 rounded-full border-2 shrink-0 flex items-center justify-center",
                  m.done ? "border-green-600 bg-green-600" : "border-muted-foreground"
                )}>
                  {m.done && <span className="text-white text-[8px]">✓</span>}
                </div>
                <span className={cn("text-[11px]", m.done ? "text-muted-foreground line-through" : "text-foreground")}>
                  {m.label}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <p className="text-[11px] font-bold uppercase tracking-wider text-foreground mb-2">Q2 2026</p>
          <div className="flex flex-col gap-1.5">
            {MILESTONES_Q2.map((m) => (
              <div key={m.label} className="flex items-start gap-2">
                <div className="mt-0.5 w-3.5 h-3.5 rounded-full border-2 border-muted-foreground shrink-0" />
                <span className="text-[11px] text-muted-foreground">{m.label}</span>
              </div>
            ))}
          </div>
        </div>

        <button className="w-full h-7 border border-border text-[11px] font-medium rounded-md hover:bg-muted transition-colors flex items-center justify-center gap-1.5">
          <Plus size={11} /> Add Milestone
        </button>
      </StudioPanel>

      {/* Renewal Signal */}
      <StudioPanel title="Renewal Signal">
        <div className="text-center mb-3">
          <p className="text-[36px] font-bold text-foreground leading-none">8</p>
          <p className="text-[11px] text-muted-foreground">months to renewal</p>
        </div>
        <div className="flex flex-col gap-1.5">
          {[
            { label: "Value promised", value: "$1.9M", color: "text-foreground" },
            { label: "Value realized (to date)", value: "$222K", color: "text-yellow-600" },
            { label: "Expansion potential", value: "$350K", color: "text-green-600" },
          ].map((r) => (
            <div key={r.label} className="flex items-center justify-between text-[12px]">
              <span className="text-muted-foreground">{r.label}</span>
              <span className={cn("font-bold", r.color)}>{r.value}</span>
            </div>
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
      <span className="h-6 px-2.5 bg-primary/10 text-primary text-[11px] font-semibold rounded flex items-center">87% of pace</span>
      <span>2 KPIs on track</span>
      <span className="text-orange-600 font-medium">1 at risk</span>
      <span>Renewal: 8 months</span>
      <span className="text-green-600 font-medium">Expansion potential: $350K</span>
    </>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function Stage6Tracking() {
  return (
    <ValueStudioShell
      stageId={6}
      title="Tracking"
      subtitle="Measure actual outcomes against the model — close the loop between promised and realized value"
      deal={DEMO_DEAL}
      stages={buildStages(6)}
      prevLabel="Narrative"
      prevPath="/model/value-studio/narrative"
      extraActions={
        <button className="h-8 px-3 border border-border text-[12px] font-medium rounded-md hover:bg-muted transition-colors flex items-center gap-1.5">
          <Download size={13} /> Export Realization Report
        </button>
      }
      leftPanel={<LeftPanel />}
      centerPanel={<CenterPanel />}
      rightPanel={<RightPanel />}
      statusBar={<StatusBar />}
    />
  );
}
