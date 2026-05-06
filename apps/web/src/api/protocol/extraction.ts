/**
 * extraction.ts — Tier 1 Protocol Hooks for Layer 2 Extraction API
 *
 * Contract: Hook Architecture Contract §2.1
 * These functions contain ONLY HTTP mechanics + Zod validation.
 * No React Query, no domain logic, no error formatting.
 */
import { z } from 'zod';
import { apiClient, type LayerKey } from '@/api/client';

// ── Request / Response Schemas ───────────────────────────────────────────────

const ExtractionStatusResponseSchema = z.object({
  job_id: z.string(),
  overall_status: z.string(),
  extraction_status: z.string(),
  ingestion_status: z.string().optional(),
  entities_extracted: z.number(),
  relationships_extracted: z.number(),
  last_error: z.string().nullable(),
  started_at: z.string(),
  completed_at: z.string().nullable(),
});

const ExtractedEntitySchema = z.object({
  name: z.string(),
  type: z.enum(['Capability', 'UseCase', 'Persona', 'ValueDriver']),
  confidence: z.number().min(0).max(1),
  source: z.string(),
  status: z.enum(['extracted', 'pending', 'failed']),
});

const ExtractedEntityListSchema = z.array(ExtractedEntitySchema);

// ── Types ────────────────────────────────────────────────────────────────────

export type ExtractionStatusResponse = z.infer<typeof ExtractionStatusResponseSchema>;
export type ExtractedEntity = z.infer<typeof ExtractedEntitySchema>;

// ── Tier 1 Fetchers ──────────────────────────────────────────────────────────

const LAYER: LayerKey = 'l2';

/**
 * Fetch extraction job status.
 * Tier 1: HTTP mechanics + Zod validation only.
 */
export async function fetchExtractionStatus(jobId: string): Promise<ExtractionStatusResponse> {
  const response = await apiClient.get(LAYER, `/v1/extract/status/${jobId}`);
  const parsed = ExtractionStatusResponseSchema.safeParse(response.data);
  if (!parsed.success) {
    throw new Error(`Invalid extraction status response: ${parsed.error.message}`);
  }
  return parsed.data;
}

/**
 * Fetch extracted entities for a job.
 * Tier 1: HTTP mechanics + Zod validation only.
 *
 * NOTE: Backend endpoint is pending (ticket L2-42).
 * When available, this will call GET /v1/extract/{job_id}/entities.
 * Until then, it returns an empty array to prevent mock data in production.
 */
export async function fetchExtractedEntities(jobId: string): Promise<ExtractedEntity[]> {
  // NOTE: Real endpoint is pending backend implementation (ticket L2-42).
  // To enable: Uncomment the commented code below and remove the console.warn.
  // const response = await apiClient.get(LAYER, `/v1/extract/${jobId}/entities`);
  // const parsed = ExtractedEntityListSchema.safeParse(response.data);
  // if (!parsed.success) {
  //   throw new Error(`Invalid extracted entities response: ${parsed.error.message}`);
  // }
  // return parsed.data;

  console.warn(
    `[protocol/extraction] fetchExtractedEntities called for job ${jobId} ` +
    `but backend endpoint is not yet available (ticket L2-42). Returning empty array.`
  );
  return [];
}
