/**
 * useHarness — TanStack Query hooks for the Fabric Harness API.
 *
 * Covers: runs, checkpoints, gates, validation, and health.
 * Polling is enabled for non-terminal runs (5 s interval, matching workflows).
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type ClaimToValidate,
  type CreateRunRequest,
  type GateDecision,
  type GateType,
  type HarnessRunStatus,
  type HarnessState,
  type HarnessWorkflowType,
  type TransitionRequest,
  harnessApi,
  isTerminalState,
} from "@/api/harness";
import { QK } from "./queryKeys";
import { STALE_TIME } from "./useApiShared";
import { POLL_INTERVALS } from "./usePolling";

// ── Runs ──────────────────────────────────────────────────────────────────────

export function useHarnessRuns(params?: {
  status?: HarnessRunStatus;
  workflow_type?: HarnessWorkflowType;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: QK.harness.runs(params ?? {}),
    queryFn: () => harnessApi.listRuns(params),
    staleTime: STALE_TIME.list,
  });
}

export function useHarnessRun(runId: string | undefined) {
  return useQuery({
    queryKey: QK.harness.run(runId ?? ""),
    queryFn: () => harnessApi.getRun(runId!),
    enabled: !!runId,
    staleTime: STALE_TIME.detail,
    // Poll while the run is in a non-terminal state
    refetchInterval: (query) => {
      const run = query.state.data;
      if (!run) return false;
      return isTerminalState(run.current_state) ? false : POLL_INTERVALS.workflows;
    },
  });
}

// ── Checkpoints ───────────────────────────────────────────────────────────────

export function useHarnessCheckpoints(runId: string | undefined) {
  return useQuery({
    queryKey: QK.harness.checkpoints(runId ?? ""),
    queryFn: () => harnessApi.listCheckpoints(runId!),
    enabled: !!runId,
    staleTime: STALE_TIME.detail,
  });
}

// ── Gates ─────────────────────────────────────────────────────────────────────

export function useHarnessGates(runId: string | undefined) {
  return useQuery({
    queryKey: QK.harness.gates(runId ?? ""),
    queryFn: () => harnessApi.listGates(runId!),
    enabled: !!runId,
    staleTime: STALE_TIME.approvals,
    // Poll while there are pending gates
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      const hasPending = data.items.some((g) => g.status === "pending");
      return hasPending ? POLL_INTERVALS.workflows : false;
    },
  });
}

// ── Health ────────────────────────────────────────────────────────────────────

export function useHarnessHealth() {
  return useQuery({
    queryKey: QK.harness.health(),
    queryFn: () => harnessApi.health(),
    staleTime: STALE_TIME.stats,
    retry: false,
  });
}

// ── Mutations ─────────────────────────────────────────────────────────────────

export function useCreateHarnessRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateRunRequest) => harnessApi.createRun(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK.harness.all });
    },
  });
}

export function useTransitionHarnessRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ runId, data }: { runId: string; data: TransitionRequest }) =>
      harnessApi.transitionRun(runId, data),
    onSuccess: (result) => {
      qc.setQueryData(QK.harness.run(result.run.id), result.run);
      qc.invalidateQueries({ queryKey: QK.harness.runs({}) });
    },
  });
}

export function useCancelHarnessRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (runId: string) => harnessApi.cancelRun(runId),
    onSuccess: (_data, runId) => {
      qc.invalidateQueries({ queryKey: QK.harness.run(runId) });
      qc.invalidateQueries({ queryKey: QK.harness.runs({}) });
    },
  });
}

export function useDecideGate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      gateId,
      runId,
      decision,
      reason,
    }: {
      gateId: string;
      runId: string;
      decision: GateDecision;
      reason?: string;
    }) => harnessApi.decideGate(gateId, { decision, decision_reason: reason }),
    onSuccess: (_data, { runId }) => {
      qc.invalidateQueries({ queryKey: QK.harness.gates(runId) });
      qc.invalidateQueries({ queryKey: QK.harness.run(runId) });
    },
  });
}

export function useCreateHarnessGate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ runId, gate_type }: { runId: string; gate_type: GateType }) =>
      harnessApi.createGate(runId, { gate_type }),
    onSuccess: (_data, { runId }) => {
      qc.invalidateQueries({ queryKey: QK.harness.gates(runId) });
    },
  });
}

export function useValidateHarnessClaims() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ runId, claims }: { runId: string; claims: ClaimToValidate[] }) =>
      harnessApi.validateClaims(runId, { claims }),
    onSuccess: (_data, { runId }) => {
      qc.invalidateQueries({ queryKey: QK.harness.run(runId) });
    },
  });
}
