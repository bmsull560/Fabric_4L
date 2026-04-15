/**
 * Soak Test: Extended stability testing
 * 
 * Purpose: Detect memory leaks and degradation over time
 * Pattern: Sustained moderate load for 8 hours
 * 
 * Usage:
 *   k6 run --env PERF_DURATION=8h tests/performance/k6/soak-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

const L2_URL = (__ENV.L2_URL || 'http://localhost:8002').replace(/\/$/, '');
const L3_URL = (__ENV.L3_URL || 'http://localhost:8003').replace(/\/$/, '');
const L4_URL = (__ENV.L4_URL || 'http://localhost:8004').replace(/\/$/, '');

// Duration configuration (default 30m for testing, use 8h for production soak)
const DURATION = __ENV.PERF_DURATION || '30m';

// Custom metrics for trend analysis
const memoryLeakIndicator = new Trend('soak_memory_leak_indicator');
const degradationRate = new Rate('soak_performance_degradation');
const errorRate = new Rate('soak_error_rate');
const hourlyThroughput = new Counter('soak_hourly_requests');

const authHeaders = {};
if (__ENV.PERF_AUTH_BEARER) {
  authHeaders.Authorization = `Bearer ${__ENV.PERF_AUTH_BEARER}`;
}
if (__ENV.PERF_TENANT_ID) {
  authHeaders['X-Tenant-ID'] = __ENV.PERF_TENANT_ID;
}

export const options = {
  scenarios: {
    soak_l2_l3_l4: {
      executor: 'constant-vus',
      exec: 'runSoak',
      vus: 20, // Moderate sustained load
      duration: DURATION,
    },
  },
  thresholds: {
    soak_error_rate: ['rate<0.01'],         // <1% errors over duration
    http_req_failed: ['rate<0.02'],        // <2% hard limit
    http_req_duration: ['p(95)<5000'],     // Consistent <5s p95
  },
};

// Track iteration count for trend detection
let iterationCount = 0;
const responseTimeHistory = [];

function defaultHeaders() {
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
}

export function runSoak() {
  iterationCount++;
  
  // Rotate between L2, L3, and L4 APIs to simulate realistic mixed load
  const apiChoice = iterationCount % 3;
  
  let response;
  let duration;
  let success;
  
  switch (apiChoice) {
    case 0:
      ({ response, duration, success } = runL2Soak());
      break;
    case 1:
      ({ response, duration, success } = runL3Soak());
      break;
    case 2:
      ({ response, duration, success } = runL4Soak());
      break;
  }
  
  // Track response times for degradation detection
  responseTimeHistory.push(duration);
  if (responseTimeHistory.length > 100) {
    responseTimeHistory.shift(); // Keep last 100 measurements
  }
  
  // Detect performance degradation
  if (responseTimeHistory.length >= 50) {
    const avgRecent = responseTimeHistory.slice(-10).reduce((a, b) => a + b, 0) / 10;
    const avgEarlier = responseTimeHistory.slice(0, 10).reduce((a, b) => a + b, 0) / 10;
    
    if (avgEarlier > 0 && avgRecent > avgEarlier * 1.5) {
      degradationRate.add(true); // Degradation detected
    } else {
      degradationRate.add(false);
    }
  }
  
  errorRate.add(!success);
  hourlyThroughput.add(1);
  
  // Variable think time to simulate realistic usage patterns
  sleep(randomIntBetween(1, 3));
}

function runL2Soak() {
  const payload = JSON.stringify({
    content_id: `soak-l2-${Date.now()}-${__VU}`,
    source_url: 'https://example.com/soak-test',
    markdown_content: `# Soak Test Document ${iterationCount}

This is a long-running stability test payload. Content varies: ${randomIntBetween(1, 1000)}`,
    extraction_config: {
      extract_values: true,
      extract_entities: false, // Reduce load for long test
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
    'soak L2: status is 200/202': (r) => r.status === 200 || r.status === 202,
    'soak L2: no timeouts': () => duration < 30000,
  });

  return { response, duration, success };
}

function runL3Soak() {
  const payload = JSON.stringify({
    query: `soak test query ${iterationCount}`,
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
    'soak L3: status is 200': (r) => r.status === 200,
    'soak L3: response valid': (r) => r.json('results') !== undefined,
  });

  return { response, duration, success };
}

function runL4Soak() {
  const payload = JSON.stringify({
    workflow_id: `soak-wf-${Date.now()}-${__VU}`,
    agent_type: 'analyzer',
    input_context: {
      query: `soak workflow ${iterationCount}`,
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
    'soak L4: status is 200/202': (r) => r.status === 200 || r.status === 202,
    'soak L4: workflow accepted': (r) => r.json('workflow_id') !== undefined,
  });

  return { response, duration, success };
}

export function handleSummary(data) {
  const totalRequests = data.metrics.soak_hourly_requests?.count || 0;
  const errorRateValue = data.metrics.soak_error_rate?.rate || 0;
  const degradationRateValue = data.metrics.soak_performance_degradation?.rate || 0;
  const duration = data.state.testRunDuration;
  
  // Calculate requests per hour
  const durationHours = parseDurationHours(duration);
  const requestsPerHour = durationHours > 0 ? totalRequests / durationHours : 0;
  
  // Memory leak detection heuristics
  const httpTrends = data.metrics.http_req_duration;
  const p95Start = httpTrends?.['p(50)'] || 0; // Approximate starting point
  const p95End = httpTrends?.['p(95)'] || 0;
  const memoryLeakSuspected = p95End > p95Start * 2 && durationHours >= 1;

  return {
    stdout: JSON.stringify({
      test_type: 'soak',
      duration: duration,
      duration_hours: durationHours.toFixed(2),
      total_requests: totalRequests,
      requests_per_hour: Math.round(requestsPerHour),
      error_rate: (errorRateValue * 100).toFixed(2) + '%',
      degradation_rate: (degradationRateValue * 100).toFixed(2) + '%',
      memory_leak_suspected: memoryLeakSuspected,
      latency_p95: data.metrics.http_req_duration?.['p(95)'],
      latency_p99: data.metrics.http_req_duration?.['p(99)'],
      passed: errorRateValue < 0.01 && degradationRateValue < 0.05 && !memoryLeakSuspected,
      recommendation: memoryLeakSuspected
        ? 'WARNING: Possible memory leak or connection pool exhaustion detected. Investigate heap usage and connection leaks.'
        : degradationRateValue > 0.05
        ? 'WARNING: Performance degradation detected. Review resource utilization trends.'
        : 'System stable over extended duration.',
    }, null, 2),
    'artifacts/performance/soak-test-summary.json': JSON.stringify(data, null, 2),
  };
}

function parseDurationHours(durationStr) {
  // Parse duration like "8h30m10s" to hours
  let hours = 0;
  
  const hourMatch = durationStr.match(/(\d+)h/);
  const minMatch = durationStr.match(/(\d+)m/);
  const secMatch = durationStr.match(/(\d+)s/);
  
  if (hourMatch) hours += parseInt(hourMatch[1]);
  if (minMatch) hours += parseInt(minMatch[1]) / 60;
  if (secMatch) hours += parseInt(secMatch[1]) / 3600;
  
  return hours;
}
