import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import type { ValueCaseResponse } from "@/hooks/useCalculators";
import ValueCase from "./ValueCase";

vi.mock("../store/workflowStore", () => ({
  useWorkflowStore: () => ({
    prospect: { companyName: "Meridian Automotive" },
    generatedCaseId: "VC-2026-0417",
    sessionId: "wf-session-1",
    initSession: vi.fn(),
    setWorkflowContext: vi.fn(),
  }),
}));

const valueCaseFixture = {
  case_id: "VC-2026-0417",
  account_id: "acct-1",
  created_at: "2026-05-01T00:00:00Z",
  updated_at: "2026-05-02T00:00:00Z",
  levers: [],
  scenarios: [
    { name: "Conservative", total_value: 1000000, breakdown: [] },
    {
      name: "Expected",
      total_value: 2000000,
      breakdown: [
        { area: "Labor", value: 1200000, percentage: 60 },
        { area: "Quality", value: 800000, percentage: 40 },
      ],
    },
  ],
  metadata: {
    generated_by: "test",
    confidence_score: 82,
  },
} satisfies ValueCaseResponse;

vi.mock("@/hooks/useCalculators", () => ({
  useValueCase: () => ({ data: valueCaseFixture, isLoading: false, error: null }),
}));

describe("ValueCase", () => {
  it("renders typed expected-scenario breakdown rows", () => {
    render(
      <MemoryRouter>
        <ValueCase />
      </MemoryRouter>
    );

    expect(screen.getByText("Labor")).toBeInTheDocument();
    expect(screen.getByText("Quality")).toBeInTheDocument();
    expect(screen.getByText("$1.20M")).toBeInTheDocument();
    expect(screen.getByText("60% of total")).toBeInTheDocument();
  });
});
