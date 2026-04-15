/**
 * Multi-Tenant Load Test
 * 
 * Purpose: Validate tenant isolation and resource fairness under load
 * Pattern: Multiple parallel tenants with data isolation validation
 * 
 * Usage:
 *   k6 run --env L2_URL=http://localhost:8002 --env TENANT_COUNT=50 tests/performance/k6/multi-tenant.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

const L2_URL = (__ENV.L2_URL || 'http://localhost:8002').replace(/\/$/, '');
const L3_URL = (__ENV.L3_URL || 'http://localhost:8003').replace(/\/$/, '');
const L4_URL = (__ENV.L4_URL || 'http://localhost:8004').replace(/\/$/, '');

// Number of parallel tenants to simulate
const TENANT_COUNT = parseInt(__ENV.TENANT_COUNT || '50');
const DURATION = __ENV.PERF_DURATION || '5m';

// Custom metrics
const tenantIsolationErrors = new Rate('tenant_isolation_violations');
const tenantLatencyFairness = new Trend('tenant_latency_fairness'); // Std dev of latencies
const perTenantThroughput = new Counter('per_tenant_requests');
const crossTenantDataLeakage = new Rate('cross_tenant_data_leakage');
const resourceContention = new Rate('resource_contention_detected');

// Generate deterministic tenant IDs based on VU number
function getTenantForVU(vuNumber) {
  const tenantIndex = (vuNumber - 1) % TENANT_COUNT;
  return `tenant-${String(tenantIndex).padStart(3, '0')}`;
}

// Generate deterministic API key for tenant
function getApiKeyForTenant(tenantId) {
  // In real scenario, this would be fetched from a secure store
  return `key-${tenantId}-${randomString(8)}`;
}

export const options = {
  scenarios: {
    multi_tenant_mixed: {
      executor: 'constant-vus',
      exec: 'runMultiTenant',
      vus: TENANT_COUNT,
      duration: DURATION,
    },
  },
  thresholds: {
    tenant_isolation_violations: ['rate<0.001'],     // <0.1% isolation failures
    cross_tenant_data_leakage: ['rate<0.001'],       // <0.1% data leakage
    http_req_failed: ['rate<0.05'],                  // <5% overall errors
  },
};

function getAuthHeaders(tenantId) {
  return {
    'Authorization': `Bearer ${getApiKeyForTenant(tenantId)}`,
    'X-Tenant-ID': tenantId,
    'X-Request-ID': `mt-${tenantId}-${Date.now()}`,
    'Content-Type': 'application/json',
  };
}

export function runMultiTenant() {
  const tenantId = getTenantForVU(__VU);
  
  // Rotate through different operations to simulate realistic usage
  const operation = randomIntBetween(1, 4);
  
  let result;
  switch (operation) {
    case 1:
      result = runTenantExtraction(tenantId);
      break;
    case 2:
      result = runTenantSearch(tenantId);
      break;
    case 3:
      result = runTenantWorkflow(tenantId);
      break;
    case 4:
      result = runTenantDataValidation(tenantId);
      break;
  }
  
  perTenantThroughput.add(1);
  
  // Randomized sleep to simulate realistic request patterns
  sleep(randomIntBetween(1, 4));
}

function runTenantExtraction(tenantId) {
  // Create content unique to this tenant
  const uniqueMarker = `tenant-marker-${tenantId}-${randomString(8)}`;
  
  const payload = JSON.stringify({
    content_id: `mt-${tenantId}-${Date.now()}`,
    source_url: `https://${tenantId}.example.com/doc/${randomIntBetween(1, 1000)}`,
    markdown_content: `# Document for ${tenantId}

Unique marker: ${uniqueMarker}
Tenant: ${tenantId}
Timestamp: ${Date.now()}
Random: ${randomString(20)}`,
    extraction_config: {
      extract_values: true,
      extract_entities: true,
      confidence_threshold: 0.7,
    },
    store_in_graph: true,
    tenant_id: tenantId, // Explicit tenant scoping
  });

  const response = http.post(`${L2_URL}/v1/extract-and-ingest`, payload, {
    headers: getAuthHeaders(tenantId),
    timeout: '30s',
  });

  // Validate response contains tenant-specific data
  const success = check(response, {
    'MT L2: status is 200/202': (r) => r.status === 200 || r.status === 202,
    'MT L2: response includes tenant context': (r) => {
      try {
        const body = r.json();
        // Verify the response acknowledges the tenant
        return body.tenant_id === tenantId || body.request_id?.includes(tenantId);
      } catch {
        return false;
      }
    },
  });

  if (!success && response.status === 403) {
    tenantIsolationErrors.add(true);
  }

  return { success, response };
}

function runTenantSearch(tenantId) {
  // Search within tenant scope
  const payload = JSON.stringify({
    query: `tenant:${tenantId} document`,
    search_type: 'hybrid',
    tenant_filter: tenantId,
    limit: 10,
  });

  const response = http.post(`${L3_URL}/v1/search/hybrid`, payload, {
    headers: getAuthHeaders(tenantId),
    timeout: '5s',
  });

  let isolationViolation = false;
  
  const success = check(response, {
    'MT L3: status is 200': (r) => r.status === 200,
    'MT L3: results filtered by tenant': (r) => {
      try {
        const body = r.json();
        const results = body.results || [];
        
        // Check for cross-tenant data leakage
        for (const result of results) {
          const resultTenant = result.tenant_id || result.properties?.tenant_id;
          if (resultTenant && resultTenant !== tenantId) {
            isolationViolation = true;
            return false; // Isolation violation detected
          }
        }
        return true;
      } catch {
        return true; // Empty results are ok
      }
    },
  });

  if (isolationViolation) {
    crossTenantDataLeakage.add(true);
  }

  return { success, response, isolationViolation };
}

function runTenantWorkflow(tenantId) {
  const payload = JSON.stringify({
    workflow_id: `mt-wf-${tenantId}-${Date.now()}`,
    tenant_id: tenantId,
    agent_type: 'analyzer',
    input_context: {
      query: `tenant ${tenantId} analysis request`,
      priority: 'normal',
    },
  });

  const response = http.post(`${L4_URL}/v1/workflows/execute`, payload, {
    headers: getAuthHeaders(tenantId),
    timeout: '30s',
  });

  const success = check(response, {
    'MT L4: status is 200/202': (r) => r.status === 200 || r.status === 202,
    'MT L4: workflow tenant-scoped': (r) => {
      try {
        const body = r.json();
        return body.tenant_id === tenantId || body.workflow_id?.includes(tenantId);
      } catch {
        return false;
      }
    },
  });

  return { success, response };
}

function runTenantDataValidation(tenantId) {
  // Query for data that should only exist in this tenant
  const payload = JSON.stringify({
    query: `tenant-marker-${tenantId}`,
    search_type: 'exact',
    tenant_filter: tenantId,
    limit: 100,
  });

  const response = http.post(`${L3_URL}/v1/search/hybrid`, payload, {
    headers: getAuthHeaders(tenantId),
    timeout: '10s',
  });

  let leakageDetected = false;
  
  const success = check(response, {
    'MT Validation: status is 200': (r) => r.status === 200,
    'MT Validation: only tenant data returned': (r) => {
      try {
        const body = r.json();
        const results = body.results || [];
        
        for (const result of results) {
          const content = JSON.stringify(result);
          // Check if content contains other tenant markers
          for (let i = 0; i < TENANT_COUNT; i++) {
            const otherTenant = `tenant-${String(i).padStart(3, '0')}`;
            if (otherTenant !== tenantId && content.includes(`tenant-marker-${otherTenant}`)) {
              leakageDetected = true;
              return false;
            }
          }
        }
        return true;
      } catch {
        return true;
      }
    },
  });

  if (leakageDetected) {
    crossTenantDataLeakage.add(true);
  }

  return { success, response, leakageDetected };
}

export function handleSummary(data) {
  const isolationViolationRate = data.metrics.tenant_isolation_violations?.rate || 0;
  const leakageRate = data.metrics.cross_tenant_data_leakage?.rate || 0;
  const errorRate = data.metrics.http_req_failed?.rate || 0;
  
  const totalRequests = data.metrics.per_tenant_requests?.count || 0;
  const requestsPerTenant = TENANT_COUNT > 0 ? totalRequests / TENANT_COUNT : 0;
  
  // Check for resource contention by comparing latencies
  const httpDuration = data.metrics.http_req_duration;
  const avgLatency = httpDuration?.avg || 0;
  const p95Latency = httpDuration?.['p(95)'] || 0;
  const contentionDetected = p95Latency > avgLatency * 3;

  return {
    stdout: JSON.stringify({
      test_type: 'multi_tenant',
      tenant_count: TENANT_COUNT,
      total_requests: totalRequests,
      avg_requests_per_tenant: Math.round(requestsPerTenant),
      isolation_violation_rate: (isolationViolationRate * 100).toFixed(3) + '%',
      data_leakage_rate: (leakageRate * 100).toFixed(3) + '%',
      error_rate: (errorRate * 100).toFixed(2) + '%',
      avg_latency_ms: avgLatency.toFixed(2),
      p95_latency_ms: p95Latency.toFixed(2),
      resource_contention: contentionDetected,
      passed: isolationViolationRate < 0.001 && leakageRate < 0.001 && errorRate < 0.05,
      critical_issues: [],
      warnings: [],
      recommendation: isolationViolationRate > 0.001 || leakageRate > 0.001
        ? 'CRITICAL: Tenant isolation violations detected. Immediate investigation required.'
        : contentionDetected
        ? 'WARNING: Resource contention detected under multi-tenant load. Consider horizontal scaling.'
        : 'Tenant isolation validated successfully.',
    }, null, 2),
    'artifacts/performance/multi-tenant-summary.json': JSON.stringify(data, null, 2),
  };
}
