/**
 * CRM and External Integrations Validation Suite
 *
 * Traceability: CRM-001, CRM-IMPORT-001, CRM-PUSH-001, CRM-FAIL-001.
 * These tests validate that CRM connect, import, push, retry, and sync-log
 * workflows are visible and fail safely through the UI.
 */
import { journeyTest } from '../helpers/journey-fixture';
import {
  attemptOptionalAction,
  expectAnyVisible,
  expectRouteSupportsWorkflow,
} from '../helpers/validation-program';

journeyTest.describe('CRM and External Integrations Validation Suite', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      {
        pattern: '**/api/v1/agents/integrations**',
        body: {
          integrations: [
            {
              id: 'int-salesforce-001',
              provider: 'salesforce',
              enabled: true,
              status: 'error',
              instance_url: 'https://tenant.salesforce.com',
              records_failed: 3,
              last_error_message: 'Field mapping failure: ROI field is not writable.',
              sync_log: [
                { id: 'sync-001', outcome: 'failure', message: 'Permission denied on ROI field push.' },
              ],
            },
          ],
        },
      },
    ]);
  });

  journeyTest('test_crm_sync_failure_displays_retryable_status', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/context/integrations',
      [/integrations/i, /crm/i, /salesforce/i, /retry/i, /sync log/i, /field mapping/i],
      'CRM connection and failed-sync workflow',
    );

    const attempted = await attemptOptionalAction(authedPage, /retry|sync|push/i);
    if (attempted) {
      await expectAnyVisible(
        authedPage,
        [/retry/i, /permission/i, /failed/i, /mapping/i, /started/i],
        'CRM retry status feedback',
      );
    }
  });

  journeyTest('test_crm_import_and_push_controls_are_visible_to_authorized_users', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/context/integrations',
      [/connect crm/i, /import account/i, /import opportunity/i, /push roi/i, /business case link/i],
      'CRM import and push controls',
    );
  });
});
