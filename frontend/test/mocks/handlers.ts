/**
 * MSW API Mock Handlers
 *
 * Mocks for L3 (Knowledge Graph) and L4 (Agents) API endpoints.
 * Provides predictable responses for testing hooks and components.
 */
import { http, HttpResponse, delay, type PathParams } from 'msw';

// Base API paths from environment config
const API_BASE = '/api/v1';
const L3_PREFIX = '/graph';
const L4_PREFIX = '/agents';
const L2_PREFIX = '/extract';

// ===== Workflow Mocks (L4) =====

export const workflowMocks = [
  http.get(`${API_BASE}${L4_PREFIX}/workflows/active`, async () => {
    await delay(100);
    return HttpResponse.json([
      {
        workflow_id: 'wf-1',
        workflow_type: 'market_analysis',
        name: 'Market Analysis Workflow',
        status: 'running',
        progress_percentage: 65,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
      },
      {
        workflow_id: 'wf-2',
        workflow_type: 'entity_extraction',
        name: 'Entity Extraction',
        status: 'pending',
        progress_percentage: 0,
        created_at: '2024-01-15T11:00:00Z',
        updated_at: '2024-01-15T11:00:00Z',
      },
      {
        workflow_id: 'wf-3',
        workflow_type: 'completed_job',
        name: 'Completed Analysis',
        status: 'completed',
        progress_percentage: 100,
        created_at: '2024-01-14T09:00:00Z',
        completed_at: '2024-01-14T10:30:00Z',
      },
    ]);
  }),

  http.post(`${API_BASE}${L4_PREFIX}/workflows`, async ({ request }) => {
    await delay(150);
    const body = (await request.json()) as { name?: string; workflow_type?: string };
    return HttpResponse.json({
      workflow_id: `wf-${Date.now()}`,
      workflow_instance_id: `wf-${Date.now()}`,
      name: body?.name || 'New Workflow',
      workflow_type: body?.workflow_type || 'generic',
      status: 'started',
      created_at: new Date().toISOString(),
    });
  }),

  http.delete(`${API_BASE}${L4_PREFIX}/workflows/:id`, async () => {
    await delay(100);
    return HttpResponse.json({ success: true });
  }),

  http.get(`${API_BASE}${L4_PREFIX}/workflows/:id/events`, async () => {
    // SSE endpoint - returns a stream (mocked as regular response for testing)
    return HttpResponse.json({
      type: 'workflow_update',
      payload: {
        workflow_id: 'wf-1',
        status: 'running',
        progress_percentage: 70,
      },
    });
  }),
];

// ===== Job Stream Mocks (L2) =====

