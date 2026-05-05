import { describe, expect, it } from "vitest";

import { AgentEventType } from "./events";
import { parseAgentEvent, parseAgentEventJson } from "./eventSchemas";
import { parseJobStreamEventJson } from "../hooks/useJobStream";
import { parseWorkflowSseMessageJson } from "../hooks/useWorkflows";

describe("AgentEvent runtime boundary schemas", () => {
  it("parses backend-shaped AGUI text deltas from SSE JSON", () => {
    const event = parseAgentEventJson(
      JSON.stringify({
        type: AgentEventType.TEXT_MESSAGE_CONTENT,
        timestamp: "2026-05-05T21:00:00.000Z",
        runId: "run-123",
        messageId: "msg-1",
        delta: "partial response",
      })
    );

    expect(event).toMatchObject({
      type: AgentEventType.TEXT_MESSAGE_CONTENT,
      messageId: "msg-1",
      delta: "partial response",
    });
  });

  it("rejects malformed AGUI events before they reach stream consumers", () => {
    expect(() =>
      parseAgentEvent({
        type: AgentEventType.TOOL_CALL_END,
        timestamp: "2026-05-05T21:00:00.000Z",
        toolCallId: "tool-1",
      })
    ).toThrow();
  });
});

describe("job stream runtime boundary parser", () => {
  it("parses valid extraction job stream events from JSON", () => {
    const event = parseJobStreamEventJson(
      JSON.stringify({
        type: "progress",
        timestamp: "2026-05-05T21:00:00.000Z",
        data: 45,
      })
    );

    expect(event).toMatchObject({ type: "progress", data: 45 });
  });

  it("returns null for malformed or structurally invalid job stream events", () => {
    expect(parseJobStreamEventJson("{not-json")).toBeNull();
    expect(
      parseJobStreamEventJson(JSON.stringify({ type: "unknown", data: 1 }))
    ).toBeNull();
  });
});

describe("workflow SSE runtime boundary parser", () => {
  it("extracts backend-shaped workflow payloads from SSE JSON", () => {
    const payload = parseWorkflowSseMessageJson(
      JSON.stringify({
        event: "workflow_update",
        payload: {
          workflow_instance_id: "wf-123",
          workflow_type: "analysis",
          status: "running",
          progress_percentage: 25,
        },
      })
    );

    expect(payload).toMatchObject({
      workflow_instance_id: "wf-123",
      workflow_type: "analysis",
      status: "running",
      progress_percentage: 25,
    });
  });

  it("returns null for malformed workflow SSE JSON and missing payload envelopes", () => {
    expect(parseWorkflowSseMessageJson("{not-json")).toBeNull();
    expect(
      parseWorkflowSseMessageJson(JSON.stringify({ event: "heartbeat" }))
    ).toBeNull();
  });
});
