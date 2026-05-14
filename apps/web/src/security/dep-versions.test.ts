/**
 * Regression guard: ensures the resolved mermaid version in the lockfile
 * is not vulnerable (CVE-2026-41148, CVE-2026-41150, CVE-2026-41159,
 * GHSA-ghcm-xqfw-q4vr — all patched in mermaid >=11.15.0).
 *
 * If this test fails, a vulnerable mermaid version has re-entered the
 * dependency tree. Fix by ensuring the root package.json pnpm.overrides
 * contains `"mermaid": ">=11.15.0"` and re-running pnpm install.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const MINIMUM_SAFE_MERMAID = [11, 15, 0] as const;

function parseSemver(version: string): [number, number, number] {
  const parts = version.split(".").map(Number);
  if (parts.length < 3 || parts.some(isNaN)) {
    throw new Error(`Cannot parse semver: ${version}`);
  }
  return [parts[0], parts[1], parts[2]];
}

function isAtLeast(
  actual: [number, number, number],
  minimum: readonly [number, number, number],
): boolean {
  for (let i = 0; i < 3; i++) {
    if (actual[i] > minimum[i]) return true;
    if (actual[i] < minimum[i]) return false;
  }
  return true; // equal
}

describe("dependency version security gates", () => {
  it("mermaid resolves to >=11.15.0 (no CVE-2026-41148/41150/41159)", () => {
    // Lockfile lives two levels above apps/web
    const lockfilePath = resolve(__dirname, "../../../../pnpm-lock.yaml");
    const lockfile = readFileSync(lockfilePath, "utf-8");

    // Extract all resolved mermaid versions from the lockfile
    const mermaidVersionPattern = /^\s{2}mermaid@(\d+\.\d+\.\d+):/gm;
    const resolvedVersions: string[] = [];
    let match: RegExpExecArray | null;

    while ((match = mermaidVersionPattern.exec(lockfile)) !== null) {
      resolvedVersions.push(match[1]);
    }

    expect(
      resolvedVersions.length,
      "No mermaid version found in pnpm-lock.yaml — lockfile may be stale",
    ).toBeGreaterThan(0);

    const vulnerableVersions = resolvedVersions.filter((v) => {
      try {
        return !isAtLeast(parseSemver(v), MINIMUM_SAFE_MERMAID);
      } catch {
        return false;
      }
    });

    expect(
      vulnerableVersions,
      `Vulnerable mermaid version(s) found in lockfile: ${vulnerableVersions.join(", ")}. ` +
        `All resolved versions must be >=11.15.0. ` +
        `Ensure root package.json pnpm.overrides contains "mermaid": ">=11.15.0" and re-run pnpm install.`,
    ).toHaveLength(0);
  });
});
