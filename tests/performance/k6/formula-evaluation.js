/**
 * Formula Evaluation Performance Test
 * 
 * Purpose: Validate Layer 3 formula evaluation throughput and latency
 * Pattern: Varying formula complexity and concurrent evaluation
 * 
 * Usage:
 *   k6 run --env L3_URL=http://localhost:8003 tests/performance/k6/formula-evaluation.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

const L3_URL = (__ENV.L3_URL || 'http://localhost:8003').replace(/\/$/, '');
const DURATION = __ENV.PERF_DURATION || '5m';

// Custom metrics
const formulaEvalTime = new Trend('formula_eval_duration_ms');
const formulaErrorRate = new Rate('formula_eval_error_rate');
const formulaComplexity = new Trend('formula_complexity_score');

const authHeaders = {};
if (__ENV.PERF_AUTH_BEARER) {
  authHeaders.Authorization = `Bearer ${__ENV.PERF_AUTH_BEARER}`;
}
if (__ENV.PERF_TENANT_ID) {
  authHeaders['X-Tenant-ID'] = __ENV.PERF_TENANT_ID;
}

export const options = {
  scenarios: {
    simple_formulas: {
      executor: 'constant-arrival-rate',
      exec: 'runSimpleFormula',
      rate: 10,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: 5,
      maxVUs: 20,
      startTime: '0s',
    },
    medium_formulas: {
      executor: 'constant-arrival-rate',
      exec: 'runMediumFormula',
      rate: 5,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: 5,
      maxVUs: 15,
      startTime: '1m',
    },
    complex_formulas: {
      executor: 'constant-arrival-rate',
      exec: 'runComplexFormula',
      rate: 2,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: 3,
      maxVUs: 10,
      startTime: '2m',
    },
    batch_evaluations: {
      executor: 'constant-arrival-rate',
      exec: 'runBatchEvaluation',
      rate: 1,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: 2,
      maxVUs: 5,
      startTime: '3m',
    },
  },
  thresholds: {
    formula_eval_duration_ms: ['p(95)<2000'],    // <2s for formula eval
    formula_eval_error_rate: ['rate<0.02'],      // <2% errors
    http_req_failed: ['rate<0.05'],               // <5% hard limit
  },
};

function defaultHeaders() {
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
}

export function runSimpleFormula() {
  // Simple arithmetic: revenue * margin
  const payload = JSON.stringify({
    formula: 'revenue * margin',
    variables: {
      revenue: randomIntBetween(10000, 1000000),
      margin: 0.15 + (Math.random() * 0.25), // 15-40% margin
    },
    precision: 2,
  });

  const startTime = Date.now();
  const response = http.post(`${L3_URL}/v1/formulas/evaluate`, payload, {
    headers: defaultHeaders(),
    timeout: '5s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'Simple formula: status is 200': (r) => r.status === 200,
    'Simple formula: result present': (r) => r.json('result') !== undefined,
    'Simple formula: duration < 500ms': () => duration < 500,
  });

  formulaEvalTime.add(duration);
  formulaErrorRate.add(!success);
  formulaComplexity.add(1); // Score: 1 = simple

  sleep(randomIntBetween(0, 1));
}

export function runMediumFormula() {
  // Medium complexity: weighted average with conditional
  const payload = JSON.stringify({
    formula: '(q1_revenue + q2_revenue + q3_revenue + q4_revenue) / 4 * (1 + growth_rate)',
    variables: {
      q1_revenue: randomIntBetween(100000, 500000),
      q2_revenue: randomIntBetween(100000, 500000),
      q3_revenue: randomIntBetween(100000, 500000),
      q4_revenue: randomIntBetween(100000, 500000),
      growth_rate: 0.05 + (Math.random() * 0.15),
    },
    precision: 2,
  });

  const startTime = Date.now();
  const response = http.post(`${L3_URL}/v1/formulas/evaluate`, payload, {
    headers: defaultHeaders(),
    timeout: '10s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'Medium formula: status is 200': (r) => r.status === 200,
    'Medium formula: result is number': (r) => typeof r.json('result') === 'number',
    'Medium formula: duration < 1000ms': () => duration < 1000,
  });

  formulaEvalTime.add(duration);
  formulaErrorRate.add(!success);
  formulaComplexity.add(2); // Score: 2 = medium

  sleep(randomIntBetween(0, 1));
}

export function runComplexFormula() {
  // Complex: Nested formulas with aggregation
  const payload = JSON.stringify({
    formula: `sum(map(products, p => p.price * p.quantity * (1 - p.discount))) * 
              (1 + tax_rate) - 
              fixed_costs`,
    variables: {
      products: [
        { price: randomIntBetween(10, 100), quantity: randomIntBetween(1, 50), discount: 0.1 },
        { price: randomIntBetween(10, 100), quantity: randomIntBetween(1, 50), discount: 0.15 },
        { price: randomIntBetween(10, 100), quantity: randomIntBetween(1, 50), discount: 0.05 },
        { price: randomIntBetween(10, 100), quantity: randomIntBetween(1, 50), discount: 0.2 },
        { price: randomIntBetween(10, 100), quantity: randomIntBetween(1, 50), discount: 0 },
      ],
      tax_rate: 0.08,
      fixed_costs: randomIntBetween(1000, 10000),
    },
    precision: 2,
  });

  const startTime = Date.now();
  const response = http.post(`${L3_URL}/v1/formulas/evaluate`, payload, {
    headers: defaultHeaders(),
    timeout: '15s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'Complex formula: status is 200': (r) => r.status === 200,
    'Complex formula: result computed': (r) => r.json('result') !== undefined,
    'Complex formula: duration < 2000ms': () => duration < 2000,
  });

  formulaEvalTime.add(duration);
  formulaErrorRate.add(!success);
  formulaComplexity.add(3); // Score: 3 = complex

  sleep(randomIntBetween(0, 2));
}

export function runBatchEvaluation() {
  // Batch evaluate multiple formulas at once
  const payload = JSON.stringify({
    evaluations: [
      {
        id: 'revenue-calc',
        formula: 'units_sold * unit_price',
        variables: { units_sold: randomIntBetween(100, 10000), unit_price: 29.99 },
      },
      {
        id: 'profit-calc',
        formula: 'revenue - (units_sold * unit_cost)',
        variables: { 
          revenue: randomIntBetween(10000, 500000),
          units_sold: randomIntBetween(100, 5000),
          unit_cost: 15.50,
        },
      },
      {
        id: 'roi-calc',
        formula: '(profit - investment) / investment * 100',
        variables: {
          profit: randomIntBetween(50000, 200000),
          investment: randomIntBetween(100000, 500000),
        },
      },
      {
        id: 'growth-calc',
        formula: '(current - previous) / previous * 100',
        variables: {
          current: randomIntBetween(1000000, 5000000),
          previous: randomIntBetween(800000, 4500000),
        },
      },
    ],
  });

  const startTime = Date.now();
  const response = http.post(`${L3_URL}/v1/formulas/evaluate-batch`, payload, {
    headers: defaultHeaders(),
    timeout: '20s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'Batch eval: status is 200': (r) => r.status === 200,
    'Batch eval: all results returned': (r) => {
      try {
        const body = r.json();
        const results = body.results || [];
        return results.length === 4;
      } catch {
        return false;
      }
    },
    'Batch eval: duration < 3000ms': () => duration < 3000,
  });

  formulaEvalTime.add(duration);
  formulaErrorRate.add(!success);
  formulaComplexity.add(4); // Score: 4 = batch

  sleep(randomIntBetween(1, 3));
}

export function handleSummary(data) {
  const metrics = data.metrics;
  
  const simpleLatency = metrics.formula_eval_duration_ms?.values?.[1] || 0;
  const complexLatency = metrics.formula_eval_duration_ms?.values?.[3] || 0;
  const errorRate = metrics.formula_eval_error_rate?.rate || 0;
  
  // Calculate throughput by complexity
  const totalRequests = metrics.http_reqs?.count || 0;
  const durationMinutes = parseDurationMinutes(data.state.testRunDuration);
  const throughputPerMinute = durationMinutes > 0 ? totalRequests / durationMinutes : 0;

  return {
    stdout: JSON.stringify({
      test_type: 'formula_evaluation',
      simple_formula_latency_ms: simpleLatency.toFixed(2),
      complex_formula_latency_ms: complexLatency.toFixed(2),
      latency_multiplier: complexLatency > 0 ? (complexLatency / simpleLatency).toFixed(2) : 'N/A',
      error_rate: (errorRate * 100).toFixed(2) + '%',
      throughput_per_minute: Math.round(throughputPerMinute),
      p95_latency_ms: metrics.formula_eval_duration_ms?.['p(95)'],
      passed: errorRate < 0.02 && metrics.formula_eval_duration_ms?.['p(95)'] < 2000,
      recommendation: errorRate > 0.02
        ? 'High error rate detected. Review formula parsing and variable resolution.'
        : complexLatency > simpleLatency * 10
        ? 'Complex formulas show significant slowdown. Consider caching or optimization.'
        : 'Formula evaluation performance within acceptable bounds.',
    }, null, 2),
    'artifacts/performance/formula-eval-summary.json': JSON.stringify(data, null, 2),
  };
}

function parseDurationMinutes(durationStr) {
  let minutes = 0;
  const hourMatch = durationStr.match(/(\d+)h/);
  const minMatch = durationStr.match(/(\d+)m/);
  
  if (hourMatch) minutes += parseInt(hourMatch[1]) * 60;
  if (minMatch) minutes += parseInt(minMatch[1]);
  
  return minutes || 5; // Default 5 min
}
