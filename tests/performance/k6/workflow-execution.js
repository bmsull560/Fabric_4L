/**
 * Workflow Execution Performance Test
 * 
 * Purpose: Validate Layer 4 workflow lifecycle and throughput
 * Pattern: Workflow submission, monitoring, and completion validation
 * 
 * Usage:
 *   k6 run --env L4_URL=http://localhost:8004 tests/performance/k6/workflow-execution.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

const L4_URL = (__ENV.L4_URL || 'http://localhost:8004').replace(/\/$/, '');
const DURATION = __ENV.PERF_DURATION || '10m';

// Workflow timeout configuration
const WORKFLOW_TIMEOUT_SECONDS = parseInt(__ENV.WORKFLOW_TIMEOUT || '120');
const POLL_INTERVAL_SECONDS = parseInt(__ENV.POLL_INTERVAL || '5');

// Custom metrics
const workflowSubmitTime = new Trend('workflow_submit_duration_ms');
const workflowCompleteTime = new Trend('workflow_complete_duration_ms');
const workflowSuccessRate = new Rate('workflow_success_rate');
const workflowQueueDepth = new Trend('workflow_queue_depth');
const workflowErrorRate = new Rate('workflow_error_rate');
const workflowThroughput = new Counter('workflows_completed');

const authHeaders = {};
if (__ENV.PERF_AUTH_BEARER) {
  authHeaders.Authorization = `Bearer ${__ENV.PERF_AUTH_BEARER}`;
}
if (__ENV.PERF_TENANT_ID) {
  authHeaders['X-Tenant-ID'] = __ENV.PERF_TENANT_ID;
}

export const options = {
  scenarios: {
    workflow_submit: {
      executor: 'constant-arrival-rate',
      exec: 'submitWorkflow',
      rate: 5,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: 10,
      maxVUs: 30,
      startTime: '0s',
    },
    workflow_monitor: {
      executor: 'constant-vus',
      exec: 'monitorWorkflow',
      vus: 5,
      duration: DURATION,
      startTime: '30s',
    },
    workflow_list: {
      executor: 'constant-arrival-rate',
      exec: 'listWorkflows',
      rate: 2,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: 3,
      maxVUs: 10,
      startTime: '1m',
    },
  },
  thresholds: {
    workflow_submit_duration_ms: ['p(95)<1000'],      // <1s to accept
    workflow_complete_duration_ms: ['p(95)<60000'],  // <60s to complete
    workflow_success_rate: ['rate>0.95'],            // >95% success
    workflow_error_rate: ['rate<0.05'],              // <5% errors
  },
};

function defaultHeaders() {
  return {
    'Content-Type': 'application/json',
    ...authHeaders,
  };
}

export function submitWorkflow() {
  const workflowTypes = ['analyzer', 'extractor', 'validator', 'reporter'];
  const workflowType = workflowTypes[randomIntBetween(0, workflowTypes.length - 1)];
  
  const payload = JSON.stringify({
    workflow_id: `perf-wf-${randomString(8)}-${Date.now()}`,
    agent_type: workflowType,
    priority: ['low', 'normal', 'high'][randomIntBetween(0, 2)],
    input_context: {
      query: `Performance test workflow ${randomString(10)}`,
      data_source: 'performance_test',
      parameters: {
        complexity: randomIntBetween(1, 5),
        dataset_size: randomIntBetween(10, 1000),
        parallel_tasks: randomIntBetween(1, 4),
      },
    },
    timeout_seconds: WORKFLOW_TIMEOUT_SECONDS,
  });

  const startTime = Date.now();
  const response = http.post(`${L4_URL}/v1/workflows/execute`, payload, {
    headers: defaultHeaders(),
    timeout: '10s',
  });
  const duration = Date.now() - startTime;

  const success = check(response, {
    'Workflow submit: status is 200/202': (r) => r.status === 200 || r.status === 202,
    'Workflow submit: workflow_id returned': (r) => r.json('workflow_id') !== undefined,
    'Workflow submit: duration < 1s': () => duration < 1000,
  });

  workflowSubmitTime.add(duration);
  workflowErrorRate.add(!success);

  if (success) {
    // Store workflow ID for monitoring (in real test, use shared state or external store)
    const workflowId = response.json('workflow_id');
    __ENV.LAST_WORKFLOW_ID = workflowId;
  }

  sleep(randomIntBetween(1, 3));
}

export function monitorWorkflow() {
  // In a real scenario, we'd poll for specific workflows submitted by this test
  // For k6, we simulate workflow monitoring by querying recent workflows
  
  const response = http.get(`${L4_URL}/v1/workflows/active?limit=20`, {
    headers: defaultHeaders(),
    timeout: '5s',
  });

  check(response, {
    'Workflow monitor: status is 200': (r) => r.status === 200,
    'Workflow monitor: returns workflow list': (r) => {
      try {
        const body = r.json();
        return Array.isArray(body.workflows) || Array.isArray(body);
      } catch {
        return false;
      }
    },
  });

  // Check queue depth
  try {
    const body = response.json();
    const workflows = body.workflows || body || [];
    const pendingCount = workflows.filter(w => w.status === 'pending' || w.state === 'pending').length;
    workflowQueueDepth.add(pendingCount);
  } catch {
    workflowQueueDepth.add(0);
  }

  sleep(POLL_INTERVAL_SECONDS);
}

export function listWorkflows() {
  // Test workflow listing API performance
  const filters = ['active', 'completed', 'failed', 'all'];
  const filter = filters[randomIntBetween(0, filters.length - 1)];
  
  const response = http.get(`${L4_URL}/v1/workflows?status=${filter}&limit=50`, {
    headers: defaultHeaders(),
    timeout: '5s',
  });

  const startTime = Date.now();
  const duration = Date.now() - startTime;

  const success = check(response, {
    'Workflow list: status is 200': (r) => r.status === 200,
    'Workflow list: returns results': (r) => {
      try {
        const body = r.json();
        return body.workflows !== undefined || body.count !== undefined || Array.isArray(body);
      } catch {
        return false;
      }
    },
    'Workflow list: duration < 2s': () => duration < 2000,
  });

  workflowErrorRate.add(!success);

  sleep(randomIntBetween(1, 2));
}

// Lifecycle workflow: submit, poll, validate completion
export function runWorkflowLifecycle() {
  const workflowId = `lifecycle-${randomString(8)}-${Date.now()}`;
  
  // Submit workflow
  const submitPayload = JSON.stringify({
    workflow_id: workflowId,
    agent_type: 'analyzer',
    priority: 'normal',
    input_context: {
      query: 'Lifecycle performance test',
      data_source: 'lifecycle_test',
    },
  });

  const submitStart = Date.now();
  const submitResponse = http.post(`${L4_URL}/v1/workflows/execute`, submitPayload, {
    headers: defaultHeaders(),
    timeout: '10s',
  });
  const submitDuration = Date.now() - submitStart;
  workflowSubmitTime.add(submitDuration);

  if (submitResponse.status !== 200 && submitResponse.status !== 202) {
    workflowErrorRate.add(true);
    return;
  }

  // Poll for completion (simplified - real test would use persistent storage)
  const maxPolls = WORKFLOW_TIMEOUT_SECONDS / POLL_INTERVAL_SECONDS;
  let completed = false;
  let pollCount = 0;

  while (!completed && pollCount < maxPolls) {
    sleep(POLL_INTERVAL_SECONDS);
    pollCount++;

    const statusResponse = http.get(`${L4_URL}/v1/workflows/${workflowId}`, {
      headers: defaultHeaders(),
      timeout: '5s',
    });

    if (statusResponse.status === 200) {
      try {
        const body = statusResponse.json();
        const status = body.status || body.state;
        
        if (status === 'completed' || status === 'success') {
          completed = true;
          workflowSuccessRate.add(true);
          workflowThroughput.add(1);
        } else if (status === 'failed' || status === 'error') {
          workflowSuccessRate.add(false);
          workflowErrorRate.add(true);
          break;
        }
      } catch {
        // Continue polling
      }
    }
  }

  const totalDuration = (pollCount * POLL_INTERVAL_SECONDS + 1) * 1000;
  workflowCompleteTime.add(totalDuration);
}

export function handleSummary(data) {
  const metrics = data.metrics;
  
  const submitP95 = metrics.workflow_submit_duration_ms?.['p(95)'] || 0;
  const completeP95 = metrics.workflow_complete_duration_ms?.['p(95)'] || 0;
  const successRate = metrics.workflow_success_rate?.rate || 0;
  const errorRate = metrics.workflow_error_rate?.rate || 0;
  const queueDepth = metrics.workflow_queue_depth?.avg || 0;
  
  const completedWorkflows = metrics.workflows_completed?.count || 0;
  const durationMinutes = parseDurationMinutes(data.state.testRunDuration);
  const workflowsPerMinute = durationMinutes > 0 ? completedWorkflows / durationMinutes : 0;

  return {
    stdout: JSON.stringify({
      test_type: 'workflow_execution',
      submit_latency_p95_ms: submitP95.toFixed(2),
      complete_latency_p95_ms: completeP95 > 0 ? (completeP95 / 1000).toFixed(2) + 's' : 'N/A',
      success_rate: (successRate * 100).toFixed(2) + '%',
      error_rate: (errorRate * 100).toFixed(2) + '%',
      avg_queue_depth: queueDepth.toFixed(2),
      completed_workflows: completedWorkflows,
      workflows_per_minute: workflowsPerMinute.toFixed(2),
      passed: successRate > 0.95 && errorRate < 0.05 && submitP95 < 1000,
      recommendation: successRate < 0.95
        ? 'Low success rate. Investigate workflow failures and agent health.'
        : queueDepth > 50
        ? 'High queue depth detected. Scale agent workers or implement backpressure.'
        : completeP95 > 60000
        ? 'Slow workflow completion. Optimize agent processing or increase parallelism.'
        : 'Workflow execution performance acceptable.',
    }, null, 2),
    'artifacts/performance/workflow-exec-summary.json': JSON.stringify(data, null, 2),
  };
}

function parseDurationMinutes(durationStr) {
  let minutes = 0;
  const hourMatch = durationStr.match(/(\d+)h/);
  const minMatch = durationStr.match(/(\d+)m/);
  
  if (hourMatch) minutes += parseInt(hourMatch[1]) * 60;
  if (minMatch) minutes += parseInt(minMatch[1]);
  
  return minutes || 10;
}
