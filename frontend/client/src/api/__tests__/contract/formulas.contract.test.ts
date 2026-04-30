import { describe, it } from 'vitest';

/**
 * Contract tests: Formulas (L3)
 */

describe('Contract: Formulas', () => {
  it.todo('should expose GET /formulas, GET /formulas/{id}, POST /formulas, PATCH /formulas/{id}, DELETE /formulas/{id}');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching FormulaSchema');
  it.todo('should include required fields: id, formula_id, name, expression, version, status, owner, updated_at, created_at, variables');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Formula Evaluation', () => {
  it.todo('should expose POST /formulas/evaluate');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching FormulaEvaluationResultSchema');
  it.todo('should include required fields: result, unit, confidence, calculation_steps, formula_used');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Formula Scenario', () => {
  it.todo('should expose POST /formulas/scenario');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching FormulaEvaluationResultSchema');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Formula Approvals', () => {
  it.todo('should expose GET /formulas/approvals/pending');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return array of ApprovalRequest shapes');
  it.todo('should include required fields: id, formula_id, formula_name, submitted_by, submitted_at, status');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});
