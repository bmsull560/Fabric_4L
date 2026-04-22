/**
 * Intelligence → Drivers Tab
 *
 * Root cause analysis connecting validated signals to underlying factors.
 * Shows the "why" behind each pain signal — what's driving the problem.
 *
 * Migrated from: Stage2Mapping (value driver mapping) + WorkflowDriverTree
 */
import { useState } from "react";
import { useParams } from "wouter";
import { GitBranch, ChevronRight } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentStream } from "@/hooks/useAgentStream";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

// ── Demo Data ─────────────────────────────────────────────────────────────────

const DEMO_ACCOUNT = {
  accountName: "Meridian Automotive Components",
  industry: "Manufacturing",
  revenue: "$4.2B",
};

interface Driver {
  id: string;
  name: string;
  contribution: number;
  parentSignal: string;
  subDrivers: string[];
}

const DEMO_DRIVERS: Driver[] = [
  { id: "d1", name: "Aging Equipment",        contribution: 45, parentSignal: "Production Downtime",    subDrivers: ["Manual weld stations (15+ yrs)", "No predictive maintenance"] },
  { id: "d2", name: "Changeover Delays",      contribution: 30, parentSignal: "Production Downtime",    subDrivers: ["Manual tooling swaps", "No standardized procedures"] },
  { id: "d3", name: "Material Shortages",     contribution: 25, parentSignal: "Production Downtime",    subDrivers: ["Single-source suppliers", "No buffer inventory"] },
  { id: "d4", name: "Skilled Labor Gap",       contribution: 60, parentSignal: "Labor Shortage — Welders", subDrivers: ["18% turnover rate", "340 unfilled positions"] },
  { id: "d5", name: "Training Bottleneck",    contribution: 40, parentSignal: "Labor Shortage — Welders", subDrivers: ["12-week onboarding cycle", "No simulation-based training"] },
  { id: "d6", name: "Torque Inconsistency",   contribution: 55, parentSignal: "Quality Defect Rate",    subDrivers: ["Manual torque application", "Operator fatigue variance"] },
  { id: "d7", name: "Inspection Gaps",        contribution: 45, parentSignal: "Quality Defect Rate",    subDrivers: ["End-of-line only", "No inline vision systems"] },
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function DriversTab() {
  const params = useParams<{ accountId: string }>();
  const [selectedDriver, setSelectedDriver] = useState<Driver | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("detail");
  const { messages, sendMessage, suggestedActions } = useAgentStream({
    activeTab: "drivers",
    accountName: DEMO_ACCOUNT.accountName,
  });

  // Group drivers by parent signal
  const grouped = DEMO_DRIVERS.reduce<Record<string, Driver[]>>((acc, d) => {
    (acc[d.parentSignal] ??= []).push(d);
    return acc;
  }, {});

  const detailContent = selectedDriver ? (
    <div className="space-y-4">
      <div>
        <h3 className="text-[14px] font-bold text-foreground mb-1">{selectedDriver.name}</h3>
        <span className="text-[11px] text-muted-foreground">
          Root driver for: {selectedDriver.parentSignal}
        </span>
      </div>

      <div className="p-3 bg-muted/50 rounded-md">
        <div className="text-[10px] text-muted-foreground uppercase mb-1">Contribution</div>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full"
              style={{ width: `${selectedDriver.contribution}%` }}
            />
          </div>
          <span className="text-[14px] font-bold text-foreground">{selectedDriver.contribution}%</span>
        </div>
      </div>

      <div>
        <h4 className="text-[12px] font-semibold text-foreground mb-2">Sub-Drivers</h4>
        <div className="space-y-1.5">
          {selectedDriver.subDrivers.map((sd, i) => (
            <div key={i} className="flex items-center gap-2 text-[11px] text-muted-foreground">
              <ChevronRight size={10} className="shrink-0" />
              {sd}
            </div>
          ))}
        </div>
      </div>

      <div>
        <h4 className="text-[12px] font-semibold text-foreground mb-1">Implication</h4>
        <p className="text-[11px] text-muted-foreground leading-relaxed">
          This driver accounts for {selectedDriver.contribution}% of the "{selectedDriver.parentSignal}" signal.
          Addressing it directly with a targeted product capability would reduce the overall signal impact proportionally.
        </p>
      </div>
    </div>
  ) : null;

  const rightRail = (
    <RightRail
      mode={railMode}
      onModeChange={setRailMode}
      detailContent={detailContent}
      activeTab="drivers"
      messages={messages}
      onSendMessage={sendMessage}
      suggestedActions={suggestedActions}
    />
  );

  return (
    <IntelligenceShell account={DEMO_ACCOUNT} rightRail={rightRail}>
      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard label="Root Drivers" value={String(DEMO_DRIVERS.length)} trend="Across 3 signals" />
        <MetricCard label="Top Contributor" value="Skilled Labor Gap" trend="60% of Labor Shortage" />
        <MetricCard label="Signals Analyzed" value="3" trend="Of 6 detected" />
      </div>

      {/* Driver groups by signal */}
      {Object.entries(grouped).map(([signal, drivers]) => (
        <SectionCard key={signal} title={signal} className="mb-4">
          <div className="space-y-1">
            {drivers.map((driver) => (
              <button
                key={driver.id}
                onClick={() => { setSelectedDriver(driver); setRailMode("detail"); }}
                className={cn(
                  "flex items-center gap-4 w-full px-3 py-3 rounded-md text-left transition-colors",
                  selectedDriver?.id === driver.id ? "bg-primary/5" : "hover:bg-muted/50"
                )}
              >
                <GitBranch size={14} className="text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] font-medium text-foreground">{driver.name}</div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">
                    {driver.subDrivers.join(" · ")}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${driver.contribution}%` }}
                    />
                  </div>
                  <span className="text-[11px] font-semibold text-foreground w-8 text-right">
                    {driver.contribution}%
                  </span>
                </div>
                <ChevronRight size={12} className="text-muted-foreground shrink-0" />
              </button>
            ))}
          </div>
        </SectionCard>
      ))}
    </IntelligenceShell>
  );
}
