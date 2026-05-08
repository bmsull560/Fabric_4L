#!/usr/bin/env node
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const webRoot = resolve(__dirname, '..', '..');
const srcRoot = resolve(webRoot, 'src');
const cleanupSummaryPath = resolve(webRoot, 'FRONTEND_CLEANUP_SUMMARY.md');

const componentExtensions = new Set(['.tsx', '.jsx']);
const sourceExtensions = new Set(['.ts', '.tsx', '.js', '.jsx', '.css', '.scss', '.md']);

const violations = [];

function walk(dir, extensions) {
  const results = [];
  for (const entry of readdirSync(dir)) {
    if (entry === 'node_modules' || entry === 'dist' || entry.startsWith('.')) continue;
    const fullPath = resolve(dir, entry);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      results.push(...walk(fullPath, extensions));
      continue;
    }
    const ext = entry.slice(entry.lastIndexOf('.'));
    if (extensions.has(ext)) {
      results.push(fullPath);
    }
  }
  return results;
}

function addViolation(filePath, line, message) {
  const rel = relative(webRoot, filePath);
  violations.push(`${rel}:${line} ${message}`);
}

const conflictMarkers = [/^<<<<<<< /, /^=======\s*$/, /^>>>>>>> /];
for (const filePath of walk(srcRoot, sourceExtensions)) {
  const lines = readFileSync(filePath, 'utf8').split(/\r?\n/);
  lines.forEach((line, index) => {
    if (conflictMarkers.some((pattern) => pattern.test(line))) {
      addViolation(filePath, index + 1, 'merge-conflict marker detected');
    }
  });
}

const routeConcatPatterns = [
  {
    regex: /(["'`])\/[A-Za-z0-9_\-/]*\1\s*\+\s*[A-Za-z$_({]/,
    message: 'direct route concatenation detected (string literal + expression)',
  },
  {
    regex: /\b(?:navigate|to|href|pathname)\s*[:(]\s*[A-Za-z$_][\w$.]*\s*\+\s*(["'`])\/[A-Za-z0-9_\-/]*\1/,
    message: 'route suffix concatenation detected; use centralized route helpers',
  },
];

for (const filePath of walk(srcRoot, componentExtensions)) {
  const lines = readFileSync(filePath, 'utf8').split(/\r?\n/);
  lines.forEach((line, index) => {
    for (const { regex, message } of routeConcatPatterns) {
      if (regex.test(line)) {
        addViolation(filePath, index + 1, message);
        break;
      }
    }
  });
}

const cleanupSummary = readFileSync(cleanupSummaryPath, 'utf8');
cleanupSummary.split(/\r?\n/).forEach((line, index) => {
  if (/claim not verified/i.test(line)) {
    addViolation(cleanupSummaryPath, index + 1, 'stale "claim not verified" marker detected');
  }
});

if (violations.length > 0) {
  console.error('Frontend hygiene checks failed:\n');
  for (const violation of violations) {
    console.error(`- ${violation}`);
  }
  process.exit(1);
}

console.log('Frontend hygiene checks passed.');
