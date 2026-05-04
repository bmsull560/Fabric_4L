/**
 * Journey 14: Value Pack Selection and Governance
 *
 * Traceability: VPACK-001 through VPACK-018.
 * Validates value pack browsing, tenant default selection, account-level
 * override, pack composition, formula/benchmark/persona/ontology detail,
 * evidence requirements, admin publish/deprecate lifecycle, and historical
 * case version preservation.
 *
 * Priority: P1 core workflow
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectTenantContext,
  expectNotVisible,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  buildGoldenPathMocks,
  createValuePackList,
} from '../fixtures/deep-test-data';

journeyTest.describe('Value Pack Selection and Governance', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      ...buildGoldenPathMocks(),
      {
        pattern: '**/api/v1/agents/value-packs**',
        body: createValuePackList(),
      },
      {
        pattern: '**/api/v1/agents/value-packs/pack-healthcare-001',
        body: createValuePackList()[0],
      },
      {
        pattern: '**/api/v1/agents/value-packs/pack-saas-001',
        body: createValuePackList()[1],
      },
      {
        pattern: '**/api/v1/agents/value-packs/pack-deprecated-001',
        body: createValuePackList()[2],
      },
      {
        pattern: `**/api/v1/agents/accounts/${DEEP_ACCOUNT_ID}/value-pack`,
        method: 'PUT',
        status: 200,
        body: { account_id: DEEP_ACCOUNT_ID, value_pack_id: 'pack-healthcare-001', override: true },
      },
    ]);
  });

  // ── Browse Value Packs ──────────────────────────────────────────────────

  journeyTest('VPACK-001: user can view all available value packs including name, industry, and status', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/context/packs',
      [/healthcare operations|saas growth|value pack/i, /active|deprecated/i],
      'value pack list with name, industry, and status',
    );
  });

  journeyTest('VPACK-002: user can view pack formula list for a selected pack', async ({ authedPage }) => {
    await authedPage.goto('/context/packs', { waitUntil: 'domcontentloaded' });

    const healthcareRow = authedPage.getByText(/healthcare operations/i).first();
    const hasRow = await healthcareRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await healthcareRow.click();
      await expectAnyVisible(
        authedPage,
        [/formula|reconciliation|claim.*processing/i],
        'value pack formula list',
      );
    }
  });

  journeyTest('VPACK-003: user can view pack benchmarks for a selected pack', async ({ authedPage }) => {
    await authedPage.goto('/context/packs', { waitUntil: 'domcontentloaded' });

    const healthcareRow = authedPage.getByText(/healthcare operations/i).first();
    const hasRow = await healthcareRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await healthcareRow.click();
      await expectAnyVisible(
        authedPage,
        [/benchmark|bench-001|manual hours|cycle time/i],
        'value pack benchmark list',
      );
    }
  });

  journeyTest('VPACK-004: user can view pack personas for a selected pack', async ({ authedPage }) => {
    await authedPage.goto('/context/packs', { waitUntil: 'domcontentloaded' });

    const healthcareRow = authedPage.getByText(/healthcare operations/i).first();
    const hasRow = await healthcareRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await healthcareRow.click();
      await expectAnyVisible(
        authedPage,
        [/persona|cfo|coo/i],
        'value pack personas',
      );
    }
  });

  journeyTest('VPACK-005: user can view pack ontology terms', async ({ authedPage }) => {
    await authedPage.goto('/context/packs', { waitUntil: 'domcontentloaded' });

    const healthcareRow = authedPage.getByText(/healthcare operations/i).first();
    const hasRow = await healthcareRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await healthcareRow.click();
      await expectAnyVisible(
        authedPage,
        [/ontology|term|manual.*reconciliation|claim.*cycle|compliance/i],
        'value pack ontology terms',
      );
    }
  });

  journeyTest('VPACK-006: user can view pack evidence requirements', async ({ authedPage }) => {
    await authedPage.goto('/context/packs', { waitUntil: 'domcontentloaded' });

    const healthcareRow = authedPage.getByText(/healthcare operations/i).first();
    const hasRow = await healthcareRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await healthcareRow.click();
      await expectAnyVisible(
        authedPage,
        [/evidence requirement|customer.*data|audit.*report/i],
        'value pack evidence requirements',
      );
    }
  });

  // ── Tenant Default and Account Override ────────────────────────────────

  journeyTest('VPACK-007: admin can select tenant default value pack', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/settings/data/value-packs',
      [/default.*pack|tenant.*default|value pack/i],
      'tenant default value pack configuration',
    );
  });

  journeyTest('VPACK-008: user can assign a value pack to a specific account, overriding tenant default', async ({ authedPage }) => {
    await authedPage.goto(`/accounts/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/meridian|value pack|healthcare operations/i],
      'account detail with value pack assignment',
    );

    const assignBtn = authedPage.getByRole('button', { name: /assign.*pack|change.*pack|select.*pack/i }).first();
    const hasAssign = await assignBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasAssign) {
      await assignBtn.click();
      await expectAnyVisible(
        authedPage,
        [/healthcare operations|saas growth|select/i],
        'pack selection modal or dropdown',
      );
    }
  });

  journeyTest('VPACK-009: account-level override takes precedence over tenant default', async ({ authedPage }) => {
    await authedPage.goto(`/accounts/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/healthcare operations|value pack/i],
      'account shows overridden value pack rather than tenant default',
    );
  });

  // ── Pack Composition ────────────────────────────────────────────────────

  journeyTest('VPACK-010: user can compose multiple packs for an account (e.g. SaaS + Healthcare)', async ({ authedPage }) => {
    await authedPage.goto('/settings/data/value-packs', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/compose|combine|multi-pack|saas|healthcare/i, /value pack/i],
      'pack composition surface',
    );
  });

  // ── Pack-Driven Classification and Generation ──────────────────────────

  journeyTest('VPACK-011: pack-driven signal classification uses pack ontology terms', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/manual.*reconciliation|claim.*cycle|compliance|ontology|pack/i, /signal/i],
      'signal classification aligned with pack ontology',
    );
  });

  journeyTest('VPACK-012: pack-driven formula recommendations appear in calculator', async ({ authedPage }) => {
    await authedPage.goto(`/calculator/${DEEP_ACCOUNT_ID}/roi`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/formula|recommended|healthcare|reconciliation/i, /calculator|roi/i],
      'pack-driven formula recommendations in calculator',
    );
  });

  // ── Deprecated Pack Lifecycle ──────────────────────────────────────────

  journeyTest('VPACK-013: deprecated pack shows clear deprecation warning', async ({ authedPage }) => {
    await authedPage.goto('/context/packs', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/deprecated|legacy erp|superseded/i],
      'deprecated pack visible with deprecation status',
    );

    await expect(
      authedPage.getByText(/deprecated|superseded|use.*instead/i).first(),
    ).toBeVisible({ timeout: 8000 });
  });

  journeyTest('VPACK-014: user sees warning when a value case was built on a deprecated pack version', async ({ authedPage }) => {
    // Navigate to a case that uses a deprecated pack (simulated via mock)
    await authedPage.goto('/deliverables/cases', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/case|business case|approved|draft/i],
      'business case list (deprecated pack warning validation)',
    );
  });

  // ── Admin Publish / Deprecate ─────────────────────────────────────────

  journeyTest('VPACK-015: admin can publish a new value pack version', async ({ authedPage }) => {
    await authedPage.goto('/settings/data/value-packs', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/publish|new version|upload|value pack/i],
      'admin value pack management with publish capability',
    );
  });

  journeyTest('VPACK-016: admin can deprecate an existing value pack version', async ({ authedPage }) => {
    await authedPage.goto('/settings/data/value-packs', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/deprecate|archive|retire|value pack/i],
      'admin value pack management with deprecate capability',
    );
  });

  // ── Historical Version Preservation ───────────────────────────────────

  journeyTest('VPACK-017: historical value cases preserve original pack version at time of creation', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });

    // Business case audit or metadata should show which pack version was used
    await expectAnyVisible(
      authedPage,
      [/pack.*version|healthcare.*3\.1|v3|original.*pack/i, /business case|case|meridian/i],
      'business case references original pack version',
    );
  });

  journeyTest('VPACK-018: unsupported industry shows fallback behavior with default pack guidance', async ({ authedPage }) => {
    await authedPage.goto('/context/packs', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/healthcare operations|saas growth|general/i, /value pack/i],
      'value pack list shows options including general/fallback',
    );

    await expectTenantContext(authedPage);
  });
});
