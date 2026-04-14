#!/usr/bin/env tsx
/**
 * verify-secrets.ts — Verify that Infisical paths contain the required secrets.
 *
 * Usage (requires infisical CLI and login):
 *   npx tsx scripts/infisical/verify-secrets.ts --env=dev
 *   npx tsx scripts/infisical/verify-secrets.ts --env=staging
 *   npx tsx scripts/infisical/verify-secrets.ts --env=prod
 *
 * This script does NOT read secret values. It only checks that the expected
 * keys exist in each Infisical path for the given environment.
 */

import { execSync } from "child_process";

const envArg = process.argv.find((a) => a.startsWith("--env="));
const env = envArg?.split("=")[1] ?? "dev";

/** Required backend secrets (Class A & B) that must exist in Infisical. */
const REQUIRED_BACKEND_KEYS = [
  "OPENAI_API_KEY",
  "JWT_SECRET",
  "API_KEY_HMAC_SECRET",
  "NEO4J_PASSWORD",
];

/** Optional but expected backend keys — warning only if missing. */
const OPTIONAL_BACKEND_KEYS = [
  "ANTHROPIC_API_KEY",
  "PINECONE_API_KEY",
  "BROWSERBASE_API_KEY",
  "FIRECRAWL_API_KEY",
  "CRM_API_KEY",
  "THESYS_API_KEY",
];

interface SecretEntry {
  key: string;
}

function listKeys(path: string, environment: string): string[] {
  try {
    const output = execSync(
      `infisical secrets --env=${environment} --path=${path} --plain 2>/dev/null`,
      { encoding: "utf-8" },
    );
    // Parse key names from the output (first column of each line)
    return output
      .trim()
      .split("\n")
      .filter(Boolean)
      .map((line) => line.split(/\s+/)[0])
      .filter(Boolean);
  } catch {
    return [];
  }
}

console.log(`🔐 Verifying Infisical secrets for environment: ${env}`);
console.log("=".repeat(60));

const backendPath = `/fabric-4l/value-fabric/${env}`;
console.log(`\n📂 ${backendPath}`);

const backendKeys = listKeys(backendPath, env);

if (backendKeys.length === 0) {
  console.error("   ❌ Could not read secrets — check CLI login and path access");
  process.exit(1);
}

let hasErrors = false;

for (const key of REQUIRED_BACKEND_KEYS) {
  if (backendKeys.includes(key)) {
    console.log(`   ✅ ${key}`);
  } else {
    console.error(`   ❌ ${key} — MISSING (required)`);
    hasErrors = true;
  }
}

for (const key of OPTIONAL_BACKEND_KEYS) {
  if (backendKeys.includes(key)) {
    console.log(`   ✅ ${key}`);
  } else {
    console.warn(`   ⚠️  ${key} — not set (optional)`);
  }
}

console.log("");

if (hasErrors) {
  console.error("❌ Required secrets are missing. Add them in Infisical before proceeding.");
  process.exit(1);
} else {
  console.log("✅ All required secrets are present.");
}
