#!/usr/bin/env tsx
/**
 * check-env.ts — Validate environment variables against the shared schema.
 *
 * Usage:
 *   npx tsx scripts/check-env.ts backend   # validate backend env
 *   npx tsx scripts/check-env.ts frontend  # validate frontend env
 *   npx tsx scripts/check-env.ts all       # validate both
 *
 * Exit code 0 = valid, 1 = validation errors.
 */

import { backendEnvSchema } from "../../packages/config/src/env/backend.js";
import { frontendEnvSchema } from "../../packages/config/src/env/frontend.js";

type Target = "backend" | "frontend" | "all";

const target = (process.argv[2] ?? "all") as Target;

function validate(
  label: string,
  schema: { safeParse: (v: unknown) => { success: boolean; error?: { issues: Array<{ path: (string | number)[]; message: string }> } } },
  env: Record<string, string | undefined>,
): boolean {
  const result = schema.safeParse(env);
  if (result.success) {
    console.log(`✅ ${label}: all variables valid`);
    return true;
  }
  console.error(`❌ ${label}: validation failed`);
  for (const issue of result.error!.issues) {
    console.error(`   • ${issue.path.join(".")}: ${issue.message}`);
  }
  return false;
}

let ok = true;

if (target === "backend" || target === "all") {
  ok = validate("Backend", backendEnvSchema, process.env) && ok;
}

if (target === "frontend" || target === "all") {
  ok = validate("Frontend", frontendEnvSchema, process.env) && ok;
}

if (!ok) {
  console.error("\nFix the issues above and re-run.");
  process.exit(1);
}
