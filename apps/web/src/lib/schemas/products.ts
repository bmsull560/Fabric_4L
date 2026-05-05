import { z } from "zod";

const UnknownRecordSchema = z.object({}).catchall(z.unknown());

export const ProductFeatureSchema = UnknownRecordSchema;

export const ProductCapabilitySchema = UnknownRecordSchema;

export const ProductSchema = z
  .object({
    id: z.string(),
    name: z.string(),
    description: z.string().nullable().optional(),
    category: z.string().nullable().optional(),
    sku: z.string().nullable().optional(),
    pricing_model: z.string().nullable().optional(),
    target_personas: z.array(z.string()).optional().default([]),
    industries: z.array(z.string()).optional().default([]),
    features: z.array(ProductFeatureSchema).optional().default([]),
    capabilities: z.array(ProductCapabilitySchema).optional().default([]),
    created_at: z.string().nullable().optional(),
    updated_at: z.string().nullable().optional(),
  })
  .passthrough();

export const ProductListResponseSchema = z
  .object({
    products: z.array(ProductSchema),
    total: z.number().int().nonnegative(),
    skip: z.number().int().nonnegative().optional().default(0),
    limit: z.number().int().nonnegative().optional().default(0),
  })
  .passthrough();

export const SignalMatchSchema = z
  .object({
    product: ProductSchema.or(UnknownRecordSchema),
    total_score: z.number(),
    signal_count: z.number().int().nonnegative(),
    top_matches: z.array(UnknownRecordSchema),
  })
  .passthrough();

export const PortfolioSummarySchema = z
  .object({
    total_products: z.number().int().nonnegative(),
    total_features: z.number().int().nonnegative(),
    total_capabilities: z.number().int().nonnegative(),
    categories: z.array(z.string()),
    avg_features_per_product: z.number(),
    avg_capabilities_per_product: z.number(),
  })
  .passthrough();

export const CapabilityCoverageSchema = z
  .object({
    capability: ProductCapabilitySchema,
    products: z.array(ProductSchema.or(UnknownRecordSchema)),
    signal_demand: z.number().int().nonnegative(),
    status: z.string(),
  })
  .passthrough();

export const FeatureMutationResponseSchema = UnknownRecordSchema;

export const CapabilityMutationResponseSchema = UnknownRecordSchema;

export type ProductFeature = z.infer<typeof ProductFeatureSchema>;
export type ProductCapability = z.infer<typeof ProductCapabilitySchema>;
export type Product = z.infer<typeof ProductSchema>;
export type ProductListResponse = z.infer<typeof ProductListResponseSchema>;
export type SignalMatch = z.infer<typeof SignalMatchSchema>;
export type PortfolioSummary = z.infer<typeof PortfolioSummarySchema>;
export type CapabilityCoverage = z.infer<typeof CapabilityCoverageSchema>;
export type FeatureMutationResponse = z.infer<typeof FeatureMutationResponseSchema>;
export type CapabilityMutationResponse = z.infer<typeof CapabilityMutationResponseSchema>;

export function parseProduct(data: unknown): Product {
  return ProductSchema.parse(data);
}

export function parseProductListResponse(data: unknown): ProductListResponse {
  return ProductListResponseSchema.parse(data);
}

export function parseSignalMatchList(data: unknown): SignalMatch[] {
  return z.array(SignalMatchSchema).parse(data);
}

export function parsePortfolioSummary(data: unknown): PortfolioSummary {
  return PortfolioSummarySchema.parse(data);
}

export function parseCapabilityCoverageList(data: unknown): CapabilityCoverage[] {
  return z.array(CapabilityCoverageSchema).parse(data);
}

export function parseFeatureMutationResponse(data: unknown): FeatureMutationResponse {
  return FeatureMutationResponseSchema.parse(data);
}

export function parseCapabilityMutationResponse(data: unknown): CapabilityMutationResponse {
  return CapabilityMutationResponseSchema.parse(data);
}
