import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import type { FullConfig } from '@playwright/test';

const execFileAsync = promisify(execFile);

function selectedBackendProject(config: FullConfig): boolean {
  return config.projects.some((project) => project.name === 'backend-integrated');
}

export default async function globalSetup(config: FullConfig) {
  const backendUrl = process.env.PLAYWRIGHT_BACKEND_URL;

  if (!backendUrl || process.env.E2E_SEED_DATA === 'false' || !selectedBackendProject(config)) {
    return;
  }

  console.log(`[e2e] Seeding deterministic backend data at ${backendUrl}`);
  const { stdout, stderr } = await execFileAsync(
    'pnpm',
    ['exec', 'tsx', '../../scripts/db/seed-e2e-data.ts', `--base-url=${backendUrl}`],
    {
      cwd: new URL('..', import.meta.url),
      env: { ...process.env, PLAYWRIGHT_BACKEND_URL: backendUrl },
      maxBuffer: 1024 * 1024 * 8,
    },
  );

  if (stdout.trim()) {
    console.log(stdout.trim());
  }
  if (stderr.trim()) {
    console.error(stderr.trim());
  }
}
