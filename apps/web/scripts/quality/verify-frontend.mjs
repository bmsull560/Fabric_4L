#!/usr/bin/env node
/**
 * Frontend release-confidence verifier.
 *
 * This script intentionally runs gates in dependency order so engineers get a
 * fast, actionable failure before expensive workflow suites. Use
 * FRONTEND_VERIFY_MODE=full to include the broad validation E2E suite in CI.
 */
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(__dirname, '..', '..');
const mode = process.env.FRONTEND_VERIFY_MODE || 'standard';

const gates = [
  ['Workflow matrix', ['pnpm', ['run', 'test:workflow-matrix']]],
  ['TypeScript', ['pnpm', ['run', 'check']]],
  ['Contract tests', ['pnpm', ['run', 'test:contracts']]],
  ['Unit/component tests', ['pnpm', ['run', 'test']]],
  ['Critical E2E guard', ['pnpm', ['run', 'test:e2e:guard']]],
  ['Production build', ['pnpm', ['run', 'build']]],
  ['Bundle budget', ['pnpm', ['run', 'test:bundle-budget']]],
];

if (mode === 'full') {
  gates.splice(5, 0, ['P0 workflow validation', ['pnpm', ['run', 'test:e2e:validation:p0']]]);
  gates.splice(6, 0, ['Broad workflow validation', ['pnpm', ['run', 'test:e2e:validation']]]);
}

for (const [label, [command, args]] of gates) {
  console.log(`\n## ${label}`);
  const result = spawnSync(command, args, {
    cwd: webRoot,
    stdio: 'inherit',
    shell: false,
    env: process.env,
  });

  if (result.error) {
    console.error(`${label} could not start: ${result.error.message}`);
    process.exit(1);
  }
  if (result.status !== 0) {
    console.error(`${label} failed with exit code ${result.status}.`);
    process.exit(result.status || 1);
  }
}

console.log(`\nFrontend verification passed in ${mode} mode.`);
