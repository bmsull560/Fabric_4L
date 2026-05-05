import { z } from "zod";

const UnknownRecordSchema = z.object({}).catchall(z.unknown());
const StringArraySchema = z.array(z.string());

export const CompetitiveStatusSchema = z.enum([
  "created",
  "updated",
  "deleted",
  "recorded",
]);

export const WinLossOutcomeSchema = z.enum([
  "won",
  "lost",
  "win",
  "loss",
  "no_decision",
]);

export const CompetingProductSchema = z
  .object({
    id: z.string().nullable().optional(),
    name: z.string().nullable().optional(),
    overlap_score: z.number().nullable().optional(),
  })
  .passthrough();

export const BattlecardPreviewSchema = z
  .object({
    id: z.string().nullable().optional(),
    product_id: z.string().nullable().optional(),
    positioning: z.string().nullable().optional(),
  })
  .passthrough();

export const CompetitorSchema = z
  .object({
    id: z.string(),
    name: z.string(),
    description: z.string().nullable().optional(),
    domain: z.string().nullable().optional(),
    website: z.string().nullable().optional(),
    founded_year: z.number().int().nullable().optional(),
    strengths: StringArraySchema.optional().default([]),
    weaknesses: StringArraySchema.optional().default([]),
    market_position: z.string().nullable().optional(),
    pricing_tier: z.string().nullable().optional(),
    target_segments: StringArraySchema.optional().default([]),
    products_competed: StringArraySchema.optional().default([]),
    product_overlap_count: z.number().int().nonnegative().optional(),
    competing_products: z.array(CompetingProductSchema).optional().default([]),
    battlecards: z.array(BattlecardPreviewSchema).optional().default([]),
    status: CompetitiveStatusSchema.optional(),
    entity_type: z.string().nullable().optional(),
    tenant_id: z.string().nullable().optional(),
    created_at: z.string().nullable().optional(),
    updated_at: z.string().nullable().optional(),
  })
  .passthrough();

export const CompetitorListResponseSchema = z
  .object({
    competitors: z.array(CompetitorSchema),
    total: z.number().int().nonnegative(),
    skip: z.number().int().nonnegative().optional().default(0),
    limit: z.number().int().nonnegative().optional().default(0),
  })
  .passthrough();

export const ObjectionHandlersSchema = z.union([
  z.array(z.string()),
  z.record(z.string(), z.string()),
  z.array(z.record(z.string(), z.string())),
]);

export const BattlecardSchema = z
  .object({
    id: z.string(),
    competitor_id: z.string(),
    product_id: z.string(),
    positioning: z.string().nullable().optional(),
    differentiators: StringArraySchema.optional().default([]),
    key_differentiators: StringArraySchema.optional().default([]),
    objection_handlers: ObjectionHandlersSchema.optional().default([]),
    talk_tracks: StringArraySchema.optional().default([]),
    win_themes: StringArraySchema.optional().default([]),
    trap_questions: StringArraySchema.optional().default([]),
    status: CompetitiveStatusSchema.optional(),
    entity_type: z.string().nullable().optional(),
    tenant_id: z.string().nullable().optional(),
    last_reviewed_at: z.string().nullable().optional(),
    created_at: z.string().nullable().optional(),
    updated_at: z.string().nullable().optional(),
  })
  .passthrough();

export const WinLossRecordSchema = z
  .object({
    id: z.string(),
    outcome: WinLossOutcomeSchema,
    competitor_id: z.string().nullable().optional(),
    account_id: z.string().nullable().optional(),
    product_id: z.string().nullable().optional(),
    deal_size: z.number().nullable().optional(),
    deal_size_usd: z.number().nullable().optional(),
    reason: z.string().nullable().optional(),
    notes: z.string().nullable().optional(),
    industry: z.string().nullable().optional(),
    deal_date: z.string().nullable().optional(),
    recorded_at: z.string().nullable().optional(),
    status: CompetitiveStatusSchema.optional(),
  })
  .passthrough();

