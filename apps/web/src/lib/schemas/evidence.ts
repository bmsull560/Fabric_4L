import { z } from "zod";

const StringArraySchema = z.array(z.string());
const NumericRecordSchema = z.record(z.string(), z.number());

export const EvidenceStatusSchema = z.enum(["created", "updated", "deleted"]);

export const CaseStudyOutcomeSchema = z
  .object({
    metric: z.string(),
    before_value: z.string().nullable().optional(),
    after_value: z.string().nullable().optional(),
    improvement_pct: z.number().nullable().optional(),
    time_to_achieve_days: z.number().int().nullable().optional(),
  })
  .passthrough();

export const CaseStudySchema = z
  .object({
    id: z.string(),
    title: z.string(),
    evidence_type: z.string().nullable().optional(),
    content: z.string().nullable().optional(),
    summary: z.string().nullable().optional(),
    industry: z.string().nullable().optional(),
    company_name: z.string().nullable().optional(),
    company_size: z.string().nullable().optional(),
    products_used: StringArraySchema.optional().default([]),
    pain_signals_addressed: StringArraySchema.optional().default([]),
    outcomes: z.array(CaseStudyOutcomeSchema).optional().default([]),
    time_to_value_days: z.number().int().nullable().optional(),
    deal_size_usd: z.number().nullable().optional(),
    published_date: z.string().nullable().optional(),
    tags: StringArraySchema.optional().default([]),
    created_at: z.string().nullable().optional(),
    updated_at: z.string().nullable().optional(),
    linked_products: StringArraySchema.optional().default([]),
    linked_signals: StringArraySchema.optional().default([]),

    // Legacy frontend-only fields are tolerated for seeded data and older callers.
    customer_name: z.string().nullable().optional(),
    product_ids: StringArraySchema.optional().default([]),
    challenge: z.string().nullable().optional(),
    solution: z.string().nullable().optional(),
    outcome: z.string().nullable().optional(),
    metrics_before: NumericRecordSchema.optional().default({}),
    metrics_after: NumericRecordSchema.optional().default({}),
    improvement_pct: NumericRecordSchema.optional().default({}),
    published: z.boolean().nullable().optional(),
  })
  .passthrough();

export const CaseStudyListResponseSchema = z
  .object({
    items: z.array(CaseStudySchema),
    total: z.number().int().nonnegative(),
    offset: z.number().int().nonnegative(),
    limit: z.number().int().nonnegative(),
  })
  .passthrough();

export const CaseStudyMutationResponseSchema = z
  .object({
    id: z.string(),
    title: z.string(),
    industry: z.string().nullable().optional(),
    status: EvidenceStatusSchema.extract(["created", "updated"]),
  })
  .passthrough();

export const DeleteCaseStudyResponseSchema = z
  .object({
    id: z.string(),
    status: EvidenceStatusSchema.extract(["deleted"]),
  })
  .passthrough();

export const EvidenceStatsResponseSchema = z.record(
  z.string(),
  z.number().int().nonnegative()
);

export const BulkImportErrorSchema = z
  .object({
    index: z.number().int().nonnegative(),
    title: z.string(),
    error: z.string(),
  })
  .passthrough();

export const BulkImportResponseSchema = z
  .object({
    total: z.number().int().nonnegative(),
    created: z.number().int().nonnegative(),
    errors: z.array(BulkImportErrorSchema),
  })
  .passthrough();

export const EvidenceSearchResultSchema = z
  .object({
    evidence_id: z.string(),
    evidence_type: z.string(),
    title: z.string(),
    match_score: z.number().int().min(0).max(100),
    match_reasoning: z.string(),
    relevance_quote: z.string().nullable().optional(),
  })
  .passthrough();

export const EvidenceSearchResponseSchema = z
  .object({
    query: z.string(),
    total: z.number().int().nonnegative(),
    results: z.array(EvidenceSearchResultSchema),
  })
  .passthrough();

export type EvidenceStatus = z.infer<typeof EvidenceStatusSchema>;
export type CaseStudyOutcome = z.infer<typeof CaseStudyOutcomeSchema>;
export type CaseStudy = z.infer<typeof CaseStudySchema>;
export type CaseStudyListResponse = z.infer<typeof CaseStudyListResponseSchema>;
export type CaseStudyMutationResponse = z.infer<
  typeof CaseStudyMutationResponseSchema
>;
export type DeleteCaseStudyResponse = z.infer<
  typeof DeleteCaseStudyResponseSchema
>;
export type EvidenceStatsResponse = z.infer<typeof EvidenceStatsResponseSchema>;
export type IndustryStats = EvidenceStatsResponse;
export type ProductStats = EvidenceStatsResponse;
export type BulkImportError = z.infer<typeof BulkImportErrorSchema>;
export type BulkImportResponse = z.infer<typeof BulkImportResponseSchema>;
export type EvidenceSearchResult = z.infer<typeof EvidenceSearchResultSchema>;
export type EvidenceSearchResponse = z.infer<
  typeof EvidenceSearchResponseSchema
>;

export function parseCaseStudy(data: unknown): CaseStudy {
  return CaseStudySchema.parse(data);
}

export function parseCaseStudyListResponse(
  data: unknown
): CaseStudyListResponse {
  return CaseStudyListResponseSchema.parse(data);
}

export function parseCaseStudyMutationResponse(
  data: unknown
): CaseStudyMutationResponse {
  return CaseStudyMutationResponseSchema.parse(data);
}

export function parseDeleteCaseStudyResponse(
  data: unknown
): DeleteCaseStudyResponse {
  return DeleteCaseStudyResponseSchema.parse(data);
}

export function parseEvidenceStatsResponse(
  data: unknown
): EvidenceStatsResponse {
  return EvidenceStatsResponseSchema.parse(data);
}

export function parseBulkImportResponse(data: unknown): BulkImportResponse {
  return BulkImportResponseSchema.parse(data);
}

export function parseEvidenceSearchResponse(
  data: unknown
): EvidenceSearchResponse {
  return EvidenceSearchResponseSchema.parse(data);
}
