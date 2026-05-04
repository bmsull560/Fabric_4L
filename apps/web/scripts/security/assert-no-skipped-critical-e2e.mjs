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
  'package.json',
  'e2e/helpers/validation-program.ts',
  'e2e/journeys/j6-account-prospect-lifecycle.spec.ts',
  'e2e/journeys/j7-value-realization-and-calculation.spec.ts',
  'e2e/journeys/j8-approval-review-gates.spec.ts',
  'e2e/journeys/j9-agent-grounding-governance.spec.ts',
  'e2e/journeys/j10-layer-ui-validation.spec.ts',
  'e2e/security/tenant-isolation-validation.spec.ts',
  'e2e/resilience/operational-resilience.spec.ts',
  'e2e/collaboration/collaboration-notifications-tasks.spec.ts',
  'e2e/export-workflows.spec.ts',
  'e2e/personas/persona-journeys.spec.ts',
  'e2e/journeys/j11-golden-path-business-lifecycle.spec.ts',
  'e2e/integrations/crm-external-integrations.spec.ts',
  'e2e/journeys/j1-golden-path-deep.spec.ts',
  'e2e/journeys/j7-calculation-evidence-deep.spec.ts',
  'e2e/journeys/j8-approval-review-deep.spec.ts',
  'e2e/journeys/j9-agent-grounding-deep.spec.ts',
  'e2e/journeys/j10-layer-ui-validation-deep.spec.ts',
  'e2e/security/tenant-isolation-deep.spec.ts',
  'e2e/export/export-workflows-deep.spec.ts',
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
  {
    file: 'package.json',
    pattern: /test:e2e:validation/,
    label: 'dedicated validation-program E2E command',
  },
  {
    file: 'package.json',
    pattern: /j11-golden-path-business-lifecycle\.spec\.ts/,
    label: 'golden-path validation suite wiring',
  },
  {
    file: 'package.json',
    pattern: /crm-external-integrations\.spec\.ts/,
    label: 'CRM validation suite wiring',
  },
  {
    file: 'e2e/journeys/j9-agent-grounding-governance.spec.ts',
    pattern: /SECURITY-PROMPT-INJECTION-001/,
    label: 'agent prompt-injection validation coverage',
  },
  {
    file: 'e2e/security/tenant-isolation-validation.spec.ts',
    pattern: /SEC-TENANT-001/,
    label: 'tenant isolation validation coverage',
  },
  {
    file: 'e2e/export-workflows.spec.ts',
    pattern: /EXPORT-GATE-001/,
    label: 'approval-gated export validation coverage',
  },
  {
    file: 'e2e/journeys/j11-golden-path-business-lifecycle.spec.ts',
    pattern: /test_golden_path_account_to_approved_business_case @backend/,
    label: 'backend-integrated golden path validation coverage',
  },
  {
    file: 'package.json',
    pattern: /test:e2e:validation:deep/,
    label: 'dedicated deep validation-program E2E command',
  },
  {
    file: 'e2e/journeys/j1-golden-path-deep.spec.ts',
    pattern: /GP-DEEP-001/,
    label: 'deep golden path validation coverage',
  },
  {
    file: 'e2e/security/tenant-isolation-deep.spec.ts',
    pattern: /SEC-DEEP-001/,
    label: 'deep tenant isolation validation coverage',
  },
  {
    file: 'e2e/journeys/j9-agent-grounding-deep.spec.ts',
    pattern: /AG-DEEP-001/,
    label: 'deep agent grounding validation coverage',
  },
  {
    file: 'e2e/export/export-workflows-deep.spec.ts',
    pattern: /EXPORT-DEEP-001/,
    label: 'deep export gate validation coverage',
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

console.log('Critical E2E journey guard passed: no skipped mobile, backend CRUD, or validation-program journeys, and product-confidence wiring is present.');
