#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..', '..');
const ua = process.env.npm_config_user_agent || '';
const packageJsonPath = path.join(repoRoot, 'package.json');
const lockfilePath = path.join(repoRoot, 'package-lock.json');

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

console.log('✅ Package manager policy check passed.');
