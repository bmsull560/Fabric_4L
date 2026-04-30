import { describe, it } from 'vitest';

/**
 * Contract tests: Extraction (L2)
 *
 * NOTE: There is a known path mismatch between frontend expectations
 * (GET /jobs/{id}) and backend canonical routes (GET /extract/status/{id}).
 * These tests document the intended contract regardless of current alignment.
 */

describe('Contract: Extraction Status', () => {
  it.todo('should expose GET /extract/status/{job_id} (or aligned alias GET /jobs/{job_id})');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching ExtractionJob with required fields: id, status, progress_percent_complete, progress_pages_found, progress_processed_pages, progress_logs, extracted_entities');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Extraction Results', () => {
  it.todo('should expose GET /extract/results/{job_id} (or equivalent)');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape with extracted records and metadata');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Extraction Events (SSE)', () => {
  it.todo('should expose SSE GET /extract/jobs/{job_id}/events');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should stream event types: job_started, job_progress, job_completed, job_failed');
  it.todo('should close stream when job reaches terminal state');
});
