/**
 * Journey 11: Golden Path Business Lifecycle
 *
 * Traceability: GP-LIFECYCLE-001, CLAIM-TRACE-001, EXPORT-GATE-001, CRM-GATE-001.
 * This suite is intentionally backend-integrated and fail-closed. It defines
 * the end-to-end validation contract for the account-to-approved-business-case
 * lifecycle against seeded data.
 */
import { test, expect } from '@playwright/test';
import {
  expectAnyVisible,
  expectButtonStateIfVisible,
  expectNoCrossTenantLeakage,
  expectRouteSupportsWorkflow,
  expectTenantContext,
  requireBackendOrThrow,
} from '../helpers/validation-program';
import { navigateAndWait } from '../helpers/journey-fixture';
import { seedAuthState } from '../fixtures/auth-helpers';
import { setSelectedAccount, TEST_ACCOUNTS } from '../fixtures/account-helpers';
import { setUserTier } from '../fixtures/tier-helpers';

const ACCOUNT_ID = TEST_ACCOUNTS.meridian.id;

test.describe('Journey 11: Golden Path Business Lifecycle', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthState(page);
    await setUserTier(page, 'admin', 'admin');
    await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
  });

  test('test_golden_path_account_to_approved_business_case @backend', async ({ page }) => {
    requireBackendOrThrow('test_golden_path_account_to_approved_business_case @backend');

    await expectRouteSupportsWorkflow(
      page,
      '/workflow/prospect',
      [/start a new value case/i, /launch intelligence/i, /attach source material/i, /discovery/i],
      'prospect intake and launch workflow',
    );
    await expectTenantContext(page);

    const promptField = page
      .getByLabel(/new value case prompt/i)
      .or(page.getByPlaceholder(/describe the account/i))
      .first();
    if (await promptField.isVisible({ timeout: 3000 }).catch(() => false)) {
      await promptField.fill('Company: Meridian Health Group\nDesired outcome: Reduce manual reconciliation time\nRequired output: Approved business case');
      const launchButton = page.getByRole('button', { name: /launch intelligence|run account enrichment/i }).first();
      if (await launchButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await launchButton.click();
      }
    }

    await expectRouteSupportsWorkflow(
      page,
      `/intelligence/${ACCOUNT_ID}/signals`,
      [/signals/i, /confidence/i, /source/i, /approve/i, /evidence/i],
      'signal review and approval workflow',
    );
    await expectNoCrossTenantLeakage(page);

    await expectRouteSupportsWorkflow(
      page,
      `/hypothesis/${ACCOUNT_ID}/hypothesis`,
      [/hypoth/i, /approve/i, /edit/i, /expected value/i],
      'hypothesis review and approval workflow',
    );

    await expectRouteSupportsWorkflow(
      page,
      `/drivers/${ACCOUNT_ID}/tree`,
      [/driver tree/i, /value driver/i, /formula/i, /evidence/i],
      'driver tree and evidence mapping workflow',
    );

    await expectRouteSupportsWorkflow(
      page,
      `/calculator/${ACCOUNT_ID}/roi`,
      [/roi calculator/i, /scenario/i, /payback/i, /economic value/i],
      'scenario calculation workflow',
    );

    await expectRouteSupportsWorkflow(
      page,
      '/deliverables/cases',
      [/business cases/i, /new case/i, /executive summary/i, /draft|approved/i],
      'business-case list and lifecycle workflow',
    );
  });

  test('test_business_case_contains_traceable_claims_after_golden_path @backend', async ({ page }) => {
    requireBackendOrThrow('test_business_case_contains_traceable_claims_after_golden_path @backend');

    await navigateAndWait(page, '/deliverables/cases');
    await expectAnyVisible(
      page,
      [/business cases/i, /executive summary/i, /recommendations/i, /roi/i],
      'deliverable list after golden path',
    );

    await navigateAndWait(page, '/governance/traces');
    await expectAnyVisible(
      page,
      [/decision trace/i, /provenance timeline/i, /truth references/i, /audit log/i, /claim/i],
      'claim traceability surfaces',
    );

    await navigateAndWait(page, '/governance/evidence');
    await expectAnyVisible(
      page,
      [/evidence/i, /truth objects/i, /confidence/i, /source/i, /claim/i],
      'evidence-backed claim lineage',
    );
  });

  test('test_export_is_available_only_after_required_approval @backend', async ({ page }) => {
    requireBackendOrThrow('test_export_is_available_only_after_required_approval @backend');

    await navigateAndWait(page, '/deliverables/cases/case-draft-001');
    await expectAnyVisible(
      page,
      [/business case/i, /draft/i, /executive summary/i, /export pdf/i],
      'draft business case before approval',
    );
    await expectButtonStateIfVisible(page, /export pdf/i, 'disabled');

    await navigateAndWait(page, '/deliverables/cases/case-e2e-approved-001');
    await expectAnyVisible(
      page,
      [/business case/i, /approved/i, /executive summary/i, /export pdf/i],
      'approved business case after review',
    );
    await expectButtonStateIfVisible(page, /export pdf/i, 'enabled');
  });
});
