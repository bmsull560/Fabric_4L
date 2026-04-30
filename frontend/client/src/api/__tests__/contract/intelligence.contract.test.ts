import { describe, it } from 'vitest';

/**
 * Contract tests: Intelligence / Signals / Narratives (L4 + L3 composition)
 *
 * These endpoints are composed product surfaces. The contract tests
 * assert the frontend expectation of the composed shape, regardless
 * of whether the backing implementation is a single layer or a BFF.
 */

describe('Contract: Account Intelligence Briefing', () => {
  it.todo('should expose GET /v1/intelligence/account/{account_id}/briefing');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching AccountBriefing');
  it.todo('should include required fields: account_id, executive_summary, key_signals, recommended_actions, generated_at');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Deal Readiness', () => {
  it.todo('should expose GET /v1/intelligence/account/{account_id}/deal-readiness');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching DealReadiness');
  it.todo('should include required fields: account_id, readiness_score, gaps, strengths, recommended_next_steps');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Pipeline Summary', () => {
  it.todo('should expose GET /v1/intelligence/pipeline-summary');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching PipelineSummary');
  it.todo('should include required fields: total_accounts, avg_readiness, stage_breakdown, last_updated');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Narratives', () => {
  it.todo('should expose GET /v1/narratives, GET /v1/narratives/{id}, POST /v1/narratives/generate, PATCH /v1/narratives/{id}/status, DELETE /v1/narratives/{id}');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching Narrative with sections array');
  it.todo('should include required fields: id, title, status, account_id, sections, created_at, updated_at');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Intelligence Composition (BFF candidate)', () => {
  it.todo('should expose a unified product endpoint (e.g., GET /api/product/accounts/{id}/intelligence)');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return composed shape: account + briefing + deal_readiness + signals + activity');
  it.todo('should gracefully degrade if one backing layer is unavailable');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});
