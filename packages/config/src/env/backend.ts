import { z } from "zod";
import { logLevelSchema, nodeEnvSchema, parseEnvOrThrow, portSchema } from "./shared.js";

const requiredSecretSchema = z
  .string()
  .trim()
  .min(1, "must be set")
  .refine((value) => !/^CHANGE_ME/i.test(value), "must not use a CHANGE_ME placeholder");

export const backendEnvSchema = z.object({
  NODE_ENV: z.string().trim().min(1, "NODE_ENV must be set"),
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

/**
 * Relaxed schema for development/test environments.
 * Allows wildcard CORS and does not require all production-only fields.
 */
const devBackendEnvSchema = z.object({
  NODE_ENV: z.string().trim().min(1),
  LOG_LEVEL: logLevelSchema,
  PORT: portSchema.optional(),
  DATABASE_URL: z.string().trim().min(1, "DATABASE_URL must be set"),
  REDIS_URL: z.string().trim().min(1, "REDIS_URL must be set"),
  JWT_SECRET: z.string().trim().min(1, "JWT_SECRET must be set"),
  API_KEY_HMAC_SECRET: z.string().trim().min(1, "API_KEY_HMAC_SECRET must be set"),
  SERVICE_AUTH_SECRET: z.string().trim().min(1, "SERVICE_AUTH_SECRET must be set"),
  OPENAI_API_KEY: z.string().trim().min(1, "OPENAI_API_KEY must be set"),
  NEO4J_PASSWORD: z.string().trim().min(1, "NEO4J_PASSWORD must be set"),
  CORS_ORIGINS: z.string().trim().min(1, "CORS_ORIGINS must be set"),
});

export type BackendEnv = z.infer<typeof backendEnvSchema>;

export function loadBackendEnv(env: Record<string, unknown>): BackendEnv {
  return parseEnvOrThrow(backendEnvSchema, env);
}

// ───────────────────────────────────────────────────────────────────────────
// Production-like fail-closed validation
// ───────────────────────────────────────────────────────────────────────────

const PRODUCTION_LIKE_ENVS = new Set(["production", "staging"]);
const DEV_ENVIRONMENTS = new Set(["development", "test", "testing", "ci", "local", "dev"]);

function isProductionLikeEnvironment(nodeEnv: string): boolean {
  const env = nodeEnv.trim().toLowerCase();
  return PRODUCTION_LIKE_ENVS.has(env) || !DEV_ENVIRONMENTS.has(env);
}

export interface ProductionSafetyViolation {
  control: string;
  message: string;
}

/**
 * Fail-closed validator for required production dependencies.
 *
 * Authentication, persistence, encryption, API keys, CORS origins, and tenant
 * isolation must never downgrade to mock, fallback, or development behavior in
 * ``production`` or ``staging`` modes (or any unknown environment).
 *
 * @throws Error when any required control is missing or misconfigured.
 */
export function validateBackendEnvForProductionLike(
  env: Record<string, unknown>,
): void {
  const nodeEnv = String(env.NODE_ENV ?? "development").trim().toLowerCase();
  const isProductionLike = isProductionLikeEnvironment(nodeEnv);

  const violations: ProductionSafetyViolation[] = [];

  // Authentication
  const jwtSecret = String(env.JWT_SECRET ?? "").trim();
  if (!jwtSecret) {
    violations.push({ control: "authentication", message: "JWT_SECRET is required in production-like environments" });
  } else if (jwtSecret.length < 32) {
    violations.push({ control: "authentication", message: `JWT_SECRET is too short (${jwtSecret.length} chars); use at least 32 characters` });
  } else if (/^changeme|password|secret|test-secret|default$/i.test(jwtSecret)) {
    violations.push({ control: "authentication", message: "JWT_SECRET appears to be a placeholder or weak value" });
  }

  if (String(env.ALLOW_INSECURE_DEV_AUTH_BYPASS ?? "").toLowerCase() === "true") {
    violations.push({ control: "authentication", message: "ALLOW_INSECURE_DEV_AUTH_BYPASS must be false or unset in production-like environments" });
  }
  if (String(env.JWT_FALLBACK_TO_QUERY_PARAM ?? "").toLowerCase() === "true") {
    violations.push({ control: "authentication", message: "JWT_FALLBACK_TO_QUERY_PARAM must be false or unset in production-like environments" });
  }

  // Persistence
  const databaseUrl = String(env.DATABASE_URL ?? "").trim();
  if (!databaseUrl) {
    violations.push({ control: "persistence", message: "DATABASE_URL is required in production-like environments" });
  } else if (databaseUrl.startsWith("sqlite")) {
    violations.push({ control: "persistence", message: "SQLite is not permitted in production-like environments; use PostgreSQL" });
  } else {
    try {
      const url = new URL(databaseUrl);
      const host = (url.hostname || "").toLowerCase();
      const user = (url.username || "").toLowerCase();
      if (host === "localhost" || host === "127.0.0.1" || host === "::1") {
        violations.push({ control: "persistence", message: `DATABASE_URL host '${host}' is localhost; use a network-resident database` });
      }
      if (["postgres", "admin", "root", "user", "dbuser"].includes(user)) {
        violations.push({ control: "persistence", message: `DATABASE_URL user '${user}' is a default/weak account; create a dedicated role` });
      }
      if (["postgres", "rdsadmin", "cloudsqladmin", "azure_superuser"].includes(user)) {
        violations.push({ control: "persistence", message: `DATABASE_URL user '${user}' is a superuser; superusers bypass RLS` });
      }
    } catch {
      violations.push({ control: "persistence", message: "DATABASE_URL is malformed" });
    }
  }

  if (String(env.MOCK_PERSISTENCE ?? "").toLowerCase() === "true") {
    violations.push({ control: "persistence", message: "MOCK_PERSISTENCE must be false or unset in production-like environments" });
  }

  // Encryption
  const masterKey = String(env.CREDENTIALS_MASTER_KEY ?? "").trim();
  if (!masterKey) {
    violations.push({ control: "encryption", message: "CREDENTIALS_MASTER_KEY is required in production-like environments" });
  }
  if (String(env.ALLOW_EPHEMERAL_ENCRYPTION ?? "").toLowerCase() === "true") {
    violations.push({ control: "encryption", message: "ALLOW_EPHEMERAL_ENCRYPTION must be false or unset in production-like environments" });
  }

  // API Keys
  const apiKeyHmac = String(env.API_KEY_HMAC_SECRET ?? "").trim();
  if (!apiKeyHmac) {
    violations.push({ control: "api_keys", message: "API_KEY_HMAC_SECRET is required in production-like environments" });
  } else if (apiKeyHmac.length < 32) {
    violations.push({ control: "api_keys", message: `API_KEY_HMAC_SECRET is too short (${apiKeyHmac.length} chars); use at least 32 characters` });
  }

  // CORS Origins
  const corsOrigins = String(env.CORS_ORIGINS ?? "").trim();
  if (!corsOrigins) {
    violations.push({ control: "cors", message: "CORS_ORIGINS is required in production-like environments" });
  } else {
    const origins = corsOrigins.split(",").map((o) => o.trim()).filter(Boolean);
    if (origins.length === 0) {
      violations.push({ control: "cors", message: "CORS_ORIGINS is empty after parsing" });
    } else if (origins.includes("*")) {
      violations.push({ control: "cors", message: "CORS_ORIGINS must not contain wildcard '*'" });
    } else {
      for (const origin of origins) {
        if (origin.includes("*")) {
          violations.push({ control: "cors", message: `CORS origin '${origin}' contains a wildcard; use exact URLs` });
        }
        if (origin.startsWith("http://")) {
          violations.push({ control: "cors", message: `CORS origin '${origin}' must use HTTPS in production-like environments` });
        }
      }
    }
  }

  // Tenant Isolation
  const defaultTenant = String(env.DEFAULT_TENANT_ID ?? "").trim();
  if (!defaultTenant) {
    violations.push({ control: "tenant_isolation", message: "DEFAULT_TENANT_ID is required in production-like environments" });
  } else if (defaultTenant.toLowerCase() === "default") {
    violations.push({ control: "tenant_isolation", message: "DEFAULT_TENANT_ID must not use the literal value 'default'" });
  } else if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(defaultTenant)) {
    violations.push({ control: "tenant_isolation", message: `DEFAULT_TENANT_ID '${defaultTenant}' is not a valid UUID` });
  }

  const serviceAuth = String(env.SERVICE_AUTH_SECRET ?? "").trim();
  if (!serviceAuth) {
    violations.push({ control: "tenant_isolation", message: "SERVICE_AUTH_SECRET is required in production-like environments" });
  } else if (serviceAuth.length < 32) {
    violations.push({ control: "tenant_isolation", message: `SERVICE_AUTH_SECRET is too short (${serviceAuth.length} chars); use at least 32 characters` });
  }

  if (String(env.MULTI_TENANT_MODE ?? "").toLowerCase() === "false") {
    violations.push({ control: "tenant_isolation", message: "MULTI_TENANT_MODE must not be explicitly disabled in production-like environments" });
  }

  // External Providers
  if (String(env.LLM_PROVIDER ?? "").trim().toLowerCase() === "mock") {
    violations.push({ control: "external_providers", message: "LLM_PROVIDER='mock' is not permitted in production-like environments" });
  }
  if (String(env.ALLOW_MOCK_LLM ?? "").toLowerCase() === "true") {
    violations.push({ control: "external_providers", message: "ALLOW_MOCK_LLM must be false or unset in production-like environments" });
  }

  // Debug / Development Flags
  if (String(env.DEBUG ?? "").toLowerCase() === "true") {
    violations.push({ control: "debug", message: "DEBUG must be false or unset in production-like environments" });
  }
  if (String(env.SEED_DEMO_DATA ?? "").toLowerCase() === "true") {
    violations.push({ control: "debug", message: "SEED_DEMO_DATA must be false or unset in production-like environments" });
  }

  if (isProductionLike && violations.length > 0) {
    const lines = violations.map((v) => `  • [${v.control}] ${v.message}`);
    throw new Error(
      `Production safety validation failed for environment='${nodeEnv}':\n${lines.join("\n")}`,
    );
  }

  // Run appropriate schema validation so type-narrowing still works
  if (isProductionLike) {
    parseEnvOrThrow(backendEnvSchema, env);
  } else {
    parseEnvOrThrow(devBackendEnvSchema, env);
  }
}
