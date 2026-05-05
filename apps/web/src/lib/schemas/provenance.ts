import { z } from "zod";

export const ProvenanceStepSchema = z.object({
  step: z.number(),
  label: z.string(),
  detail: z.string(),
  timestamp: z.string(),
  agent: z.string().optional(),
  entity_id: z.string().optional(),
});

export const ProvenanceTrailSchema = z.object({
  entity_id: z.string(),
  entity_type: z.string(),
  entity_name: z.string(),
  created_at: z.string(),
  source: z.string(),
  extraction_job_id: z.string().optional(),
  steps: z.array(ProvenanceStepSchema),
  confidence_score: z.number().optional(),
});

export const AuditLogEntrySchema = z.object({
  id: z.string(),
  timestamp: z.string(),
  source: z.enum(["provenance", "access_log"]),
  event_type: z.string(),
  entity_id: z.string().optional(),
  entity_type: z.string().optional(),
  action: z.string(),
  agent: z.string(),
  details: z.record(z.string(), z.unknown()),
});

export const AuditLogResponseSchema = z.object({
  entries: z.array(AuditLogEntrySchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

export type ProvenanceStep = z.infer<typeof ProvenanceStepSchema>;
export type ProvenanceTrail = z.infer<typeof ProvenanceTrailSchema>;
export type AuditLogEntry = z.infer<typeof AuditLogEntrySchema>;
export type AuditLogResponse = z.infer<typeof AuditLogResponseSchema>;

export function parseProvenanceTrail(data: unknown): ProvenanceTrail {
  return ProvenanceTrailSchema.parse(data);
}

export function parseAuditLogResponse(data: unknown): AuditLogResponse {
  return AuditLogResponseSchema.parse(data);
}
