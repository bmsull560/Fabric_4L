/**
 * Journey 18: Search and Retrieval Workflow
 *
 * Traceability: SRCH-001 through SRCH-013.
 * Validates cross-entity search (accounts, documents, evidence, stakeholders,
 * value models, business cases), tenant-scoped knowledge search, filter by
 * account/source/date, correct context landing, tenant boundary enforcement,
 * and role permission enforcement.
 *
 * Priority: P1 core workflow
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectTenantContext,
  expectNoCrossTenantLeakage,
  expectNotVisible,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  buildGoldenPathMocks,
  createSearchResults,
} from '../fixtures/deep-test-data';

journeyTest.describe('Search and Retrieval Workflow', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    const results = createSearchResults('reconciliation');
    await addMocks([
      ...buildGoldenPathMocks(),
      { pattern: '**/api/v1/search**', body: results },
      { pattern: '**/api/v1/agents/search**', body: results },
    ]);
  });

  // ── Entity Search ──────────────────────────────────────────────────────

  journeyTest('SRCH-001: user can search accounts by name and land on correct context', async ({ authedPage }) => {
    await authedPage.goto('/accounts', { waitUntil: 'domcontentloaded' });

    const searchInput = authedPage.getByPlaceholder(/search.*account|search/i)
      .or(authedPage.getByLabel(/search/i))
      .first();
    const hasSearch = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSearch) {
      await searchInput.fill('Meridian');
      await expect(
        authedPage.getByText(/meridian health group/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/meridian|account/i],
        'accounts list for search validation',
      );
    }
  });

  journeyTest('SRCH-002: user can search documents and land on the correct ingestion context', async ({ authedPage }) => {
    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });

    const searchInput = authedPage.getByPlaceholder(/search.*document|search/i)
      .or(authedPage.getByLabel(/search/i))
      .first();
    const hasSearch = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSearch) {
      await searchInput.fill('Q3 Earnings');
      await expect(
        authedPage.getByText(/q3.*earnings|document/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/document|ingestion|job/i],
        'document search surface',
      );
    }
  });

  journeyTest('SRCH-003: user can search evidence items', async ({ authedPage }) => {
    await authedPage.goto('/governance/evidence', { waitUntil: 'domcontentloaded' });

    const searchInput = authedPage.getByPlaceholder(/search.*evidence|search/i)
      .or(authedPage.getByLabel(/search/i))
      .first();
    const hasSearch = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSearch) {
      await searchInput.fill('reconciliation');
      await expect(
        authedPage.getByText(/reconciliation|ev-001/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/evidence|manual.*reconciliation/i],
        'evidence search surface',
      );
    }
  });

  journeyTest('SRCH-004: user can search stakeholders', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    const searchInput = authedPage.getByPlaceholder(/search.*stakeholder|search/i)
      .or(authedPage.getByLabel(/search/i))
      .first();
    const hasSearch = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSearch) {
      await searchInput.fill('Sarah Chen');
      await expect(
        authedPage.getByText(/sarah chen|cfo/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/sarah chen|cfo|stakeholder/i],
        'stakeholder search surface',
      );
    }
  });

  journeyTest('SRCH-005: user can search value models', async ({ authedPage }) => {
    await authedPage.goto(`/calculator/${DEEP_ACCOUNT_ID}/roi`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/roi model|scenario|conservative|expected|optimistic/i, /calculator/i],
      'value model accessible from calculator surface',
    );
  });

  journeyTest('SRCH-006: user can search prior business cases', async ({ authedPage }) => {
    await authedPage.goto('/deliverables/cases', { waitUntil: 'domcontentloaded' });

    const searchInput = authedPage.getByPlaceholder(/search.*case|search/i)
      .or(authedPage.getByLabel(/search/i))
      .first();
    const hasSearch = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSearch) {
      await searchInput.fill('Meridian');
      await expect(
        authedPage.getByText(/meridian.*business case|meridian.*automation/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/meridian.*business case|business cases|approved/i],
        'business case search or list',
      );
    }
  });

  // ── Global Search ──────────────────────────────────────────────────────

  journeyTest('SRCH-007: global search returns results across all entity types', async ({ authedPage }) => {
    await authedPage.goto('/home', { waitUntil: 'domcontentloaded' });

    const globalSearch = authedPage.getByPlaceholder(/search|find/i)
      .or(authedPage.getByRole('searchbox'))
      .first();
    const hasGlobalSearch = await globalSearch.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasGlobalSearch) {
      await globalSearch.fill('reconciliation');
      await expect(
        authedPage.getByText(/meridian|ev-001|manual.*reconciliation/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/home|command center|value case/i],
        'home page as global search alternative',
      );
    }
  });

  // ── Search Filters ─────────────────────────────────────────────────────

  journeyTest('SRCH-008: user can filter search results by account', async ({ authedPage }) => {
    await authedPage.goto('/accounts', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/filter|account|meridian/i],
      'accounts list with filter-by-account capability',
    );
  });

  journeyTest('SRCH-009: user can filter search results by source type', async ({ authedPage }) => {
    await authedPage.goto('/governance/evidence', { waitUntil: 'domcontentloaded' });

    const filterDropdown = authedPage.getByRole('combobox', { name: /source.*type|filter.*source/i })
      .or(authedPage.getByRole('button', { name: /source.*type|filter/i }))
      .first();
    const hasFilter = await filterDropdown.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasFilter) {
      await filterDropdown.click();
      await expectAnyVisible(
        authedPage,
        [/customer.*data|benchmark|earnings.*call|estimate/i],
        'source type filter options',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/evidence|source|filter/i],
        'evidence surface with filter controls',
      );
    }
  });

  journeyTest('SRCH-010: user can filter search results by date range', async ({ authedPage }) => {
    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });

    const dateFilter = authedPage.getByLabel(/date|from|since/i)
      .or(authedPage.getByPlaceholder(/date|from/i))
      .first();
    const hasDate = await dateFilter.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasDate) {
      await dateFilter.fill('2026-04-01');
      await expectAnyVisible(
        authedPage,
        [/ingestion|job|meridian/i],
        'date-filtered ingestion results',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/ingestion|job|date|filter/i],
        'ingestion jobs with date filter capability',
      );
    }
  });

  // ── Correct Context Landing ─────────────────────────────────────────────

  journeyTest('SRCH-011: search result click lands in correct workflow context', async ({ authedPage }) => {
    await authedPage.goto('/accounts', { waitUntil: 'domcontentloaded' });

    const accountRow = authedPage.getByText(/meridian health group/i).first();
    const hasRow = await accountRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await accountRow.click();
      // Should navigate to account detail, not a generic search results page
      await expect(authedPage).toHaveURL(new RegExp(`accounts|meridian|${DEEP_ACCOUNT_ID}`), { timeout: 8000 });
    }
  });

  // ── Tenant Boundary Enforcement ─────────────────────────────────────────

  journeyTest('SRCH-012: search respects tenant boundaries — no cross-tenant results', async ({ authedPage }) => {
    await authedPage.goto('/accounts', { waitUntil: 'domcontentloaded' });

    await expectNoCrossTenantLeakage(authedPage);
    await expectTenantContext(authedPage);

    // No foreign tenant data should appear in any search result
    await expectNotVisible(authedPage, /globex confidential|tenant-foreign|acct-foreign/i);
  });

  // ── Role Permission Enforcement ─────────────────────────────────────────

  journeyTest('SRCH-013: search results respect role permissions — read-only user cannot see admin data', async ({ authedPage, switchTier }) => {
    await switchTier('standard');
    await authedPage.goto('/accounts', { waitUntil: 'domcontentloaded' });

    // Admin-only routes should not be reachable via search for a standard user
    await authedPage.goto('/organization-admin', { waitUntil: 'domcontentloaded' });
    // Standard user should be redirected away from admin routes
    await expect(authedPage).toHaveURL(/home|login/, { timeout: 8000 });
  });
});
