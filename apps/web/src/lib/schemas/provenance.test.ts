import { describe, expect, it } from "vitest";

import { parseAuditLogResponse, parseProvenanceTrail } from "./provenance";

describe("provenance runtime boundary schemas", () => {
  it("parses backend-shaped provenance trails", () => {
    const parsed = parseProvenanceTrail({
      entity_id: "entity-1",
      entity_type: "account",
      entity_name: "Acme Corp",
      created_at: "2026-05-05T21:00:00.000Z",
      source: "crm",
      extraction_job_id: "job-1",
      confidence_score: 0.92,
      steps: [
        {
          step: 1,
          label: "ingested",
          detail: "CRM record imported",
          timestamp: "2026-05-05T21:00:00.000Z",
          agent: "l3-knowledge",
          entity_id: "entity-1",
        },
      ],
    });

    expect(parsed.entity_id).toBe("entity-1");
    expect(parsed.steps[0]?.label).toBe("ingested");
  });

  it("rejects malformed provenance trails", () => {
    expect(() =>
      parseProvenanceTrail({
        entity_id: "entity-1",
        entity_type: "account",
        entity_name: "Acme Corp",
        created_at: "2026-05-05T21:00:00.000Z",
        source: "crm",
        steps: [
          {
            step: "one",
            label: "ingested",
            detail: "imported",
            timestamp: "2026-05-05T21:00:00.000Z",
          },
        ],
      })
    ).toThrow();
  });

  it("parses backend-shaped audit log responses", () => {
    const parsed = parseAuditLogResponse({
      entries: [
        {
          id: "audit-1",
          timestamp: "2026-05-05T21:00:00.000Z",
          source: "provenance",
          event_type: "entity.created",
          entity_id: "entity-1",
          entity_type: "account",
          action: "create",
          agent: "l3-knowledge",
          details: { confidence: 0.92 },
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });

    expect(parsed.total).toBe(1);
    expect(parsed.entries[0]?.source).toBe("provenance");
  });

  it("rejects malformed audit log responses", () => {
    expect(() =>
      parseAuditLogResponse({
        entries: [
          {
            id: "audit-1",
            timestamp: "2026-05-05T21:00:00.000Z",
            source: "access",
            event_type: "entity.created",
            action: "create",
            agent: "l3-knowledge",
            details: {},
          },
        ],
        total: 1,
        page: 1,
        per_page: 50,
      })
    ).toThrow();
  });
});
