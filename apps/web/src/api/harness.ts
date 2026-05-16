import { apiClient } from './client';

// ── Harness Types ─────────────────────────────────────────────────────────────

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

export type GateType =
  | 'approve_claims'
  | 'approve_assumptions'
  | 'approve_customer_output'
  | 'resolve_conflict';

export type GateStatus = 'pending' | 'approved' | 'rejected' | 'modified' | 'expired';

export type GateDecision = 'approved' | 'rejected' | 'modified' | 'expired';

export type ValidationState =
  | 'passed'
  | 'failed'
  | 'needs_review'
  | 'insufficient_evidence';

export type InitiatedBy = 'user' | 'system' | 'agent' | 'scheduled_job';

export const TERMINAL_STATES: HarnessState[] = ['DONE', 'FAILED', 'CANCELLED'];

export function isTerminalState(state: HarnessState): boolean {
  return TERMINAL_STATES.includes(state);
}

// ── Domain Models ─────────────────────────────────────────────────────────────

export interface HarnessRun {
  id: string;
  tenant_id: string;
  account_id: string | null;
  workflow_type: HarnessWorkflowType;
  initiated_by: InitiatedBy;
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
  input_hash: string;
  output_hash: string | null;
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
  validator: string;
  reason: string;
  created_at: string;
}

// ── Request / Response Types ──────────────────────────────────────────────────

export interface CreateRunRequest {
  workflow_type: HarnessWorkflowType;
  initiated_by?: InitiatedBy;
  account_id?: string;
  value_pack_id?: string;
}

export interface RunListResponse {
  items: HarnessRun[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface TransitionRequest {
  to_state: HarnessState;
  human_override?: boolean;
  state_payload?: Record<string, unknown>;
  validation_results?: ClaimValidationResult[];
}

export interface TransitionResponse {
  run: HarnessRun;
  trace_event: {
    trace_id: string;
    run_id: string;
    from_state: HarnessState | null;
    to_state: HarnessState | null;
    event_type: string;
    timestamp: string;
  } | null;
}

export interface CheckpointListResponse {
  items: HarnessCheckpoint[];
  total: number;
}

export interface GateListResponse {
  items: HumanGate[];
  total: number;
}

export interface GateDecisionRequest {
  decision: GateDecision;
  decision_reason?: string;
}

export interface ClaimToValidate {
  claim_id: string;
  claim_text: string;
  evidence_refs?: string[];
  value_pack_id?: string;
  account_id?: string;
}

export interface ValidateClaimsRequest {
  claims: ClaimToValidate[];
}

export interface ValidateClaimsResponse {
  results: ClaimValidationResult[];
  total: number;
  passed: number;
  failed: number;
  needs_review: number;
  insufficient_evidence: number;
}

export interface HarnessHealthResponse {
  status: 'ok' | 'degraded';
  validation_available: boolean;
  l5_healthy: boolean;
  db_healthy: boolean;
}

// ── API Client ────────────────────────────────────────────────────────────────

const L4 = 'l4' as const;

export const harnessApi = {
  // Runs
  createRun: (data: CreateRunRequest) =>
    apiClient.post(L4, '/harness/runs', data).then(r => r.data as HarnessRun),

  listRuns: (params?: {
    status?: HarnessRunStatus;
    workflow_type?: HarnessWorkflowType;
    limit?: number;
    offset?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.workflow_type) query.set('workflow_type', params.workflow_type);
    if (params?.limit != null) query.set('limit', String(params.limit));
    if (params?.offset != null) query.set('offset', String(params.offset));
    const qs = query.toString();
    return apiClient.get(L4, `/harness/runs${qs ? `?${qs}` : ''}`).then(r => r.data as RunListResponse);
  },

  getRun: (runId: string) =>
    apiClient.get(L4, `/harness/runs/${runId}`).then(r => r.data as HarnessRun),

  transitionRun: (runId: string, data: TransitionRequest) =>
    apiClient.post(L4, `/harness/runs/${runId}/transition`, data).then(r => r.data as TransitionResponse),

  cancelRun: (runId: string) =>
    apiClient.delete(L4, `/harness/runs/${runId}`).then(r => r.data),

  // Checkpoints
  listCheckpoints: (runId: string) =>
    apiClient.get(L4, `/harness/runs/${runId}/checkpoints`).then(r => r.data as CheckpointListResponse),

  getLatestCheckpoint: (runId: string) =>
    apiClient.get(L4, `/harness/runs/${runId}/checkpoints/latest`).then(r => r.data as HarnessCheckpoint),

  // Gates
  listGates: (runId: string) =>
    apiClient.get(L4, `/harness/runs/${runId}/gates`).then(r => r.data as GateListResponse),

  createGate: (runId: string, data: { gate_type: GateType }) =>
    apiClient.post(L4, `/harness/runs/${runId}/gates`, data).then(r => r.data as HumanGate),

  decideGate: (gateId: string, data: GateDecisionRequest) =>
    apiClient.post(L4, `/harness/gates/${gateId}/decide`, data).then(r => r.data as HumanGate),

  // Validation
  validateClaims: (runId: string, data: ValidateClaimsRequest) =>
    apiClient.post(L4, `/harness/runs/${runId}/validate`, data).then(r => r.data as ValidateClaimsResponse),

  // Health
  health: () =>
    apiClient.get(L4, '/harness/health').then(r => r.data as HarnessHealthResponse),
};
