import { z } from "zod";

export const ServiceStatusSchema = z.enum([
  "healthy",
  "degraded",
  "unhealthy",
  "unknown",
]);

export const ServiceHealthSchema = z.object({
  name: z.string(),
  status: ServiceStatusSchema,
  version: z.string(),
  uptime_seconds: z.number(),
  last_check_at: z.string(),
  response_time_ms: z.number(),
  error_message: z.string().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export const SystemHealthSchema = z.object({
  overall_status: ServiceStatusSchema,
  checked_at: z.string(),
  services: z.array(ServiceHealthSchema),
  summary: z.object({
    healthy: z.number(),
    degraded: z.number(),
    unhealthy: z.number(),
    unknown: z.number(),
    total: z.number(),
  }),
});

export const HealthAlertSchema = z.object({
  id: z.string(),
  service_name: z.string(),
  severity: z.enum(["critical", "warning", "info"]),
  message: z.string(),
  started_at: z.string(),
  resolved_at: z.string().optional(),
  acknowledged: z.boolean().optional(),
});

export const HealthAlertListSchema = z.array(HealthAlertSchema);

export type ServiceStatus = z.infer<typeof ServiceStatusSchema>;
export type ServiceHealth = z.infer<typeof ServiceHealthSchema>;
export type SystemHealth = z.infer<typeof SystemHealthSchema>;
export type HealthAlert = z.infer<typeof HealthAlertSchema>;

export function parseSystemHealth(data: unknown): SystemHealth {
  return SystemHealthSchema.parse(data);
}

export function parseHealthAlerts(data: unknown): HealthAlert[] {
  return HealthAlertListSchema.parse(data);
}
