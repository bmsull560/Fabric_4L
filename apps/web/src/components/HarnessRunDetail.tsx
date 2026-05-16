/**
 * HarnessRunDetail — Drill-down sheet for a single HarnessRun.
 *
 * Shows: run metadata, state machine progress, checkpoints,
 * human gates (with approve/reject actions), and validation outcomes.
 */

import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock,
  Loader2,
  ShieldCheck,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import type { HarnessRun, HumanGate, ValidationState } from "@/api/harness";
import { TERMINAL_STATES, isTerminalState } from "@/api/harness";
import {
  useDecideGate,
  useHarnessCheckpoints,
  useHarnessGates,
  useHarnessRun,
  useTransitionHarnessRun,
} from "@/hooks/useHarness";

// ── Constants ─────────────────────────────────────────────────────────────────

const STATE_ORDER = [
  "INIT",
  "RESOLVE_CONTEXT",
  "LOAD_VALUE_PACK",
  "RETRIEVE_KNOWLEDGE",
  "GENERATE_HYPOTHESES",
  "MATCH_EVIDENCE",
  "QUANTIFY_IMPACT",
  "VALIDATE_CLAIMS",
  "HUMAN_REVIEW",
  "PUBLISH_OUTPUT",
  "DONE",
] as const;

// ── Helpers ───────────────────────────────────────────────────────────────────

function statusColor(status: string): string {
  switch (status) {
    case "completed": return "bg-emerald-500/15 text-emerald-700 border-emerald-200";
    case "running":   return "bg-blue-500/15 text-blue-700 border-blue-200";
    case "failed":    return "bg-red-500/15 text-red-700 border-red-200";
    case "cancelled": return "bg-slate-400/15 text-slate-600 border-slate-200";
    case "waiting_for_human": return "bg-amber-500/15 text-amber-700 border-amber-200";
    default:          return "bg-slate-100 text-slate-600 border-slate-200";
  }
}

function gateStatusColor(status: string): string {
  switch (status) {
    case "approved": return "bg-emerald-500/15 text-emerald-700";
    case "rejected": return "bg-red-500/15 text-red-700";
    case "expired":  return "bg-slate-400/15 text-slate-500";
    case "modified": return "bg-blue-500/15 text-blue-700";
    default:         return "bg-amber-500/15 text-amber-700"; // pending
  }
}

