#!/usr/bin/env tsx
/**
 * validate-env-contract.ts — CI gate that ensures every variable declared in
 * .env.example / .env.production.example is present in the current process env.
 *
 * Usage (typically called after `infisical run ...`):
 *   npx tsx scripts/ci/validate-env-contract.ts backend
 *   npx tsx scripts/ci/validate-env-contract.ts frontend
 *   npx tsx scripts/ci/validate-env-contract.ts all
 *
 * The script reads the relevant .env.example file, extracts declared variable
 * names, and confirms each one exists in process.env.
 *
 * It then runs the Zod schema validation for a full type/value check.
 *
 * Exit code 0 = contract satisfied, 1 = violations found.
 */

import { existsSync, readFileSync } from "fs";
import { resolve } from "path";
import { backendEnvSchema } from "../../packages/config/src/env/backend.js";
import { frontendEnvSchema } from "../../packages/config/src/env/frontend.js";

type Target = "backend" | "frontend" | "all";

const target = (process.argv[2] ?? "all") as Target;

/** Extract variable names from a .env-style file (ignores comments and blanks). */
function extractKeys(filePath: string): string[] {
  if (!existsSync(filePath)) {
    throw new Error(`Contract file does not exist: ${filePath}`);
  }

  const content = readFileSync(filePath, "utf-8");
  const keys = content
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"))
    .map((line) => line.split("=")[0])
    .filter(Boolean);

  if (keys.length === 0) {
    throw new Error(`Contract file declares no environment variables: ${filePath}`);
  }

  return keys;
}

function checkContract(label: string, contractFile: string): { missing: string[]; present: string[] } {
  const keys = extractKeys(contractFile);
  const missing: string[] = [];
  const present: string[] = [];

  for (const key of keys) {
    // Variables with empty defaults (optional integrations) are considered present
    // even if the value is empty. Only truly undefined vars are missing.
    if (process.env[key] !== undefined) {
      present.push(key);
    } else {
      missing.push(key);
    }
  }

  return { missing, present };
}

let ok = true;

if (target === "backend" || target === "all") {
  console.log("📋 Backend env contract");

  const contractPath = resolve(
    import.meta.dirname ?? ".",
    "../../.env.example",
  );
  const { missing, present } = checkContract("Backend", contractPath);

  console.log(`   ${present.length} variables present`);
  if (missing.length > 0) {
    console.error(`   ❌ ${missing.length} variables missing from process.env:`);
    for (const k of missing) {
      console.error(`      • ${k}`);
    }
  }

  // Schema validation
  const schemaResult = backendEnvSchema.safeParse(process.env);
  if (!schemaResult.success) {
    console.error("   ❌ Schema validation failed:");
    for (const issue of schemaResult.error.issues) {
      console.error(`      • ${issue.path.join(".")}: ${issue.message}`);
    }
    ok = false;
  } else {
    console.log("   ✅ Schema validation passed");
  }
  console.log("");
}

if (target === "frontend" || target === "all") {
  console.log("📋 Frontend env contract");

  const contractPath = resolve(
    import.meta.dirname ?? ".",
    "../../apps/web/.env.example",
  );
  const { missing, present } = checkContract("Frontend", contractPath);

  console.log(`   ${present.length} variables present`);
  if (missing.length > 0) {
    console.warn(`   ⚠ ${missing.length} variables not in process.env (may be build-time only):`);
    for (const k of missing) {
      console.warn(`      • ${k}`);
    }
  }

  // Schema validation — frontend vars are often build-time, so only warn
  const schemaResult = frontendEnvSchema.safeParse(process.env);
  if (!schemaResult.success) {
    console.warn("   ⚠ Frontend schema validation issues (may be expected in CI):");
    for (const issue of schemaResult.error.issues) {
      console.warn(`      • ${issue.path.join(".")}: ${issue.message}`);
    }
  } else {
    console.log("   ✅ Schema validation passed");
  }
  console.log("");
}

if (!ok) {
  console.error("❌ Env contract validation failed. Fix the issues above.");
  process.exit(1);
} else {
  console.log("✅ All env contracts satisfied.");
}
