/**
 * Tests for useNavigation hook — §2.6 canonical navigation abstraction.
 *
 * Verifies that navigateTo() supports optional router state so callers
 * (e.g. HypothesesTab) do not need to fall back to raw useNavigate().
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { ReactNode } from "react";
import { useNavigation } from "./useNavigation";

// useWorkflowContext is used internally by useNavigation to merge query params.
vi.mock("@/hooks/useWorkflowContext", () => ({
  useWorkflowContext: () => ({}),
}));

vi.mock("@/workflow/context", () => ({
  serializeWorkflowContextToQuery: () => ({}),
}));

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

function wrapper({ children }: { children: ReactNode }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe("useNavigation — navigateTo with state", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it("navigates to a direct path without state", () => {
    const { result } = renderHook(() => useNavigation(), { wrapper });
    result.current.navigateTo("/accounts/123/intelligence");
    expect(mockNavigate).toHaveBeenCalledWith(
      "/accounts/123/intelligence",
      undefined
    );
  });

  it("navigates to a direct path with router state", () => {
    const { result } = renderHook(() => useNavigation(), { wrapper });
    result.current.navigateTo("/drivers/abc/evidence", {
      state: {
        hypothesisId: "hyp-1",
        evidenceIds: ["ev-1", "ev-2"],
        accountId: "abc",
      },
    });
    expect(mockNavigate).toHaveBeenCalledWith("/drivers/abc/evidence", {
      state: {
        hypothesisId: "hyp-1",
        evidenceIds: ["ev-1", "ev-2"],
        accountId: "abc",
      },
    });
  });

  it("navigates with state and replace option together", () => {
    const { result } = renderHook(() => useNavigation(), { wrapper });
    result.current.navigateTo("/home", {
      replace: true,
      state: { returnTo: "hypotheses" },
    });
    expect(mockNavigate).toHaveBeenCalledWith("/home", {
      replace: true,
      state: { returnTo: "hypotheses" },
    });
  });

  it("navigates via RouteState without state (existing callers unchanged)", () => {
    const { result } = renderHook(() => useNavigation(), { wrapper });
    result.current.navigateTo("home");
    expect(mockNavigate).toHaveBeenCalledWith("/home", expect.anything());
  });

  it("navigates via RouteState with params", () => {
    const { result } = renderHook(() => useNavigation(), { wrapper });
    result.current.navigateTo("account-detail", { accountId: "acct-99" });
    expect(mockNavigate).toHaveBeenCalledWith(
      "/accounts/acct-99",
      expect.anything()
    );
  });
});

describe("useNavigation — goBack / goForward", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it("calls navigate(-1) for goBack", () => {
    const { result } = renderHook(() => useNavigation(), { wrapper });
    result.current.goBack();
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it("calls navigate(1) for goForward", () => {
    const { result } = renderHook(() => useNavigation(), { wrapper });
    result.current.goForward();
    expect(mockNavigate).toHaveBeenCalledWith(1);
  });
});
