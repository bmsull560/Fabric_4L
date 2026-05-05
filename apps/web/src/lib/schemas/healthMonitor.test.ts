import { describe, expect, it } from "vitest";

import { parseHealthAlerts, parseSystemHealth } from "./healthMonitor";

describe("health monitor runtime boundary schemas", () => {
  it("parses backend-shaped system health payloads", () => {
    const parsed = parseSystemHealth({
      overall_status: "healthy",
      checked_at: "2026-05-05T21:00:00.000Z",
      services: [
        {
          name: "layer4-agents",
          status: "healthy",
          version: "1.0.0",
          uptime_seconds: 1234,
          last_check_at: "2026-05-05T21:00:00.000Z",
          response_time_ms: 42,
          metadata: { region: "test" },
        },
      ],
      summary: {
        healthy: 1,
        degraded: 0,
        unhealthy: 0,
        unknown: 0,
        total: 1,
      },
    });

    expect(parsed.overall_status).toBe("healthy");
    expect(parsed.services[0]?.name).toBe("layer4-agents");
  });

  it("rejects malformed system health payloads", () => {
    expect(() =>
      parseSystemHealth({
        overall_status: "offline",
        checked_at: "2026-05-05T21:00:00.000Z",
        services: [],
        summary: { total: 0 },
      })
    ).toThrow();
  });

  it("parses backend-shaped health alert lists", () => {
    const parsed = parseHealthAlerts([
      {
        id: "alert-1",
        service_name: "layer4-agents",
        severity: "warning",
        message: "latency high",
        started_at: "2026-05-05T21:00:00.000Z",
        acknowledged: false,
      },
    ]);

    expect(parsed).toHaveLength(1);
    expect(parsed[0]?.severity).toBe("warning");
  });

  it("rejects malformed health alert lists", () => {
    expect(() =>
      parseHealthAlerts([
        {
          id: "alert-1",
          service_name: "layer4-agents",
          severity: "urgent",
          message: "latency high",
          started_at: "2026-05-05T21:00:00.000Z",
        },
      ])
    ).toThrow();
  });
});
