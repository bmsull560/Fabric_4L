#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..', '..');
const ua = process.env.npm_config_user_agent || '';
const packageJsonPath = path.join(repoRoot, 'package.json');
const lockfilePath = path.join(repoRoot, 'package-lock.json');
const policyScanRoots = ['.github/workflows', 'Makefile', 'scripts'];
const forbiddenPackageManagerPattern = /(?<!p)\bnpm\s+(?:ci|install)\b|\byarn\s+install\b/;
const forbiddenWorkflowPackageManagerPattern = /\bnpm\b|\byarn\b/;

const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

if (!packageJson.packageManager || !packageJson.packageManager.startsWith('pnpm@')) {
  console.error('❌ Root package.json must declare "packageManager": "pnpm@<version>".');
  process.exit(1);
}

if (fs.existsSync(lockfilePath)) {
  console.error('❌ package-lock.json detected at repository root. This repo uses pnpm; remove npm lockfile.');
  process.exit(1);
}

if (ua && !ua.includes('pnpm')) {
  console.error('❌ This repository uses pnpm. Please run: pnpm install');
  process.exit(1);
}

function* iterFiles(target) {
  if (!fs.existsSync(target)) {
    return;
  }
  const stat = fs.statSync(target);
  if (stat.isFile()) {
    yield target;
    return;
  }
  for (const entry of fs.readdirSync(target, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name === '__pycache__') {
      continue;
    }
    const child = path.join(target, entry.name);
    if (entry.isDirectory()) {
      yield* iterFiles(child);
    } else if (entry.isFile()) {
      yield child;
    }
  }
}

const violations = [];
for (const root of policyScanRoots) {
  for (const file of iterFiles(path.join(repoRoot, root))) {
    const relative = path.relative(repoRoot, file).replaceAll(path.sep, '/');
    const text = fs.readFileSync(file, 'utf8');
    for (const [index, line] of text.split(/\r?\n/).entries()) {
      if (forbiddenPackageManagerPattern.test(line)) {
        violations.push(`${relative}:${index + 1}: ${line.trim()}`);
      }

      const isWorkflowYaml =
        relative.startsWith('.github/workflows/') &&
        (relative.endsWith('.yml') || relative.endsWith('.yaml'));
      if (isWorkflowYaml && forbiddenWorkflowPackageManagerPattern.test(line)) {
        violations.push(`${relative}:${index + 1}: ${line.trim()}`);
      }
    }
  }
}

if (violations.length > 0) {
  console.error('❌ Forbidden package-manager install commands found. Use pnpm only.');
  for (const violation of violations) {
    console.error(`- ${violation}`);
  }
  process.exit(1);
}

console.log('✅ Package manager policy check passed.');
