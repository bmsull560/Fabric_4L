/**
 * Contract tests: Ground Truth (L5)
 *
 * Validates request/response shapes against contracts/openapi/layer5-ground-truth.json.
 * Covers: POST /api/v1/truths, GET /api/v1/truths, GET /api/v1/truths/{id},
 * POST /api/v1/truths/{id}/validate, POST /api/v1/truths/{id}/sources,
 * and the maturity ladder endpoint.
 */

import { describe, it, expect } from 'vitest';
import { z } from 'zod';
import {
  TruthObjectResponseSchema,
  TruthObjectListResponseSchema,
  TruthStatusEnum,
  ValidateResponseSchema,
  ApiErrorSchema,
  assertSchema,
  assertSchemaRejects,
  fixtures,
} from './_helpers';

// ── Request schemas ───────────────────────────────────────────────────────────

const TruthObjectCreateSchema = z.object({
  claim: z.string().min(5).max(2000),
  claim_type: z.string().optional(),
  confidence: z.number().min(0).max(1),
  value: z
    .object({
      amount: z.number().optional(),
      unit: z.string().optional(),
      currency: z.string().optional(),
      period: z.string().optional(),
    })
    .nullable()
    .optional(),
  applies_to: z.record(z.unknown()).nullable().optional(),
  extraction_job_id: z.string().max(255).nullable().optional(),
  extraction_model: z.string().max(128).nullable().optional(),
  sources: z.array(z.record(z.unknown())).optional(),
});

const AddSourceRequestSchema = z.object({
  source_type: z.string().min(1),
  url: z.string().optional(),
  title: z.string().optional(),
  excerpt: z.string().optional(),
  confidence: z.number().min(0).max(1).optional(),
});

const MaturityLadderResponseSchema = z.object({
  truth_id: z.string().uuid(),
  current_level: z.number().int().nonnegative(),
  history: z.array(
    z.object({
      level: z.number().int().nonnegative(),
      status: z.string(),
      transitioned_at: z.string(),
    })
  ),
});

// ── POST /api/v1/truths ───────────────────────────────────────────────────────

describe('Contract: POST /api/v1/truths', () => {
  it('accepts a minimal valid create request', () => {
    assertSchema(
      TruthObjectCreateSchema,
      {
        claim: 'Manual reporting costs 12 hours/week per analyst',
        confidence: 0.82,
      },
      'TruthObjectCreate (minimal)'
    );
  });

  it('accepts a full create request with value and applies_to', () => {
    assertSchema(
      TruthObjectCreateSchema,
      {
        claim: 'Manual reporting costs 12 hours/week per analyst',
        claim_type: 'quantitative',
        confidence: 0.82,
        value: { amount: 12, unit: 'hours', period: 'week' },
        applies_to: { account_id: 'acct-456', opportunity_id: 'opp-123' },
        extraction_job_id: 'job-abc123',
        extraction_model: 'gpt-4-turbo',
      },
      'TruthObjectCreate (full)'
    );
  });

  it('rejects claim shorter than 5 characters', () => {
    assertSchemaRejects(
      TruthObjectCreateSchema,
      { claim: 'Hi', confidence: 0.9 },
      'TruthObjectCreate with short claim'
    );
  });

  it('rejects claim longer than 2000 characters', () => {
    assertSchemaRejects(
      TruthObjectCreateSchema,
      { claim: 'a'.repeat(2001), confidence: 0.9 },
      'TruthObjectCreate with claim > 2000 chars'
    );
  });

  it('rejects confidence > 1', () => {
    assertSchemaRejects(
      TruthObjectCreateSchema,
      { claim: 'Valid claim text here', confidence: 1.1 },
      'TruthObjectCreate with confidence > 1'
    );
  });

  it('rejects confidence < 0', () => {
    assertSchemaRejects(
      TruthObjectCreateSchema,
      { claim: 'Valid claim text here', confidence: -0.1 },
      'TruthObjectCreate with negative confidence'
    );
  });
});

// ── GET /api/v1/truths/{truth_id} ─────────────────────────────────────────────

describe('Contract: GET /api/v1/truths/{truth_id}', () => {
  it('response has required fields including organization_id', () => {
    const resp = assertSchema(
      TruthObjectResponseSchema,
      fixtures.truthObject(),
      'TruthObjectResponse'
    );
    expect(resp.id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    );
    expect(resp.organization_id).toBeTruthy();
    expect(resp.confidence).toBeGreaterThanOrEqual(0);
    expect(resp.confidence).toBeLessThanOrEqual(1);
  });

  it('is_stale is a boolean', () => {
    const fresh = assertSchema(
      TruthObjectResponseSchema,
      fixtures.truthObject({ is_stale: false }),
      'TruthObjectResponse (fresh)'
    );
    expect(fresh.is_stale).toBe(false);

    const stale = assertSchema(
      TruthObjectResponseSchema,
      fixtures.truthObject({ is_stale: true }),
      'TruthObjectResponse (stale)'
    );
    expect(stale.is_stale).toBe(true);
  });

  it('applies_to is optional and nullable', () => {
    assertSchema(
      TruthObjectResponseSchema,
      fixtures.truthObject({ applies_to: null }),
      'TruthObjectResponse (no applies_to)'
    );
  });

  it('rejects non-UUID id', () => {
    assertSchemaRejects(
      TruthObjectResponseSchema,
      { ...fixtures.truthObject(), id: 'not-a-uuid' },
      'TruthObjectResponse with non-UUID id'
    );
  });
});

