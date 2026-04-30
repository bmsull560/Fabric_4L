import { describe, it } from 'vitest';

/**
 * Contract tests: Agent Workflows (L4)
 */

describe('Contract: Workflow Create', () => {
  it.todo('should expose POST /workflows');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should accept request body with workflow_type, tenant_id, user_id, inputs, priority');
  it.todo('should return shape with workflow_instance_id, status, estimated_duration_seconds');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Workflow Status', () => {
  it.todo('should expose GET /workflows/{workflow_id}');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching WorkflowStatusResponse');
  it.todo('should include required fields: workflow_instance_id, workflow_type, status, current_state, progress_percentage, started_at, completed_at, error_count, has_output');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Workflow Result', () => {
  it.todo('should expose GET /workflows/{workflow_id}/result');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching WorkflowResultResponse');
  it.todo('should include required fields: workflow_id, status, output, errors, completed_at');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Workflow List Active', () => {
  it.todo('should expose GET /workflows/active?limit=&offset=&status=');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return paginated shape: { items, total, limit, offset, has_more }');
  it.todo('should support status filter');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Workflow Control', () => {
  it.todo('should expose POST /workflows/{id}/pause');
  it.todo('should expose POST /workflows/{id}/resume');
  it.todo('should expose DELETE /workflows/{id}');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return updated workflow status on control actions');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});
