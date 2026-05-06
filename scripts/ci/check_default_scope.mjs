#!/usr/bin/env node

import { execFileSync } from 'node:child_process';

const blockedSegments = ['/archive/', '/prototypes/'];

const output = execFileSync('pnpm', ['-r', 'list', '--depth', '-1', '--json'], {
  encoding: 'utf8',
});

const packages = JSON.parse(output);
const leaked = packages.filter((pkg) => {
  const path = String(pkg.path ?? '');
  return blockedSegments.some((segment) => path.includes(segment));
});

if (leaked.length > 0) {
  console.error('Default workspace scope leaked excluded directories.');
  for (const pkg of leaked) {
    console.error(` - ${pkg.name ?? '<unknown>'}: ${pkg.path ?? '<unknown path>'}`);
  }
  process.exit(1);
}

console.log('Default workspace scope is canonical (apps/web, packages/*, services/* only).');
