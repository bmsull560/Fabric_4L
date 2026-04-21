/**
 * Value Studio — Shared Shell
 *
 * Provides:
 *  - Persistent deal context header (account / deal type / ARR / CRM stage)
 *  - Stage progress bar with completion state per stage
 *  - Three-panel layout: left context (260px) | center workspace (flex) | right panel (240px)
 *  - Stage navigation (prev / next) with primary CTA button
 *  - extraActions slot for stage-specific secondary buttons
 */
import { Link, useLocation } from "wouter";
import { CheckCircle2, Building2, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { SectionCard, Btn } from "@/components/WfPrimitives";

// ── Types ─────────────────────────────────────────────────────────────────────

export type StageId = 1 | 2 | 3 | 4 | 5 | 6;

export interface StageStatus {
  id: StageId;
  label: string;
  path: string;
  status: "complete" | "active" | "pending";
}

export interface DealContext {
  accountName: string;
  dealType: string;
  arr: string;
  crmStage: string;
}

interface ValueStudioShellProps {
  stageId: StageId;
  title: string;
  subtitle: string;
  deal: DealContext;
  stages: StageStatus[];
  prevLabel?: string;
  prevPath?: string;
  nextLabel?: string;
  nextPath?: string;
  onNextClick?: () => void;
  secondaryAction?: { label: string; onClick: () => void };
  /** Additional action buttons rendered between secondaryAction and the primary next button */
  extraActions?: React.ReactNode;
  leftPanel: React.ReactNode;
  centerPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  statusBar?: React.ReactNode;
}

// ── Stage Progress Bar ─────────────────────────────────────────────────────────

function StageProgressBar({ stages }: { stages: StageStatus[] }) {
  return (
    <div className="flex items-center gap-0 px-6 py-2 border-b border-border bg-background">
      {stages.map((stage, i) => (
        <div key={stage.id} className="flex items-center">
          <Link href={stage.path}>
            <div
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-medium cursor-pointer transition-colors",
                stage.status === "active" && "bg-primary/10 text-primary",
                stage.status === "complete" && "text-foreground hover:bg-muted",
                stage.status === "pending" && "text-muted-foreground hover:bg-muted"
              )}
            >
              {stage.status === "complete" ? (
                <CheckCircle2 size={13} className="text-green-500 shrink-0" />
              ) : (
                <span
                  className={cn(
                    "w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0",
                    stage.status === "active"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {stage.id}
                </span>
              )}
              <span>{stage.label}</span>
            </div>
          </Link>
          {i < stages.length - 1 && (
            <ChevronRight size={12} className="text-muted-foreground mx-0.5 shrink-0" />
          )}
        </div>
      ))}
    </div>
  );
}

// ── Deal Context Header ────────────────────────────────────────────────────────

function DealContextHeader({ deal }: { deal: DealContext }) {
  return (
    <div className="h-9 bg-muted/50 border-b border-border flex items-center px-6 gap-3 text-[12px] shrink-0">
      <Building2 size={13} className="text-muted-foreground shrink-0" />
      <span className="font-semibold text-foreground">{deal.accountName}</span>
      <ChevronRight size={11} className="text-muted-foreground/50" />
      <span className="text-muted-foreground">{deal.dealType}</span>
      <ChevronRight size={11} className="text-muted-foreground/50" />
      <span className="text-muted-foreground">{deal.arr}</span>
      <div className="flex-1" />
      <span className="text-muted-foreground text-[11px]">⊙ {deal.crmStage}</span>
    </div>
  );
}

// ── Shell ──────────────────────────────────────────────────────────────────────

export default function ValueStudioShell({
  stageId,
  title,
  subtitle,
  deal,
  stages,
  prevLabel,
  prevPath,
  nextLabel,
  nextPath,
  onNextClick,
  secondaryAction,
  extraActions,
  leftPanel,
  centerPanel,
  rightPanel,
  statusBar,
}: ValueStudioShellProps) {
  const [, navigate] = useLocation();

  const handleNext = () => {
    if (onNextClick) onNextClick();
    if (nextPath) navigate(nextPath);
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Deal context header */}
      <DealContextHeader deal={deal} />

      {/* Stage progress bar */}
      <StageProgressBar stages={stages} />

      {/* Stage title row */}
      <div className="flex items-start justify-between px-6 pt-4 pb-3 shrink-0">
        <div>
          <h1 className="text-[18px] font-bold text-foreground leading-tight">
            Stage {stageId}: {title}
          </h1>
          <p className="text-[12px] text-muted-foreground mt-0.5">{subtitle}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {prevLabel && prevPath && (
            <Link href={prevPath}>
              <Btn variant="outline">
                ← {prevLabel}
              </Btn>
            </Link>
          )}
          {secondaryAction && (
            <Btn variant="outline" onClick={secondaryAction.onClick}>
              {secondaryAction.label}
            </Btn>
          )}
          {extraActions}
          {nextLabel && (
            <Btn variant="primary" onClick={handleNext}>
              {nextLabel} →
            </Btn>
          )}
        </div>
      </div>

      {/* Three-panel body */}
      <div className="flex flex-1 min-h-0 gap-0 px-6 pb-4">
        {/* Left panel */}
        <div className="w-[260px] shrink-0 flex flex-col gap-3 mr-4">
          {leftPanel}
        </div>

        {/* Center panel */}
        <div className="flex-1 min-w-0 flex flex-col gap-3 overflow-y-auto pr-4">
          {centerPanel}
        </div>

        {/* Right panel */}
        <div className="w-[240px] shrink-0 flex flex-col gap-3">
          {rightPanel}
        </div>
      </div>

      {/* Status bar */}
      {statusBar && (
        <div className="h-10 shrink-0 border-t border-border bg-background flex items-center px-6 gap-4 text-[11px] text-muted-foreground">
          {statusBar}
        </div>
      )}
    </div>
  );
}

// ── Shared panel card ──────────────────────────────────────────────────────────

export function StudioPanel({
  title,
  subtitle,
  children,
  className,
  action,
}: {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}) {
  return (
    <SectionCard
      title={title}
      className={cn("flex flex-col", className)}
    >
      {subtitle && (
        <p className="text-[10px] text-muted-foreground -mt-2 mb-3">{subtitle}</p>
      )}
      {action && (
        <div className="absolute top-2.5 right-4">
          {action}
        </div>
      )}
      {children}
    </SectionCard>
  );
}

// ── Shared stage config ────────────────────────────────────────────────────────

export const DEMO_DEAL: DealContext = {
  accountName: "Acme Corp",
  dealType: "Enterprise Deal",
  arr: "$280K ARR",
  crmStage: "Stage 3 — Proposal",
};

export function buildStages(activeId: StageId): StageStatus[] {
  const defs: { id: StageId; label: string; path: string }[] = [
    { id: 1, label: "Discovery",  path: "/model/value-studio/discovery" },
    { id: 2, label: "Mapping",    path: "/model/value-studio/mapping" },
    { id: 3, label: "Modeling",   path: "/model/value-studio/modeling" },
    { id: 4, label: "Validation", path: "/model/value-studio/validation" },
    { id: 5, label: "Narrative",  path: "/model/value-studio/narrative" },
    { id: 6, label: "Tracking",   path: "/model/value-studio/tracking" },
  ];
  return defs.map((d) => ({
    ...d,
    status: d.id < activeId ? "complete" : d.id === activeId ? "active" : "pending",
  }));
}
