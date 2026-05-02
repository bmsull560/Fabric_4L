/**
 * Variable Zod Schemas
 *
 * Runtime validation for Variable API responses.
 * These schemas enforce data integrity at the trust boundary.
 */
import { z } from 'zod';

export const VariableTypeSchema = z.enum(['rate', 'currency', 'integer', 'float', 'boolean', 'string']);

export const SourceTypeSchema = z.enum(['CRM', 'Billing', 'ERP', 'Manual', 'Model', 'API', 'Database']);

export const ValidationStatusSchema = z.enum(['validated', 'pending', 'failed', 'deprecated']);

export const ValidRangeSchema = z.object({
  min: z.number(),
  max: z.number(),
}).refine((data) => data.min <= data.max, {
  message: 'Min must be less than or equal to max',
});

export const VariableSchema = z.object({
  id: z.string(),
  variable_id: z.string(),
  name: z.string().min(1, 'Variable name cannot be empty'),
  display_name: z.string().min(1, 'Display name cannot be empty'),
  description: z.string().optional(),
  type: VariableTypeSchema,
  unit: z.string(),
  source: SourceTypeSchema,
  binding: z.string(),
  binding_path: z.string().optional(),
  default_value: z.string().optional(),
  valid_range: ValidRangeSchema.optional(),
  used_in_count: z.number().int().min(0),
  validation_status: ValidationStatusSchema,
  validation_message: z.string().optional(),
  tags: z.array(z.string()),
  created_at: z.string(),
  updated_at: z.string(),
  version: z.string(),
});

export const VariableListSchema = z.array(VariableSchema);

export const SourceBindingSchema = z.object({
  id: z.string(),
  name: z.string(),
  source_type: SourceTypeSchema,
  connection_string: z.string().optional(),
  status: z.enum(['connected', 'disconnected', 'error']),
  last_sync: z.string().optional(),
  variables_bound: z.number().int().min(0),
  error_message: z.string().optional(),
});

export const SourceBindingListSchema = z.array(SourceBindingSchema);

export const VariableStatsSchema = z.object({
  total: z.number().int().min(0),
  validated: z.number().int().min(0),
  pending: z.number().int().min(0),
  failed: z.number().int().min(0),
  manual_sources: z.number().int().min(0),
  avg_usage: z.number().min(0),
});

// Inferred TypeScript types
export type Variable = z.infer<typeof VariableSchema>;
export type VariableType = z.infer<typeof VariableTypeSchema>;
export type SourceType = z.infer<typeof SourceTypeSchema>;
export type ValidationStatus = z.infer<typeof ValidationStatusSchema>;
export type SourceBinding = z.infer<typeof SourceBindingSchema>;
export type VariableStats = z.infer<typeof VariableStatsSchema>;
