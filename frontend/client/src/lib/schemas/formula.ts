/**
 * Formula Zod Schemas
 *
 * Runtime validation for Formula API responses.
 * These schemas enforce data integrity at the trust boundary.
 */
import { z } from 'zod';

export const FormulaStatusSchema = z.enum(['active', 'draft', 'pending', 'deprecated', 'archived']);

export const FormulaTypeSchema = z.enum(['simple', 'composite', 'derived']);

/** Schema for a single calculation step in formula evaluation */
export const CalculationStepSchema = z.object({
  step: z.number().int().min(1, 'Step number must be positive'),
  operation: z.string().min(1, 'Operation description is required'),
  result: z.string(),
});

/** Schema for formula data with governance and versioning */
export const FormulaSchema = z.object({
  id: z.string().uuid('ID must be a valid UUID'),
  formula_id: z.string().min(1, 'Formula ID is required'),
  name: z.string().min(1, 'Formula name cannot be empty'),
  description: z.string().optional(),
  domain: z.string().optional(),
  formula_type: FormulaTypeSchema.optional(),
  pack_id: z.string().optional(),
  pack_name: z.string().optional(),
  version: z.string().regex(/^\d+\.\d+(\.\d+)?$/, 'Version must follow semantic versioning (e.g., 1.0.0)'),
  status: FormulaStatusSchema,
  owner: z.string().email('Owner must be a valid email').optional(),
  updated_at: z.string().datetime({ offset: true }, 'Updated at must be ISO 8601 datetime'),
  created_at: z.string().datetime({ offset: true }, 'Created at must be ISO 8601 datetime'),
  used_in_count: z.number().int().min(0),
  governance_score: z.number().min(0).max(1).optional(),
  last_reviewed: z.string().datetime({ offset: true }, 'Last reviewed must be ISO 8601 datetime').optional(),
  reviewers: z.array(z.string().email('Reviewer must be a valid email')).optional(),
  expression: z.string().optional(),
  variables: z.array(z.string()).optional(),
});

export const FormulaListSchema = z.array(FormulaSchema);

export const ApprovalStatusSchema = z.enum(['pending', 'approved', 'rejected']);

/** Schema for formula approval request workflow */
export const ApprovalRequestSchema = z.object({
  id: z.string().uuid('ID must be a valid UUID'),
  formula_id: z.string(),
  formula_name: z.string().min(1, 'Formula name is required'),
  submitted_by: z.string().email('Submitter must be a valid email'),
  submitted_at: z.string().datetime({ offset: true }, 'Submitted at must be ISO 8601 datetime'),
  change_summary: z.string().min(1, 'Change summary is required'),
  previous_version: z.string().regex(/^\d+\.\d+(\.\d+)?$/, 'Version must follow semantic versioning'),
  status: ApprovalStatusSchema,
});

export const ApprovalRequestListSchema = z.array(ApprovalRequestSchema);

/** Schema for formula evaluation results with calculation trace */
export const FormulaEvaluationResultSchema = z.object({
  result: z.number(),
  unit: z.string(),
  confidence: z.number().min(0).max(1),
  calculation_steps: z.array(CalculationStepSchema),
  formula_used: z.string(),
});

// Inferred TypeScript types with JSDoc for IDE IntelliSense
/** Formula data type with governance and versioning */
export type Formula = z.infer<typeof FormulaSchema>;

/** Formula status lifecycle: draft → pending_validation → active → deprecated */
export type FormulaStatus = z.infer<typeof FormulaStatusSchema>;

/** Formula type classification: simple, composite, or derived */
export type FormulaType = z.infer<typeof FormulaTypeSchema>;

/** Single step in formula calculation trace */
export type CalculationStep = z.infer<typeof CalculationStepSchema>;

/** Formula approval request for governance workflow */
export type ApprovalRequest = z.infer<typeof ApprovalRequestSchema>;

/** Result of formula evaluation with trace and confidence */
export type FormulaEvaluationResult = z.infer<typeof FormulaEvaluationResultSchema>;
