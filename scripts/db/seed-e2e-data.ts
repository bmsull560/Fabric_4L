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

import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';

const BASE_URL =
  process.argv.find((a) => a.startsWith('--base-url='))?.split('=')[1] ??
  process.env.PLAYWRIGHT_BACKEND_URL ??
  'http://localhost:8004';

const REPORT_JSON =
  process.argv.find((a) => a.startsWith('--report-json='))?.split('=')[1] ??
  process.env.SEED_REPORT_JSON ??
  '';

const STRICT_SEED =
  process.argv.includes('--strict') || /^(1|true|yes|on)$/i.test(process.env.SEED_STRICT ?? 'false');

const E2E_TENANT_ID = '00000000-0000-4000-e2e0-000000000001';
const E2E_TENANT_BETA_ID = '00000000-0000-4000-e2e0-000000000002';
const E2E_ADMIN_USER_ID = 'e2e-admin-user';
const E2E_REVIEWER_USER_ID = 'e2e-reviewer-user';
const E2E_READ_ONLY_USER_ID = 'e2e-read-only-user';
const E2E_SALES_USER_ID = 'e2e-sales-user';

type SeedStatus = 'present' | 'partial' | 'missing' | 'blocked';

interface SeedReportRow {
  seedArea: string;
  recordsCreated: string;
  method: string;
  persistenceVerified: string;
  status: SeedStatus;
}

// Headers injected on every request — DEV_AUTH_BYPASS reads these
const HEADERS: Record<string, string> = {
  'Content-Type': 'application/json',
  'X-Tenant-ID': E2E_TENANT_ID,
  'X-User-ID': E2E_ADMIN_USER_ID,
  'X-User-Role': 'super_admin',
  'X-Role': 'super_admin',
  'X-Privileged-Reason': 'playwright-backend-validation-seed',
};

