import { describe, expect, it } from "vitest";

import { formatViolations, scanSource } from "./trustBoundaryGuard";

describe("trustBoundaryGuard", () => {
  it("allows protected hooks to return schema-parsed response data", () => {
    const violations = scanSource(
      "src/hooks/useEvidence.ts",
      `
        const response = await apiClient.get("/evidence");
        return parseEvidenceListResponse(response.data);
      `
    );

    expect(violations).toEqual([]);
  });

  it("flags response.data type assertions in migrated hook boundaries", () => {
    const violations = scanSource(
      "src/hooks/useCompetitiveIntel.ts",
      `
        const response = await apiClient.get("/competitive-intel");
        return response.data as CompetitiveLandscapeResponse;
      `
    );

    expect(violations).toHaveLength(1);
    expect(violations[0]).toMatchObject({
      file: "src/hooks/useCompetitiveIntel.ts",
      line: 3,
      kind: "response-data-cast",
    });
    expect(formatViolations(violations)).toContain(
      "schema-owned parse* helper"
    );
  });

  it("flags direct JSON.parse usage in migrated stream boundaries", () => {
    const violations = scanSource(
      "src/hooks/useJobStream.ts",
      `
        const raw = event.data;
        const parsed = JSON.parse(raw);
      `
    );

    expect(violations).toHaveLength(1);
    expect(violations[0]).toMatchObject({
      file: "src/hooks/useJobStream.ts",
      line: 3,
      kind: "direct-json-parse",
    });
    expect(formatViolations(violations)).toContain(
      "centralized schema boundary helper"
    );
  });

  it("does not flag direct JSON parsing outside the migrated stream guard scope", () => {
    const violations = scanSource(
      "src/hooks/useOntology.ts",
      `
        const parsedSchema = JSON.parse(jsonData);
        const result = OntologySchemaSchema.parse(parsedSchema);
      `
    );

    expect(violations).toEqual([]);
  });
});
