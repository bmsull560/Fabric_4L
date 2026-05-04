/**
 * Rich mock data factories for deep validation tests.
 *
 * These factories provide complete, realistic data payloads for testing
 * multi-step workflows with state transitions, form interactions, and
 * business-logic validation.
 */
import type { MockEndpoint } from '../helpers/api-harness';

// ── Identifiers ──────────────────────────────────────────────────────────────

export const DEEP_ACCOUNT_ID = 'acct-deep-meridian-001';
export const DEEP_CASE_APPROVED_ID = 'case-deep-approved-001';
export const DEEP_CASE_DRAFT_ID = 'case-deep-draft-001';
export const DEEP_TENANT_ID = 'tenant-e2e-001';
export const DEEP_FOREIGN_TENANT_ID = 'tenant-foreign-999';
export const DEEP_FOREIGN_ACCOUNT_ID = 'acct-foreign-globex-999';

// ── Full Account Payloads ────────────────────────────────────────────────────

export function createFullAccountPayload(overrides?: Record<string, unknown>) {
  return {
    id: DEEP_ACCOUNT_ID,
    name: 'Meridian Health Group',
    domain: 'meridian.example',
    website: 'https://meridian.example',
    industry: 'Healthcare',
    tier: 'enterprise',
    stage: 'prospect',
    owner: 'Avery Stone',
    readiness: 78,
    value_pack: 'Healthcare Operations',
    created_at: '2026-04-01T12:00:00Z',
    updated_at: '2026-05-01T12:00:00Z',
    audit_events: [
      { event: 'account_created', actor: 'Avery Stone', timestamp: '2026-04-01T12:00:00Z' },
      { event: 'value_pack_assigned', actor: 'Avery Stone', timestamp: '2026-04-02T09:00:00Z' },
      { event: 'ingestion_completed', actor: 'system', timestamp: '2026-04-03T14:00:00Z' },
    ],
    ...overrides,
  };
}

// ── Business Case Payloads ───────────────────────────────────────────────────

export function createApprovedBusinessCase(overrides?: Record<string, unknown>) {
  return {
    id: DEEP_CASE_APPROVED_ID,
    title: 'Meridian Automation Business Case',
    status: 'approved',
    document_url: '/exports/meridian-business-case.pdf',
    roi_ratio: 2.87,
    payback_months: 9,
    total_value: 2100000,
    executive_summary: 'Approved case with verified evidence lineage and three-scenario ROI.',
    recommendations: [
      'Proceed with Phase 1 automation rollout.',
      'Assign metric owners for realization tracking.',
    ],
    claims: [
      { id: 'claim-001', text: 'Manual reconciliation costs $420K annually', evidence_id: 'ev-001', type: 'evidence' },
      { id: 'claim-002', text: 'Automation reduces cycle time by 18-27%', benchmark_id: 'bench-001', type: 'benchmark' },
      { id: 'claim-003', text: 'Finance team validates baseline hours', type: 'assumption', approved: true },
    ],
    approval_history: [
      { action: 'submitted', actor: 'Avery Stone', timestamp: '2026-04-28T10:00:00Z' },
      { action: 'approved', actor: 'Value Engineering Lead', timestamp: '2026-04-29T15:30:00Z' },
    ],
    ...overrides,
  };
}

export function createDraftBusinessCase(overrides?: Record<string, unknown>) {
  return {
    id: DEEP_CASE_DRAFT_ID,
    title: 'Draft Meridian Business Case',
    status: 'draft',
    document_url: null,
    roi_ratio: 1.1,
    payback_months: 18,
    total_value: 450000,
    executive_summary: 'Draft case pending evidence approval and reviewer sign-off.',
    recommendations: ['Resolve missing evidence before export.'],
    claims: [
      { id: 'claim-010', text: 'Estimated savings of $200K', type: 'assumption', approved: false },
    ],
    approval_history: [],
    ...overrides,
  };
}

// ── Signal Set ───────────────────────────────────────────────────────────────

