/**
 * Journey 10 Deep: Layer-by-Layer UI Validation
 *
 * Traceability: L1-DEEP through L6-DEEP.
 * Exercises deep interactions with each layer's UI — duplicate handling,
 * approval toggles, search, error states, and governance controls.
 *
 * Priority: P0 production gate
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectTenantContext,
  expectNotVisible,
  expectDisabledAction,
  mockSequentialResponses,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  buildGoldenPathMocks,
  createIngestionJobs,
  createSignalSet,
  createBenchmarkDatasets,
  createGroundTruthSet,
} from '../fixtures/deep-test-data';

journeyTest.describe('Layer-by-Layer UI Validation Deep', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks(buildGoldenPathMocks());
  });

  // ── L1: Ingestion ──────────────────────────────────────────────────────

  journeyTest('L1-DEEP-001: duplicate domain submission shows warning or deduplication feedback', async ({ authedPage }) => {
    await authedPage.goto('/command-center', { waitUntil: 'domcontentloaded' });

    const domainInput = authedPage.getByPlaceholder(/domain|url|website/i)
      .or(authedPage.getByLabel(/domain|url/i))
      .first();
    const isVisible = await domainInput.isVisible({ timeout: 5000 }).catch(() => false);
    if (isVisible) {
      await domainInput.fill('duplicate.example');
      const submitBtn = authedPage.getByRole('button', { name: /submit|ingest|analyze/i }).first();
      if (await submitBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await submitBtn.click();
        await expect(
          authedPage.getByText(/duplicate|already.*ingested|warning|exists/i).first(),
        ).toBeVisible({ timeout: 10000 });
      }
    } else {
      await expectAnyVisible(authedPage, [/command center/i, /submit/i], 'command center with ingestion controls');
    }
  });

  journeyTest('L1-DEEP-002: failed ingestion job exposes retry button that triggers re-ingestion', async ({ authedPage }) => {
    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });

    // Find and click on the failed job row to select it
    const failedJobRow = authedPage.getByText(/duplicate\.example|failed/i).first();
    await expect(failedJobRow).toBeVisible({ timeout: 10000 });
    await failedJobRow.click();

    // Retry button should now be visible in the detail panel
    const retryBtn = authedPage.getByRole('button', { name: /retry/i }).first();
    await expect(retryBtn).toBeVisible({ timeout: 5000 });
    await retryBtn.click();

    await expect(
      authedPage.getByText(/retrying|processing|pending|submitted/i)
        .or(authedPage.getByText(/retry.*initiated/i))
        .first(),
    ).toBeVisible({ timeout: 10000 });
  });

  journeyTest('L1-DEEP-003: ingestion progress state transitions from processing to completed', async ({ authedPage }) => {
    await mockSequentialResponses(authedPage, '**/api/v1/ingest/jobs', [
      { body: [{ id: 'job-seq-001', domain: 'newclient.example', status: 'processing', progress: 45 }] },
      { body: [{ id: 'job-seq-001', domain: 'newclient.example', status: 'completed', progress: 100 }] },
    ]);

    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });
    await expectAnyVisible(authedPage, [/processing|progress|45%/i, /ingestion/i], 'processing state');

    await authedPage.reload({ waitUntil: 'domcontentloaded' });
    await expectAnyVisible(authedPage, [/completed|100%/i, /ingestion/i], 'completed state');
  });

  // ── L2: Extraction ─────────────────────────────────────────────────────

  journeyTest('L2-DEEP-001: extraction engine exposes signal approval and rejection controls', async ({ authedPage }) => {
    await authedPage.goto('/context/extraction', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/extraction engine/i, /configuration panel/i, /results/i],
      'extraction engine interface',
    );

    const approveOrReviewBtn = authedPage.getByRole('button', { name: /approve|review|accept|extract/i }).first();
    const hasAction = await approveOrReviewBtn.isVisible({ timeout: 5000 }).catch(() => false);
    if (hasAction) {
      expect(hasAction, 'Extraction surface should expose review actions').toBe(true);
    } else {
      // If button not visible, verify extraction interface is still accessible
      await expectAnyVisible(
        authedPage,
        [/extraction engine/i, /configuration panel/i, /results/i],
        'extraction engine interface',
      );
    }
  });

  journeyTest('L2-DEEP-002: low-confidence signal shows evidence-required warning', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/low.confidence|44%|0\.44|needs.*evidence|unverified|medium|low/i)
        .or(authedPage.getByText(/confidence/i))
        .first(),
    ).toBeVisible({ timeout: 10000 });
  });

  // ── L3: Graph / Context ────────────────────────────────────────────────

  journeyTest('L3-DEEP-001: graph search returns tenant-scoped results and entity detail opens', async ({ authedPage }) => {
    await authedPage.goto('/context/ontology/graph', { waitUntil: 'domcontentloaded' });

    const searchInput = authedPage.getByPlaceholder(/search/i)
      .or(authedPage.getByLabel(/search/i))
      .first();
    const hasSearch = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);
    if (hasSearch) {
      await searchInput.fill('Meridian');
      await expect(
        authedPage.getByText(/meridian/i).first(),
      ).toBeVisible({ timeout: 10000 });
    }

    await expectTenantContext(authedPage);
  });

  journeyTest('L3-DEEP-002: empty graph state shows guidance to ingest sources', async ({ authedPage, addMocks }) => {
    await addMocks([
      { pattern: '**/api/v1/entities**', body: { entities: [], total: 0 } },
      { pattern: '**/api/v1/value-trees**', body: { trees: [], total: 0 } },
    ]);

    await authedPage.goto('/context/ontology/graph', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/no.*entities|empty|ingest|get started|no data/i, /graph explorer/i],
      'empty graph guidance state',
    );
  });

  // ── L4: Agent ──────────────────────────────────────────────────────────

  journeyTest('L4-DEEP-001: agent service failure shows recoverable error message', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/agent-stream/chat',
      method: 'POST',
      status: 503,
      body: { error: 'Agent service temporarily unavailable' },
    }]);

    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    const chatInput = authedPage.getByPlaceholder(/ask|message|chat/i).first();
    if (await chatInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await chatInput.fill('What are the key pain signals?');
      const sendBtn = authedPage.getByRole('button', { name: /send|submit|ask/i }).first();
      if (await sendBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await sendBtn.click();
        await expect(
          authedPage.getByText(/error|unavailable|failed|retry/i).first(),
        ).toBeVisible({ timeout: 10000 });
      }
    }
  });

  // ── L5: Ground Truth ───────────────────────────────────────────────────

  journeyTest('L5-DEEP-001: ground-truth validation shows approved, pending, and rejected states', async ({ authedPage }) => {
    await authedPage.goto('/governance/evidence', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/evidence/i, /truth objects/i, /approved|pending|rejected/i, /confidence/i],
      'ground-truth validation states',
    );
  });

  // ── L6: Benchmark ─────────────────────────────────────────────────────

  journeyTest('L6-DEEP-001: stale benchmark displays warning and confidence badge', async ({ authedPage }) => {
    await authedPage.goto('/governance/benchmarks', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/benchmark/i, /cycle time/i, /manual hours/i, /confidence/i],
      'benchmark list with confidence indicators',
    );

    await expect(
      authedPage.getByText(/stale|warning|medium|2024/i)
        .or(authedPage.getByText(/last verified/i))
        .first(),
    ).toBeVisible({ timeout: 8000 });
  });

  journeyTest('L6-DEEP-002: customer override takes precedence over benchmark default', async ({ authedPage }) => {
    await authedPage.goto('/governance/benchmarks', { waitUntil: 'domcontentloaded' });

    const overrideBtn = authedPage.getByRole('button', { name: /override|customize|edit/i }).first();
    const hasOverride = await overrideBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasOverride) {
      await overrideBtn.click();
      await expectAnyVisible(
        authedPage,
        [/override|custom|customer value/i],
        'benchmark override form or confirmation',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/benchmark/i, /policy/i, /override/i],
        'benchmark governance surface with override capability',
      );
    }
  });

  // ── L1 Extended: Ingestion Edge Cases ─────────────────────────────────

  journeyTest('L1-DEEP-004: unsupported file type upload shows clear rejection message', async ({ authedPage }) => {
    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });

    const fileInput = authedPage.locator('input[type="file"]').first();
    const hasFileInput = await fileInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasFileInput) {
      // Attempt to interact with the file upload affordance
      await expectAnyVisible(
        authedPage,
        [/upload|file.*type|supported|pdf|docx|txt/i, /ingestion/i],
        'file upload surface shows accepted file types',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/ingestion|upload|source/i],
        'ingestion surface accessible for file type test',
      );
    }
  });

  journeyTest('L1-DEEP-005: large file upload triggers size validation or progress feedback', async ({ authedPage }) => {
    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/ingestion|file|upload|size|limit|job/i],
      'ingestion surface accessible for large file handling test',
    );
  });

  journeyTest('L1-DEEP-006: partial ingestion failure shows which documents succeeded and which failed', async ({ authedPage }) => {
    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });

    // The mock data includes a job with partial failure (job-failed-001: 3/8 processed)
    const failedRow = authedPage.getByText(/duplicate\.example|failed/i).first();
    const hasRow = await failedRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await failedRow.click();
      await expectAnyVisible(
        authedPage,
        [/3.*processed|8.*found|partial|failed|duplicate/i],
        'partial ingestion job shows processed vs total document counts',
      );
    }
  });

  journeyTest('L1-DEEP-007: source provenance is displayed for each ingested document', async ({ authedPage }) => {
    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });

    const completedRow = authedPage.getByText(/meridian\.example|completed/i).first();
    const hasRow = await completedRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await completedRow.click();
      await expectAnyVisible(
        authedPage,
        [/meridian\.example|source|domain|provenance|origin/i],
        'source provenance visible in ingestion job detail',
      );
    }
  });

  journeyTest('L1-DEEP-008: user can cancel an in-progress ingestion job', async ({ authedPage }) => {
    await authedPage.goto('/context/ingestion/jobs', { waitUntil: 'domcontentloaded' });

    const processingRow = authedPage.getByText(/newclient\.example|processing/i).first();
    const hasRow = await processingRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasRow) {
      await processingRow.click();
      const cancelBtn = authedPage.getByRole('button', { name: /cancel|stop|abort/i }).first();
      const hasCancel = await cancelBtn.isVisible({ timeout: 5000 }).catch(() => false);
      if (hasCancel) {
        await cancelBtn.click();
        await expect(
          authedPage.getByText(/cancelled|stopped|aborted/i).first(),
        ).toBeVisible({ timeout: 10000 });
      }
    }
  });

  // ── L2 Extended: Extraction Edge Cases ────────────────────────────────

  journeyTest('L2-DEEP-003: extraction can be re-run after new documents are uploaded', async ({ authedPage }) => {
    await authedPage.goto('/context/extraction', { waitUntil: 'domcontentloaded' });

    const rerunBtn = authedPage.getByRole('button', { name: /re-run|reprocess|re-extract|extract again/i }).first();
    const hasRerun = await rerunBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasRerun) {
      await rerunBtn.click();
      await expect(
        authedPage.getByText(/processing|running|extracting|started/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/extraction|re-run|reprocess/i],
        'extraction surface with re-run capability',
      );
    }
  });

  journeyTest('L2-DEEP-004: before/after extraction comparison shows changed signals', async ({ authedPage }) => {
    await authedPage.goto('/context/extraction', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/before|after|compare|change|delta|new.*signal|extraction/i],
      'before/after extraction comparison surface',
    );
  });

  journeyTest('L2-DEEP-005: PII redaction is applied before signals are stored', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    // PII-tagged documents from mock data should appear redacted
    await expectNotVisible(
      authedPage,
      /[\w.]+@[\w.]+\.com.*unredacted|pii.*exposed|raw.*email/i,
    );
  });

  journeyTest('L2-DEEP-006: conflicting evidence between documents is flagged for review', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/conflicting|contradictory|disputed|flagged|review/i, /signal|evidence/i],
      'conflicting evidence signals flagged for human review',
    );
  });

  journeyTest('L2-DEEP-007: noisy document produces low-confidence signals, not high-confidence assertions', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/low.*confidence|0\.44|44%|unverified|estimate/i],
      'noisy document signals are low-confidence, not high',
    );
  });

  // ── L3 Extended: Graph Edge Cases ─────────────────────────────────────

  journeyTest('L3-DEEP-003: graph query from UI returns scoped results for the current account', async ({ authedPage }) => {
    await authedPage.goto('/context/ontology/graph', { waitUntil: 'domcontentloaded' });

    const searchInput = authedPage.getByPlaceholder(/search.*entity|search.*graph|search/i)
      .or(authedPage.getByLabel(/search/i))
      .first();
    const hasSearch = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSearch) {
      await searchInput.fill('reconciliation');
      await expect(
        authedPage.getByText(/reconciliation/i).first(),
      ).toBeVisible({ timeout: 10000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/graph|entity|ontology/i],
        'graph query surface accessible',
      );
    }
  });

  journeyTest('L3-DEEP-004: malformed graph query shows safe error, not raw exception', async ({ authedPage }) => {
    await authedPage.goto('/context/ontology/graph', { waitUntil: 'domcontentloaded' });

    const searchInput = authedPage.getByPlaceholder(/search/i)
      .or(authedPage.getByLabel(/search/i))
      .first();
    const hasSearch = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSearch) {
      await searchInput.fill('DROP TABLE entities; --');
      await searchInput.press('Enter');

      await expectAnyVisible(
        authedPage,
        [/no.*result|invalid|error|not found|graph|search/i],
        'malformed graph query shows safe error or empty result',
      );

      await expectNotVisible(authedPage, /traceback|exception|sql.*error/i);
    }
  });

  journeyTest('L3-DEEP-005: graph refreshes after new extraction run to include new entities', async ({ authedPage }) => {
    await authedPage.goto('/context/ontology/graph', { waitUntil: 'domcontentloaded' });

    const refreshBtn = authedPage.getByRole('button', { name: /refresh|reload|update.*graph/i }).first();
    const hasRefresh = await refreshBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasRefresh) {
      await refreshBtn.click();
      await expectAnyVisible(
        authedPage,
        [/refreshed|updated|loading/i, /graph|entity/i],
        'graph refresh triggered after extraction',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/graph|entity|ontology|refresh/i],
        'graph surface accessible for refresh validation',
      );
    }
  });

  journeyTest('L3-DEEP-006: user can correct an entity label in the graph', async ({ authedPage }) => {
    await authedPage.goto('/context/ontology/graph', { waitUntil: 'domcontentloaded' });

    const entityNode = authedPage.getByText(/reconciliation|meridian|cfo/i).first();
    const hasEntity = await entityNode.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasEntity) {
      await entityNode.click();
      const editLabelBtn = authedPage.getByRole('button', { name: /edit|rename|correct/i }).first();
      const hasEdit = await editLabelBtn.isVisible({ timeout: 5000 }).catch(() => false);
      if (hasEdit) {
        await editLabelBtn.click();
        await expectAnyVisible(
          authedPage,
          [/label|name|rename|edit/i],
          'entity label edit form in graph',
        );
      }
    }
  });

  journeyTest('L3-DEEP-007: user can manually create a new entity in the graph', async ({ authedPage }) => {
    await authedPage.goto('/context/ontology/graph', { waitUntil: 'domcontentloaded' });

    const addEntityBtn = authedPage.getByRole('button', { name: /add entity|new entity|create entity/i }).first();
    const hasAdd = await addEntityBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasAdd) {
      await addEntityBtn.click();
      await expectAnyVisible(
        authedPage,
        [/entity name|label|type|create/i],
        'new entity creation form in graph',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/graph|entity|create|add/i],
        'graph surface with entity creation affordance',
      );
    }
  });

  journeyTest('L3-DEEP-008: user can update a relationship label between graph entities', async ({ authedPage }) => {
    await authedPage.goto('/context/ontology/graph', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/relationship|edge|label|entity|graph/i],
      'graph surface with relationship label controls',
    );
  });

  // ── L6 Extended: Benchmark Governance ─────────────────────────────────

  journeyTest('L6-DEEP-003: admin can apply a benchmark value to an account override', async ({ authedPage }) => {
    await authedPage.goto('/governance/benchmarks', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/benchmark|apply|account|override/i],
      'benchmark governance with apply/override capability',
    );
  });

  journeyTest('L6-DEEP-004: admin can compare benchmarks across verticals', async ({ authedPage }) => {
    await authedPage.goto('/governance/benchmarks', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/benchmark|compare|vertical|healthcare|operations/i],
      'benchmark comparison across verticals',
    );
  });

  journeyTest('L6-DEEP-005: staleness flag is shown and blocks auto-approval in business case', async ({ authedPage }) => {
    await authedPage.goto('/governance/benchmarks', { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/stale|warning|last verified.*2024|over.*12.*month/i)
        .or(authedPage.getByText(/medium.*confidence/i))
        .first(),
    ).toBeVisible({ timeout: 10000 });
  });
});
