#!/usr/bin/env npx tsx
/**
 * seed-e2e-data.ts — Deterministic E2E Test Data Seeder
 *
 * Seeds the canonical "Meridian Automotive" fixture into the local backend
 * so the 16 data-dependent journey tests have a controlled world.
 *
 * Design principles:
 *   - Idempotent: safe to run multiple times (upsert semantics)
 *   - Scoped: all data belongs to the E2E tenant only
 *   - Deterministic: same IDs, same values, every run
 *   - Fast: completes in < 5 seconds against a healthy backend
 *
 * Usage:
 *   npx tsx scripts/seed-e2e-data.ts
 *   npx tsx scripts/seed-e2e-data.ts --base-url http://localhost:8004
 *   PLAYWRIGHT_BACKEND_URL=http://localhost:8004 npx tsx scripts/seed-e2e-data.ts
 */

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const BASE_URL =
  process.argv.find((a) => a.startsWith('--base-url='))?.split('=')[1] ??
  process.env.PLAYWRIGHT_BACKEND_URL ??
  'http://localhost:8004';

const E2E_TENANT_ID = '00000000-0000-4000-e2e0-000000000001';

// Headers injected on every request — DEV_AUTH_BYPASS reads these
const HEADERS: Record<string, string> = {
  'Content-Type': 'application/json',
  'X-Tenant-ID': E2E_TENANT_ID,
  'X-User-ID': 'e2e-admin-user',
  'X-User-Role': 'admin',
};

// ---------------------------------------------------------------------------
// Canonical Fixture: Meridian Automotive
// ---------------------------------------------------------------------------

import { MERIDIAN_FIXTURE } from './fixtures/meridian-automotive';

// ---------------------------------------------------------------------------
// HTTP Helpers
// ---------------------------------------------------------------------------

async function api(
  method: string,
  path: string,
  body?: unknown,
): Promise<{ status: number; data: unknown }> {
  const url = `${BASE_URL}${path}`;
  const opts: RequestInit = {
    method,
    headers: HEADERS,
    body: body ? JSON.stringify(body) : undefined,
  };

  const res = await fetch(url, opts);
  let data: unknown;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  return { status: res.status, data };
}

async function upsertAccount(account: typeof MERIDIAN_FIXTURE.account) {
  // Try to get existing account first
  const existing = await api('GET', `/v1/accounts/${account.id}`);
  if (existing.status === 200) {
    console.log(`  ✓ Account "${account.name}" already exists`);
    return;
  }

  // Create via the accounts endpoint
  const result = await api('POST', '/v1/accounts/search', {
    query: account.name,
    limit: 1,
  });

  // If search doesn't find it, we need to create it via direct DB seeding
  // The accounts API may not have a direct POST /accounts endpoint (CRM-sourced)
  // Fall back to the sync endpoint with manual provider
  console.log(`  → Seeding account "${account.name}" via API...`);
  const createResult = await api('POST', '/v1/accounts/sync', {
    provider: 'manual',
    accounts: [account],
  });

  if (createResult.status >= 200 && createResult.status < 300) {
    console.log(`  ✓ Account "${account.name}" created`);
  } else {
    console.log(`  ⚠ Account sync returned ${createResult.status} — may need direct DB seed`);
  }
}

async function ensureCase(accountId: string, caseData: typeof MERIDIAN_FIXTURE.case) {
  // Check if case already exists
  const existing = await api('GET', `/v1/analysis/cases?account_id=${accountId}`);
  const items = Array.isArray((existing.data as any)?.items)
    ? (existing.data as any).items
    : [];

  if (items.length > 0) {
    console.log(`  ✓ Case already exists for account ${accountId}`);
    return items[0].case_id || items[0].id;
  }

  // Create case
  const result = await api('POST', '/v1/analysis/cases', {
    account_id: accountId,
    title: caseData.title,
  });

  const caseId = (result.data as any)?.case_id || (result.data as any)?.id;
  if (caseId) {
    console.log(`  ✓ Case created: ${caseId}`);
  } else {
    console.log(`  ⚠ Case creation returned ${result.status}`);
  }
  return caseId;
}

