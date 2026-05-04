#!/usr/bin/env node

import { execSync } from 'node:child_process';
import path from 'node:path';

const GENERATED_ROOT = 'frontend/client/src/api/generated';

const OUTPUT_TO_SPEC = new Map([
  ['frontend/client/src/api/generated/l1-types.ts', 'contracts/openapi/layer1-ingestion.json'],
  ['frontend/client/src/api/generated/l2-types.ts', 'contracts/openapi/layer2-extraction.json'],
  ['frontend/client/src/api/generated/l3-types.ts', 'contracts/openapi/layer3-knowledge.json'],
  ['frontend/client/src/api/generated/l4-types.ts', 'contracts/openapi/layer4-agents.json'],
  ['frontend/client/src/api/generated/l5-types.ts', 'contracts/openapi/layer5-ground-truth.json'],
  ['frontend/client/src/api/generated/signals-types.ts', 'contracts/openapi/signals.json'],
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
console.error('  pnpm --dir frontend run generate:types');
console.error('  git add frontend/client/src/api/generated');
console.error('  git commit');
