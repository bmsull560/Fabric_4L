import { describe, expect, it } from "vitest";
import { deliverableRoutes } from "./deliverableRoutes";

describe("deliverableRoutes", () => {
  describe("businessCaseDetail", () => {
    it("builds the correct path for a given caseId", () => {
      expect(deliverableRoutes.businessCaseDetail("case-123")).toBe(
        "/deliverables/cases/case-123"
      );
    });

    it("handles caseIds with special characters by passing them through", () => {
      expect(deliverableRoutes.businessCaseDetail("abc-def-456")).toBe(
        "/deliverables/cases/abc-def-456"
      );
    });

    it("returns a string starting with /deliverables/cases/", () => {
      const path = deliverableRoutes.businessCaseDetail("x");
      expect(path).toMatch(/^\/deliverables\/cases\//);
    });
  });

  describe("businessCaseList", () => {
    it("returns the deliverables list path", () => {
      expect(deliverableRoutes.businessCaseList()).toBe("/deliverables/cases");
    });

    it("returns a consistent value on repeated calls", () => {
      expect(deliverableRoutes.businessCaseList()).toBe(
        deliverableRoutes.businessCaseList()
      );
    });
  });
});
