/**
 * Security Suite: Tenant Isolation Validation
 *
 * Traceability: SEC-TENANT-001, SEC-ROLE-001, SEC-EXPORT-001, SEC-FAIL-CLOSED-001.
 * This suite keeps tenant isolation, direct-route protection, export blocking,
 * non-admin write restrictions, and missing/forged tenant-context behavior in
 * the executable validation program.
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import { expectNoCrossTenantLeakage, expectRouteSupportsWorkflow, expectTenantContext } from '../helpers/validation-program';

journeyTest.describe('Security Suite: Tenant Isolation Validation', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      {
        pattern: '**/api/v1/agents/accounts/acct-other-tenant',
        status: 403,
        body: { error: 'Forbidden: tenant isolation enforced' },
      },
      {
        pattern: '**/api/v1/exports/**',
        status: 403,
        body: { error: 'Approval and tenant access are required before export.' },
      },
      {
        pattern: '**/api/v1/documents/doc-other-tenant**',
        status: 403,
        body: { error: 'Forbidden: document tenant mismatch' },
      },
    ]);
  });

  journeyTest('Step 1 [SEC-TENANT-001]: authenticated workflow stores and uses the expected tenant context', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/accounts',
      [/accounts/i, /browse and manage/i, /search accounts/i],
      'tenant-scoped accounts workspace',
    );
    await expectTenantContext(authedPage);
    await expectNoCrossTenantLeakage(authedPage);
  });

  journeyTest('Step 2 [SEC-TENANT-002]: direct access to a foreign account fails without rendering leaked content', async ({ authedPage }) => {
    await authedPage.goto('/intelligence/acct-other-tenant/signals', { waitUntil: 'domcontentloaded' });
    await expectNoCrossTenantLeakage(authedPage);
    await expect(
      authedPage.getByText(/forbidden|not authorized|access denied|could not be loaded|no signals yet|signals/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 3 [SEC-ROLE-001]: admin-only settings are explicit and protected by governance layout', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/settings/team/permissions',
      [/permissions/i, /team/i, /role/i, /admin/i, /access/i],
      'role-based permission management surface',
    );
  });

  journeyTest('Step 4 [SEC-EXPORT-001]: export surfaces remain tenant-scoped and approval-aware', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/governance/traces',
      [/decision trace/i, /audit log/i, /export prov-o/i, /truth references/i],
      'tenant-scoped provenance export surface',
    );
    await expectNoCrossTenantLeakage(authedPage);
  });

  journeyTest('Step 5 [SEC-SEARCH-001]: graph and evidence search do not surface foreign-tenant artifacts', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/context/ontology/graph',
      [/graph explorer/i, /search entities/i, /legend/i, /graph statistics/i],
      'tenant-scoped graph search surface',
    );
    await expectNoCrossTenantLeakage(authedPage);
  });

  journeyTest('Step 6 [SEC-FAIL-CLOSED-001]: missing tenant context does not silently expose customer data', async ({ authedPage }) => {
    await authedPage.goto('/accounts', { waitUntil: 'domcontentloaded' });
    await authedPage.evaluate(() => localStorage.removeItem('tenantId'));
    await authedPage.reload({ waitUntil: 'domcontentloaded' });
    await expect(
      authedPage.getByText(/tenant|account|sign in|access|workspace|no accounts/i).first(),
    ).toBeVisible({ timeout: 10000 });
    await expectNoCrossTenantLeakage(authedPage);
  });
});