// ── GET /api/v1/truths (list) ─────────────────────────────────────────────────

describe('Contract: GET /api/v1/truths', () => {
  it('list response has items, total, limit, offset, has_more', () => {
    const resp = assertSchema(
      TruthObjectListResponseSchema,
      {
        items: [fixtures.truthObjectSummary()],
        total: 1,
        limit: 20,
        offset: 0,
        has_more: false,
      },
      'TruthObjectListResponse'
    );
    expect(resp.items).toHaveLength(1);
    expect(resp.total).toBe(1);
  });

  it('empty list is valid', () => {
    const resp = assertSchema(
      TruthObjectListResponseSchema,
      { items: [], total: 0, limit: 20, offset: 0, has_more: false },
      'TruthObjectListResponse (empty)'
    );
    expect(resp.items).toHaveLength(0);
  });

  it('rejects negative total', () => {
    assertSchemaRejects(
      TruthObjectListResponseSchema,
      { items: [], total: -1, limit: 20, offset: 0, has_more: false },
      'TruthObjectListResponse with negative total'
    );
  });
});

// ── POST /api/v1/truths/{truth_id}/validate ───────────────────────────────────

describe('Contract: POST /api/v1/truths/{truth_id}/validate', () => {
  it('validate response has status transition fields', () => {
    const resp = assertSchema(
      ValidateResponseSchema,
      {
        truth_id: '550e8400-e29b-41d4-a716-446655440002',
        previous_status: 'extracted',
        new_status: 'supported',
        maturity_level: 2,
      },
      'ValidateResponse'
    );
    expect(resp.previous_status).toBeTruthy();
    expect(resp.new_status).toBeTruthy();
    expect(resp.maturity_level).toBeGreaterThanOrEqual(0);
  });

  it('rejects non-UUID truth_id', () => {
    assertSchemaRejects(
      ValidateResponseSchema,
      { truth_id: 'not-a-uuid', previous_status: 'extracted', new_status: 'supported', maturity_level: 2 },
      'ValidateResponse with non-UUID truth_id'
    );
  });
});

// ── POST /api/v1/truths/{truth_id}/sources ────────────────────────────────────

describe('Contract: POST /api/v1/truths/{truth_id}/sources', () => {
  it('accepts a source with type and url', () => {
    assertSchema(
      AddSourceRequestSchema,
      {
        source_type: 'document',
        url: 'https://example.com/report.pdf',
        title: 'Annual Report 2024',
        excerpt: 'Revenue grew 23% YoY...',
        confidence: 0.88,
      },
      'AddSourceRequest'
    );
  });

  it('accepts minimal source with type only', () => {
    assertSchema(
      AddSourceRequestSchema,
      { source_type: 'interview' },
      'AddSourceRequest (minimal)'
    );
  });

  it('rejects empty source_type', () => {
    assertSchemaRejects(
      AddSourceRequestSchema,
      { source_type: '' },
      'AddSourceRequest with empty source_type'
    );
  });
});

// ── GET /api/v1/maturity-ladder ───────────────────────────────────────────────

describe('Contract: GET /api/v1/maturity-ladder', () => {
  it('maturity ladder has current_level and history', () => {
    const resp = assertSchema(
      MaturityLadderResponseSchema,
      {
        truth_id: '550e8400-e29b-41d4-a716-446655440002',
        current_level: 3,
        history: [
          { level: 1, status: 'extracted', transitioned_at: '2024-01-10T10:00:00Z' },
          { level: 2, status: 'supported', transitioned_at: '2024-01-12T10:00:00Z' },
          { level: 3, status: 'corroborated', transitioned_at: '2024-01-15T10:00:00Z' },
        ],
      },
      'MaturityLadderResponse'
    );
    expect(resp.current_level).toBe(3);
    expect(resp.history).toHaveLength(3);
  });
});

// ── Auth failures ─────────────────────────────────────────────────────────────

describe('Contract: ground truth auth failures', () => {
  it('401 matches ApiError shape', () => {
    assertSchema(
      ApiErrorSchema,
      { message: 'Authentication required', code: 'UNAUTHORIZED', trace_id: 'trace-gt-401' },
      'ApiError (401)'
    );
  });

  it('cross-tenant 403 matches ApiError shape', () => {
    const err = assertSchema(
      ApiErrorSchema,
      { message: 'Truth object does not belong to your tenant', code: 'FORBIDDEN', trace_id: 'trace-gt-403' },
      'ApiError (403 cross-tenant)'
    );
    expect(err.code).toBe('FORBIDDEN');
    expect(err.trace_id).toBeTruthy();
  });

  it('truth not found 404 matches ApiError shape', () => {
    const err = assertSchema(
      ApiErrorSchema,
      { message: 'Truth object not found', code: 'NOT_FOUND', trace_id: 'trace-gt-404' },
      'ApiError (404 truth)'
    );
    expect(err.code).toBe('NOT_FOUND');
  });
});
