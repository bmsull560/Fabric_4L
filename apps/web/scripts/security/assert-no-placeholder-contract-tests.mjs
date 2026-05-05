#!/usr/bin/env node
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const contractDir = fileURLToPath(new URL('../../src/api/__tests__/contract/', import.meta.url));
const forbiddenPatterns = [
  {
    pattern: /expect\(\s*true\s*\)\.toBe\(\s*true\s*\)/,
    message: 'trivial expect(true).toBe(true) placeholder',
  },
  {
    pattern: /placeholder/i,
    message: 'placeholder marker in contract test',
  },
];

function listContractTests(directory) {
  return readdirSync(directory).flatMap((entry) => {
    const path = join(directory, entry);
    const stat = statSync(path);
    if (stat.isDirectory()) {
      return listContractTests(path);
    }
    return path.endsWith('.contract.test.ts') ? [path] : [];
  });
}

const failures = [];
for (const file of listContractTests(contractDir)) {
  const source = readFileSync(file, 'utf8');
  for (const { pattern, message } of forbiddenPatterns) {
    if (pattern.test(source)) {
      failures.push(`${file}: ${message}`);
    }
  }

  // Require OpenAPI-backed validation either directly or via _helpers.ts.
  // The openapi-drift.contract.test.ts suite covers full schema drift;
  // individual files may reuse the canonical validators through _helpers.
  const hasDirectOpenApiAssertion =
    /assertOpenApiSchema\(/.test(source) ||
    /assertCanonicalSchema\(/.test(source);
  const importsOpenApiHelpers =
    /from ['"`]._helpers['"`]/.test(source) ||
    /from ['"`].\/openapi-validator['"`]/.test(source);
  if (!hasDirectOpenApiAssertion && !importsOpenApiHelpers) {
    failures.push(
      `${file}: missing OpenAPI-backed validation (import from ./_helpers or use assertOpenApiSchema/assertCanonicalSchema)`
    );
  }

  // Require a dedicated auth-failure describe block
  const hasAuthFailureBlock =
    /describe\(['"`](.*)auth failures?.*['"`],/.test(source);
  if (!hasAuthFailureBlock) {
    failures.push(
      `${file}: missing dedicated auth-failure describe block (e.g. describe('Contract: ... auth failures', ...))`
    );
  }
}

if (failures.length > 0) {
  console.error('Frontend contract test violations found.');
  for (const failure of failures) {
    console.error(` - ${failure}`);
  }
  process.exit(1);
}

console.log('Frontend contract tests contain no placeholder assertions and meet coverage requirements.');
