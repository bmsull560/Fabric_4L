#!/usr/bin/env npx tsx
import { execSync } from 'node:child_process';

execSync('pnpm --filter @fabric/platform-contract run generate:openapi-types', { stdio: 'inherit' });