export const jobStreamMocks = [
  http.get(`${API_BASE}${L2_PREFIX}/jobs/:jobId`, async ({ params }) => {
    await delay(100);
    const jobId = params.jobId as string;

    // Return specific responses for test job IDs
    if (jobId === 'job-with-logs') {
      return HttpResponse.json({
        id: jobId,
        status: 'EXTRACTING',
        progress_percent_complete: 60,
        progress_pages_found: 15,
        progress_processed_pages: 9,
        progress_logs: [
          { timestamp: '2024-01-15T10:00:00Z', level: 'INFO', message: 'Job started', status: 'OK' },
          { timestamp: '2024-01-15T10:05:00Z', level: 'INFO', message: 'Processing page 5', status: 'OK' },
          { timestamp: '2024-01-15T10:10:00Z', level: 'INFO', message: 'Extracted 10 entities', status: 'OK' },
        ],
        extracted_entities: [],
        configuration: { url: 'https://example.com' },
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:15:00Z',
      });
    }

    if (jobId === 'job-with-entities') {
      return HttpResponse.json({
        id: jobId,
        status: 'EXTRACTING',
        progress_percent_complete: 75,
        progress_pages_found: 20,
        progress_processed_pages: 15,
        progress_logs: [],
        extracted_entities: [
          { type: 'Capability', name: 'AI Analytics' },
          { type: 'Outcome', name: 'Revenue Growth' },
          { type: 'Persona', name: 'Data Scientist' },
        ],
        configuration: { url: 'https://example.com' },
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:15:00Z',
      });
    }

    if (jobId === 'completed-job') {
      return HttpResponse.json({
        id: jobId,
        status: 'COMPLETED',
        progress_percent_complete: 100,
        progress_pages_found: 20,
        progress_processed_pages: 20,
        progress_logs: [{ timestamp: '2024-01-15T10:00:00Z', level: 'INFO', message: 'Job completed', status: 'OK' }],
        extracted_entities: [{ type: 'Outcome', name: 'Completed Result' }],
        configuration: { url: 'https://example.com' },
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
      });
    }

    if (jobId === 'failed-job') {
      return HttpResponse.json({
        id: jobId,
        status: 'FAILED',
        progress_percent_complete: 45,
        progress_pages_found: 10,
        progress_processed_pages: 5,
        progress_logs: [{ timestamp: '2024-01-15T10:00:00Z', level: 'ERROR', message: 'Extraction failed', status: 'ERROR' }],
        extracted_entities: [],
        configuration: { url: 'https://example.com' },
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:15:00Z',
      });
    }

    if (jobId === 'non-existent-job') {
      return new HttpResponse(JSON.stringify({ error: 'Job not found' }), { status: 404 });
    }

    // Default response for any job ID
    return HttpResponse.json({
      id: jobId,
      status: 'EXTRACTING',
      progress_percent_complete: 45,
      progress_pages_found: 10,
      progress_processed_pages: 5,
      progress_logs: [
        { timestamp: '2024-01-15T10:00:00Z', level: 'INFO', message: 'Job started', status: 'OK' },
        { timestamp: '2024-01-15T10:05:00Z', level: 'INFO', message: 'Crawling domain', status: 'OK' },
        { timestamp: '2024-01-15T10:10:00Z', level: 'INFO', message: 'Extracting entities', status: 'OK' },
      ],
      extracted_entities: [
        { type: 'Outcome', name: 'Revenue Growth' },
        { type: 'Capability', name: 'Data Analytics' },
      ],
      configuration: { url: 'https://example.com' },
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:15:00Z',
    });
  }),

  // Polling endpoint - returns same data as single job endpoint
  http.get(`${API_BASE}${L2_PREFIX}/jobs/:jobId/poll`, async ({ params }) => {
    await delay(100);
    const jobId = params.jobId as string;

    // Return consistent status for completed/failed jobs
    if (jobId === 'completed-job') {
      return HttpResponse.json({
        id: jobId,
        status: 'COMPLETED',
        progress_percent_complete: 100,
        progress_logs: [],
        extracted_entities: [],
      });
    }
    if (jobId === 'failed-job') {
      return HttpResponse.json({
        id: jobId,
        status: 'FAILED',
        progress_percent_complete: 45,
        progress_logs: [{ timestamp: '2024-01-15T10:00:00Z', level: 'ERROR', message: 'Extraction failed' }],
        extracted_entities: [],
      });
    }

    return HttpResponse.json({
      id: jobId,
      status: 'EXTRACTING',
      progress_percent_complete: 50,
      progress_pages_found: 12,
      progress_processed_pages: 6,
      progress_logs: [
        { timestamp: '2024-01-15T10:15:00Z', level: 'INFO', message: 'Processing page 6', status: 'OK' },
      ],
      extracted_entities: [{ type: 'Outcome', name: 'Cost Reduction' }],
      configuration: { url: 'https://example.com' },
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:15:00Z',
    });
  }),

  http.get(`${API_BASE}${L2_PREFIX}/jobs/:jobId/events`, async () => {
    // SSE endpoint for job streaming
    return HttpResponse.json({
      type: 'progress',
      data: 50,
    });
  }),
];

// ===== Graph Query Mocks (L3) =====

