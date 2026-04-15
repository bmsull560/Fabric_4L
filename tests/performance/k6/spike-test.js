/**
 * Spike Test: Sudden traffic spikes
 * 
 * Purpose: Validate handling of sudden traffic increases
 * Pattern: Normal load → Sudden spike → Recovery
 * 
 * Usage:
 *   k6 run --env L3_URL=http://localhost:8003 tests/performance/k6/spike-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const L2_URL = (__ENV.L2_URL || 'http://localhost:8002').replace(/\/$/, '');
const L3_URL = (__ENV.L3_URL || 'http://localhost:8003').replace(/\/$/, '');
const L4_URL = (__ENV.L4_URL || 'http://localhost:8004').replace(/\/$/, '');

// Custom metrics
const spikeErrorRate = new Rate('spike_error_rate');
const spikeRecoveryTime = new Trend('spike_recovery_time_ms');
const spikeLatency = new Trend('spike_latency_ms');

const authHeaders = {};
if (__ENV.PERF_AUTH_BEARER) {
  authHeaders.Authorization = `Bearer ${__ENV.PERF_AUTH_BEARER}`;
}
if (__ENV.PERF_TENANT_ID) {
  authHeaders['X-Tenant-ID'] = __ENV.PERF_TENANT_ID;
}

export const options = {
  scenarios: {
    // Baseline traffic (warmup)
    baseline: {
      executor: 'constant-vus',
      exec: 'runBaseline',
      vus: 5,
      duration: '2m',
      startTime: '0s',
    },
    // Sudden spike (10x traffic)
    spike_l3: {
      executor: 'shared-iterations',
      exec: 'runSpike',
      vus: 100,
      iterations: 1000,
      maxDuration: '5m',
      startTime: '2m', // Start after baseline
    },
    // Recovery monitoring
    recovery: {
      executor: 'constant-vus',
      exec: 'runRecovery',
      vus: 5,
      duration: '3m',
      startTime: '7m',
    },
  },
  thresholds: {
    spike_error_rate: ['rate<0.10'],      // <10% errors during spike
    spike_latency_ms: ['p(95)<15000'],    // <15s even during spike
    http_req_failed: ['rate<0.15'],        // Hard limit: <15% failures
  },
};

function defaultHeaders() {
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
}

export function runBaseline() {
  // Normal search traffic
  const payload = JSON.stringify({
    query: 'baseline search query',
    search_type: 'semantic',
    limit: 5,
  });

  const response = http.post(`${L3_URL}/v1/search/hybrid`, payload, {
    headers: defaultHeaders(),
    timeout: '5s',
  });

  check(response, {
    'baseline: status is 200': (r) => r.status === 200,
  });

  sleep(1); // 1 RPS per VU
}

export function runSpike() {
  // Sudden burst of search requests
  const payload = JSON.stringify({
    query: `spike test query ${__VU}-${__ITER}`,
    search_type: 'hybrid',
    limit: 10,
    filters: {
      confidence_min: 0.6,
    },
  });

  const startTime = Date.now();
  const response = http.post(`${L3_URL}/v1/search/hybrid`, payload, {
    headers: defaultHeaders(),
    timeout: '15s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'spike: status is 200': (r) => r.status === 200,
    'spike: no timeout errors': () => duration < 15000,
  });

  spikeErrorRate.add(!success);
  spikeLatency.add(duration);

  // No sleep - maximum throughput during spike
}

export function runRecovery() {
  // Monitor system recovery after spike
  const payload = JSON.stringify({
    query: 'recovery monitoring query',
    search_type: 'semantic',
    limit: 5,
  });

  const startTime = Date.now();
  const response = http.post(`${L3_URL}/v1/search/hybrid`, payload, {
    headers: defaultHeaders(),
    timeout: '5s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'recovery: status is 200': (r) => r.status === 200,
    'recovery: latency normalizing': () => duration < 2000,
  });

  spikeRecoveryTime.add(duration);
  spikeErrorRate.add(!success);

  sleep(1);
}

export function handleSummary(data) {
  const baselineP95 = data.metrics.http_req_duration?.['p(95)'] || 0;
  const spikeP95 = data.metrics.spike_latency_ms?.['p(95)'] || baselineP95;
  const recoveryP95 = data.metrics.spike_recovery_time_ms?.['p(95)'] || 0;

  const spikeMultiplier = baselineP95 > 0 ? spikeP95 / baselineP95 : 0;
  const recoveryRatio = baselineP95 > 0 ? recoveryP95 / baselineP95 : 0;

  return {
    stdout: JSON.stringify({
      test_type: 'spike',
      baseline_latency_p95: baselineP95,
      spike_latency_p95: spikeP95,
      spike_multiplier: spikeMultiplier.toFixed(2) + 'x',
      recovery_latency_p95: recoveryP95,
      recovery_ratio: recoveryRatio.toFixed(2) + 'x',
      spike_error_rate: data.metrics.spike_error_rate?.rate || 0,
      passed: spikeMultiplier < 10 && recoveryRatio < 2,
      recommendation: spikeMultiplier > 10 
        ? 'Critical: Spike handling insufficient. Implement circuit breakers and rate limiting.'
        : spikeMultiplier > 5 
        ? 'Warning: Spike causes significant degradation. Consider caching and autoscaling.'
        : 'System handles spikes well.',
    }, null, 2),
    'artifacts/performance/spike-test-summary.json': JSON.stringify(data, null, 2),
  };
}
