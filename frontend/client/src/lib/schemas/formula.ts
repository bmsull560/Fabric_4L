/**
 * Formula Zod Schemas
 *
 * Runtime validation for Formula API responses.
 * These schemas enforce data integrity at the trust boundary.
 */
import { z } from 'zod';

export const FormulaStatusSchema = z.enum(['active', 'draft', 'pending', 'deprecated', 'archived']);

export const FormulaTypeSchema = z.enum(['simple', 'composite', 'derived']);

export const FormulaSchema = z.object({
  id: z.string(),
  formula_id: z.string(),
  name: z.string().min(1, 'Formula name cannot be empty'),
  description: z.string().optional(),
  domain: z.string().optional(),
  formula_type: FormulaTypeSchema.optional(),
  pack_id: z.string().optional(),
  pack_name: z.string().optional(),
  version: z.string(),
  status: FormulaStatusSchema,
  owner: z.string().optional(),
  updated_at: z.string(),
  created_at: z.string(),
  used_in_count: z.number().int().min(0),
  governance_score: z.number().min(0).max(1).optional(),
  last_reviewed: z.string().optional(),
  reviewers: z.array(z.string()).optional(),
  expression: z.string().optional(),
  variables: z.array(z.string()).optional(),
});

export const FormulaListSchema = z.array(FormulaSchema);

export const ApprovalStatusSchema = z.enum(['pending', 'approved', 'rejected']);

export const ApprovalRequestSchema = z.object({
  id: z.string(),
  formula_id: z.string(),
  formula_name: z.string(),
  submitted_by: z.string(),
  submitted_at: z.string(),
  change_summary: z.string(),
  previous_version: z.string(),
  status: ApprovalStatusSchema,
});

export const ApprovalRequestListSchema = z.array(ApprovalRequestSchema);

export const FormulaEvaluationResultSchema = z.object({
  result: z.number(),
  unit: z.string(),
  confidence: z.number().min(0).max(1),
  calculation_steps: z.array(z.object({
    step: z.number(),
    operation: z.string(),
    result: z.string(),
  })),
  formula_used: z.string(),
});

// Inferred TypeScript types
export type Formula = z.infer<typeof FormulaSchema>;
export type FormulaStatus = z.infer<typeof FormulaStatusSchema>;
export type ApprovalRequest = z.infer<typeof ApprovalRequestSchema>;
export type FormulaEvaluationResult = z.infer<typeof FormulaEvaluationResultSchema>;