const reportRows: SeedReportRow[] = [];

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
  headers: Record<string, string> = HEADERS,
): Promise<{ status: number; data: unknown }> {
  const url = `${BASE_URL}${path}`;
  const opts: RequestInit = {
    method,
    headers,
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

function recordSeed(row: SeedReportRow): void {
  reportRows.push(row);
}

function printSeedReport(): void {
  console.log('\n# Backend Seed Data Report');
  console.log('');
  console.log('| Seed Area | Records Created | Method | Persistence Verified | Status |');
  console.log('|---|---|---|---|---|');
  for (const row of reportRows) {
    console.log(
      `| ${row.seedArea} | ${row.recordsCreated} | ${row.method} | ${row.persistenceVerified} | ${row.status} |`,
    );
  }
}

function aggregateSeedStatus(): SeedStatus {
  if (reportRows.some((row) => row.status === 'blocked')) {
    return 'blocked';
  }
  if (reportRows.some((row) => row.status === 'partial' || row.status === 'missing')) {
    return 'partial';
  }
  return 'present';
}

function writeSeedReportJson(): void {
  if (!REPORT_JSON) {
    return;
  }

  const aggregateStatus = aggregateSeedStatus();
  const requiredRowsPresent = reportRows.every((row) => row.status === 'present');
  const payload = {
    generatedAt: new Date().toISOString(),
    backendUrl: BASE_URL,
    strictSeed: STRICT_SEED,
    aggregateStatus,
    requiredRowsPresent,
    tenant: {
      alphaTenantId: E2E_TENANT_ID,
      betaTenantId: E2E_TENANT_BETA_ID,
    },
    users: {
      admin: E2E_ADMIN_USER_ID,
      reviewer: E2E_REVIEWER_USER_ID,
      readOnly: E2E_READ_ONLY_USER_ID,
      sales: E2E_SALES_USER_ID,
    },
    fixture: {
      accountId: MERIDIAN_FIXTURE.account.id,
      caseId: MERIDIAN_FIXTURE.case.id,
      accountName: MERIDIAN_FIXTURE.account.name,
    },
    rows: reportRows,
  };

  mkdirSync(dirname(REPORT_JSON), { recursive: true });
  writeFileSync(REPORT_JSON, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
  console.log(`\nSeed report JSON written to ${REPORT_JSON}`);
}

async function verifyAccountExists(accountId: string): Promise<boolean> {
  const result = await api('GET', `/v1/accounts/${accountId}`);
  return result.status === 200;
}

async function verifyCaseExists(accountId: string): Promise<boolean> {
  const result = await api('GET', `/v1/analysis/cases?account_id=${accountId}`);
  return result.status === 200 && Array.isArray((result.data as any)?.items);
}

async function verifyWorkspaceTab(caseId: string, tabKey: string): Promise<boolean> {
  const result = await api('GET', `/v1/analysis/cases/${caseId}/workspace/${tabKey}`);
  return result.status === 200 && result.data !== null;
}

async function attemptCrossTenantVerification(): Promise<boolean> {
  const betaHeaders = {
    ...HEADERS,
    'X-Tenant-ID': E2E_TENANT_BETA_ID,
    'X-User-ID': E2E_REVIEWER_USER_ID,
  };
  const result = await api('GET', `/v1/accounts/${MERIDIAN_FIXTURE.account.id}`, undefined, betaHeaders);
  return [401, 403, 404].includes(result.status);
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
  recordSeed({
    seedArea: 'Backend health',
    recordsCreated: 'n/a',
    method: 'GET /health',
    persistenceVerified: '200 OK',
    status: 'present',
  });

  // Step 1: Seed account
  console.log('\n[1/6] Seeding account...');
  await upsertAccount(MERIDIAN_FIXTURE.account);
  recordSeed({
    seedArea: 'Tenant Alpha account',
    recordsCreated: '1 account',
    method: 'API /v1/accounts/sync (manual provider fallback)',
    persistenceVerified: (await verifyAccountExists(MERIDIAN_FIXTURE.account.id)) ? 'yes' : 'no',
    status: (await verifyAccountExists(MERIDIAN_FIXTURE.account.id)) ? 'present' : 'partial',
  });

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
  recordSeed({
    seedArea: 'Analysis workspace case',
    recordsCreated: '1 case workspace',
    method: 'API /v1/analysis/cases',
    persistenceVerified: (await verifyCaseExists(MERIDIAN_FIXTURE.account.id)) ? 'yes' : 'no',
    status: (await verifyCaseExists(MERIDIAN_FIXTURE.account.id)) ? 'present' : 'partial',
  });

  // Step 3: Seed workspace tabs (intelligence)
  console.log('\n[3/6] Seeding intelligence workspace...');
  await seedWorkspaceTab(caseId, 'signals', MERIDIAN_FIXTURE.workspace.signals);
  await seedWorkspaceTab(caseId, 'drivers', MERIDIAN_FIXTURE.workspace.drivers);
  await seedWorkspaceTab(caseId, 'evidence', MERIDIAN_FIXTURE.workspace.evidence);
  await seedWorkspaceTab(caseId, 'stakeholders', MERIDIAN_FIXTURE.workspace.stakeholders);
  recordSeed({
    seedArea: 'Signals / drivers / evidence / stakeholders',
    recordsCreated: `${MERIDIAN_FIXTURE.workspace.signals.length + MERIDIAN_FIXTURE.workspace.drivers.length + MERIDIAN_FIXTURE.workspace.evidence.length + MERIDIAN_FIXTURE.workspace.stakeholders.length} workspace records`,
    method: 'API /v1/analysis/cases/{caseId}/workspace/*',
    persistenceVerified:
      (await verifyWorkspaceTab(caseId, 'signals')) &&
      (await verifyWorkspaceTab(caseId, 'drivers')) &&
      (await verifyWorkspaceTab(caseId, 'evidence')) &&
      (await verifyWorkspaceTab(caseId, 'stakeholders'))
        ? 'yes'
        : 'partial',
    status:
      (await verifyWorkspaceTab(caseId, 'signals')) &&
      (await verifyWorkspaceTab(caseId, 'drivers')) &&
      (await verifyWorkspaceTab(caseId, 'evidence')) &&
      (await verifyWorkspaceTab(caseId, 'stakeholders'))
        ? 'present'
        : 'partial',
  });

  // Step 4: Seed value studio tabs
  console.log('\n[4/6] Seeding value studio workspace...');
  await seedWorkspaceTab(caseId, 'value-model', MERIDIAN_FIXTURE.workspace.valueModel);
  await seedWorkspaceTab(caseId, 'narrative', MERIDIAN_FIXTURE.workspace.narrative);
  await seedWorkspaceTab(caseId, 'action-plan', MERIDIAN_FIXTURE.workspace.actionPlan);
  recordSeed({
    seedArea: 'Value model / narrative / action plan',
    recordsCreated: `${MERIDIAN_FIXTURE.workspace.valueModel.length + MERIDIAN_FIXTURE.workspace.narrative.length + MERIDIAN_FIXTURE.workspace.actionPlan.length} workspace records`,
    method: 'API /v1/analysis/cases/{caseId}/workspace/*',
    persistenceVerified:
      (await verifyWorkspaceTab(caseId, 'value-model')) &&
      (await verifyWorkspaceTab(caseId, 'narrative')) &&
      (await verifyWorkspaceTab(caseId, 'action-plan'))
        ? 'yes'
        : 'partial',
    status:
      (await verifyWorkspaceTab(caseId, 'value-model')) &&
      (await verifyWorkspaceTab(caseId, 'narrative')) &&
      (await verifyWorkspaceTab(caseId, 'action-plan'))
        ? 'present'
        : 'partial',
  });

  // Step 5: Seed platform settings
  console.log('\n[5/6] Seeding platform settings...');
  const settingsResult = await api('PATCH', '/v1/tenant/settings', MERIDIAN_FIXTURE.settings);
  if (settingsResult.status >= 200 && settingsResult.status < 300) {
    console.log('  ✓ Platform settings seeded');
  } else {
    console.log(`  ⚠ Platform settings returned ${settingsResult.status}`);
  }
  recordSeed({
    seedArea: 'Tenant settings / value-pack-adjacent governance',
    recordsCreated: '1 tenant settings payload',
    method: 'API /v1/tenant/settings',
    persistenceVerified: settingsResult.status >= 200 && settingsResult.status < 300 ? 'yes' : `status ${settingsResult.status}`,
    status: settingsResult.status >= 200 && settingsResult.status < 300 ? 'present' : 'partial',
  });

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
  recordSeed({
    seedArea: 'Tenant Beta isolation check',
    recordsCreated: `users reserved: ${E2E_REVIEWER_USER_ID}, ${E2E_READ_ONLY_USER_ID}, ${E2E_SALES_USER_ID}`,
    method: 'Cross-tenant read probe with alternate tenant header',
    persistenceVerified: (await attemptCrossTenantVerification()) ? 'denied as expected' : 'not verified',
    status: (await attemptCrossTenantVerification()) ? 'present' : 'partial',
  });
  recordSeed({
    seedArea: 'Business case draft / approved / approval history / export state / audit trail',
    recordsCreated: '0 deterministic records',
    method: 'Blocked pending live L4 case + approval/export seed APIs or documented DB fallback',
    persistenceVerified: 'not yet verified',
    status: 'blocked',
  });

  console.log('\n══════════════════════════════════════════════════════════');
  if (accountOk && caseOk) {
    console.log('  E2E seed complete — ready for journey tests');
  } else {
    console.log('  E2E seed partially complete — some endpoints may need direct DB access');
    console.log('  Journey tests may still pass if workspace data was seeded via PUT');
  }
  console.log('══════════════════════════════════════════════════════════');
  printSeedReport();
  writeSeedReportJson();

  if (STRICT_SEED && reportRows.some((row) => row.status !== 'present')) {
    console.error('Strict seed verification failed: one or more required seed areas are not present.');
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('Seed script failed:', err);
  process.exit(1);
});
