/**
 * API Validation — Runtime Type Guards with Zod
 *
 * Validates API responses at runtime to ensure contract compliance.
 * All external data must pass through these validators.
 */

import { z } from 'zod';
import { createFeatureLogger } from '@/lib/telemetry';

const log = createFeatureLogger('api-validation');

// Re-export formula schemas for unified API validation access
export {
  FormulaStatusSchema,
  FormulaTypeSchema,
  CalculationStepSchema,
  FormulaSchema,
  FormulaListSchema,
  ApprovalStatusSchema,
  ApprovalRequestSchema,
  FormulaEvaluationResultSchema,
} from '@/lib/schemas/formula';

// ============================================================================
// Layer 3: Knowledge Graph Validation
// ============================================================================

export const GraphNodeSchema = z.object({
  id: z.string().min(1, 'Node ID is required'),
  name: z.string().min(1, 'Node name is required'),
  type: z.string().min(1, 'Node type is required'),
  properties: z.record(z.string(), z.unknown()).optional(),
  confidence_score: z.number().min(0).max(1).optional(),
});

export const GraphEdgeSchema = z.object({
  source: z.string().min(1, 'Source ID is required'),
  target: z.string().min(1, 'Target ID is required'),
  relationship: z.string().min(1, 'Relationship type is required'),
  properties: z.record(z.string(), z.unknown()).optional(),
});

export const SubgraphResponseSchema = z.object({
  root_entity_id: z.string(),
  nodes: z.array(GraphNodeSchema),
  edges: z.array(GraphEdgeSchema),
  depth: z.number().int().min(0),
  stats: z.object({
    total_nodes: z.number().int(),
    total_edges: z.number().int(),
    density: z.number(),
  }),
});

export const EntitySchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  type: z.string().min(1),
  domain: z.string().optional(),
  status: z.enum(['draft', 'validated', 'deprecated']),
  properties: z.record(z.string(), z.unknown()),
  relationships: z.array(z.object({
    target_id: z.string(),
    relationship_type: z.string(),
  })).optional(),
  created_at: z.string().datetime({ message: 'Invalid datetime' }),
  updated_at: z.string().datetime({ message: 'Invalid datetime' }),
});

export const EntityListResponseSchema = z.object({
  results: z.array(EntitySchema),
  total: z.number().int(),
  page: z.number().int(),
});

// ============================================================================
// Layer 4: Workflow Validation
// ============================================================================

export const WorkflowSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  status: z.enum(['active', 'paused', 'completed', 'failed']),
  last_run: z.string().datetime({ message: 'Invalid datetime' }).optional(),
  configuration: z.record(z.string(), z.unknown()).optional(),
});

export const WorkflowExecutionSchema = z.object({
  id: z.string().uuid(),
  workflow_id: z.string().uuid(),
  status: z.enum(['pending', 'running', 'completed', 'failed']),
  started_at: z.string().datetime({ message: 'Invalid datetime' }),
  completed_at: z.string().datetime({ message: 'Invalid datetime' }).optional(),
  results: z.record(z.string(), z.unknown()).optional(),
  logs: z.array(z.object({
    timestamp: z.string().datetime({ message: 'Invalid datetime' }),
    level: z.enum(['info', 'warning', 'error']),
    message: z.string(),
  })),
});

// ============================================================================
// Value Trees
// ============================================================================

export const ValueTreeNodeSchema: z.ZodType<{
  id: string;
  name: string;
  value: number;
  confidence: number;
  children?: Array<{
    id: string;
    name: string;
    value: number;
    confidence: number;
    children?: unknown[];
    formula_id?: string;
  }>;
  formula_id?: string;
}> = z.object({
  id: z.string().uuid(),
  name: z.string(),
  value: z.number(),
  confidence: z.number().min(0).max(1),
  children: z.lazy(() => ValueTreeNodeSchema.array()).optional(),
  formula_id: z.string().uuid().optional(),
});

export const ValueTreeSchema = z.object({
  id: z.string().uuid(),
  entity_id: z.string().uuid(),
  root_node: ValueTreeNodeSchema,
  total_value: z.number(),
  currency: z.string(),
  confidence: z.number().min(0).max(1),
});

// ============================================================================
// Validation Helpers
// ============================================================================

export class ValidationError extends Error {
  constructor(
    message: string,
    public readonly zodError: z.ZodError,
    public readonly path: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Validate data against a Zod schema with detailed error reporting
 */
export function validate<T>(schema: z.ZodType<T>, data: unknown, path: string): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    const errorMessage = `Validation failed for ${path}: ${result.error.issues.map(i => i.message).join(', ')}`;
    if (process.env.NODE_ENV === 'development') {
      log.error('API Validation failed', { errorCode: errorMessage });
    }
    throw new ValidationError(errorMessage, result.error, path);
  }
  return result.data;
}

/**
 * Validate with fallback — returns default value on validation failure
 */
export function validateWithFallback<T>(
  schema: z.ZodType<T>,
  data: unknown,
  fallback: T,
  context?: string
): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    if (process.env.NODE_ENV === 'development' && context) {
      log.warn(`${context} failed validation, using fallback`);
    }
    return fallback;
  }
  return result.data;
}