export const graphMocks = [
  http.post(`${API_BASE}${L3_PREFIX}/v1/query/graph`, async () => {
    await delay(150);
    return HttpResponse.json({
      query: 'test query',
      entities: [
        {
          id: 'ent-1',
          name: 'Test Entity',
          entity_type: 'capability',
          confidence_score: 0.95,
          description: 'A test entity',
        },
      ],
      relationships: [
        { source: 'ent-1', target: 'ent-2', type: 'RELATED_TO', confidence: 0.9 },
      ],
      context_graph: {
        nodes: [
          { id: 'ent-1', name: 'Test Entity', entity_type: 'capability', confidence_score: 0.95 },
          { id: 'ent-2', name: 'Related Entity', entity_type: 'usecase', confidence_score: 0.88 },
        ],
        relationships: [{ source: 'ent-1', target: 'ent-2', type: 'RELATED_TO' }],
      },
      confidence_score: 0.92,
      processing_time_ms: 120,
    });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/v1/entity/:entityId/context`, async ({ params, request }) => {
    await delay(100);
    const entityId = decodeURIComponent(params.entityId as string);
    const url = new URL(request.url);
    const hops = url.searchParams.get('hops') || '2';

    return HttpResponse.json({
      entity_id: entityId,
      center: {
        id: entityId,
        name: 'Center Entity',
        entity_type: 'capability',
        confidence_score: 0.95,
      },
      neighbors: [
        {
          id: 'neighbor-1',
          name: 'Neighbor One',
          entity_type: 'usecase',
          confidence_score: 0.88,
        },
        {
          id: 'neighbor-2',
          name: 'Neighbor Two',
          entity_type: 'persona',
          confidence_score: 0.82,
        },
      ],
      relationships: [
        { source: entityId, target: 'neighbor-1', type: 'ENABLES' },
        { source: 'neighbor-2', target: entityId, type: 'USES' },
      ],
      entity_count: 3,
      relationship_count: 2,
      hops: parseInt(hops, 10),
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/v1/entity/traverse`, async () => {
    await delay(150);
    return HttpResponse.json({
      start_entity_id: 'ent-1',
      direction: 'both',
      paths: [
        {
          nodes: [
            { id: 'ent-1', name: 'Start', entity_type: 'capability', confidence_score: 0.95 },
            { id: 'ent-2', name: 'End', entity_type: 'outcome', confidence_score: 0.92 },
          ],
          relationships: [{ source: 'ent-1', target: 'ent-2', type: 'DRIVES' }],
          value_score: 0.88,
        },
      ],
      path_count: 1,
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/v1/search/hybrid`, async () => {
    await delay(100);
    return HttpResponse.json({
      results: [
        { id: 'ent-1', name: 'Entity One', entity_type: 'capability', confidence_score: 0.95 },
        { id: 'ent-2', name: 'Entity Two', entity_type: 'usecase', confidence_score: 0.88 },
        { id: 'ent-3', name: 'Entity Three', entity_type: 'persona', confidence_score: 0.82 },
      ],
      total: 3,
    });
  }),
];

// ===== Benchmark Mocks (L3) =====

export const benchmarkMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/benchmarks`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const industry = url.searchParams.get('industry');

    const benchmarks = [
      {
        id: 'bench-1',
        benchmark_id: 'bench-1',
        name: 'Industry Average ROI',
        industry: industry || 'Software',
        vertical: 'SaaS',
        value_range: '2.5x - 4.0x',
        confidence: 'High',
        source: 'Industry Research',
        year: 2024,
        status: 'active',
        tags: ['roi', 'saas'],
        usage_count: 15,
      },
      {
        id: 'bench-2',
        benchmark_id: 'bench-2',
        name: 'Implementation Timeline',
        industry: industry || 'Software',
        vertical: 'Enterprise',
        value_range: '3-6 months',
        confidence: 'Medium',
        source: 'Survey Data',
        year: 2024,
        status: 'active',
        tags: ['timeline'],
        usage_count: 8,
      },
    ];

    return HttpResponse.json(benchmarks);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/benchmarks/policies`, async () => {
    await delay(100);
    return HttpResponse.json([
      {
        id: 'policy-1',
        policy_type: 'threshold',
        name: 'Minimum Confidence Threshold',
        description: 'Minimum confidence level for benchmark usage',
        value: '0.7',
        is_enabled: true,
        scope: 'tenant',
      },
      {
        id: 'policy-2',
        policy_type: 'cadence',
        name: 'Update Cadence',
        description: 'How often benchmarks are refreshed',
        value: 'monthly',
        is_enabled: true,
        scope: 'pack',
      },
    ]);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/benchmarks/:id`, async ({ params }) => {
    await delay(100);
    const id = params.id as string;
    return HttpResponse.json({
      id,
      benchmark_id: id,
      name: 'Detailed Benchmark',
      industry: 'Software',
      value_range: '2.5x - 4.0x',
      confidence: 'High',
      source: 'Industry Research',
      year: 2024,
      status: 'active',
      tags: ['detailed'],
      usage_count: 10,
    });
  }),

  http.put(`${API_BASE}${L3_PREFIX}/benchmarks/policies/:id`, async ({ params, request }) => {
    await delay(100);
    const id = params.id as string;
    const body = (await request.json()) as { value?: string; is_enabled?: boolean };
    return HttpResponse.json({
      id,
      policy_type: 'threshold',
      name: 'Updated Policy',
      description: 'Updated description',
      value: body?.value || '0.8',
      is_enabled: body?.is_enabled ?? true,
      scope: 'tenant',
    });
  }),
];

// ===== Formula Mocks (L3) =====

export const formulaMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/formulas/approvals/pending`, async () => {
    await delay(100);
    return HttpResponse.json([
      {
        id: 'approval-1',
        formula_id: 'formula-2',
        formula_name: 'Payback Period',
        submitted_by: 'user@example.com',
        submitted_at: '2024-01-10T09:00:00Z',
        change_summary: 'Updated calculation method',
        previous_version: '1.0.0',
        status: 'pending',
      },
    ]);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/formulas`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const statusFilter = url.searchParams.get('status');

    let formulas = [
      {
        id: 'formula-1',
        formula_id: 'formula-1',
        name: 'ROI Calculation',
        version: '1.0.0',
        status: 'active',
        owner: 'user@example.com',
        updated_at: '2024-01-15T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        used_in_count: 5,
        governance_score: 0.92,
        expression: 'revenue / cost',
        variables: ['revenue', 'cost'],
      },
      {
        id: 'formula-2',
        formula_id: 'formula-2',
        name: 'Payback Period',
        version: '2.0.0',
        status: 'draft',
        owner: 'user@example.com',
        updated_at: '2024-01-10T09:00:00Z',
        created_at: '2024-01-05T00:00:00Z',
        used_in_count: 2,
        governance_score: 0.75,
        expression: 'investment / monthly_savings',
        variables: ['investment', 'monthly_savings'],
      },
    ];

    // Apply status filter if provided
    if (statusFilter) {
      formulas = formulas.filter(f => f.status === statusFilter);
    }

    return HttpResponse.json(formulas);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/formulas/:id`, async ({ params }) => {
    await delay(100);
    const id = params.id as string;
    return HttpResponse.json({
      id,
      formula_id: id,
      name: 'Detailed Formula',
      version: '1.0.0',
      status: 'active',
      owner: 'user@example.com',
      updated_at: '2024-01-15T10:00:00Z',
      created_at: '2024-01-01T00:00:00Z',
      used_in_count: 10,
      governance_score: 0.95,
      expression: 'a + b',
      variables: ['a', 'b'],
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/formulas/:id/approve`, async ({ params }) => {
    await delay(150);
    return HttpResponse.json({
      formula_id: params.id,
      status: 'approved',
      approved_at: new Date().toISOString(),
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/formulas/:id/submit`, async ({ params }) => {
    await delay(150);
    return HttpResponse.json({
      formula_id: params.id,
      status: 'pending_approval',
      submitted_at: new Date().toISOString(),
    });
  }),
];

// ===== Variable Mocks (L3) =====

export const variableMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/variables`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const type = url.searchParams.get('type');
    const status = url.searchParams.get('status');
    const source = url.searchParams.get('source');

    let variables = [
      {
        id: 'var-1',
        variable_id: 'var-1',
        name: 'monthly_revenue',
        display_name: 'Monthly Revenue',
        type: type || 'currency',
        unit: 'USD',
        source: 'CRM',
        binding: 'salesforce.revenue',
        binding_path: 'opportunities.amount',
        default_value: '0',
        used_in_count: 5,
        validation_status: 'validated',
        tags: ['financial', 'revenue'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
        version: '1.0.0',
      },
      {
        id: 'var-2',
        variable_id: 'var-2',
        name: 'employee_count',
        display_name: 'Employee Count',
        type: 'integer',
        unit: 'count',
        source: 'ERP',
        binding: 'workday.headcount',
        used_in_count: 3,
        validation_status: 'pending',
        tags: ['hr'],
        created_at: '2024-01-05T00:00:00Z',
        updated_at: '2024-01-10T09:00:00Z',
        version: '1.0.0',
      },
    ];

    // Apply filters if provided
    if (status) {
      variables = variables.filter(v => v.validation_status === status);
    }
    if (source) {
      variables = variables.filter(v => v.source === source);
    }
    if (type) {
      variables = variables.filter(v => v.type === type);
    }

    return HttpResponse.json(variables);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/variables/stats`, async () => {
    await delay(100);
    return HttpResponse.json({
      total: 50,
      validated: 40,
      pending: 8,
      failed: 2,
      manual_sources: 15,
      avg_usage: 4.5,
    });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/variables/bindings`, async () => {
    await delay(100);
    return HttpResponse.json([
      {
        id: 'binding-1',
        name: 'Salesforce CRM',
        source_type: 'CRM',
        connection_string: 'salesforce://production',
        status: 'connected',
        last_sync: '2024-01-15T10:00:00Z',
        variables_bound: 10,
      },
      {
        id: 'binding-2',
        name: 'Workday HR',
        source_type: 'ERP',
        status: 'disconnected',
        variables_bound: 5,
        error_message: 'Authentication expired',
      },
    ]);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/variables/:id`, async ({ params }) => {
    await delay(100);
    const id = params.id as string;
    return HttpResponse.json({
      id,
      variable_id: id,
      name: 'detailed_variable',
      display_name: 'Detailed Variable',
      type: 'float',
      unit: 'percentage',
      source: 'Database',
      binding: 'custom.db',
      binding_path: 'metrics.conversion_rate',
      default_value: '0.0',
      used_in_count: 10,
      validation_status: 'validated',
      tags: ['detailed'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      version: '1.0.0',
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/variables/:id/validate`, async ({ params }) => {
    await delay(150);
    return HttpResponse.json({
      variable_id: params.id,
      validation_status: 'validated',
      validated_at: new Date().toISOString(),
    });
  }),
];

// ===== Provenance Mocks (L3) =====

export const provenanceMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/provenance/:entityId`, async ({ params, request }) => {
    await delay(100);
    const entityId = decodeURIComponent(params.entityId as string);
    const url = new URL(request.url);
    const format = url.searchParams.get('format') || 'json';

    return HttpResponse.json({
      entity_id: entityId,
      entity_type: 'business_case',
      entity_name: 'Test Business Case',
      source: 'extraction',
      extraction_job_id: 'job-123',
      confidence_score: 0.95,
      created_at: '2024-01-15T10:00:00Z',
      format,
      steps: [
        {
          step: 1,
          label: 'Entity Extraction',
          detail: 'Extracted from source document',
          timestamp: '2024-01-15T10:00:00Z',
          agent: 'extraction_agent',
        },
        {
          step: 2,
          label: 'Formula Application',
          detail: 'Applied ROI calculation formula',
          timestamp: '2024-01-15T10:05:00Z',
          agent: 'formula_agent',
        },
        {
          step: 3,
          label: 'Value Calculation',
          detail: 'Computed total value: $1.2M',
          timestamp: '2024-01-15T10:10:00Z',
          agent: 'calculation_agent',
        },
      ],
    });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/audit/logs`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const source = url.searchParams.get('source') || 'all';

    return HttpResponse.json({
      entries: [
        {
          id: 'audit-1',
          timestamp: '2024-01-15T10:00:00Z',
          source: source === 'all' ? 'provenance' : (source as 'provenance' | 'access'),
          event_type: 'create',
          entity_id: 'entity-1',
          entity_type: 'business_case',
          action: 'create',
          agent: 'user@example.com',
          details: {},
        },
        {
          id: 'audit-2',
          timestamp: '2024-01-15T10:05:00Z',
          source: source === 'all' ? 'provenance' : (source as 'provenance' | 'access'),
          event_type: 'update',
          entity_id: 'entity-1',
          entity_type: 'business_case',
          action: 'update_value',
          agent: 'formula_agent',
          details: { field: 'total_value' },
        },
      ],
      total: 2,
      page: 1,
      per_page: 20,
    });
  }),
];

// ===== Business Case Mocks (L4) =====

export const businessCaseMocks = [
  http.get(`${API_BASE}${L4_PREFIX}/analysis/cases/:caseId`, async ({ params }) => {
    await delay(100);
    const caseId = params.caseId as string;
    return HttpResponse.json({
      case_id: caseId,
      title: 'Test Business Case',
      summary: 'This is a test business case with comprehensive analysis.',
      total_value: 1200000,
      implementation_cost: 300000,
      roi_ratio: 4.0,
      payback_months: 12,
      confidence_score: 0.92,
      recommendations: [
        'Implement solution within Q2',
        'Focus on high-value customer segments',
        'Monitor metrics monthly',
      ],
      status: 'completed',
      created_at: '2024-01-15T10:00:00Z',
      page_count: 15,
      file_size_bytes: 102400,
      document_url: 'https://example.com/docs/case.pdf',
    });
  }),

  http.get(`${API_BASE}${L4_PREFIX}/analysis/cases/:caseId/export`, async ({ params, request }) => {
    await delay(200);
    const caseId = params.caseId as string;
    const url = new URL(request.url);
    const format = url.searchParams.get('format') || 'pdf';

    return HttpResponse.json({
      case_id: caseId,
      format,
      document_url: `https://example.com/downloads/${caseId}.${format}`,
      download_ready: true,
    });
  }),
];

// ===== Value Pack Mocks (L3) =====

export const valuePackMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/packs`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const industry = url.searchParams.get('industry');
    const status = url.searchParams.get('status');
    const scope = url.searchParams.get('scope');
    const search = url.searchParams.get('search');

    let packs = [
      {
        id: 'pack-1',
        pack_id: 'enterprise-security-roi',
        name: 'Enterprise Security ROI',
        industry: 'SaaS / B2B',
        description: 'Comprehensive security ROI calculations for enterprise customers',
        driver_count: 5,
        formula_count: 12,
        benchmark_count: 8,
        workflow_count: 3,
        status: 'active',
        scope: 'global' as const,
        updated_at: '2024-01-15T10:00:00Z',
        created_at: '2024-01-10T08:00:00Z',
        version: '1.2.0',
        owner: 'security-team',
      },
      {
        id: 'pack-2',
        pack_id: 'churn-reduction',
        name: 'Customer Churn Reduction',
        industry: 'SaaS / B2B',
        description: 'Analyze and reduce customer churn with predictive models',
        driver_count: 3,
        formula_count: 8,
        benchmark_count: 5,
        workflow_count: 2,
        status: 'published',
        scope: 'global' as const,
        updated_at: '2024-01-14T15:30:00Z',
        created_at: '2024-01-12T09:00:00Z',
        version: '1.0.0',
        owner: 'customer-success',
      },
      {
        id: 'pack-3',
        pack_id: 'healthcare-compliance',
        name: 'Healthcare Compliance',
        industry: 'Healthcare',
        description: 'HIPAA compliance and risk assessment tools',
        driver_count: 4,
        formula_count: 6,
        benchmark_count: 10,
        workflow_count: 4,
        status: 'draft',
        scope: 'tenant' as const,
        updated_at: '2024-01-13T11:00:00Z',
        created_at: '2024-01-13T10:00:00Z',
        version: '0.9.0',
        owner: 'compliance-team',
      },
      {
        id: 'pack-4',
        pack_id: 'fintech-metrics',
        name: 'Fintech Metrics Suite',
        industry: 'Financial Services',
        description: 'Regulatory and growth metrics for fintech companies',
        driver_count: 6,
        formula_count: 15,
        benchmark_count: 12,
        workflow_count: 5,
        status: 'archived',
        scope: 'global' as const,
        updated_at: '2023-12-01T09:00:00Z',
        created_at: '2023-11-15T08:00:00Z',
        version: '0.5.0',
        owner: 'finance-team',
      },
    ];

    // Apply filters
    if (industry && industry !== 'all') {
      packs = packs.filter(p => p.industry.toLowerCase().includes(industry.toLowerCase()));
    }
    if (status && status !== 'all') {
      packs = packs.filter(p => p.status === status);
    }
    if (scope && scope !== 'all') {
      packs = packs.filter(p => p.scope === scope);
    }
    if (search) {
      const searchLower = search.toLowerCase();
      packs = packs.filter(p => 
        p.name.toLowerCase().includes(searchLower) ||
        p.description?.toLowerCase().includes(searchLower)
      );
    }

    return HttpResponse.json(packs);
  }),

  http.post(`${API_BASE}${L3_PREFIX}/packs/:packId/apply`, async ({ params, request }) => {
    await delay(300);
    const packId = params.packId as string;
    const body = (await request.json()) as { entity_id?: string };

    // Simulate error for specific test case
    if (packId === 'error-pack') {
      return HttpResponse.json(
        { error: 'Failed to apply pack: Entity not found' },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      success: true,
      pack_id: packId,
      entity_id: body?.entity_id || 'default-entity',
      applied_at: new Date().toISOString(),
      applied_drivers: 3,
      applied_formulas: 5,
    });
  }),
];

// ===== Error Simulation Mocks =====

export const errorMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/error/500`, () => {
    return HttpResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/error/404`, () => {
    return HttpResponse.json({ error: 'Not Found' }, { status: 404 });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/error/timeout`, async () => {
    await delay(30000); // Will trigger timeout
    return HttpResponse.json({ error: 'Timeout' });
  }),
];

// ===== Combine all handlers =====

export const handlers = [
  ...workflowMocks,
  ...jobStreamMocks,
  ...graphMocks,
  ...benchmarkMocks,
  ...formulaMocks,
  ...variableMocks,
  ...provenanceMocks,
  ...businessCaseMocks,
  ...valuePackMocks,
  ...errorMocks,
];
