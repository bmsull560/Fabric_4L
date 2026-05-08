#!/usr/bin/env node

import { execFileSync } from 'node:child_process';

const blockedSegments = ['/archive/', '/prototypes/'];
const pnpmArgs = ['-r', 'list', '--depth', '-1', '--json'];

const output =
  process.platform === 'win32'
    ? execFileSync('cmd.exe', ['/d', '/s', '/c', `pnpm ${pnpmArgs.join(' ')}`], {
        encoding: 'utf8',
      })
    : execFileSync('pnpm', pnpmArgs, {
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
