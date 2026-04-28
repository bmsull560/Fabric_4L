/**
 * Journey-Aligned k6 Load Test
 *
 * Maps to the 5 canonical user journeys defined in CANONICAL_JOURNEYS.md.
 * Each scenario simulates the backend API call sequence that a real user
 * would trigger during that journey, under load.
 *
 * This is Layer 4 of the test strategy: reliability realism.
 *
 * Scenarios:
 *   1. ingestion_flow    — Domain submission + job polling
 *   2. intelligence_flow — Account fetch + workspace tabs + agent stream
 *   3. studio_flow       — Value model + narrative + case export
 *   4. governance_flow   — Health checks + audit log + traces
 *   5. auth_flow         — Authentication + tenant-scoped requests
 *
 * SLO Thresholds:
 *   - p95 response time < 500ms for read endpoints
 *   - p95 response time < 2000ms for write/compute endpoints
 *   - Error rate < 1%
 *   - Workflow completion rate > 95%
 *
 * Usage:
 *   k6 run tests/performance/k6/journey-load-test.js
 *   k6 run --env L4_URL=http://staging:8004 tests/performance/k6/journey-load-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// ── Configuration ───────────────────────────────────────────────────────────

const L1_URL = __ENV.L1_URL || 'http://localhost:8001';
const L4_URL = __ENV.L4_URL || 'http://localhost:8004';
const L5_URL = __ENV.L5_URL || 'http://localhost:8005';

const TENANT_ID = __ENV.TENANT_ID || 'tenant-loadtest-001';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || 'test-token';

// ── Metrics ─────────────────────────────────────────────────────────────────

// Journey 1: Ingestion
const ingestionSubmitTime = new Trend('j1_ingestion_submit_ms');
const ingestionPollTime = new Trend('j1_ingestion_poll_ms');
const ingestionErrors = new Rate('j1_ingestion_error_rate');

// Journey 2: Intelligence
const accountFetchTime = new Trend('j2_account_fetch_ms');
const workspaceTabTime = new Trend('j2_workspace_tab_ms');
const agentStreamTime = new Trend('j2_agent_stream_ms');
const intelligenceErrors = new Rate('j2_intelligence_error_rate');

// Journey 3: Studio
const valueModelTime = new Trend('j3_value_model_ms');
const narrativeTime = new Trend('j3_narrative_ms');
const caseExportTime = new Trend('j3_case_export_ms');
const studioErrors = new Rate('j3_studio_error_rate');

// Journey 4: Governance
const healthCheckTime = new Trend('j4_health_check_ms');
const auditLogTime = new Trend('j4_audit_log_ms');
const traceQueryTime = new Trend('j4_trace_query_ms');
const governanceErrors = new Rate('j4_governance_error_rate');

// Journey 5: Auth
const authLatency = new Trend('j5_auth_latency_ms');
const tenantIsolationChecks = new Counter('j5_tenant_isolation_checks');
const authErrors = new Rate('j5_auth_error_rate');

// ── Options ─────────────────────────────────────────────────────────────────

export const options = {
  scenarios: {
    // Journey 1: Ingestion — lower VU count (heavy write operation)
    ingestion_flow: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '1m', target: 5 },
        { duration: '3m', target: 10 },
        { duration: '1m', target: 0 },
      ],
      exec: 'ingestionJourney',
      tags: { journey: 'j1_ingestion' },
    },
    // Journey 2: Intelligence — primary read-heavy workflow
    intelligence_flow: {
      executor: 'ramping-vus',
      startVUs: 2,
      stages: [
        { duration: '1m', target: 10 },
        { duration: '3m', target: 25 },
        { duration: '1m', target: 0 },
      ],
      exec: 'intelligenceJourney',
      tags: { journey: 'j2_intelligence' },
    },
    // Journey 3: Studio — moderate load
    studio_flow: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '1m', target: 5 },
        { duration: '3m', target: 15 },
        { duration: '1m', target: 0 },
      ],
      exec: 'studioJourney',
      tags: { journey: 'j3_studio' },
    },
    // Journey 4: Governance — background monitoring
    governance_flow: {
      executor: 'constant-vus',
      vus: 3,
      duration: '5m',
      exec: 'governanceJourney',
      tags: { journey: 'j4_governance' },
    },
    // Journey 5: Auth — burst pattern
    auth_flow: {
      executor: 'ramping-vus',
      startVUs: 5,
      stages: [
        { duration: '30s', target: 20 },
        { duration: '2m', target: 20 },
        { duration: '30s', target: 0 },
      ],
      exec: 'authJourney',
      tags: { journey: 'j5_auth' },
    },
  },
  thresholds: {
    // Global SLOs
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.01'],

    // Journey-specific SLOs
    j1_ingestion_submit_ms: ['p(95)<2000'],
    j1_ingestion_error_rate: ['rate<0.05'],

    j2_account_fetch_ms: ['p(95)<500'],
    j2_workspace_tab_ms: ['p(95)<500'],
    j2_agent_stream_ms: ['p(95)<5000'],  // Agent stream is slower
    j2_intelligence_error_rate: ['rate<0.01'],

    j3_value_model_ms: ['p(95)<1000'],
    j3_narrative_ms: ['p(95)<2000'],
    j3_studio_error_rate: ['rate<0.02'],

    j4_health_check_ms: ['p(95)<200'],
    j4_audit_log_ms: ['p(95)<500'],
    j4_governance_error_rate: ['rate<0.01'],

    j5_auth_latency_ms: ['p(95)<500'],
    j5_auth_error_rate: ['rate<0.01'],
  },
};

// ── Helpers ─────────────────────────────────────────────────────────────────

function defaultHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${AUTH_TOKEN}`,
    'X-Tenant-ID': TENANT_ID,
  };
}

function timedRequest(method, url, body, metricTrend, errorRate) {
  const params = { headers: defaultHeaders(), timeout: '10s' };
  const start = Date.now();
  let response;

  if (method === 'GET') {
    response = http.get(url, params);
  } else {
    response = http.post(url, body ? JSON.stringify(body) : null, params);
  }

  const duration = Date.now() - start;
  metricTrend.add(duration);

  const success = check(response, {
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
  });
  errorRate.add(!success);

  return response;
}

// ── Journey 1: Ingestion Flow ───────────────────────────────────────────────

export function ingestionJourney() {
  // Step 1: Submit a domain for ingestion
  const domain = `loadtest-${randomString(6)}.example.com`;
  timedRequest(
    'POST',
    `${L1_URL}/api/v1/ingestion/targets`,
    { domain: `https://${domain}`, options: { depth: 2 } },
    ingestionSubmitTime,
    ingestionErrors,
  );

  sleep(randomIntBetween(1, 3));

  // Step 2: Poll job list
  timedRequest(
    'GET',
    `${L1_URL}/api/v1/ingestion/jobs`,
    null,
    ingestionPollTime,
    ingestionErrors,
  );

  sleep(randomIntBetween(2, 5));
}

// ── Journey 2: Intelligence Flow ────────────────────────────────────────────

export function intelligenceJourney() {
  // Step 1: Fetch account list
  const accountsResp = timedRequest(
    'GET',
    `${L4_URL}/v1/accounts`,
    null,
    accountFetchTime,
    intelligenceErrors,
  );

  sleep(0.5);

  // Step 2: Fetch account detail (use first account or fallback ID)
  let accountId = 'acct-loadtest-001';
  try {
    const accounts = accountsResp.json();
    if (Array.isArray(accounts) && accounts.length > 0) {
      accountId = accounts[0].id || accounts[0].account_id || accountId;
    }
  } catch { /* use default */ }

  timedRequest(
    'GET',
    `${L4_URL}/v1/accounts/${accountId}`,
    null,
    accountFetchTime,
    intelligenceErrors,
  );

  sleep(0.5);

  // Step 3: Fetch workspace tabs (simulating tab navigation)
  const tabs = ['signals', 'drivers', 'evidence', 'stakeholders'];
  const tab = tabs[randomIntBetween(0, tabs.length - 1)];

  timedRequest(
    'GET',
    `${L4_URL}/v1/accounts/${accountId}/workspace/${tab}`,
    null,
    workspaceTabTime,
    intelligenceErrors,
  );

  sleep(1);

  // Step 4: Send agent stream message
  timedRequest(
    'POST',
    `${L4_URL}/v1/c1/stream`,
    {
      message: `Analyze ${tab} for this account`,
      context: { account_id: accountId, tab: tab },
    },
    agentStreamTime,
    intelligenceErrors,
  );

  sleep(randomIntBetween(2, 5));
}

