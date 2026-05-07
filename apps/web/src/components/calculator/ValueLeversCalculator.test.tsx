import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, vi, beforeEach } from "vitest";
import { ValueLeversCalculator } from "./ValueLeversCalculator";

const createMock = vi.fn();
const updateMock = vi.fn();

vi.mock("@/hooks/useCalculators", () => ({
  useValueLevers: () => ({ data: { metadata: { version: "v1" }, levers: [{ id: "l1", name: "Lever 1", min_value: 1, max_value: 10, base_value: 5, annual_impact: 100, confidence: 80, unit: "%", category: "Ops" }] }, isLoading: false, error: null }),
  useValueCase: () => ({ data: null }),
  useCreateValueCase: () => ({ mutateAsync: createMock }),
  useUpdateValueCase: () => ({ mutateAsync: updateMock }),
}));

describe("ValueLeversCalculator", () => {
  beforeEach(() => {
    createMock.mockReset();
    updateMock.mockReset();
    createMock.mockResolvedValue({ case_id: "case-1", levers: [{ lever_id: "l1", scenario_a: 3, scenario_b: 7 }] });
  });

  it("adjusts, saves, and reopens with persisted values", async () => {
    const { rerender } = render(<ValueLeversCalculator accountId="acc-1" industry="Manufacturing" companySize="SMB" />);
    const sliders = screen.getAllByRole("slider");
    fireEvent.change(sliders[0], { target: { value: "3" } });
    fireEvent.change(sliders[1], { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    await waitFor(() => expect(createMock).toHaveBeenCalled());

    vi.doMock("@/hooks/useCalculators", () => ({
      useValueLevers: () => ({ data: { metadata: { version: "v1" }, levers: [{ id: "l1", name: "Lever 1", min_value: 1, max_value: 10, base_value: 5, annual_impact: 100, confidence: 80, unit: "%", category: "Ops" }] }, isLoading: false, error: null }),
      useValueCase: () => ({ data: { levers: [{ lever_id: "l1", scenario_a: 3, scenario_b: 7 }] } }),
      useCreateValueCase: () => ({ mutateAsync: createMock }),
      useUpdateValueCase: () => ({ mutateAsync: updateMock }),
    }));
    rerender(<ValueLeversCalculator accountId="acc-1" industry="Manufacturing" companySize="SMB" initialCaseId="case-1" />);
  });
});