export const WinLossSummaryCompetitorSchema = z
  .object({
    id: z.string().nullable().optional(),
    name: z.string().nullable().optional(),
    market_position: z.string().nullable().optional(),
  })
  .passthrough();

export const WinLossSummaryEntrySchema = z
  .object({
    competitor: WinLossSummaryCompetitorSchema,
    wins: z.number().int().nonnegative(),
    losses: z.number().int().nonnegative(),
    total_deals: z.number().int().nonnegative(),
    win_rate: z.number(),
    won_revenue: z.number().nullable().optional(),
    lost_revenue: z.number().nullable().optional(),
  })
  .passthrough();

export const WinLossSummaryResponseSchema = z
  .object({
    competitors: z.array(WinLossSummaryEntrySchema),
    total_competitors: z.number().int().nonnegative(),
  })
  .passthrough();

export const LandscapeCompetitorSchema = z
  .object({
    id: z.string().nullable().optional(),
    name: z.string().nullable().optional(),
    market_position: z.string().nullable().optional(),
    pricing_tier: z.string().nullable().optional(),
  })
  .passthrough();

export const LandscapeEntrySchema = z
  .object({
    competitor: LandscapeCompetitorSchema,
    product_overlaps: z.number().int().nonnegative(),
    wins: z.number().int().nonnegative(),
    losses: z.number().int().nonnegative(),
    win_rate: z.number(),
    overlap_score: z.number(),
  })
  .passthrough();

export const CompetitiveLandscapeResponseSchema = z
  .object({
    landscape: z.array(LandscapeEntrySchema),
    total_competitors: z.number().int().nonnegative(),
    total_wins: z.number().int().nonnegative(),
    total_losses: z.number().int().nonnegative(),
    overall_win_rate: z.number(),
  })
  .passthrough();

export type CompetitiveStatus = z.infer<typeof CompetitiveStatusSchema>;
export type WinLossOutcome = z.infer<typeof WinLossOutcomeSchema>;
export type CompetingProduct = z.infer<typeof CompetingProductSchema>;
export type BattlecardPreview = z.infer<typeof BattlecardPreviewSchema>;
export type Competitor = z.infer<typeof CompetitorSchema>;
export type CompetitorListResponse = z.infer<
  typeof CompetitorListResponseSchema
>;
export type Battlecard = z.infer<typeof BattlecardSchema>;
export type WinLossRecord = z.infer<typeof WinLossRecordSchema>;
export type WinLossSummaryEntry = z.infer<typeof WinLossSummaryEntrySchema>;
export type WinLossSummaryResponse = z.infer<
  typeof WinLossSummaryResponseSchema
>;
export type LandscapeEntry = z.infer<typeof LandscapeEntrySchema>;
export type CompetitiveLandscapeResponse = z.infer<
  typeof CompetitiveLandscapeResponseSchema
>;

export function parseCompetitor(data: unknown): Competitor {
  return CompetitorSchema.parse(data);
}

export function parseCompetitorListResponse(
  data: unknown
): CompetitorListResponse {
  return CompetitorListResponseSchema.parse(data);
}

export function parseBattlecardList(data: unknown): Battlecard[] {
  return z.array(BattlecardSchema).parse(data);
}

export function parseBattlecard(data: unknown): Battlecard {
  return BattlecardSchema.parse(data);
}

export function parseWinLossRecord(data: unknown): WinLossRecord {
  return WinLossRecordSchema.parse(data);
}

export function parseWinLossSummaryResponse(
  data: unknown
): WinLossSummaryResponse {
  return WinLossSummaryResponseSchema.parse(data);
}

export function parseCompetitiveLandscapeResponse(
  data: unknown
): CompetitiveLandscapeResponse {
  return CompetitiveLandscapeResponseSchema.parse(data);
}
