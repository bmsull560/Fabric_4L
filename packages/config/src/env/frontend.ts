import { z } from "zod";
import { boolStringSchema, parseEnvOrThrow } from "./shared.js";

const pathPrefixSchema = z.string().trim().min(1).refine((value) => value.startsWith("/"), {
  message: "must start with /",
});

export const frontendEnvSchema = z.object({
  VITE_API_BASE: pathPrefixSchema,
  VITE_L1_PREFIX: pathPrefixSchema,
  VITE_L2_PREFIX: pathPrefixSchema,
  VITE_L3_PREFIX: pathPrefixSchema,
  VITE_L4_PREFIX: pathPrefixSchema,
  VITE_L5_PREFIX: pathPrefixSchema,
  VITE_L6_PREFIX: pathPrefixSchema,
  VITE_ENABLE_CRM_SYNC: boolStringSchema,
  VITE_CRM_PROVIDER: z.enum(["salesforce", "hubspot", "pipedrive", "zoho"]),
  VITE_CRM_API_PROXY: pathPrefixSchema,
  VITE_ENABLE_C1_REPORTS: boolStringSchema,
  VITE_USE_MOCKS: boolStringSchema,
});

export type FrontendEnv = z.infer<typeof frontendEnvSchema>;

export function loadFrontendEnv(env: Record<string, unknown>): FrontendEnv {
  return parseEnvOrThrow(frontendEnvSchema, env);
}
