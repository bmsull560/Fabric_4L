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
];

const forbidden = [
  { pattern: /test\.(skip|fixme)\s*\(/, label: 'test.skip/test.fixme' },
  { pattern: /\btest\.skip\s*\(/, label: 'test.skip' },
  { pattern: /\btest\.fixme\s*\(/, label: 'test.fixme' },
  { pattern: /\bSKIP_BACKEND_TESTS\b/, label: 'SKIP_BACKEND_TESTS backend skip valve' },
  { pattern: /Mobile navigation.*skipped|not yet implemented in AppShell/i, label: 'stale mobile-navigation skipped claim' },
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

if (failures.length > 0) {
  console.error('Critical E2E journey coverage must fail closed.');
  for (const failure of failures) {
    console.error(` - ${failure}`);
  }
  process.exit(1);
}

console.log('Critical E2E journey guard passed: no skipped mobile or backend CRUD journeys.');
