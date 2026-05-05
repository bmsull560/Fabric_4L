/**
 * @fabric/config — Shared environment validation for Value Fabric.
 *
 * Usage:
 *   import { loadBackendEnv } from "@fabric/config/env/backend";
 *   import { loadFrontendEnv } from "@fabric/config/env/frontend";
 */

export {
  backendEnvSchema,
  loadBackendEnv,
  validateBackendEnvForProductionLike,
  type BackendEnv,
  type ProductionSafetyViolation,
} from "./env/backend.js";
export { frontendEnvSchema, loadFrontendEnv, type FrontendEnv } from "./env/frontend.js";
export { testEnvSchema, type TestEnv } from "./env/test.js";
export {
  nodeEnvSchema,
  portSchema,
  logLevelSchema,
  boolStringSchema,
  parseEnvOrThrow,
} from "./env/shared.js";
