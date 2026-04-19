/**
 * ValuePack Zod Schemas
 *
 * Runtime validation for ValuePack API responses.
 * These schemas enforce data integrity at the trust boundary.
 */
import { z } from 'zod';

export const PackStatusSchema = z.enum(['active', 'draft', 'archived', 'published']);

export const PackScopeSchema = z.enum(['global', 'tenant']);

export const ValuePackSchema = z.object({
  id: z.string(),
  pack_id: z.string(),
  name: z.string().min(1, 'Pack name cannot be empty'),
  industry: z.string(),
  description: z.string().optional(),
  driver_count: z.number().int().min(0),
  formula_count: z.number().int().min(0),
  benchmark_count: z.number().int().min(0),
  workflow_count: z.number().int().min(0),
  status: PackStatusSchema,
  scope: PackScopeSchema,
  updated_at: z.string(),
  created_at: z.string().optional(),
  version: z.string().optional(),
  owner: z.string().optional(),
  category: z.string().optional(),
});

export const ValuePackListSchema = z.array(ValuePackSchema);

// Inferred TypeScript types
export type ValuePack = z.infer<typeof ValuePackSchema>;
export type PackStatus = z.infer<typeof PackStatusSchema>;
export type PackScope = z.infer<typeof PackScopeSchema>;
