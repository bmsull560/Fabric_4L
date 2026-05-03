#!/usr/bin/env node
/**
 * Fails when critical E2E journeys are weakened with test.skip/test.fixme or
 * a backend skip valve. H-06 requires mobile navigation and backend CRUD
 * journeys to fail closed rather than disappearing from CI coverage.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, relative } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(__dirname, '..', '..');

const criticalFiles = [
  'e2e/navigation.spec.ts',
  'e2e/my-models.spec.ts',
  'playwright.config.ts',
  'e2e/global-setup.ts',
];

const forbidden = [
  { pattern: /test\.(skip|fixme)\s*\(/, label: 'test.skip/test.fixme' },
  { pattern: /\btest\.skip\s*\(/, label: 'test.skip' },
  { pattern: /\btest\.fixme\s*\(/, label: 'test.fixme' },
  { pattern: /\bSKIP_BACKEND_TESTS\b/, label: 'SKIP_BACKEND_TESTS backend skip valve' },
  { pattern: /Mobile navigation.*skipped|not yet implemented in AppShell/i, label: 'stale mobile-navigation skipped claim' },
];

const requiredEvidence = [
  {
    file: 'playwright.config.ts',
    pattern: /name:\s*['"]backend-integrated['"]/,
    label: 'backend-integrated Playwright project',
  },
  {
    file: 'playwright.config.ts',
    pattern: /grep:\s*\/@backend\//,
    label: '@backend-only backend-integrated project filter',
  },
  {
    file: 'playwright.config.ts',
    pattern: /globalSetup:\s*['"]\.\/e2e\/global-setup\.ts['"]/,
    label: 'backend deterministic global setup wiring',
  },
  {
    file: 'e2e/my-models.spec.ts',
    pattern: /PLAYWRIGHT_BACKEND_URL is required for the @backend My Models CRUD journey/,
    label: 'fail-closed backend URL requirement in My Models CRUD journey',
  },
  {
    file: 'e2e/global-setup.ts',
    pattern: /seed-e2e-data/,
    label: 'deterministic backend seed execution',
  },
];

const failures = [];
for (const file of criticalFiles) {
  const path = resolve(webRoot, file);
  const text = readFileSync(path, 'utf8');
  for (const { pattern, label } of forbidden) {
    if (pattern.test(text)) {
      failures.push(`${relative(webRoot, path)} contains forbidden ${label}`);
    }
  }
}

for (const { file, pattern, label } of requiredEvidence) {
  const path = resolve(webRoot, file);
  const text = readFileSync(path, 'utf8');
  if (!pattern.test(text)) {
    failures.push(`${relative(webRoot, path)} is missing required ${label}`);
  }
}

if (failures.length > 0) {
  console.error('Critical E2E journey coverage must fail closed.');
  for (const failure of failures) {
    console.error(` - ${failure}`);
  }
  process.exit(1);
}

console.log('Critical E2E journey guard passed: no skipped mobile or backend CRUD journeys, and backend-integrated product-confidence wiring is present.');
