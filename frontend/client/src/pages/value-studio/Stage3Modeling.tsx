/**
 * Value Studio — Stage 3: Modeling
 * Quantify business impact with financial rigor — baselines, projections, and scenario analysis
 */
import { useState, useEffect, useRef } from "react";
import { Plus, Phone } from "lucide-react";
import ValueStudioShell, {
  StudioPanel, DEMO_DEAL, buildStages,
} from "./ValueStudioShell";
import { cn } from "@/lib/utils";
import { Btn, DataTable } from "@/components/WfPrimitives";

// ── Mock data ──────────────────────────────────────────────────────────────────

const VALUE_CHAINS = [
  { id: 1, name: "Chain 1 — Content Search", value: "$840K/YR", pct: 70, complete: true },
  { id: 2, name: "Chain 2 — Rep Ramp Time", value: "$1.2M/YR", pct: 88, complete: true },
  { id: 3, name: "Chain 3 — Deal Visibility", value: "—", pct: 20, complete: false, note: "Incomplete — needs capability" },
];

const PROJECTION = [
  { label: "Benefits", y1: "$340K", y2: "$840K", y3: "$1.1M" },
  { label: "Costs",    y1: "$180K", y2: "$120K", y3: "$120K" },
  { label: "Net",      y1: "$160K", y2: "$720K", y3: "$1.0M", bold: true },
];

const KEY_METRICS = [
  { label: "3-Year ROI", value: "412%", sub: "Conservative: 289% | Expected: 412% | Optimistic: 535%" },
  { label: "Payback Period", value: "8 months" },
  { label: "NPV", value: "$1.67M" },
  { label: "Benefit/Cost", value: "4.2×" },
];

const SCENARIOS = [
  { label: "3-Year ROI",  conservative: "289%",   expected: "412%",    optimistic: "535%" },
  { label: "Payback",     conservative: "12 mo",  expected: "8 mo",    optimistic: "6 mo" },
  { label: "NPV",         conservative: "$1.1M",  expected: "$1.67M",  optimistic: "$2.2M" },
];

const ASSUMPTIONS = [
  { confidence: "high",   color: "bg-green-100 text-green-800 border-green-200",   label: "HIGH",   items: ["Revenue per rep stated by customer", "Rep headcount — CRM confirmed"] },
  { confidence: "medium", color: "bg-yellow-100 text-yellow-800 border-yellow-200", label: "MEDIUM", items: ["Adoption curve — 8-month S-curve", "Ramp period — industry average", "Content utilization rate"] },
  { confidence: "low",    color: "bg-red-100 text-red-800 border-red-200",          label: "LOW",    items: ["Cross-sell uplift %", "Manager coaching adoption", "Content find rate improvement"] },
];

// ── S-Curve Chart ──────────────────────────────────────────────────────────────

function SCurveChart() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    // Draw axes
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(40, 10);
    ctx.lineTo(40, H - 30);
    ctx.lineTo(W - 10, H - 30);
    ctx.stroke();

    // S-curve path
    const points: [number, number][] = [];
    const months = 18;
    for (let m = 0; m <= months; m++) {
      const t = m / months;
      // Logistic S-curve
      const sigmoid = 1 / (1 + Math.exp(-10 * (t - 0.5)));
      const x = 40 + (m / months) * (W - 60);
      const y = H - 30 - sigmoid * (H - 50);
      points.push([x, y]);
    }

    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    points.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
    ctx.stroke();

    // X-axis labels
    ctx.fillStyle = "#9ca3af";
    ctx.font = "10px system-ui";
    ctx.textAlign = "center";
    [0, 3, 6, 9, 12, 15, 18].forEach((m) => {
      const x = 40 + (m / 18) * (W - 60);
      ctx.fillText(`M${m}`, x, H - 14);
    });
  }, []);

  return (
    <div>
      <canvas ref={canvasRef} width={860} height={120} className="w-full" />
      <p className="text-[11px] text-muted-foreground mt-1">
        Adoption reaches 100% at month 18 · Primary sensitivity driver
      </p>
    </div>
  );
}

// ── Left Panel ─────────────────────────────────────────────────────────────────

function LeftPanel() {
  return (
    <StudioPanel title="Value Chains (from Mapping)">
      <div className="flex flex-col gap-3">
        {VALUE_CHAINS.map((c) => (
          <div key={c.id} className="pb-3 border-b border-border last:border-0">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[12px] font-medium text-foreground">{c.name}</span>
              <span className="text-[12px] font-semibold text-foreground">{c.value}</span>
            </div>
            <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden mb-1">
              <div
                className={cn("h-full rounded-full", c.complete ? "bg-foreground" : "bg-muted-foreground/40")}
                style={{ width: `${c.pct}%` }}
              />
            </div>
            {c.note && (
              <p className="text-[10px] text-yellow-600 font-medium">{c.note}</p>
            )}
          </div>
        ))}
      </div>
    </StudioPanel>
  );
}

// ── Center Panel ───────────────────────────────────────────────────────────────