async function seedWorkspaceTab(
  caseId: string,
  tabKey: string,
  data: unknown[],
) {
  const result = await api(
    'PUT',
    `/v1/analysis/cases/${caseId}/workspace/${tabKey}`,
    { [tabKey]: data },
  );

  if (result.status >= 200 && result.status < 300) {
    console.log(`  ✓ Workspace tab "${tabKey}" seeded (${(data as unknown[]).length} items)`);
  } else {
    console.log(`  ⚠ Workspace tab "${tabKey}" seed returned ${result.status}`);
  }
}

// ---------------------------------------------------------------------------
// Main Seed Sequence
// ---------------------------------------------------------------------------

async function main() {
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║  Fabric 4L — E2E Data Seeder                           ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log(`  Backend: ${BASE_URL}`);
  console.log(`  Tenant:  ${E2E_TENANT_ID}`);
  console.log('');

  // Step 0: Health check
  console.log('[0/6] Health check...');
  const health = await api('GET', '/health');
  if (health.status !== 200) {
    console.error(`  ✗ Backend not healthy (status ${health.status})`);
    console.error('  → Is docker-compose.e2e.yml running?');
    process.exit(1);
  }
  console.log('  ✓ Backend healthy');

  // Step 1: Seed account
  console.log('\n[1/6] Seeding account...');
  await upsertAccount(MERIDIAN_FIXTURE.account);

  // Step 2: Ensure case exists
  console.log('\n[2/6] Ensuring case workspace...');
  const caseId = await ensureCase(
    MERIDIAN_FIXTURE.account.id,
    MERIDIAN_FIXTURE.case,
  );

  if (!caseId) {
    console.error('  ✗ Could not create or find case — aborting workspace seed');
    process.exit(1);
  }

  // Step 3: Seed workspace tabs (intelligence)
  console.log('\n[3/6] Seeding intelligence workspace...');
  await seedWorkspaceTab(caseId, 'signals', MERIDIAN_FIXTURE.workspace.signals);
  await seedWorkspaceTab(caseId, 'drivers', MERIDIAN_FIXTURE.workspace.drivers);
  await seedWorkspaceTab(caseId, 'evidence', MERIDIAN_FIXTURE.workspace.evidence);
  await seedWorkspaceTab(caseId, 'stakeholders', MERIDIAN_FIXTURE.workspace.stakeholders);

  // Step 4: Seed value studio tabs
  console.log('\n[4/6] Seeding value studio workspace...');
  await seedWorkspaceTab(caseId, 'value-model', MERIDIAN_FIXTURE.workspace.valueModel);
  await seedWorkspaceTab(caseId, 'narrative', MERIDIAN_FIXTURE.workspace.narrative);
  await seedWorkspaceTab(caseId, 'action-plan', MERIDIAN_FIXTURE.workspace.actionPlan);

  // Step 5: Seed platform settings
  console.log('\n[5/6] Seeding platform settings...');
  const settingsResult = await api('PATCH', '/v1/tenant/settings', MERIDIAN_FIXTURE.settings);
  if (settingsResult.status >= 200 && settingsResult.status < 300) {
    console.log('  ✓ Platform settings seeded');
  } else {
    console.log(`  ⚠ Platform settings returned ${settingsResult.status}`);
  }

  // Step 6: Verification
  console.log('\n[6/6] Verifying seed data...');
  const verifyAccount = await api(
    'GET',
    `/v1/accounts/${MERIDIAN_FIXTURE.account.id}`,
  );
  const verifyCase = await api(
    'GET',
    `/v1/analysis/cases?account_id=${MERIDIAN_FIXTURE.account.id}`,
  );

  const accountOk = verifyAccount.status === 200;
  const caseOk = verifyCase.status === 200;

  console.log(`  Account:   ${accountOk ? '✓' : '✗'}`);
  console.log(`  Case:      ${caseOk ? '✓' : '✗'}`);

  console.log('\n══════════════════════════════════════════════════════════');
  if (accountOk && caseOk) {
    console.log('  E2E seed complete — ready for journey tests');
  } else {
    console.log('  E2E seed partially complete — some endpoints may need direct DB access');
    console.log('  Journey tests may still pass if workspace data was seeded via PUT');
  }
  console.log('══════════════════════════════════════════════════════════');
}

main().catch((err) => {
  console.error('Seed script failed:', err);
  process.exit(1);
});
