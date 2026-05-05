#!/usr/bin/env npx tsx
/**
 * OpenAPI → TypeScript Type Generation Pipeline
 *
 * Generates TypeScript types from the backend OpenAPI specifications
 * located in contracts/openapi/. This script is the implementation
 * of Contract B (Type Synchronization Contract).
 *
 * Usage:
 *   pnpm run generate:types          # Generate all layers
 *   npx tsx scripts/generate-api-types.ts l3 l4   # Generate specific layers
 *
 * @generated — Do not edit generated output files manually.
 */

import { execSync } from 'child_process';
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ── Configuration ────────────────────────────────────────────────────────────

const ROOT = resolve(__dirname, '..', '..', '..');
const OPENAPI_DIR = resolve(ROOT, 'contracts', 'openapi');
const OUTPUT_DIR = resolve(ROOT, 'apps', 'web', 'src', 'api', 'generated');

interface LayerSpec {
  key: string;
  specFile: string;
  outputDir: string;
  description: string;
}

const LAYERS: LayerSpec[] = [
  {
    key: 'l1',
    specFile: 'layer1-ingestion.json',
    outputDir: 'l1',
    description: 'Layer 1 — Ingestion',
  },
  {
    key: 'l2',
    specFile: 'layer2-extraction.json',
    outputDir: 'l2',
    description: 'Layer 2 — Extraction',
  },
  {
    key: 'l3',
    specFile: 'layer3-knowledge.json',
    outputDir: 'l3',
    description: 'Layer 3 — Knowledge Graph',
  },
  {
    key: 'l4',
    specFile: 'layer4-agents.json',
    outputDir: 'l4',
    description: 'Layer 4 — Agents',
  },
  {
    key: 'l5',
    specFile: 'layer5-ground-truth.json',
    outputDir: 'l5',
    description: 'Layer 5 — Ground Truth',
  },
  {
    key: 'l6',
    specFile: 'layer6-benchmarks.json',
    outputDir: 'l6',
    description: 'Layer 6 — Benchmarks',
  },
  {
    key: 'signals',
    specFile: 'signals.json',
    outputDir: 'signals',
    description: 'Signals Service',
  },
];

// ── Helpers ──────────────────────────────────────────────────────────────────

function log(msg: string): void {
  console.log(`[generate-api-types] ${msg}`);
}

function error(msg: string): void {
  console.error(`[generate-api-types] ERROR: ${msg}`);
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  // Parse CLI args for optional layer filtering
  const args = process.argv.slice(2);
  const requestedLayers = args.length > 0 ? args : LAYERS.map((l) => l.key);

  // Ensure output directory exists
  if (!existsSync(OUTPUT_DIR)) {
    mkdirSync(OUTPUT_DIR, { recursive: true });
    log(`Created output directory: ${OUTPUT_DIR}`);
  }

  const results: { layer: string; status: 'success' | 'skipped' | 'failed'; message: string }[] = [];

  for (const layer of LAYERS) {
    if (!requestedLayers.includes(layer.key)) {
      continue;
    }

    const specPath = resolve(OPENAPI_DIR, layer.specFile);
    const layerOutputDir = resolve(OUTPUT_DIR, layer.outputDir);
    const outputPath = join(layerOutputDir, 'index.ts');

    // Check if spec file exists
    if (!existsSync(specPath)) {
      error(`Spec file not found: ${specPath}`);
      results.push({ layer: layer.key, status: 'skipped', message: `Spec file missing: ${layer.specFile}` });
      continue;
    }

    // Ensure layer output directory exists
    if (!existsSync(layerOutputDir)) {
      mkdirSync(layerOutputDir, { recursive: true });
    }

    log(`Generating types for ${layer.description} ...`);
    log(`  Source: ${specPath}`);
    log(`  Output: ${outputPath}`);

    try {
      execSync(
        `npx openapi-typescript "${specPath}" -o "${outputPath}"`,
        {
          cwd: resolve(ROOT, 'apps', 'web'),
          stdio: 'pipe',
          timeout: 60_000,
        }
      );

      // Prepend the @generated header
      if (existsSync(outputPath)) {
        const content = readFileSync(outputPath, 'utf-8');
        const header = [
          '// @generated — This file is auto-generated from the OpenAPI spec.',
          '// Do not edit manually. Run `pnpm run generate:types` to regenerate.',
          `// Source: contracts/openapi/${layer.specFile}`,
          '',
        ].join('\n');

        writeFileSync(outputPath, header + content);
        log(`  ✓ Generated ${layer.outputDir}/index.ts`);
        results.push({ layer: layer.key, status: 'success', message: `${layer.outputDir}/index.ts` });
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      error(`Failed to generate ${layer.key}: ${errMsg}`);
      results.push({ layer: layer.key, status: 'failed', message: errMsg });
    }
  }

  // Write the barrel index
  const indexLines = [
    '// @generated — Barrel export for all generated API types.',
    '// Do not edit manually. Run `pnpm run generate:types` to regenerate.',
    '',
  ];

  for (const layer of LAYERS) {
    const layerOutputDir = resolve(OUTPUT_DIR, layer.outputDir);
    const indexPath = join(layerOutputDir, 'index.ts');
    if (existsSync(indexPath)) {
      indexLines.push(`export * as ${layer.key} from './${layer.outputDir}';`);
    }
  }
  indexLines.push('');

  writeFileSync(resolve(OUTPUT_DIR, 'index.ts'), indexLines.join('\n'));
  log('✓ Generated barrel index (index.ts)');

  // Summary
  log('');
  log('━━━ Generation Summary ━━━');
  for (const r of results) {
    const icon = r.status === 'success' ? '✓' : r.status === 'skipped' ? '⊘' : '✗';
    log(`  ${icon} ${r.layer}: ${r.message}`);
  }

  const failures = results.filter((r) => r.status === 'failed');
  if (failures.length > 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  error(String(err));
  process.exit(1);
});