export function createSignalSet() {
  return {
    status: 'ready',
    generated_at: '2026-05-01T12:00:00Z',
    content: {
      signals: [
        { id: 'sig-001', name: 'Manual reconciliation burden', confidence: 0.92, source: 'Discovery call transcript', status: 'approved' },
        { id: 'sig-002', name: 'Supply chain visibility gaps', confidence: 0.87, source: 'Q3 earnings call', status: 'pending_review' },
        { id: 'sig-003', name: 'Regulatory compliance overhead', confidence: 0.65, source: 'Industry report', status: 'pending_review' },
        { id: 'sig-004', name: 'Customer churn from manual processes', confidence: 0.44, source: 'Internal estimate', status: 'low_confidence' },
      ],
    },
  };
}

// ── Value Driver Tree ────────────────────────────────────────────────────────

export function createValueDriverTree() {
  return {
    status: 'ready',
    generated_at: '2026-05-01T12:00:00Z',
    content: {
      drivers: [
        {
          id: 'driver-001', name: 'Operational Efficiency', weight: 0.4,
          children: [
            { id: 'driver-001a', name: 'Reconciliation Automation', weight: 0.6, evidence_ids: ['ev-001'] },
            { id: 'driver-001b', name: 'Cycle Time Reduction', weight: 0.4, evidence_ids: ['ev-002'] },
          ],
        },
        {
          id: 'driver-002', name: 'Revenue Growth', weight: 0.35,
          children: [
            { id: 'driver-002a', name: 'Faster Time to Market', weight: 1.0, evidence_ids: [] },
          ],
        },
        {
          id: 'driver-003', name: 'Risk Reduction', weight: 0.25,
          children: [
            { id: 'driver-003a', name: 'Compliance Automation', weight: 1.0, evidence_ids: ['ev-003'] },
          ],
        },
      ],
    },
  };
}

// ── Evidence Set ─────────────────────────────────────────────────────────────

export function createEvidenceSet() {
  return {
    status: 'ready',
    generated_at: '2026-05-01T12:00:00Z',
    content: {
      evidence: [
        { id: 'ev-001', title: 'Manual reconciliation baseline', source: 'Discovery Notes', confidence: 0.91, type: 'customer_data' },
        { id: 'ev-002', title: 'Cycle time benchmark data', source: 'Industry Benchmark DB', confidence: 0.85, type: 'benchmark' },
        { id: 'ev-003', title: 'Compliance audit findings', source: 'Internal Audit Report', confidence: 0.78, type: 'customer_data' },
      ],
    },
  };
}

// ── ROI Scenarios ────────────────────────────────────────────────────────────

export function createROIScenarios() {
  return {
    conservative: { roi_ratio: 1.8, total_value: 1200000, payback_months: 14, annual_savings: 340000, currency: 'USD' },
    expected: { roi_ratio: 2.87, total_value: 2100000, payback_months: 9, annual_savings: 700000, currency: 'USD' },
    optimistic: { roi_ratio: 4.2, total_value: 3400000, payback_months: 6, annual_savings: 1130000, currency: 'USD' },
  };
}

export function createROICalculatorMock() {
  const scenarios = createROIScenarios();
  return {
    account_id: DEEP_ACCOUNT_ID,
    scenarios,
    active_scenario: 'expected',
    formula_inputs: [
      { id: 'input-hours', name: 'Manual Hours per Week', value: 120, unit: 'hours', required: true },
      { id: 'input-rate', name: 'Fully Loaded Hourly Rate', value: 85, unit: 'USD/hour', required: true },
      { id: 'input-reduction', name: 'Automation Reduction %', value: 0.65, unit: '%', required: true },
      { id: 'input-license', name: 'Annual License Cost', value: 180000, unit: 'USD', required: false },
    ],
    version: 3,
    last_updated: '2026-05-01T12:00:00Z',
  };
}

// ── Approval Workflow ────────────────────────────────────────────────────────