function CenterPanel() {
  const [activeScenario, setActiveScenario] = useState<"conservative" | "expected" | "optimistic">("expected");
  const [activeCurve, setActiveCurve] = useState<"s-curve" | "linear" | "step">("s-curve");

  return (
    <>
      {/* Year-by-year projection */}
      <StudioPanel title="Year-by-Year Projection">
        <DataTable
          columns={["", "Year 1", "Year 2", "Year 3"]}
          rows={PROJECTION.map((row) => [
            <span className={cn("text-muted-foreground text-[12px]", row.bold && "font-bold text-foreground")}>{row.label}</span>,
            <div className={cn("text-right", row.bold && "font-bold")}>{row.y1}</div>,
            <div className={cn("text-right", row.bold && "font-bold")}>{row.y2}</div>,
            <div className={cn("text-right", row.bold && "font-bold")}>{row.y3}</div>,
          ])}
        />
      </StudioPanel>

      {/* Key Metrics */}
      <StudioPanel title="Key Metrics">
        <div className="grid grid-cols-4 gap-3 mb-3">
          {KEY_METRICS.map((m) => (
            <div key={m.label} className="border border-border rounded-md p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">{m.label}</p>
              <p className="text-[20px] font-bold text-foreground">{m.value}</p>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {(["conservative", "expected", "optimistic"] as const).map((s) => (
            <Btn
              key={s}
              variant={activeScenario === s ? "primary" : "outline"}
              onClick={() => setActiveScenario(s)}
              className="h-6 px-3 text-[10px] rounded-full capitalize"
            >
              {s === "expected" ? `Expected: 412%` : s === "conservative" ? "Conservative: 289%" : "Optimistic: 535%"}
            </Btn>
          ))}
        </div>
      </StudioPanel>

      {/* Ramp & Adoption Profile */}
      <StudioPanel title="Ramp & Adoption Profile">
        <div className="flex items-center gap-2 mb-3">
          {(["s-curve", "linear", "step"] as const).map((c) => (
            <Btn
              key={c}
              variant={activeCurve === c ? "primary" : "outline"}
              onClick={() => setActiveCurve(c)}
              className="h-6 px-3 text-[10px] rounded-full capitalize"
            >
              {c === "s-curve" ? "S-curve" : c === "step" ? "Step function" : "Linear"}
            </Btn>
          ))}
          <span className="ml-auto text-[11px] text-muted-foreground">3-month ramp lag</span>
        </div>
        <SCurveChart />
      </StudioPanel>

      {/* Scenario Comparison */}
      <StudioPanel title="Scenario Comparison">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2 pr-4 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground w-32" />
              {["Conservative", "Expected", "Optimistic"].map((h) => (
                <th key={h} className={cn("text-right py-2 pr-4 text-[10px] font-semibold uppercase tracking-wider", h === "Expected" ? "text-foreground" : "text-muted-foreground")}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SCENARIOS.map((row) => (
              <tr key={row.label} className="border-b border-border last:border-0">
                <td className="py-2.5 pr-4 text-muted-foreground">{row.label}</td>
                <td className="py-2.5 pr-4 text-right text-muted-foreground">{row.conservative}</td>
                <td className="py-2.5 pr-4 text-right font-bold text-foreground">{row.expected}</td>
                <td className="py-2.5 text-right text-muted-foreground">{row.optimistic}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </StudioPanel>
    </>
  );
}

// ── Right Panel ────────────────────────────────────────────────────────────────

function RightPanel() {
  return (
    <StudioPanel
      title="Assumption Registry"
      action={
        <Btn variant="ghost" className="h-6 px-2 text-primary hover:underline">
          <Plus size={11} /> Add
        </Btn>
      }
    >
      <p className="text-[11px] text-muted-foreground mb-3">12 assumptions · Confidence breakdown:</p>
      <div className="flex flex-col gap-3">
        {ASSUMPTIONS.map((group) => (
          <div key={group.confidence}>
            <span className={cn("inline-flex items-center h-5 px-2 text-[10px] font-bold rounded border mb-2", group.color)}>
              {group.label}
            </span>
            <div className="flex flex-col gap-1">
              {group.items.map((item) => (
                <div
                  key={item}
                  className={cn("px-2 py-1.5 text-[11px] rounded border", group.color)}
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <Btn variant="outline" className="mt-4 w-full gap-2 h-8">
        <Phone size={11} /> Schedule Validation Call
      </Btn>
    </StudioPanel>
  );
}

// ── Status Bar ─────────────────────────────────────────────────────────────────

function StatusBar() {
  return (
    <>
      <span className="h-6 px-2.5 bg-primary/10 text-primary text-[11px] font-semibold rounded flex items-center">3-Year ROI: 412%</span>
      <span>Payback: 8 months</span>
      <span>NPV: $1.67M</span>
      <span className="text-yellow-600 font-medium">3 low-confidence assumptions</span>
    </>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function Stage3Modeling() {
  return (
    <ValueStudioShell
      stageId={3}
      title="Modeling"
      subtitle="Quantify business impact with financial rigor — baselines, projections, and scenario analysis"
      deal={DEMO_DEAL}
      stages={buildStages(3)}
      prevLabel="Mapping"
      prevPath="/model/value-studio/mapping"
      nextLabel="Continue to Validation"
      nextPath="/model/value-studio/validation"
      leftPanel={<LeftPanel />}
      centerPanel={<CenterPanel />}
      rightPanel={<RightPanel />}
      statusBar={<StatusBar />}
    />
  );
}
