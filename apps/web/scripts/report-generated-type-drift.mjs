#!/usr/bin/env node

import { execSync } from 'node:child_process';
import path from 'node:path';

const GENERATED_ROOTS = [
  'packages/platform-contract/src/typescript/generated',
  'apps/web/src/api/generated',
];

const OUTPUT_TO_SPEC = new Map([
  [
    'packages/platform-contract/src/typescript/generated/layer1_ingestion.ts',
    'contracts/openapi/layer1-ingestion.json',
  ],
  [
    'packages/platform-contract/src/typescript/generated/layer2_extraction.ts',
    'contracts/openapi/layer2-extraction.json',
  ],
  [
    'packages/platform-contract/src/typescript/generated/layer3_knowledge.ts',
    'contracts/openapi/layer3-knowledge.json',
  ],
  [
    'packages/platform-contract/src/typescript/generated/layer4_agents.ts',
    'contracts/openapi/layer4-agents.json',
  ],
  [
    'packages/platform-contract/src/typescript/generated/layer5_ground_truth.ts',
    'contracts/openapi/layer5-ground-truth.json',
  ],
  [
    'packages/platform-contract/src/typescript/generated/layer6_benchmarks.ts',
    'contracts/openapi/layer6-benchmarks.json',
  ],
  [
    'packages/platform-contract/src/typescript/generated/signals.ts',
    'contracts/openapi/signals.json',
  ],
  ['apps/web/src/api/generated/l1/index.ts', 'contracts/openapi/layer1-ingestion.json'],
  ['apps/web/src/api/generated/l2/index.ts', 'contracts/openapi/layer2-extraction.json'],
  ['apps/web/src/api/generated/l3/index.ts', 'contracts/openapi/layer3-knowledge.json'],
  ['apps/web/src/api/generated/l4/index.ts', 'contracts/openapi/layer4-agents.json'],
  ['apps/web/src/api/generated/l5/index.ts', 'contracts/openapi/layer5-ground-truth.json'],
  ['apps/web/src/api/generated/signals/index.ts', 'contracts/openapi/signals.json'],
]);

function run(cmd) {
  return execSync(cmd, { encoding: 'utf-8' }).trim();
}

const repoRoot = run('git rev-parse --show-toplevel');
const changedFilesRaw = run(`git diff --name-only -- ${GENERATED_ROOTS.join(' ')}`);
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
console.error('  pnpm run generate:api');
console.error('  git add packages/platform-contract/src/typescript/generated apps/web/src/api/generated');
console.error('  git commit');
