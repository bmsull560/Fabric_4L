/**
 * Journey 7: Calculation, Evidence Integrity, and Value Realization
 *
 * Traceability: CALC-001, EVIDENCE-001, VALUE-REALIZATION-001, L5-GROUNDTRUTH-001, L6-BENCHMARK-001.
 * The suite validates that economic modeling, evidence lineage, ground-truth
 * review, benchmark policy, and realization tracking are exposed as user-facing
 * workflows rather than only API or route-smoke coverage.
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import { expectAnyVisible, expectRouteSupportsWorkflow, expectTenantContext } from '../helpers/validation-program';

const ACCOUNT_ID = 'acct-meridian';

journeyTest.describe('Journey 7: Calculation, Evidence Integrity, and Value Realization', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      {
        pattern: `**/api/v1/agents/workspace/${ACCOUNT_ID}/evidence`,
        body: {
          status: 'ready',
          generated_at: '2026-05-01T12:00:00Z',
          content: {
            evidence: [
              { id: 'ev-001', title: 'Manual reconciliation baseline', source: 'Discovery Notes', confidence: 0.91 },
            ],
          },
        },
      },
      {
        pattern: '**/api/v1/benchmarks/datasets**',
        body: [
          {
            id: 'bench-001',
            benchmark_id: 'bench-manual-hours-saved',
            name: 'Manual Hours Saved',
            industry: 'Healthcare',
            vertical: 'Operations',
            value_range: '18-27%',
            confidence: 'High',
            source: 'Validated customer outcomes',
            year: 2026,
            status: 'active',
            tags: ['stale-warning', 'override-review'],
            last_verified: '2026-05-01T12:00:00Z',
            usage_count: 14,
            description: 'Benchmark policy evidence for manual reconciliation automation.',
          },
        ],
      },
      {
        pattern: '**/api/v1/agents/ground-truth/truths**',
        body: {
          truths: [
            {
              id: 'truth-001',
              truth_id: 'truth-001',
              claim: 'CFO discovery note validates baseline reconciliation hours.',
              status: 'approved',
              maturity: 'corroborated',
              confidence: 0.91,
              stale: false,
              freshness: 'current',
              source: 'CFO discovery note',
            },
          ],
          total: 1,
        },
      },
    ]);
  });

  journeyTest('Step 1 [CALC-001]: ROI calculator exposes scenario modeling and reproducibility anchors', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      `/calculator/${ACCOUNT_ID}/roi`,
      [/roi calculator/i, /scenario-based roi/i, /conservative/i, /expected/i, /optimistic/i, /payback/i],
      'ROI calculator with scenario and payback workflow',
    );
    await expectTenantContext(authedPage);
  });

  journeyTest('Step 2 [CALC-002]: value model exposes value-line and formula model surface', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      `/calculator/${ACCOUNT_ID}/value-model`,
      [/value model/i, /value lines/i, /formula/i, /model/i],
      'value model formula and value-line surface',
    );
  });

  journeyTest('Step 3 [EVIDENCE-001]: driver evidence surface supports traceable value-driver mapping', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      `/drivers/${ACCOUNT_ID}/evidence`,
      [/evidence/i, /driver/i, /source/i, /confidence/i, /alternatives/i],
      'driver evidence mapping and source confidence workflow',
    );
  });

  journeyTest('Step 4 [L5-GROUNDTRUTH-001]: governance evidence exposes truth references and provenance', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/governance/evidence',
      [/evidence/i, /truth objects/i, /search claim/i, /confidence/i, /status/i],
      'ground-truth evidence, source lineage, and provenance workflow',
    );
  });

  journeyTest('Step 5 [L6-BENCHMARK-001]: benchmark governance exposes policy and confidence controls', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/governance/benchmarks',
      [/benchmark/i, /policy/i, /confidence/i, /override/i, /stale/i],
      'benchmark selection, warning, confidence, and policy enforcement surface',
    );
  });

  journeyTest('Step 6 [VALUE-REALIZATION-001]: user can track projected versus realized value', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      `/realization/${ACCOUNT_ID}`,
      [/value realization/i, /action plan/i, /outcomes/i, /baseline/i, /actual/i, /renewal/i],
      'value realization target, baseline, actuals, and renewal narrative workflow',
    );

    await expectAnyVisible(authedPage, [/value realization/i, /action plan/i], 'realization page shell');
  });

  journeyTest('Step 7 [CALC-RELOAD-001]: calculation surfaces remain stable after reload', async ({ authedPage }) => {
    await authedPage.goto(`/calculator/${ACCOUNT_ID}/roi`, { waitUntil: 'domcontentloaded' });
    await authedPage.reload({ waitUntil: 'domcontentloaded' });
    await expect(authedPage.getByText(/roi calculator|scenario-based roi|payback/i).first()).toBeVisible({ timeout: 10000 });
  });
});
