#!/usr/bin/env node

import { existsSync, readFileSync } from 'node:fs';
import { execSync } from 'node:child_process';

const LOCKFILE_PATTERN = /(\/(?:package-lock\.json|yarn\.lock)$|^(?:package-lock\.json|yarn\.lock)$|\/(?:pnpm-lock\.yaml|uv\.lock)$|^(?:pnpm-lock\.yaml|uv\.lock)$)/;
const ALLOWED_LOCKFILE_PATHS = new Set([
  'pnpm-lock.yaml',
  'apps/web/pnpm-lock.yaml',
  'services/layer1-ingestion/uv.lock',
  'services/layer2-extraction/uv.lock',
  'services/layer3-knowledge/uv.lock',
  'services/layer4-agents/uv.lock',
  'services/layer5-ground-truth/uv.lock',
  'services/layer6-benchmarks/uv.lock',
]);

function fail(message) {
  console.error(`❌ ${message}`);
  process.exit(1);
}

function loadJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

function gitOutput(args) {
  return execSync(`git ${args}`, { encoding: 'utf8' }).trim();
}

function resolveDiffRange() {
  if (process.argv.includes('--staged')) return 'diff --cached --name-only';

  const baseSha = process.env.GITHUB_BASE_SHA;
  const headSha = process.env.GITHUB_SHA;
  if (baseSha && headSha) return `diff --name-only ${baseSha}...${headSha}`;

  const baseRef = process.env.GITHUB_BASE_REF;
  if (baseRef) {
    try {
      return `diff --name-only origin/${baseRef}...HEAD`;
    } catch {
      return 'diff --name-only';
    }
  }

  return 'diff --name-only';
}

function getChangedFiles() {
  const range = resolveDiffRange();
  const output = gitOutput(range);
  return output ? output.split('\n').map((line) => line.trim()).filter(Boolean) : [];
}

const rootPackageLockPath = 'package-lock.json';
if (existsSync(rootPackageLockPath)) {
  fail('Root package-lock.json is not allowed. Use pnpm-lock.yaml as the canonical lockfile.');
}

const rootPkg = loadJson('package.json');
if (!rootPkg.packageManager || !String(rootPkg.packageManager).startsWith('pnpm@')) {
  fail('Root package.json must pin pnpm via the packageManager field.');
}
if (rootPkg.scripts?.preinstall !== 'node scripts/enforce-package-manager.cjs') {
  fail('Root package.json must enforce pnpm via scripts.preinstall.');
}

const webPkg = loadJson('apps/web/package.json');
if (!webPkg.packageManager || !String(webPkg.packageManager).startsWith('pnpm@')) {
  fail('apps/web/package.json must pin pnpm via the packageManager field.');
}
if (webPkg.scripts?.preinstall !== 'node ./scripts/enforce-package-manager.cjs') {
  fail('apps/web/package.json must enforce pnpm via scripts.preinstall.');
}

const changedLockfiles = getChangedFiles().filter((path) => LOCKFILE_PATTERN.test(path));
const blockedNpmOrYarn = changedLockfiles.filter(
  (path) => path.endsWith('package-lock.json') || path.endsWith('yarn.lock'),
);
if (blockedNpmOrYarn.length > 0) {
  fail(`npm/yarn lockfiles are not allowed in changesets: ${blockedNpmOrYarn.join(', ')}`);
}

const unauthorizedLockfiles = changedLockfiles.filter(
  (path) => (path.endsWith('pnpm-lock.yaml') || path.endsWith('uv.lock')) && !ALLOWED_LOCKFILE_PATHS.has(path),
);
if (unauthorizedLockfiles.length > 0) {
  fail(`Lockfile churn is only allowed in approved paths. Unauthorized: ${unauthorizedLockfiles.join(', ')}`);
}

console.log('✅ Package manager policy checks passed (pnpm policy + lockfile path guard).');
