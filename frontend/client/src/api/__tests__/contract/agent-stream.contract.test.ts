import { describe, it } from 'vitest';

/**
 * Contract tests: Agent Stream / C1 / SSE (L4)
 */

describe('Contract: Agent Stream Chat (SSE)', () => {
  it.todo('should expose POST /agent-stream/chat');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should accept request body with message, thread_id, context');
  it.todo('should return SSE stream with event types: run_started, step_started, text_message, step_completed, run_finished, error');
  it.todo('should include required fields per event: event_id, event_type, timestamp, message, payload?');
  it.todo('should close stream on terminal event or client abort');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on non-SSE errors (4xx/5xx)');
});

describe('Contract: Workflow Events (SSE)', () => {
  it.todo('should expose SSE GET /workflows/{workflow_id}/events');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should stream event: workflow_event with data: { event_id, event_type, timestamp, message, payload }');
  it.todo('should send heartbeat/noop events to keep connection alive');
  it.todo('should close stream when workflow reaches completed/failed/cancelled');
});

describe('Contract: C1 Stream (SSE)', () => {
  it.todo('should expose POST /c1/stream');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should accept request body with C1Message array');
  it.todo('should return SSE stream with C1StreamChunk shape: { type, content?, component?, done? }');
  it.todo('should validate tenant ID against regex /^[a-zA-Z0-9_-]+$/');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});
