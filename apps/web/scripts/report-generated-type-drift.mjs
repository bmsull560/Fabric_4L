#!/usr/bin/env node

import { execSync } from 'node:child_process';
import path from 'node:path';

const GENERATED_ROOT = 'apps/web/src/api/generated';

const OUTPUT_TO_SPEC = new Map([
  ['apps/web/src/api/generated/l1-types.ts', 'contracts/openapi/layer1-ingestion.json'],
  ['apps/web/src/api/generated/l2-types.ts', 'contracts/openapi/layer2-extraction.json'],
  ['apps/web/src/api/generated/l3-types.ts', 'contracts/openapi/layer3-knowledge.json'],
  ['apps/web/src/api/generated/l4-types.ts', 'contracts/openapi/layer4-agents.json'],
  ['apps/web/src/api/generated/l5-types.ts', 'contracts/openapi/layer5-ground-truth.json'],
  ['apps/web/src/api/generated/signals-types.ts', 'contracts/openapi/signals.json'],
]);

function run(cmd) {
  return execSync(cmd, { encoding: 'utf-8' }).trim();
}

const repoRoot = run('git rev-parse --show-toplevel');
const changedFilesRaw = run(`git diff --name-only -- ${GENERATED_ROOT}`);
const changedFiles = changedFilesRaw
  .split('\n')
  .map((file) => file.trim())
  .filter(Boolean)
  .sort();

if (changedFiles.length === 0) {
  process.exit(0);
}

console.error('Type generation drift details (OpenAPI spec → generated file):');

for (const file of changedFiles) {
  const normalized = file.replaceAll(path.sep, '/');
  const spec = OUTPUT_TO_SPEC.get(normalized);

  if (spec) {
    console.error(`  • ${spec} -> ${normalized}`);
  } else if (normalized.endsWith('/index.ts')) {
    console.error(`  • (barrel export) -> ${normalized}`);
  } else {
    console.error(`  • (unknown spec mapping) -> ${normalized}`);
  }
}

console.error('\nChanged hunks:');
for (const file of changedFiles) {
  const normalized = file.replaceAll(path.sep, '/');
  const output = run(`git diff -- ${normalized}`);
  console.error(`\n--- ${normalized} ---`);
  console.error(output || '(no textual diff output)');
}

console.error(`\nTo fix locally from ${repoRoot}:`);
console.error('  pnpm --dir apps/web run generate:types');
console.error('  git add apps/web/src/api/generated');
console.error('  git commit');
