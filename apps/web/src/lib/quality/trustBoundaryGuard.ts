import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";

export type TrustBoundaryRuleKind = "response-data-cast" | "direct-json-parse";

export interface TrustBoundaryRule {
  readonly kind: TrustBoundaryRuleKind;
  readonly description: string;
  readonly files: readonly string[];
  readonly pattern: RegExp;
  readonly remediation: string;
}

export interface TrustBoundaryViolation {
  readonly file: string;
  readonly line: number;
  readonly column: number;
  readonly kind: TrustBoundaryRuleKind;
  readonly description: string;
  readonly remediation: string;
  readonly snippet: string;
}

const MIGRATED_RESPONSE_BOUNDARY_FILES = [
  "src/hooks/useProducts.ts",
  "src/hooks/useGroundTruthGovernance.ts",
  "src/hooks/useCompetitiveIntel.ts",
  "src/hooks/useEvidence.ts",
  "src/hooks/useHealthMonitor.ts",
  "src/hooks/useIntegrations.ts",
  "src/hooks/useProvenance.ts",
  "src/hooks/useWorkflows.ts",
] as const;

const MIGRATED_STREAM_BOUNDARY_FILES = [
  "src/agui/AgentEventClient.ts",
  "src/hooks/useJobStream.ts",
  "src/hooks/useWorkflows.ts",
] as const;

export const TRUST_BOUNDARY_RULES: readonly TrustBoundaryRule[] = [
  {
    kind: "response-data-cast",
    description:
      "Response data must be parsed by the migrated domain schema before it is returned from a protected hook boundary.",
    files: MIGRATED_RESPONSE_BOUNDARY_FILES,
    pattern: /\bresponse\.data\s+as\b/,
    remediation:
      "Replace the assertion with the schema-owned parse* helper for this boundary.",
  },
  {
    kind: "direct-json-parse",
    description:
      "Stream payload JSON must be parsed through the centralized schema boundary helper before dispatch.",
    files: MIGRATED_STREAM_BOUNDARY_FILES,
    pattern: /\bJSON\.parse\s*\(/,
    remediation:
      "Use parseJsonObject(), parseAgentEventFromJson(), parseJobStreamEventFromJson(), or the workflow stream parser.",
  },
];

function normalizePath(path: string): string {
  return path.split(sep).join("/");
}

function getLineAndColumn(
  source: string,
  index: number
): { line: number; column: number } {
  const prefix = source.slice(0, index);
  const lines = prefix.split("\n");
  return {
    line: lines.length,
    column: lines[lines.length - 1].length + 1,
  };
}

function getLine(source: string, line: number): string {
  return source.split("\n")[line - 1]?.trim() ?? "";
}

export function scanSource(
  file: string,
  source: string,
  rules: readonly TrustBoundaryRule[] = TRUST_BOUNDARY_RULES
): TrustBoundaryViolation[] {
  const normalizedFile = normalizePath(file);
  const violations: TrustBoundaryViolation[] = [];

  for (const rule of rules) {
    const protectedFiles = new Set(rule.files.map(normalizePath));
    if (!protectedFiles.has(normalizedFile)) {
      continue;
    }

    const pattern = new RegExp(
      rule.pattern.source,
      rule.pattern.flags.includes("g")
        ? rule.pattern.flags
        : `${rule.pattern.flags}g`
    );
    let match = pattern.exec(source);
    while (match !== null) {
      const index = match.index;
      const { line, column } = getLineAndColumn(source, index);
      violations.push({
        file: normalizedFile,
        line,
        column,
        kind: rule.kind,
        description: rule.description,
        remediation: rule.remediation,
        snippet: getLine(source, line),
      });
      match = pattern.exec(source);
    }
  }

  return violations;
}

function collectProtectedFiles(
  webRoot: string,
  rules: readonly TrustBoundaryRule[]
): string[] {
  return Array.from(new Set(rules.flatMap(rule => rule.files))).filter(file =>
    existsSync(resolve(webRoot, file))
  );
}

function collectSourceFiles(directory: string): string[] {
  return readdirSync(directory).flatMap(entry => {
    const path = join(directory, entry);
    const stat = statSync(path);
    if (stat.isDirectory()) {
      return collectSourceFiles(path);
    }
    return /\.[cm]?[jt]sx?$/.test(path) ? [path] : [];
  });
}

export interface ScanRepositoryOptions {
  readonly webRoot: string;
  readonly rules?: readonly TrustBoundaryRule[];
  readonly includeAllSourceFiles?: boolean;
}

export function scanRepository({
  webRoot,
  rules = TRUST_BOUNDARY_RULES,
  includeAllSourceFiles = false,
}: ScanRepositoryOptions): TrustBoundaryViolation[] {
  const root = resolve(webRoot);
  const files = includeAllSourceFiles
    ? collectSourceFiles(resolve(root, "src"))
    : collectProtectedFiles(root, rules).map(file => resolve(root, file));

  return files.flatMap(absoluteFile => {
    const relativeFile = normalizePath(relative(root, absoluteFile));
    const source = readFileSync(absoluteFile, "utf8");
    return scanSource(relativeFile, source, rules);
  });
}

export function formatViolations(
  violations: readonly TrustBoundaryViolation[]
): string {
  if (violations.length === 0) {
    return "Trust-boundary enforcement passed: migrated boundaries contain no unsafe response.data casts or direct stream JSON.parse calls.";
  }

  const details = violations.map(violation =>
    [
      `${violation.file}:${violation.line}:${violation.column}`,
      `${violation.kind}: ${violation.description}`,
      `snippet: ${violation.snippet}`,
      `remediation: ${violation.remediation}`,
    ].join("\n  ")
  );

  return [
    "Trust-boundary enforcement violations found.",
    ...details.map(detail => ` - ${detail}`),
  ].join("\n");
}
