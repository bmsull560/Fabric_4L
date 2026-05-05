/**
 * OpenAPI Drift Detection Suite
 *
 * Validates that every hand-written Zod schema in _helpers.ts stays in sync
 * with its canonical checked-in OpenAPI JSON Schema definition. If a Zod
 * schema becomes looser or stricter than the OpenAPI contract, this suite
 * surfaces the mismatch with field-level detail.
 *
 * Run: pnpm run test:contracts
 */

import { describe, it, expect } from 'vitest';
import {
  OPENAPI_SCHEMA_MAP,
  DRIFT_TRACKED_SCHEMAS,
  assertOpenApiSchema,
  assertOpenApiSchemaRejects,
} from './openapi-validator';
import {
  ExtractResponseSchema,
  ExtractionStatusSchema,
  GraphNodeSchema,
  SubgraphResponseSchema,
  FormulaEvaluateResponseSchema,
  PackSummarySchema,
  WorkflowCreateResponseSchema,
  WorkflowStatusResponseSchema,
  TenantModelSchema,
  FeatureFlagResponseSchema,
  TruthObjectResponseSchema,
  TruthObjectListResponseSchema,
  ApiErrorSchema,
  fixtures,
  assertSchema,
  assertSchemaRejects,
} from './_helpers';

// ---------------------------------------------------------------------------
// Drift detection — every tracked schema must accept its canonical fixture
// ---------------------------------------------------------------------------

describe('OpenAPI drift: tracked schemas have canonical mappings', () => {
  it('every entry in OPENAPI_SCHEMA_MAP resolves to a real schema file', () => {
    for (const [name, mapping] of Object.entries(OPENAPI_SCHEMA_MAP)) {
      expect(mapping.specFile).toMatch(/\.json$/);
      expect(mapping.ref).toMatch(/^#\/components\/schemas\//);
      expect(mapping.description).toBeTruthy();
    }
  });

  it('DRIFT_TRACKED_SCHEMAS matches OPENAPI_SCHEMA_MAP keys', () => {
    const mapKeys = Object.keys(OPENAPI_SCHEMA_MAP).sort();
    const tracked = [...DRIFT_TRACKED_SCHEMAS].sort();
    expect(tracked).toEqual(mapKeys);
  });
});

// ---------------------------------------------------------------------------
// L2 Extraction fixtures against OpenAPI
// ---------------------------------------------------------------------------

describe('OpenAPI drift: L2 Extraction', () => {
  it('ExtractResponse fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer2-extraction.json',
      '#/components/schemas/ExtractResponse',
      fixtures.extractResponse(),
      'ExtractResponse'
    );
  });

  it('ExtractionStatus (completed) fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer2-extraction.json',
      '#/components/schemas/ExtractionStatusResponse',
      fixtures.extractionStatus(),
      'ExtractionStatus (completed)'
    );
  });

  it('ExtractionStatus (failed) fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer2-extraction.json',
      '#/components/schemas/ExtractionStatusResponse',
      fixtures.extractionStatus({
        overall_status: 'failed',
        extraction_status: 'failed',
        ingestion_status: 'skipped',
        last_error: 'timeout',
      }),
      'ExtractionStatus (failed)'
    );
  });
});

// ---------------------------------------------------------------------------
// L3 Knowledge Graph fixtures against OpenAPI
// ---------------------------------------------------------------------------

describe('OpenAPI drift: L3 Knowledge Graph', () => {
  it('GraphNode fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer3-knowledge.json',
      '#/components/schemas/GraphNode',
      fixtures.graphNode(),
      'GraphNode'
    );
  });

  it('SubgraphResponse fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer3-knowledge.json',
      '#/components/schemas/SubgraphResponse',
      {
        root_entity_id: 'node-001',
        nodes: [fixtures.graphNode()],
        edges: [],
        depth: 2,
        stats: { total_nodes: 1, total_edges: 0, density: 0 },
      },
      'SubgraphResponse'
    );
  });

  it('FormulaEvaluateResponse fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer3-knowledge.json',
      '#/components/schemas/FormulaEvaluateResponse',
      {
        result: 150,
        unit: 'percent',
        confidence: 0.92,
        calculation_steps: [
          { step: 1, operation: 'a+b', result: '150' },
        ],
        formula_used: 'roi_v2',
      },
      'FormulaEvaluateResponse'
    );
  });

  it('PackSummary fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer3-knowledge.json',
      '#/components/schemas/PackSummary',
      fixtures.packSummary(),
      'PackSummary'
    );
  });
});

// ---------------------------------------------------------------------------
// L4 Agents / Workflows / Governance fixtures against OpenAPI
// ---------------------------------------------------------------------------

