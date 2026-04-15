/**
 * Stress Test: Gradual ramp to breaking point
 * 
 * Purpose: Find the maximum capacity before degradation
 * Pattern: Ramp up → Hold at peak → Ramp down
 * 
 * Usage:
 *   k6 run --env L2_URL=http://localhost:8002 tests/performance/k6/stress-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

const L2_URL = (__ENV.L2_URL || 'http://localhost:8002').replace(/\/$/, '');
const L3_URL = (__ENV.L3_URL || 'http://localhost:8003').replace(/\/$/, '');
const L4_URL = (__ENV.L4_URL || 'http://localhost:8004').replace(/\/$/, '');

// Custom metrics
const errorRate = new Rate('stress_error_rate');
const responseTime = new Trend('stress_response_time_ms');
const throughput = new Counter('stress_requests_total');
const breakingPointRPS = new Counter('stress_breaking_point_rps');

// Authentication
const authHeaders = {};
if (__ENV.PERF_AUTH_BEARER) {
  authHeaders.Authorization = `Bearer ${__ENV.PERF_AUTH_BEARER}`;
}
if (__ENV.PERF_TENANT_ID) {
  authHeaders['X-Tenant-ID'] = __ENV.PERF_TENANT_ID;
}

export const options = {
  scenarios: {
    stress_l2: {
      executor: 'ramping-vus',
      exec: 'runL2Stress',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 10 },   // Ramp up
        { duration: '2m', target: 50 },   // Continue ramp
        { duration: '2m', target: 100 },  // Near breaking
        { duration: '5m', target: 100 },  // Hold at stress
        { duration: '2m', target: 50 },   // Ramp down
        { duration: '2m', target: 0 },    // Recovery
      ],
      gracefulRampDown: '30s',
    },
    stress_l3: {
      executor: 'ramping-vus',
      exec: 'runL3Stress',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },
        { duration: '2m', target: 100 },
        { duration: '2m', target: 200 },
        { duration: '5m', target: 200 },
        { duration: '2m', target: 100 },
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
      startTime: '1m', // Offset from L2
    },
    stress_l4: {
      executor: 'ramping-vus',
      exec: 'runL4Stress',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },
        { duration: '2m', target: 100 },
        { duration: '2m', target: 150 },
        { duration: '5m', target: 150 },
        { duration: '2m', target: 100 },
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
      startTime: '2m', // Offset from L2
    },
  },
  thresholds: {
    stress_error_rate: ['rate<0.05'],        // <5% errors during stress
    stress_response_time_ms: ['p(95)<10000'],  // <10s even under stress
    http_req_failed: ['rate<0.10'],           // Hard limit: <10% failures
  },
};

function defaultHeaders() {
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
}

export function runL2Stress() {
  const payload = JSON.stringify({
    content_id: `stress-l2-${__VU}-${__ITER}`,
    source_url: 'https://example.com/stress-test',
    markdown_content: `# Stress Test Document

This is a stress test payload designed to validate extraction throughput under load.
Content: ${'Lorem ipsum dolor sit amet. '.repeat(20)}`,
    extraction_config: {
      extract_values: true,
      extract_entities: true,
      confidence_threshold: 0.7,
    },
    store_in_graph: true,
  });

  const startTime = Date.now();
  const response = http.post(`${L2_URL}/v1/extract-and-ingest`, payload, {
    headers: defaultHeaders(),
    timeout: '30s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'L2 stress: status is 200 or 202': (r) => r.status === 200 || r.status === 202,
    'L2 stress: response time < 10s': () => duration < 10000,
  });

  errorRate.add(!success);
  responseTime.add(duration);
  throughput.add(1);

  // Detect breaking point (when errors spike)
  if (!success && response.status >= 500) {
    breakingPointRPS.add(1);
  }

  sleep(Math.random() * 0.5); // Random think time 0-500ms
}

export function runL3Stress() {
  const payload = JSON.stringify({
    query: 'stress test performance validation',
    search_type: 'hybrid',
    limit: 10,
    filters: {
      entity_types: ['Value', 'Metric'],
    },
  });

  const startTime = Date.now();
  const response = http.post(`${L3_URL}/v1/search/hybrid`, payload, {
    headers: defaultHeaders(),
    timeout: '10s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'L3 stress: status is 200': (r) => r.status === 200,
    'L3 stress: response time < 5s': () => duration < 5000,
  });

  errorRate.add(!success);
  responseTime.add(duration);
  throughput.add(1);

  sleep(Math.random() * 0.3);
}

export function runL4Stress() {
  const payload = JSON.stringify({
    workflow_id: `stress-wf-${__VU}-${__ITER}`,
    agent_type: 'analyzer',
    input_context: {
      query: 'stress test workflow execution',
      priority: 'normal',
    },
  });

  const startTime = Date.now();
  const response = http.post(`${L4_URL}/v1/workflows/execute`, payload, {
    headers: defaultHeaders(),
    timeout: '30s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'L4 stress: status is 200 or 202': (r) => r.status === 200 || r.status === 202,
    'L4 stress: response time < 10s': () => duration < 10000,
  });

  errorRate.add(!success);
  responseTime.add(duration);
  throughput.add(1);

  sleep(Math.random() * 0.5);
}

export function handleSummary(data) {
  // Calculate breaking point
  const maxErrorRate = Math.max(
    data.metrics.stress_error_rate?.rate || 0,
    data.metrics.http_req_failed?.rate || 0
  );

  return {
    stdout: JSON.stringify({
      test_type: 'stress',
      breaking_point_detected: maxErrorRate > 0.05,
      max_error_rate: maxErrorRate,
      max_response_time_p95: data.metrics.stress_response_time_ms?.['p(95)'],
      total_requests: data.metrics.stress_requests_total?.count,
      recommendation: maxErrorRate > 0.05 
        ? 'Breaking point detected. Scale horizontally or optimize bottlenecks.'
        : 'System stable under stress. Consider higher load tests.',
    }, null, 2),
    'artifacts/performance/stress-test-summary.json': JSON.stringify(data, null, 2),
  };
}