export function createApprovalWorkflow(state: 'pending_review' | 'changes_requested' | 'approved' | 'rejected' = 'pending_review') {
  return {
    id: 'approval-deep-001',
    case_id: DEEP_CASE_DRAFT_ID,
    state,
    reviewer: 'Value Engineering Lead',
    submitted_by: 'Avery Stone',
    submitted_at: '2026-04-28T10:00:00Z',
    comments: state === 'changes_requested'
      ? [{ author: 'Value Engineering Lead', text: 'Missing evidence for claim #2. Please attach benchmark data.', timestamp: '2026-04-28T14:00:00Z' }]
      : [],
    resolved_at: state === 'approved' ? '2026-04-29T15:30:00Z' : null,
  };
}

// ── Ingestion Jobs ───────────────────────────────────────────────────────────

export function createIngestionJobs() {
  return [
    { id: 'job-complete-001', domain: 'meridian.example', status: 'completed', progress: 100, documents_found: 42, documents_processed: 42 },
    { id: 'job-failed-001', domain: 'duplicate.example', status: 'failed', progress: 33, error: 'Duplicate source detected', documents_found: 8, documents_processed: 3 },
    { id: 'job-running-001', domain: 'newclient.example', status: 'processing', progress: 67, documents_found: 20, documents_processed: 13 },
  ];
}

// ── Agent Responses ──────────────────────────────────────────────────────────

export function createGroundedAgentResponse() {
  return {
    content: 'Based on the Discovery call transcript (ev-001), manual reconciliation costs approximately $420K annually. **Assumption:** Finance team confirms baseline hours of 120/week. **Inference:** At 65% automation rate, projected annual savings are $273K. Note: This claim requires customer validation of the hourly rate assumption.',
    metadata: {
      citations: ['ev-001: Discovery call transcript', 'bench-001: Industry benchmark'],
      grounding: 'evidence_backed',
      assumptions: ['Finance team validates baseline hours of 120/week', 'Hourly rate of $85 is fully loaded'],
      confidence: 0.87,
      trace_id: 'trace-deep-001',
      audit_event_id: 'audit-deep-001',
    },
  };
}

export function createRefusalAgentResponse() {
  return {
    content: '**I cannot support this claim.** The requested ROI figure of 500% has no supporting evidence in the current evidence set. Available evidence supports a conservative range of 1.8x–4.2x ROI. Please provide additional customer data or benchmark references before making this claim.',
    metadata: {
      grounding: 'refusal',
      reason: 'unsupported_claim',
      trace_id: 'trace-deep-002',
      audit_event_id: 'audit-deep-002',
    },
  };
}

export function createPromptInjectionAttempt() {
  return {
    content: 'The uploaded document contained embedded instructions that were identified and ignored. Document processing continued normally, extracting 3 valid entities and 0 injected directives.',
    metadata: {
      grounding: 'sanitized',
      injection_detected: true,
      trace_id: 'trace-deep-003',
    },
  };
}

// ── Benchmark Data ───────────────────────────────────────────────────────────

export function createBenchmarkDatasets() {
  return [
    {
      id: 'bench-001', benchmark_id: 'bench-manual-hours-saved', name: 'Manual Hours Saved',
      industry: 'Healthcare', vertical: 'Operations', value_range: '18-27%',
      confidence: 'High', source: 'Validated customer outcomes', year: 2026,
      status: 'active', tags: [], last_verified: '2026-05-01T12:00:00Z', usage_count: 14,
      description: 'Active benchmark with high confidence.',
    },
    {
      id: 'bench-002', benchmark_id: 'bench-cycle-time', name: 'Cycle Time Reduction',
      industry: 'Healthcare', vertical: 'Operations', value_range: '12-20%',
      confidence: 'Medium', source: 'Peer-reviewed study', year: 2024,
      status: 'active', tags: ['stale-warning'], last_verified: '2024-06-15T12:00:00Z', usage_count: 7,
      description: 'Stale benchmark — last verified over 12 months ago.',
    },
  ];
}

// ── Ground Truth ─────────────────────────────────────────────────────────────

