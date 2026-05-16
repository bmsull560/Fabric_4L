/**
 * Harness Fixture Data
 *
 * Typed factory functions and canned fixture sets for Harness UI E2E tests.
 * Shapes are derived from services/layer4-agents/src/harness/models.py.
 *
 * API prefix: /api/v1/agents/harness/*  (Layer 4, /agents prefix)
 */

// ── Domain types (mirrors Python models) ────────────────────────────────────

export type HarnessRunStatus =
  | 'queued'
  | 'running'
  | 'waiting_for_human'
  | 'failed'
  | 'completed'
  | 'cancelled';

export type HarnessState =
  | 'INIT'
  | 'RESOLVE_CONTEXT'
  | 'LOAD_VALUE_PACK'
  | 'RETRIEVE_KNOWLEDGE'
  | 'GENERATE_HYPOTHESES'
  | 'MATCH_EVIDENCE'
  | 'QUANTIFY_IMPACT'
  | 'VALIDATE_CLAIMS'
  | 'HUMAN_REVIEW'
  | 'PUBLISH_OUTPUT'
  | 'DONE'
  | 'FAILED'
  | 'CANCELLED';

export type HarnessWorkflowType =
  | 'signal_extraction'
  | 'account_intelligence'
  | 'value_model_generation'
  | 'evidence_matching'
  | 'value_tree_generation'
  | 'roi_calculator_generation'
  | 'business_case_generation'
  | 'renewal_risk_analysis'
  | 'expansion_opportunity_analysis';

export type GateStatus = 'pending' | 'approved' | 'rejected' | 'modified' | 'expired';
export type GateType =
  | 'approve_claims'
  | 'approve_assumptions'
  | 'approve_customer_output'
  | 'resolve_conflict';

export type ValidationState = 'passed' | 'failed' | 'needs_review' | 'insufficient_evidence';

export interface HarnessRun {
  id: string;
  tenant_id: string;
  account_id: string | null;
  workflow_type: HarnessWorkflowType;
  initiated_by: 'user' | 'system' | 'agent' | 'scheduled_job';
  status: HarnessRunStatus;
  current_state: HarnessState;
  value_pack_id: string | null;
  trace_id: string;
  created_at: string;
  updated_at: string;
}

export interface HarnessCheckpoint {
  id: string;
  run_id: string;
  tenant_id: string;
  state_name: HarnessState;
  state_payload: Record<string, unknown>;
  input_hash: string;
  output_hash: string | null;
  tool_calls: unknown[];
  created_at: string;
}

export interface HumanGate {
  id: string;
  run_id: string;
  tenant_id: string;
  gate_type: GateType;
  status: GateStatus;
  decision_by: string | null;
  decision_reason: string | null;
  created_at: string;
  decided_at: string | null;
}

export interface ClaimValidationResult {
  id: string;
  tenant_id: string;
  claim_id: string;
  validation_state: ValidationState;
  evidence_refs: string[];
  confidence: number;
  trust_score: number;
  validator: 'agent' | 'human' | 'policy' | 'benchmark' | 'unavailable';
  reason: string;
  created_at: string;
}

export interface PaginatedHarnessRuns {
  items: HarnessRun[];
  total: number;
  has_more: boolean;
}

// ── Terminal state set ───────────────────────────────────────────────────────

export const TERMINAL_STATUSES: HarnessRunStatus[] = ['completed', 'failed', 'cancelled'];
export const TERMINAL_STATES: HarnessState[] = ['DONE', 'FAILED', 'CANCELLED'];

export function isTerminalStatus(status: HarnessRunStatus): boolean {
  return TERMINAL_STATUSES.includes(status);
}

// ── Factory functions ────────────────────────────────────────────────────────

export function makeHarnessRun(overrides: Partial<HarnessRun> = {}): HarnessRun {
  return {
    id: 'run_abc123def456',
    tenant_id: 'tenant-e2e-001',
    account_id: 'acct-meridian-001',
    workflow_type: 'business_case_generation',
    initiated_by: 'user',
    status: 'running',
    current_state: 'VALIDATE_CLAIMS',
    value_pack_id: null,
    trace_id: 'trace_xyz789abc',
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:05:00Z',
    ...overrides,
  };
}

export function makeHarnessCheckpoint(overrides: Partial<HarnessCheckpoint> = {}): HarnessCheckpoint {
  return {
    id: 'chk_001',
    run_id: 'run_abc123def456',
    tenant_id: 'tenant-e2e-001',
    state_name: 'GENERATE_HYPOTHESES',
    state_payload: { hypotheses_count: 4 },
    input_hash: 'abc123def456789012345678901234567890abcd',
    output_hash: '789xyz012abc345def678901234567890abcdef1',
    tool_calls: [],
    created_at: '2025-01-15T10:02:00Z',
    ...overrides,
  };
}

export function makeHumanGate(overrides: Partial<HumanGate> = {}): HumanGate {
  return {
    id: 'gate_001',
    run_id: 'run_abc123def456',
    tenant_id: 'tenant-e2e-001',
    gate_type: 'approve_claims',
    status: 'pending',
    decision_by: null,
    decision_reason: null,
    created_at: '2025-01-15T10:04:00Z',
    decided_at: null,
    ...overrides,
  };
}