function validationStateColor(state: ValidationState): string {
  switch (state) {
    case "passed":               return "text-emerald-600";
    case "failed":               return "text-red-600";
    case "needs_review":         return "text-amber-600";
    case "insufficient_evidence": return "text-slate-500";
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StateProgress({ currentState, status }: { currentState: string; status: string }) {
  const currentIdx = STATE_ORDER.indexOf(currentState as typeof STATE_ORDER[number]);
  const isFailed = status === "failed" || status === "cancelled";

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {STATE_ORDER.map((state, idx) => {
        const done = idx < currentIdx;
        const active = idx === currentIdx && !isFailed;
        const failed = idx === currentIdx && isFailed;
        return (
          <div key={state} className="flex items-center gap-1">
            <div
              className={cn(
                "h-2 w-2 rounded-full",
                done   && "bg-emerald-500",
                active && "bg-blue-500 animate-pulse",
                failed && "bg-red-500",
                !done && !active && !failed && "bg-slate-200",
              )}
              title={state}
            />
            {idx < STATE_ORDER.length - 1 && (
              <div className={cn("h-px w-3", done ? "bg-emerald-300" : "bg-slate-200")} />
            )}
          </div>
        );
      })}
      <span className="ml-2 text-xs text-muted-foreground font-mono">{currentState}</span>
    </div>
  );
}

function GateRow({ gate, runId }: { gate: HumanGate; runId: string }) {
  const decide = useDecideGate();
  const isPending = gate.status === "pending";

  return (
    <div className="flex items-start justify-between gap-3 py-2">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate">{gate.gate_type.replace(/_/g, " ")}</span>
          <Badge variant="outline" className={cn("text-xs", gateStatusColor(gate.status))}>
            {gate.status}
          </Badge>
        </div>
        {gate.decision_reason && (
          <p className="text-xs text-muted-foreground mt-0.5 truncate">{gate.decision_reason}</p>
        )}
        {gate.decision_by && (
          <p className="text-xs text-muted-foreground">by {gate.decision_by}</p>
        )}
        <p className="text-xs text-muted-foreground">{formatDate(gate.created_at)}</p>
      </div>
      {isPending && (
        <div className="flex gap-1.5 shrink-0">
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs text-emerald-700 border-emerald-200 hover:bg-emerald-50"
            disabled={decide.isPending}
            onClick={() => decide.mutate({ gateId: gate.id, runId, decision: "approved" })}
          >
            {decide.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : "Approve"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs text-red-700 border-red-200 hover:bg-red-50"
            disabled={decide.isPending}
            onClick={() => decide.mutate({ gateId: gate.id, runId, decision: "rejected" })}
          >
            Reject
          </Button>
        </div>
      )}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

interface HarnessRunDetailProps {
  runId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export function HarnessRunDetail({ runId, isOpen, onClose }: HarnessRunDetailProps) {
  const { data: run, isLoading: runLoading } = useHarnessRun(runId ?? undefined);
  const { data: checkpointsData } = useHarnessCheckpoints(runId ?? undefined);
  const { data: gatesData } = useHarnessGates(runId ?? undefined);
  const transition = useTransitionHarnessRun();

  const checkpoints = checkpointsData?.items ?? [];
  const gates = gatesData?.items ?? [];
  const pendingGates = gates.filter((g) => g.status === "pending");

  function handleResume() {
    if (!run) return;
    const nextIdx = STATE_ORDER.indexOf(run.current_state as typeof STATE_ORDER[number]) + 1;
    const nextState = STATE_ORDER[nextIdx];
    if (nextState) {
      transition.mutate({ runId: run.id, data: { to_state: nextState } });
    }
  }

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full sm:max-w-xl flex flex-col gap-0 p-0">
        <SheetHeader className="px-6 pt-6 pb-4 border-b">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <SheetTitle className="text-base font-semibold truncate">
                {run?.workflow_type?.replace(/_/g, " ") ?? "Harness Run"}
              </SheetTitle>
              {run && (
                <p className="text-xs text-muted-foreground font-mono mt-0.5 truncate">
                  {run.id}
                </p>
              )}
            </div>
            <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </SheetHeader>

        {runLoading && (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {run && (
          <ScrollArea className="flex-1">
            <div className="px-6 py-4 space-y-5">

              {/* Status + state progress */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Badge variant="outline" className={cn("text-xs", statusColor(run.status))}>
                    {run.status.replace(/_/g, " ")}
                  </Badge>
                  {run.account_id && (
                    <span className="text-xs text-muted-foreground">Account: {run.account_id}</span>
                  )}
                </div>
                <StateProgress currentState={run.current_state} status={run.status} />
              </section>

              <Separator />

              {/* Metadata */}
              <section>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                  Details
                </h3>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
                  <dt className="text-muted-foreground">Initiated by</dt>
                  <dd className="font-medium">{run.initiated_by}</dd>
                  <dt className="text-muted-foreground">Trace ID</dt>
                  <dd className="font-mono text-xs truncate">{run.trace_id}</dd>
                  <dt className="text-muted-foreground">Created</dt>
                  <dd>{formatDate(run.created_at)}</dd>
                  <dt className="text-muted-foreground">Updated</dt>
                  <dd>{formatDate(run.updated_at)}</dd>
                  {run.value_pack_id && (
                    <>
                      <dt className="text-muted-foreground">Value pack</dt>
                      <dd className="font-mono text-xs">{run.value_pack_id}</dd>
                    </>
                  )}
                </dl>
              </section>

              {/* Control actions */}
              {!isTerminalState(run.current_state) && (
                <>
                  <Separator />
                  <section>
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                      Actions
                    </h3>
                    <div className="flex gap-2">
                      {run.status === "failed" && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={transition.isPending}
                          onClick={() =>
                            transition.mutate({
                              runId: run.id,
                              data: { to_state: run.current_state, human_override: true },
                            })
                          }
                        >
                          {transition.isPending ? (
                            <Loader2 className="h-3 w-3 animate-spin mr-1" />
                          ) : null}
                          Retry
                        </Button>
                      )}
                      {run.status === "running" && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={transition.isPending}
                          onClick={handleResume}
                        >
                          Resume
                        </Button>
                      )}
                    </div>
                  </section>
                </>
              )}

              {/* Human gates */}
              {gates.length > 0 && (
                <>
                  <Separator />
                  <section>
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      Human Gates
                      {pendingGates.length > 0 && (
                        <Badge className="ml-1 h-4 px-1.5 text-[10px] bg-amber-500">
                          {pendingGates.length} pending
                        </Badge>
                      )}
                    </h3>
                    <div className="divide-y">
                      {gates.map((gate) => (
                        <GateRow key={gate.id} gate={gate} runId={run.id} />
                      ))}
                    </div>
                  </section>
                </>
              )}

              {/* Checkpoints */}
              {checkpoints.length > 0 && (
                <>
                  <Separator />
                  <section>
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5" />
                      Checkpoints ({checkpoints.length})
                    </h3>
                    <div className="space-y-1.5">
                      {checkpoints.map((chk) => (
                        <div
                          key={chk.id}
                          className="flex items-center justify-between text-sm py-1"
                        >
                          <div className="flex items-center gap-2">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                            <span className="font-mono text-xs">{chk.state_name}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(chk.created_at)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </section>
                </>
              )}

            </div>
          </ScrollArea>
        )}
      </SheetContent>
    </Sheet>
  );
}
