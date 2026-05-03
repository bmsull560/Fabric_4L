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
}

if (failures.length > 0) {
  console.error('Placeholder frontend contract tests are not allowed.');
  for (const failure of failures) {
    console.error(` - ${failure}`);
  }
  process.exit(1);
}

console.log('Frontend contract tests contain no placeholder assertions.');
