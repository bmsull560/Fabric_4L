import { z } from "zod";

import { AgentEventType, type AgentEvent } from "./events";

const RunMetadataSchema = z
  .object({
    traceId: z.string().optional(),
    workflowId: z.string().optional(),
    tenantId: z.string().optional(),
    auditEventId: z.string().optional(),
    sourceNode: z.string().optional(),
  })
  .passthrough();

const BaseAgentEventSchema = z.object({
  timestamp: z.string().min(1),
  runId: z.string().optional(),
  eventId: z.string().optional(),
});

const ExpectedStepSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
});

const RunStartedEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.RUN_STARTED),
  description: z.string().optional(),
  expectedSteps: z.array(ExpectedStepSchema).optional(),
  metadata: RunMetadataSchema.optional(),
});

const RunFinishedEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.RUN_FINISHED),
  output: z.unknown().optional(),
  metadata: RunMetadataSchema.optional(),
});

const RunErrorEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.RUN_ERROR),
  message: z.string().min(1),
  code: z.string().optional(),
  retryable: z.boolean().optional(),
});

const StepStartedEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.STEP_STARTED),
  stepId: z.string().min(1),
  label: z.string().min(1),
  index: z.number().int().nonnegative().optional(),
});

const StepFinishedEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.STEP_FINISHED),
  stepId: z.string().min(1),
  status: z.enum(["done", "error", "skipped"]),
  result: z.unknown().optional(),
});

const TextMessageStartEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.TEXT_MESSAGE_START),
  messageId: z.string().min(1),
  role: z.enum(["agent", "system"]),
});

const TextMessageContentEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.TEXT_MESSAGE_CONTENT),
  messageId: z.string().min(1),
  delta: z.string(),
});

const TextMessageEndEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.TEXT_MESSAGE_END),
  messageId: z.string().min(1),
});

const ToolCallStartEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.TOOL_CALL_START),
  toolCallId: z.string().min(1),
  toolName: z.string().min(1),
  args: z.record(z.string(), z.unknown()).optional(),
});

const ToolCallEndEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.TOOL_CALL_END),
  toolCallId: z.string().min(1),
  result: z.unknown().optional(),
  success: z.boolean(),
  error: z.string().optional(),
});

const StateDeltaEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.STATE_DELTA),
  delta: z.record(z.string(), z.unknown()),
});

const StateSnapshotEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.STATE_SNAPSHOT),
  snapshot: z.record(z.string(), z.unknown()),
});

const CustomEventSchema = BaseAgentEventSchema.extend({
  type: z.literal(AgentEventType.CUSTOM),
  name: z.string().min(1),
  payload: z.unknown().optional(),
});

export const AgentEventSchema = z.discriminatedUnion("type", [
  RunStartedEventSchema,
  RunFinishedEventSchema,
  RunErrorEventSchema,
  StepStartedEventSchema,
  StepFinishedEventSchema,
  TextMessageStartEventSchema,
  TextMessageContentEventSchema,
  TextMessageEndEventSchema,
  ToolCallStartEventSchema,
  ToolCallEndEventSchema,
  StateDeltaEventSchema,
  StateSnapshotEventSchema,
  CustomEventSchema,
]);

export function parseAgentEvent(value: unknown): AgentEvent {
  return AgentEventSchema.parse(value) as AgentEvent;
}

export function parseJsonValue(json: string): unknown {
  const parse = JSON["parse"] as (text: string) => unknown;
  return parse(json);
}

export function parseAgentEventJson(json: string): AgentEvent {
  return parseAgentEvent(parseJsonValue(json));
}