export function makeClaimValidationResult(
  overrides: Partial<ClaimValidationResult> = {},
): ClaimValidationResult {
  return {
    id: 'cvr_001',
    tenant_id: 'tenant-e2e-001',
    claim_id: 'claim_001',
    validation_state: 'needs_review',
    evidence_refs: ['ev_001'],
    confidence: 0.72,
    trust_score: 0.68,
    validator: 'agent',
    reason: 'Confidence below threshold',
    created_at: '2025-01-15T10:03:00Z',
    ...overrides,
  };
}

// ── Canned fixture sets ──────────────────────────────────────────────────────

/** A single running (non-terminal) harness run */
export const RUNNING_RUN = makeHarnessRun({
  id: 'run_running_001',
  status: 'running',
  current_state: 'VALIDATE_CLAIMS',
});

/** A completed (terminal) harness run */
export const COMPLETED_RUN = makeHarnessRun({
  id: 'run_completed_001',
  status: 'completed',
  current_state: 'DONE',
  updated_at: '2025-01-15T10:30:00Z',
});

/** A failed (terminal) harness run */
export const FAILED_RUN = makeHarnessRun({
  id: 'run_failed_001',
  status: 'failed',
  current_state: 'FAILED',
  updated_at: '2025-01-15T10:15:00Z',
});

/** A run waiting for human approval */
export const WAITING_RUN = makeHarnessRun({
  id: 'run_waiting_001',
  status: 'waiting_for_human',
  current_state: 'HUMAN_REVIEW',
});

/** A pending human gate (approve/reject actions should be visible) */
export const PENDING_GATE = makeHumanGate({
  id: 'gate_pending_001',
  run_id: 'run_waiting_001',
  status: 'pending',
});

/** An approved (terminal) human gate */
export const APPROVED_GATE = makeHumanGate({
  id: 'gate_approved_001',
  run_id: 'run_completed_001',
  status: 'approved',
  decision_by: 'user-e2e-001',
  decision_reason: 'Claims verified against evidence',
  decided_at: '2025-01-15T10:25:00Z',
});

/** A rejected (terminal) human gate */
export const REJECTED_GATE = makeHumanGate({
  id: 'gate_rejected_001',
  run_id: 'run_failed_001',
  status: 'rejected',
  decision_by: 'user-e2e-001',
  decision_reason: 'Insufficient evidence for claims',
  decided_at: '2025-01-15T10:12:00Z',
});

/** Chronologically ordered checkpoints for RUNNING_RUN */
export const RUNNING_RUN_CHECKPOINTS: HarnessCheckpoint[] = [
  makeHarnessCheckpoint({
    id: 'chk_001',
    run_id: 'run_running_001',
    state_name: 'INIT',
    state_payload: {},
    created_at: '2025-01-15T10:00:01Z',
  }),
  makeHarnessCheckpoint({
    id: 'chk_002',
    run_id: 'run_running_001',
    state_name: 'RESOLVE_CONTEXT',
    state_payload: { account_id: 'acct-meridian-001' },
    created_at: '2025-01-15T10:01:00Z',
  }),
  makeHarnessCheckpoint({
    id: 'chk_003',
    run_id: 'run_running_001',
    state_name: 'GENERATE_HYPOTHESES',
    state_payload: { hypotheses_count: 4 },
    created_at: '2025-01-15T10:03:00Z',
  }),
];

/** Paginated list response with two runs (one running, one completed) */
export const HARNESS_RUNS_LIST: PaginatedHarnessRuns = {
  items: [RUNNING_RUN, COMPLETED_RUN],
  total: 2,
  has_more: false,
};

/** Empty paginated list response */
export const EMPTY_HARNESS_RUNS_LIST: PaginatedHarnessRuns = {
  items: [],
  total: 0,
  has_more: false,
};

/** Single-item list with the waiting run */
export const WAITING_RUN_LIST: PaginatedHarnessRuns = {
  items: [WAITING_RUN],
  total: 1,
  has_more: false,
};

// ── API route patterns ───────────────────────────────────────────────────────

export const HARNESS_API = {
  runs: '**/api/v1/agents/harness/runs',
  runDetail: (runId: string) => `**/api/v1/agents/harness/runs/${runId}`,
  checkpoints: (runId: string) => `**/api/v1/agents/harness/runs/${runId}/checkpoints`,
  gates: (runId: string) => `**/api/v1/agents/harness/runs/${runId}/gates`,
  // Gate-scoped decide route — decision_by is server-derived from auth context,
  // not trusted from the client. Payload: DecideHumanGateRequest.
  decide: (gateId: string) => `**/api/v1/agents/harness/gates/${gateId}/decide`,
} as const;

/**
 * Canonical request payload for POST /v1/harness/gates/:gateId/decide.
 * decision_by is intentionally absent — the server derives it from auth context.
 */
export interface DecideHumanGateRequest {
  status: 'approved' | 'rejected' | 'modified';
  decision_reason?: string;
  human_override?: boolean;
  metadata?: Record<string, unknown>;
}

/**
 * Canonical response shape from POST /v1/harness/gates/:gateId/decide.
 */
export interface HumanGateDecision {
  gate_id: string;
  run_id: string;
  tenant_id: string;
  status: 'approved' | 'rejected' | 'modified';
  decision_by: string;       // server-derived from auth context
  decision_reason?: string;
  decided_at: string;
  human_override: boolean;
}
