#!/usr/bin/env npx tsx
import { execSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = resolve(__dirname, '..', '..', '..');
const OPENAPI_DIR = resolve(ROOT, 'contracts', 'openapi');
const OUTPUT_DIR = resolve(ROOT, 'packages', 'platform-contract', 'src', 'typescript', 'generated');

const SPECS = [
  'layer1-ingestion.json',
  'layer2-extraction.json',
  'layer3-knowledge.json',
  'layer4-agents.json',
  'layer5-ground-truth.json',
  'layer6-benchmarks.json',
  'signals.json',
];

if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true });

const exports = [];
for (const spec of SPECS) {
  const key = spec.replace('.json', '').replace(/-/g, '_');
  const out = join(OUTPUT_DIR, `${key}.ts`);
  execSync(`pnpm --dir "/workspace/Fabric_4L/apps/web" exec openapi-typescript "${join(OPENAPI_DIR, spec)}" -o "${out}"`, { stdio: 'pipe' });
  const content = readFileSync(out, 'utf8');
  writeFileSync(out, `// @generated from contracts/openapi/${spec}\n` + content);
  exports.push(`export * as ${key} from './${key}';`);
}

writeFileSync(join(OUTPUT_DIR, 'index.ts'), `// @generated\n${exports.join('\n')}\n`);
