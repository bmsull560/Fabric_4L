/**
 * Tests for ScenarioPanel component
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ScenarioPanel } from "./ScenarioPanel";
import { toVariableAdjustmentDto, createUiAdjustment, type UIVariableAdjustment } from "./ScenarioPanel";

// Mock the hook
vi.mock("@/hooks/useFormulaScenario", () => ({
  useFormulaScenario: () => ({
    mutate: vi.fn(),
    data: null,
    isPending: false,
    error: null,
  }),
}));

describe("ScenarioPanel", () => {
  it("renders with initial adjustment", () => {
    render(<ScenarioPanel formulaId="test-formula" />);
    expect(screen.getByPlaceholderText("Variable")).toBeInTheDocument();
  });

  it("allows adding adjustments", () => {
    render(<ScenarioPanel formulaId="test-formula" />);
    const addButton = screen.getByLabelText("Add variable adjustment");
    expect(addButton).toBeInTheDocument();
  });
});

describe("ScenarioPanel DTO mapping", () => {
  it("toVariableAdjustmentDto strips id field", () => {
    const uiAdjustment: UIVariableAdjustment = {
      id: "test-id-123",
      name: "Customer_Count",
      value: 1500,
      original_value: 1000,
    };

    const dto = toVariableAdjustmentDto(uiAdjustment);

    expect(dto).toEqual({
      name: "Customer_Count",
      value: 1500,
      original_value: 1000,
    });
    expect(dto).not.toHaveProperty("id");
  });

  it("createUiAdjustment generates stable id", () => {
    const adjustment = createUiAdjustment({
      name: "Test",
      value: 100,
      original_value: 50,
    });

    expect(adjustment).toHaveProperty("id");
    expect(typeof adjustment.id).toBe("string");
    expect(adjustment.id.length).toBeGreaterThan(0);
  });

  it("createUiAdjustment includes all required fields", () => {
    const adjustment = createUiAdjustment({
      name: "Test",
      value: 100,
      original_value: 50,
    });

    expect(adjustment).toEqual({
      id: expect.any(String),
      name: "Test",
      value: 100,
      original_value: 50,
    });
  });

  it("createUiAdjustment provides defaults", () => {
    const adjustment = createUiAdjustment();

    expect(adjustment.name).toBe("");
    expect(adjustment.value).toBe(0);
    expect(adjustment.original_value).toBe(0);
    expect(adjustment).toHaveProperty("id");
  });
});
