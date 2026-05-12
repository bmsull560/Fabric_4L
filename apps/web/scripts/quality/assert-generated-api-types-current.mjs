#!/usr/bin/env node
import { execSync } from 'node:child_process';

const repoRoot = execSync('git rev-parse --show-toplevel', { encoding: 'utf8' }).trim();
const run = (command) => execSync(command, { cwd: repoRoot, stdio: 'pipe', encoding: 'utf8' });

try {
  run('pnpm run generate:api');
} catch (error) {
  const stderr = error instanceof Error && 'stderr' in error ? String(error.stderr ?? '') : '';
  const stdout = error instanceof Error && 'stdout' in error ? String(error.stdout ?? '') : '';
  console.error('Failed to regenerate OpenAPI types.');
  if (stdout.trim()) console.error(stdout.trim());
  if (stderr.trim()) console.error(stderr.trim());
  process.exit(1);
}

const diff = run('git status --porcelain -- apps/web/src/api/generated apps/web/src/types packages/platform-contract/src/typescript/generated');
if (diff.trim()) {
  console.error('Generated API types are out of date with current OpenAPI contracts.');
  console.error('Run `pnpm run generate:api` from the repository root and commit the generated changes.');
  console.error('\nDetected drift in:');
  for (const line of diff.trim().split('\n')) {
    console.error(`- ${line}`);
  }
  process.exit(1);
}

console.log('Generated API types are up to date.');
