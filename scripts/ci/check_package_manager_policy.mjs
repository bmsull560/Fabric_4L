#!/usr/bin/env node

import { existsSync, readFileSync } from 'node:fs';

function fail(message) {
  console.error(`❌ ${message}`);
  process.exit(1);
}

function loadJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
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

console.log('✅ Package manager policy checks passed (root + apps/web).');
