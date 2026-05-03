import { z } from "zod";
import { boolStringSchema, nodeEnvSchema, parseEnvOrThrow } from "./shared.js";

export const testEnvSchema = z.object({
  NODE_ENV: nodeEnvSchema.default("test"),
  CI: boolStringSchema.optional(),
  DATABASE_URL: z.string().trim().min(1).optional(),
  REDIS_URL: z.string().trim().min(1).optional(),
});

export type TestEnv = z.infer<typeof testEnvSchema>;

export function loadTestEnv(env: Record<string, unknown>): TestEnv {
  return parseEnvOrThrow(testEnvSchema, env);
}
