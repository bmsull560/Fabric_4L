import { z } from "zod";
import { logLevelSchema, nodeEnvSchema, parseEnvOrThrow, portSchema } from "./shared.js";

const requiredSecretSchema = z
  .string()
  .trim()
  .min(1, "must be set")
  .refine((value) => !/^CHANGE_ME/i.test(value), "must not use a CHANGE_ME placeholder");

export const backendEnvSchema = z.object({
  NODE_ENV: nodeEnvSchema,
  LOG_LEVEL: logLevelSchema,
  PORT: portSchema.optional(),
  DATABASE_URL: z.string().trim().min(1, "DATABASE_URL must be set"),
  REDIS_URL: z.string().trim().min(1, "REDIS_URL must be set"),
  JWT_SECRET: requiredSecretSchema,
  API_KEY_HMAC_SECRET: requiredSecretSchema,
  SERVICE_AUTH_SECRET: requiredSecretSchema,
  OPENAI_API_KEY: z.string().trim().min(1, "OPENAI_API_KEY must be set"),
  NEO4J_PASSWORD: requiredSecretSchema,
  CORS_ORIGINS: z
    .string()
    .trim()
    .min(1, "CORS_ORIGINS must be set")
    .refine((value) => !value.split(",").map((origin) => origin.trim()).includes("*"), {
      message: "CORS_ORIGINS must not contain wildcard origins",
    }),
});

export type BackendEnv = z.infer<typeof backendEnvSchema>;

export function loadBackendEnv(env: Record<string, unknown>): BackendEnv {
  return parseEnvOrThrow(backendEnvSchema, env);
}
