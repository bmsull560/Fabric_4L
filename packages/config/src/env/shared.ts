import { z, type ZodTypeAny } from "zod";

export const nodeEnvSchema = z.enum(["development", "test", "staging", "production"]).default("development");

export const portSchema = z.coerce.number().int().min(1).max(65535);

export const logLevelSchema = z.enum(["trace", "debug", "info", "warn", "error", "fatal"]).default("info");

export const boolStringSchema = z
  .union([z.boolean(), z.string()])
  .transform((value) => {
    if (typeof value === "boolean") {
      return value;
    }
    return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
  });

export function parseEnvOrThrow<TSchema extends ZodTypeAny>(
  schema: TSchema,
  env: Record<string, unknown>,
): z.infer<TSchema> {
  const result = schema.safeParse(env);
  if (result.success) {
    return result.data;
  }

  const details = result.error.issues
    .map((issue) => `${issue.path.join(".") || "<root>"}: ${issue.message}`)
    .join("; ");
  throw new Error(`Environment validation failed: ${details}`);
}