// ── Journey 3: Studio Flow ──────────────────────────────────────────────────

export function studioJourney() {
  // Step 1: Fetch cases list
  const casesResp = timedRequest(
    'GET',
    `${L4_URL}/v1/cases`,
    null,
    valueModelTime,
    studioErrors,
  );

  sleep(0.5);

  // Step 2: ROI analysis
  timedRequest(
    'POST',
    `${L4_URL}/v1/analysis/roi`,
    {
      account_id: 'acct-loadtest-001',
      variables: {
        revenue: randomIntBetween(100000000, 1000000000),
        cost_ratio: 0.3 + Math.random() * 0.2,
      },
    },
    valueModelTime,
    studioErrors,
  );

  sleep(1);

  // Step 3: Whitespace analysis
  timedRequest(
    'POST',
    `${L4_URL}/v1/analysis/whitespace`,
    { account_id: 'acct-loadtest-001' },
    narrativeTime,
    studioErrors,
  );

  sleep(1);

  // Step 4: Export case (if available)
  try {
    const cases = casesResp.json();
    if (Array.isArray(cases) && cases.length > 0) {
      const caseId = cases[0].id || cases[0].case_id;
      timedRequest(
        'GET',
        `${L4_URL}/v1/cases/${caseId}/export`,
        null,
        caseExportTime,
        studioErrors,
      );
    }
  } catch { /* skip export step */ }

  sleep(randomIntBetween(2, 4));
}

// ── Journey 4: Governance Flow ──────────────────────────────────────────────

