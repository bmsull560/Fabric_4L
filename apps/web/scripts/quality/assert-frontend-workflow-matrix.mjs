#!/usr/bin/env node
/**
 * Validates the frontend workflow coverage matrix.
 *
 * The matrix is intentionally checked as release evidence, not as prose only.
 * If a critical workflow, route, test file, resilience expectation, or
 * accessibility expectation is removed, this script fails the frontend gate.
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(__dirname, '..', '..');
const matrixPath = resolve(webRoot, 'docs', 'frontend-workflow-coverage-matrix.md');
const matrix = readFileSync(matrixPath, 'utf8');

const requiredEvidence = [
  ['P0-ACCOUNT-LIFECYCLE', /P0-ACCOUNT-LIFECYCLE/, 'account lifecycle workflow row'],
  ['P0-CALC-EVIDENCE', /P0-CALC-EVIDENCE/, 'calculation and evidence workflow row'],
  ['P0-APPROVAL-EXPORT', /P0-APPROVAL-EXPORT/, 'approval and export workflow row'],
  ['P0-AGENT-GOVERNANCE', /P0-AGENT-GOVERNANCE/, 'agent governance workflow row'],
  ['P0-LAYER-VALIDATION', /P0-LAYER-VALIDATION/, 'layer validation workflow row'],
  ['P1-INTELLIGENCE', /P1-INTELLIGENCE/, 'intelligence workspace workflow row'],
  ['P1-STUDIO', /P1-STUDIO/, 'studio workflow row'],
  ['P1-CONTEXT', /P1-CONTEXT/, 'context workflow row'],
  ['P1-SETTINGS', /P1-SETTINGS/, 'settings workflow row'],
  ['P1-PERSONAL', /P1-PERSONAL/, 'personal workflow row'],
  ['P1-INTEGRATIONS', /P1-INTEGRATIONS/, 'integration workflow row'],
  ['j6', /e2e\/journeys\/j6-account-prospect-lifecycle\.spec\.ts/, 'account/prospect lifecycle journey evidence'],
  ['j7', /e2e\/journeys\/j7-value-realization-and-calculation\.spec\.ts/, 'value realization journey evidence'],
  ['j8', /e2e\/journeys\/j8-approval-review-gates\.spec\.ts/, 'approval/review journey evidence'],
  ['j9', /e2e\/journeys\/j9-agent-grounding-governance\.spec\.ts/, 'agent grounding journey evidence'],
  ['j10', /e2e\/journeys\/j10-layer-ui-validation\.spec\.ts/, 'layer UI validation evidence'],
  ['j11', /e2e\/journeys\/j11-golden-path-business-lifecycle\.spec\.ts/, 'golden path lifecycle evidence'],
  ['tenant', /e2e\/security\/tenant-isolation-validation\.spec\.ts/, 'tenant isolation evidence'],
  ['export', /e2e\/export-workflows\.spec\.ts/, 'export workflow evidence'],
  ['persona coverage', /Persona coverage/, 'persona coverage column'],
  ['resilience proof', /Resilience proof/, 'resilience proof column'],
  ['accessibility proof', /Accessibility proof/, 'accessibility proof column'],
  ['watchlist formula', /\/formula-builder/, 'formula builder watchlist'],
  ['watchlist graph', /\/graph-explorer/, 'graph explorer watchlist'],
  ['verify frontend', /verify:frontend/, 'frontend verification gate reference'],
  ['bundle budget', /test:bundle-budget/, 'bundle-budget gate reference'],
];

const failures = requiredEvidence
  .filter(([, pattern]) => !pattern.test(matrix))
  .map(([, , label]) => `Missing ${label}`);

if (failures.length > 0) {
  console.error(`Frontend workflow matrix is incomplete: ${relative(webRoot, matrixPath)}`);
  for (const failure of failures) {
    console.error(` - ${failure}`);
  }
  process.exit(1);
}

console.log(`Frontend workflow matrix passed: ${requiredEvidence.length} release-confidence markers present.`);