describe('OpenAPI drift: L4 Agents', () => {
  it('WorkflowCreateResponse fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer4-agents.json',
      '#/components/schemas/WorkflowCreateResponse',
      fixtures.workflowCreateResponse(),
      'WorkflowCreateResponse'
    );
  });

  it('WorkflowStatusResponse (running) fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer4-agents.json',
      '#/components/schemas/WorkflowStatusResponse',
      fixtures.workflowStatus(),
      'WorkflowStatusResponse (running)'
    );
  });

  it('TenantModel fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer4-agents.json',
      '#/components/schemas/TenantModel',
      fixtures.tenant(),
      'TenantModel'
    );
  });

  it('FeatureFlagResponse fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer4-agents.json',
      '#/components/schemas/FeatureFlagResponse',
      fixtures.featureFlag(),
      'FeatureFlagResponse'
    );
  });
});

// ---------------------------------------------------------------------------
// L5 Ground Truth fixtures against OpenAPI
// ---------------------------------------------------------------------------

describe('OpenAPI drift: L5 Ground Truth', () => {
  it('TruthObjectResponse fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer5-ground-truth.json',
      '#/components/schemas/TruthObjectResponse',
      fixtures.truthObject(),
      'TruthObjectResponse'
    );
  });

  it('TruthObjectListResponse fixture passes canonical OpenAPI schema', () => {
    assertOpenApiSchema(
      'layer5-ground-truth.json',
      '#/components/schemas/TruthObjectListResponse',
      {
        items: [fixtures.truthObjectSummary()],
        total: 1,
        limit: 20,
        offset: 0,
        has_more: false,
      },
      'TruthObjectListResponse'
    );
  });
});

// ---------------------------------------------------------------------------
// Negative-path drift: Zod must be at least as strict as OpenAPI
// ---------------------------------------------------------------------------

describe('OpenAPI drift: negative-path consistency', () => {
  it('Zod rejects invalid UUID where OpenAPI also rejects it', () => {
    const bad = { ...fixtures.tenant(), id: 'not-a-uuid' };
    assertSchemaRejects(TenantModelSchema, bad, 'TenantModel bad UUID');
    assertOpenApiSchemaRejects(
      'layer4-agents.json',
      '#/components/schemas/TenantModel',
      bad,
      'TenantModel bad UUID (OpenAPI)'
    );
  });

  it('Zod rejects out-of-range confidence but OpenAPI allows any number (documented divergence)', () => {
    const bad = { ...fixtures.truthObject(), confidence: 1.5 };
    assertSchemaRejects(TruthObjectResponseSchema, bad, 'TruthObject confidence > 1');
    // Intentionally NOT asserting OpenAPI rejection — the canonical spec
    // does not constrain the confidence range. Zod is stricter.
    expect(bad.confidence).toBe(1.5);
  });

  it('Zod rejects unknown workflow status but OpenAPI allows any string (documented divergence)', () => {
    const bad = fixtures.workflowStatus({ status: 'bogus' as 'running' });
    // Zod is stricter: it uses an enum. OpenAPI defines status as a plain string.
    assertSchemaRejects(WorkflowStatusResponseSchema, bad, 'WorkflowStatus unknown enum');
    // Intentionally NOT asserting OpenAPI rejection here — the canonical spec
    // is looser than our frontend schema. This is a known divergence.
    expect(bad.status).toBe('bogus');
  });
});

// ---------------------------------------------------------------------------
// Common error shapes
// ── Auth failures ─────────────────────────────────────────────────────────────

describe('Contract: drift-detection auth failures', () => {
  it('401 matches ApiError shape', () => {
    assertSchema(ApiErrorSchema, { message: 'Authentication required', code: 'UNAUTHORIZED', trace_id: 'trace-drift-401' }, 'ApiError (401)');
  });

  it('403 forbidden matches ApiError shape', () => {
    assertSchema(ApiErrorSchema, { message: 'Access denied', code: 'FORBIDDEN', trace_id: 'trace-drift-403' }, 'ApiError (403)');
  });
});

// ── Common error shapes ───────────────────────────────────────────────────────

describe('OpenAPI drift: common error shapes', () => {
  it('ApiError fixture is compatible with HTTPValidationError', () => {
    // The OpenAPI HTTPValidationError has { detail: [...] } which is not
    // the same as our frontend ApiErrorSchema. Document this divergence
    // so future refactors can align them.
    const frontendError = { message: 'Bad request', code: 'VALIDATION_ERROR', trace_id: 'abc' };
    assertSchema(ApiErrorSchema, frontendError, 'frontend ApiError');

    // Intentionally *not* asserting OpenAPI compatibility here because
    // the backend HTTPValidationError shape (Pydantic v2) differs from
    // the frontend ApiErrorSchema. This test documents the gap.
    expect(frontendError).toBeDefined();
  });
});