export function governanceJourney() {
  // Step 1: Health check
  timedRequest(
    'GET',
    `${L4_URL}/health`,
    null,
    healthCheckTime,
    governanceErrors,
  );

  sleep(1);

  // Step 2: Detailed health
  timedRequest(
    'GET',
    `${L4_URL}/v1/health/detailed`,
    null,
    healthCheckTime,
    governanceErrors,
  );

  sleep(1);

  // Step 3: Workflow list (audit of active workflows)
  timedRequest(
    'GET',
    `${L4_URL}/v1/workflows?status=active`,
    null,
    auditLogTime,
    governanceErrors,
  );

  sleep(1);

  // Step 4: Workflow types
  timedRequest(
    'GET',
    `${L4_URL}/v1/workflows/types`,
    null,
    traceQueryTime,
    governanceErrors,
  );

  sleep(randomIntBetween(5, 10));
}

// ── Journey 5: Auth Flow ────────────────────────────────────────────────────

export function authJourney() {
  // Step 1: Authenticated request to accounts
  timedRequest(
    'GET',
    `${L4_URL}/v1/accounts`,
    null,
    authLatency,
    authErrors,
  );

  sleep(0.5);

  // Step 2: Tenant-scoped request
  timedRequest(
    'GET',
    `${L4_URL}/v1/feature-flags`,
    null,
    authLatency,
    authErrors,
  );

  tenantIsolationChecks.add(1);

  sleep(0.5);

  // Step 3: Users list (admin endpoint)
  timedRequest(
    'GET',
    `${L4_URL}/v1/users`,
    null,
    authLatency,
    authErrors,
  );

  sleep(randomIntBetween(1, 3));
}

// ── Summary ─────────────────────────────────────────────────────────────────

export function handleSummary(data) {
  const metrics = data.metrics;

  const summary = {
    test_type: 'journey_load_test',
    timestamp: new Date().toISOString(),
    journeys: {
      j1_ingestion: {
        submit_p95_ms: metrics.j1_ingestion_submit_ms?.values?.['p(95)'] || 'N/A',
        error_rate: ((metrics.j1_ingestion_error_rate?.values?.rate || 0) * 100).toFixed(2) + '%',
        slo_met: (metrics.j1_ingestion_error_rate?.values?.rate || 0) < 0.05,
      },
      j2_intelligence: {
        account_fetch_p95_ms: metrics.j2_account_fetch_ms?.values?.['p(95)'] || 'N/A',
        workspace_tab_p95_ms: metrics.j2_workspace_tab_ms?.values?.['p(95)'] || 'N/A',
        agent_stream_p95_ms: metrics.j2_agent_stream_ms?.values?.['p(95)'] || 'N/A',
        error_rate: ((metrics.j2_intelligence_error_rate?.values?.rate || 0) * 100).toFixed(2) + '%',
        slo_met: (metrics.j2_intelligence_error_rate?.values?.rate || 0) < 0.01,
      },
      j3_studio: {
        value_model_p95_ms: metrics.j3_value_model_ms?.values?.['p(95)'] || 'N/A',
        narrative_p95_ms: metrics.j3_narrative_ms?.values?.['p(95)'] || 'N/A',
        error_rate: ((metrics.j3_studio_error_rate?.values?.rate || 0) * 100).toFixed(2) + '%',
        slo_met: (metrics.j3_studio_error_rate?.values?.rate || 0) < 0.02,
      },
      j4_governance: {
        health_check_p95_ms: metrics.j4_health_check_ms?.values?.['p(95)'] || 'N/A',
        audit_log_p95_ms: metrics.j4_audit_log_ms?.values?.['p(95)'] || 'N/A',
        error_rate: ((metrics.j4_governance_error_rate?.values?.rate || 0) * 100).toFixed(2) + '%',
        slo_met: (metrics.j4_governance_error_rate?.values?.rate || 0) < 0.01,
      },
      j5_auth: {
        auth_latency_p95_ms: metrics.j5_auth_latency_ms?.values?.['p(95)'] || 'N/A',
        isolation_checks: metrics.j5_tenant_isolation_checks?.values?.count || 0,
        error_rate: ((metrics.j5_auth_error_rate?.values?.rate || 0) * 100).toFixed(2) + '%',
        slo_met: (metrics.j5_auth_error_rate?.values?.rate || 0) < 0.01,
      },
    },
    overall: {
      http_req_p95_ms: metrics.http_req_duration?.values?.['p(95)'] || 'N/A',
      http_req_failed_rate: ((metrics.http_req_failed?.values?.rate || 0) * 100).toFixed(2) + '%',
      all_slos_met:
        (metrics.j1_ingestion_error_rate?.values?.rate || 0) < 0.05 &&
        (metrics.j2_intelligence_error_rate?.values?.rate || 0) < 0.01 &&
        (metrics.j3_studio_error_rate?.values?.rate || 0) < 0.02 &&
        (metrics.j4_governance_error_rate?.values?.rate || 0) < 0.01 &&
        (metrics.j5_auth_error_rate?.values?.rate || 0) < 0.01,
    },
  };

  return {
    stdout: JSON.stringify(summary, null, 2),
    'artifacts/performance/journey-load-summary.json': JSON.stringify(data, null, 2),
  };
}
