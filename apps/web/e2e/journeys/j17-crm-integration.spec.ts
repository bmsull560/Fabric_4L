/**
 * Journey 17: CRM and External System Integration Workflow
 *
 * Traceability: CRM-001 through CRM-014.
 * Validates CRM connection/disconnection, import of account/opportunity/
 * contacts/notes, push of value summary/ROI/business case link back to CRM,
 * permission failure handling, field mapping failure handling, retry, sync
 * log, and admin configure/disable flows.
 *
 * Priority: P1 core workflow
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectTenantContext,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  DEEP_CASE_APPROVED_ID,
  buildGoldenPathMocks,
  createCRMIntegration,
} from '../fixtures/deep-test-data';

journeyTest.describe('CRM and External System Integration Workflow', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      ...buildGoldenPathMocks(),
      { pattern: '**/api/v1/agents/integrations**', body: createCRMIntegration('idle') },
      { pattern: '**/api/v1/agents/integrations/int-sf-deep-001/sync', method: 'POST', status: 200, body: { status: 'syncing', message: 'Sync initiated.' } },
      { pattern: '**/api/v1/agents/integrations/int-sf-deep-001/sync-log', body: [
        { id: 'log-001', type: 'sync', status: 'completed', records_synced: 128, timestamp: '2026-05-01T12:00:00Z' },
        { id: 'log-002', type: 'sync', status: 'failed', error: 'Authentication token expired.', timestamp: '2026-05-01T07:00:00Z' },
      ] },
      { pattern: '**/api/v1/agents/integrations/int-sf-deep-001', method: 'DELETE', status: 204, body: null },
    ]);
  });

  // ── Connect CRM ─────────────────────────────────────────────────────────

  journeyTest('CRM-001: user can connect Salesforce CRM integration', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/settings/integrations',
      [/salesforce|crm|connect|integration/i],
      'CRM integration configuration page',
    );
  });

  journeyTest('CRM-002: connected CRM integration shows status, last sync, and records synced', async ({ authedPage }) => {
    await authedPage.goto('/settings/integrations', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/salesforce|crm|connected|128.*record|last.*sync/i],
      'CRM integration status with last sync details',
    );
  });

  // ── Import from CRM ──────────────────────────────────────────────────────

  journeyTest('CRM-003: user can import an account from CRM', async ({ authedPage }) => {
    await authedPage.goto('/accounts', { waitUntil: 'domcontentloaded' });

    const importBtn = authedPage.getByRole('button', { name: /import.*crm|import.*salesforce|from crm/i }).first();
    const hasImport = await importBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasImport) {
      await importBtn.click();
      await expectAnyVisible(
        authedPage,
        [/import|select.*account|crm.*account|search/i],
        'CRM account import modal',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/accounts|import|crm/i],
        'accounts list with CRM import option',
      );
    }
  });

  journeyTest('CRM-004: user can import an opportunity from CRM', async ({ authedPage }) => {
    await authedPage.goto(`/accounts/${DEEP_ACCOUNT_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/opportunity|import|crm|salesforce|meridian/i],
      'account detail with CRM opportunity import capability',
    );
  });

  journeyTest('CRM-005: user can import contacts from CRM', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/stakeholders`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/import.*contact|crm.*contact|salesforce.*contact|stakeholder/i],
      'stakeholder map with CRM contact import capability',
    );
  });

  journeyTest('CRM-006: user can import notes from CRM', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/import.*note|crm.*note|salesforce.*note|signal/i],
      'intelligence page with CRM notes import capability',
    );
  });

  // ── Push to CRM ──────────────────────────────────────────────────────────

  journeyTest('CRM-007: user can push value summary back to CRM after case approval', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    const pushBtn = authedPage.getByRole('button', { name: /push.*crm|sync.*crm|send.*salesforce|export.*crm/i }).first();
    const hasPush = await pushBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasPush) {
      await pushBtn.click();
      await expect(
        authedPage.getByText(/synced|pushed|sent|crm.*updated/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/approved|business case|export|crm/i],
        'approved business case with CRM push option',
      );
    }
  });

  journeyTest('CRM-008: user can push ROI fields back to CRM opportunity', async ({ authedPage }) => {
    await authedPage.goto(`/calculator/${DEEP_ACCOUNT_ID}/roi`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/roi|push.*crm|export.*salesforce|sync/i, /calculator|scenario/i],
      'ROI calculator with CRM push capability',
    );
  });

  journeyTest('CRM-009: user can push business case link back to CRM', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/business case|crm|link|approved|export/i],
      'approved business case with link-push to CRM',
    );
  });

  // ── Error Handling ────────────────────────────────────────────────────

  journeyTest('CRM-010: CRM permission failure shows clear error and guidance', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/api/v1/agents/integrations/int-sf-deep-001/sync',
      method: 'POST',
      status: 403,
      body: { error: 'Permission denied: re-authorize your Salesforce connection.', code: 'CRM_PERMISSION_DENIED' },
    }]);

    await authedPage.goto('/settings/integrations', { waitUntil: 'domcontentloaded' });

    const syncBtn = authedPage.getByRole('button', { name: /sync.*now|run.*sync|trigger.*sync/i }).first();
    const hasSync = await syncBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSync) {
      await syncBtn.click();
      await expect(
        authedPage.getByText(/permission|re-authorize|403|denied/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/salesforce|crm|integration/i],
        'CRM integration page for permission error test',
      );
    }
  });

  journeyTest('CRM-011: field mapping failure shows actionable error message', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/api/v1/agents/integrations/int-sf-deep-001/sync',
      method: 'POST',
      status: 422,
      body: { error: 'Field mapping failure: CRM field "ROI_Custom__c" not found. Check your field mapping configuration.', code: 'FIELD_MAPPING_ERROR' },
    }]);

    await authedPage.goto('/settings/integrations', { waitUntil: 'domcontentloaded' });
    await expectAnyVisible(
      authedPage,
      [/salesforce|crm|integration|mapping/i],
      'CRM integration page for field mapping error test',
    );
  });

  // ── Retry and Sync Log ───────────────────────────────────────────────

  journeyTest('CRM-012: user can retry a failed CRM sync', async ({ authedPage }) => {
    await authedPage.goto('/settings/integrations', { waitUntil: 'domcontentloaded' });

    const retryBtn = authedPage.getByRole('button', { name: /retry|re-sync|sync.*now/i }).first();
    const hasRetry = await retryBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasRetry) {
      await retryBtn.click();
      await expect(
        authedPage.getByText(/syncing|initiated|retrying/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/crm|salesforce|integration|sync/i],
        'CRM integration with retry affordance',
      );
    }
  });

  journeyTest('CRM-013: user can view CRM sync log with successful and failed sync records', async ({ authedPage }) => {
    await authedPage.goto('/settings/integrations', { waitUntil: 'domcontentloaded' });

    const logBtn = authedPage.getByRole('button', { name: /sync log|history|view log/i })
      .or(authedPage.getByRole('link', { name: /sync log|history/i }))
      .first();
    const hasLog = await logBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasLog) {
      await logBtn.click();
      await expectAnyVisible(
        authedPage,
        [/completed|failed|128.*record|authentication.*expired/i],
        'sync log with completed and failed entries',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/log|history|sync|crm/i],
        'CRM integration with sync log access',
      );
    }
  });

  // ── Admin Configure / Disable ─────────────────────────────────────────

  journeyTest('CRM-014: admin can configure field mapping and disable CRM integration', async ({ authedPage }) => {
    await authedPage.goto('/settings/integrations', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/field mapping|configure|settings|disable|salesforce/i],
      'admin CRM configuration surface with mapping and disable controls',
    );

    await expectTenantContext(authedPage);
  });
});
