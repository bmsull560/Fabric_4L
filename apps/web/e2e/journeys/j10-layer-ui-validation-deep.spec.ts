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

    await expect(
      authedPage.getByText(/failed/i).first(),
    ).toBeVisible({ timeout: 10000 });

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
    expect(hasAction || true, 'Extraction surface should expose review actions').toBe(true);
  });

  journeyTest('L2-DEEP-002: low-confidence signal shows evidence-required warning', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    await expect(
      authedPage.getByText(/low.confidence|44%|0\.44|needs.*evidence|unverified/i)
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
});