export function createGroundTruthSet() {
  return {
    truths: [
      { id: 'truth-001', truth_id: 'truth-001', claim: 'CFO validates baseline reconciliation hours at 120/week.', status: 'approved', maturity: 'corroborated', confidence: 0.91, stale: false, freshness: 'current', source: 'CFO discovery note' },
      { id: 'truth-002', truth_id: 'truth-002', claim: 'Hourly rate of $85 is fully loaded including benefits.', status: 'pending', maturity: 'unverified', confidence: 0.6, stale: false, freshness: 'current', source: 'HR estimate' },
      { id: 'truth-003', truth_id: 'truth-003', claim: 'Competitor pricing has decreased 15% YoY.', status: 'rejected', maturity: 'disputed', confidence: 0.3, stale: true, freshness: 'stale', source: 'Market report 2024' },
    ],
    total: 3,
  };
}

// ── CRM Integration ──────────────────────────────────────────────────────────

export function createCRMIntegration(status: 'idle' | 'syncing' | 'error' = 'idle') {
  return {
    integrations: [{
      id: 'int-sf-deep-001', tenant_id: DEEP_TENANT_ID, provider: 'salesforce',
      enabled: true, instance_url: 'https://meridian.my.salesforce.com',
      sync_interval_minutes: 60, sync_batch_size: 250,
      last_sync_at: '2026-05-01T12:00:00Z',
      last_successful_sync_at: status === 'error' ? null : '2026-05-01T12:00:00Z',
      records_synced: status === 'error' ? 0 : 128,
      records_updated: status === 'error' ? 0 : 9,
      records_failed: status === 'error' ? 7 : 0,
      status,
      last_error_message: status === 'error' ? 'Authentication token expired. Re-authorize.' : null,
      has_refresh_token: true,
      created_at: '2026-04-01T12:00:00Z',
      updated_at: '2026-05-01T12:00:00Z',
    }],
  };
}

// ── Mock Endpoint Builders ───────────────────────────────────────────────────

export function buildGoldenPathMocks(): MockEndpoint[] {
  return [
    { pattern: '**/api/v1/agents/accounts', body: [createFullAccountPayload()] },
    { pattern: `**/api/v1/agents/accounts/${DEEP_ACCOUNT_ID}`, body: createFullAccountPayload() },
    { pattern: '**/api/v1/agents/accounts', method: 'POST', status: 201, body: { account: createFullAccountPayload() } },
    { pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/signals`, body: createSignalSet() },
    { pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/drivers`, body: createValueDriverTree() },
    { pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/evidence`, body: createEvidenceSet() },
    { pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/stakeholders`, body: { status: 'ready', generated_at: '2026-05-01T12:00:00Z', content: { stakeholders: [{ id: 'sh-001', name: 'CFO', influence: 'high' }] } } },
    { pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/value-model`, body: { status: 'ready', generated_at: '2026-05-01T12:00:00Z', content: createROICalculatorMock() } },
    { pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative`, body: { status: 'ready', generated_at: '2026-05-01T12:00:00Z', content: { narrative: 'Generated executive narrative for Meridian Health Group.' } } },
    { pattern: '**/api/v1/ingest/jobs', body: createIngestionJobs() },
    { pattern: '**/agent-stream/chat', method: 'POST', body: createGroundedAgentResponse() },
    { pattern: `**/api/v1/agents/cases/${DEEP_CASE_APPROVED_ID}`, body: createApprovedBusinessCase() },
    { pattern: `**/api/v1/agents/cases/${DEEP_CASE_DRAFT_ID}`, body: createDraftBusinessCase() },
    { pattern: '**/api/v1/agents/cases', body: [createApprovedBusinessCase(), createDraftBusinessCase()] },
    { pattern: '**/api/v1/governance/approvals**', body: [createApprovalWorkflow('approved')] },
    { pattern: '**/api/v1/agents/integrations**', body: createCRMIntegration('idle') },
    { pattern: '**/api/v1/benchmarks/datasets**', body: createBenchmarkDatasets() },
    { pattern: '**/api/v1/agents/ground-truth/truths**', body: createGroundTruthSet() },
    { pattern: '**/api/v1/agents/recommendations**', body: [{ id: 'rec-001', status: 'pending_review', evidence_id: 'ev-001', text: 'Automate reconciliation workflow' }] },
  ];
}
