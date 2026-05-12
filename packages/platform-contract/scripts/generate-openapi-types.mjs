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
const WEB_APP_DIR = resolve(ROOT, 'apps', 'web');
const WEB_OUTPUT_DIR = resolve(WEB_APP_DIR, 'src', 'api', 'generated');

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
if (!existsSync(WEB_OUTPUT_DIR)) mkdirSync(WEB_OUTPUT_DIR, { recursive: true });


const WEB_LAYER_DIRS = {
  layer1_ingestion: 'l1',
  layer2_extraction: 'l2',
  layer3_knowledge: 'l3',
  layer4_agents: 'l4',
  layer5_ground_truth: 'l5',
  layer6_benchmarks: 'l6',
  signals: 'signals',
};

const exports = [];
const webExports = [];
for (const spec of SPECS) {
  const key = spec.replace('.json', '').replace(/-/g, '_');
  const out = join(OUTPUT_DIR, `${key}.ts`);
  execSync(`pnpm exec openapi-typescript "${join(OPENAPI_DIR, spec)}" -o "${out}"`, {
    cwd: WEB_APP_DIR,
    stdio: 'pipe',
  });
  const content = readFileSync(out, 'utf8');
  writeFileSync(out, `// @generated from contracts/openapi/${spec}\n` + content);
  exports.push(`export * as ${key} from './${key}.js';`);

  const webDir = WEB_LAYER_DIRS[key];
  if (webDir) {
    const webLayerDir = join(WEB_OUTPUT_DIR, webDir);
    if (!existsSync(webLayerDir)) mkdirSync(webLayerDir, { recursive: true });
    const webOut = join(webLayerDir, 'index.ts');
    writeFileSync(webOut, [
      '// @generated — This file is auto-generated from the OpenAPI spec.',
      '// Do not edit manually. Run `pnpm run generate:types` to regenerate.',
      `// Source: contracts/openapi/${spec}`,
      content,
    ].join('\n'));
    webExports.push(`export * as ${webDir} from './${webDir}';`);
  }
}

writeFileSync(join(OUTPUT_DIR, 'index.ts'), `// @generated\n${exports.join('\n')}\n`);


writeFileSync(join(WEB_OUTPUT_DIR, 'index.ts'), [
  '// @generated — Barrel export for all generated API types.',
  '// Do not edit manually. Run `pnpm run generate:types` to regenerate.',
  '',
  ...webExports,
  '',
].join('\n'));
