/**
 * Centralized Zod validation schemas for API responses.
 *
 * Contract parsing stays centralized, reusable, and easier to maintain.
 * All API response validation should use these schemas rather than inline checks.
 */

import { z } from 'zod';

// ── Base Entity Schema ───────────────────────────────────────────────────────

export const EntitySchema = z.object({
  id: z.string(),
  name: z.string(),
  entity_type: z.string(),
  domain: z.string().nullable().optional(),
  status: z.enum(['validated', 'pending', 'draft', 'deprecated']).default('draft'),
  confidence: z.number().min(0).max(1).default(0),
  confidence_label: z.enum(['high', 'medium', 'low']).default('low'),
  description: z.string().optional(),
  updated_at: z.string(),
  created_at: z.string().optional(),
  created_by: z.string().optional(),
  source_name: z.string().optional(),
  extraction_job_id: z.string().optional(),
});

// ── Entity List Response ─────────────────────────────────────────────────────

export const EntityListResponseSchema = z.object({
  results: z.array(z.record(z.unknown())), // Raw entities validated per-item by mapper
  total_count: z.number().default(0),
  filtered_count: z.number().default(0),
  limit: z.number().default(50),
  offset: z.number().default(0),
  has_more: z.boolean().default(false),
  available_domains: z.array(z.string()).default([]),
  available_sources: z.array(z.string()).default([]),
});

// ── Graph/Subgraph Schemas ───────────────────────────────────────────────────

export const GraphNodeSchema = z.object({
  id: z.string(),
  name: z.string(),
  entity_type: z.string(),
  confidence_score: z.number().min(0).max(1).default(0.8),
  description: z.string().optional(),
  properties: z.record(z.unknown()).optional(),
});

export const GraphEdgeSchema = z.object({
  source: z.string(),
  target: z.string(),
  type: z.string(),
  confidence: z.number().min(0).max(1).optional(),
  properties: z.record(z.unknown()).optional(),
});

export const SubgraphResponseSchema = z.object({
  root_entity_id: z.string(),
  nodes: z.array(GraphNodeSchema),
  edges: z.array(GraphEdgeSchema),
  depth: z.number(),
  stats: z.object({
    total_nodes: z.number(),
    total_edges: z.number(),
    density: z.number(),
  }),
});

export const GraphQueryResponseSchema = z.object({
  query: z.string(),
  entities: z.array(GraphNodeSchema).optional().default([]),
  relationships: z.array(GraphEdgeSchema).optional().default([]),
  context_graph: z.object({
    nodes: z.array(GraphNodeSchema),
    relationships: z.array(GraphEdgeSchema),
  }).optional(),
  confidence_score: z.number().min(0).max(1).default(0),
  sources: z.array(z.string()).optional().default([]),
  processing_time_ms: z.number().default(0),
});

export const EntityContextResponseSchema = z.object({
  entity_id: z.string(),
  center: GraphNodeSchema,
  neighbors: z.array(GraphNodeSchema).default([]),
  relationships: z.array(GraphEdgeSchema).default([]),
  entity_count: z.number().default(0),
  relationship_count: z.number().default(0),
});

export const EntityTraversalResponseSchema = z.object({
  start_entity_id: z.string(),
  direction: z.string(),
  paths: z.array(z.object({
    nodes: z.array(GraphNodeSchema),
    relationships: z.array(GraphEdgeSchema),
    value_score: z.number().optional(),
  })).default([]),
  path_count: z.number().default(0),
});

// ── Validation Helpers ────────────────────────────────────────────────────────

export class ValidationError extends Error {
  constructor(
    message: string,
    public context: string,
    public issues?: z.ZodIssue[]
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Validate data against a Zod schema, throwing a descriptive error on failure.
 *
 * @param schema - Zod schema to validate against
 * @param data - Unknown data to validate
 * @param context - Description of what's being validated (for error messages)
 * @returns Validated and typed data
 * @throws ValidationError if validation fails
 */
export function validateOrThrow<T>(schema: z.ZodSchema<T>, data: unknown, context: string): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    const issues = result.error.issues;
    const message = `Validation failed for ${context}: ${issues.map(i => `${i.path.join('.')}: ${i.message}`).join(', ')}`;
    throw new ValidationError(message, context, issues);
  }
  return result.data;
}

/**
 * Validate data against a Zod schema, returning null on failure.
 *
 * @param schema - Zod schema to validate against
 * @param data - Unknown data to validate
 * @returns Validated data or null if validation fails
 */
export function validateOrNull<T>(schema: z.ZodSchema<T>, data: unknown): T | null {
  const result = schema.safeParse(data);
  return result.success ? result.data : null;
}

/**
 * Validate that a value is a non-null object.
 *
 * @param value - Unknown value to check
 * @param context - Description for error message
 * @returns The value as a Record
 * @throws ValidationError if not a non-null object
 */
export function validateObject(value: unknown, context: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new ValidationError(
      `Expected object for ${context}, got ${value === null ? 'null' : typeof value}`,
      context
    );
  }
  return value as Record<string, unknown>;
}
