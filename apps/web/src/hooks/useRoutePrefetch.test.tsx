/**
 * Tests for useRoutePrefetch hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useRoutePrefetch } from "./useRoutePrefetch";
import { apiClient } from "@/api/client";

// Mock apiClient
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

vi.mock("@/pages/EntityDetail", () => ({ default: () => null }));
vi.mock("@/pages/BusinessCase", () => ({ default: () => null }));

// Mock window.matchMedia
const matchMediaMock = vi.fn().mockImplementation((query) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}));

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: matchMediaMock,
});

describe("useRoutePrefetch", () => {
  let setTimeoutSpy: any;
  let clearTimeoutSpy: any;
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    // Reset matchMedia mock to default implementation
    matchMediaMock.mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    // Create fresh spies for each test
    setTimeoutSpy = vi.spyOn(window, "setTimeout");
    clearTimeoutSpy = vi.spyOn(window, "clearTimeout");

    // Create fresh QueryClient for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  function createWrapper() {
    return ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }

  it("should prefetch account detail after debounce delay", async () => {
    (apiClient.get as any).mockResolvedValue({ data: { id: "acc-001", name: "Test Account" } });

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchAccountDetail("acc-001");

    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 150);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(150);
    });

    expect(apiClient.get).toHaveBeenCalledWith("l4", "/accounts/acc-001");
  });

  it("should prefetch business case detail after debounce delay", async () => {
    (apiClient.get as any).mockResolvedValue({ data: { id: "case-001", name: "Test Case" } });

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchBusinessCaseDetail("case-001");

    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 150);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(150);
    });

    expect(apiClient.get).toHaveBeenCalledWith("l4", "/workflows/case-001/result");
  });

  it("should cancel pending prefetch", () => {
    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchAccountDetail("acc-001");
    result.current.cancelPrefetch();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it("should skip prefetch on mobile devices", () => {
    (window.matchMedia as any).mockReturnValue({ matches: true });

    const { result } = renderHook(() => useRoutePrefetch({ skipMobile: true }), {
      wrapper: createWrapper(),
    });

    result.current.prefetchAccountDetail("acc-001");

    expect(setTimeoutSpy).not.toHaveBeenCalled();
    expect(result.current.isMobile).toBe(true);
  });

  it("should not prefetch with empty ID", () => {
    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchAccountDetail("");
    result.current.prefetchBusinessCaseDetail("");

    expect(setTimeoutSpy).not.toHaveBeenCalled();
  });

  it("should cleanup timeout on unmount", () => {
    const { unmount, result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    // Create a timeout by calling prefetch
    result.current.prefetchAccountDetail("acc-001");

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it("should handle prefetch failures silently", async () => {
    (apiClient.get as any).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    // Should not throw
    expect(() => result.current.prefetchAccountDetail("acc-001")).not.toThrow();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(150);
    });

    expect(setTimeoutSpy).toHaveBeenCalled();
    expect(apiClient.get).toHaveBeenCalledWith("l4", "/accounts/acc-001");
  });

  it("should deduplicate prefetches for the same ID", async () => {
    (apiClient.get as any).mockResolvedValue({ data: { id: "acc-001" } });

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchAccountDetail("acc-001");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(150);
    });

    result.current.prefetchAccountDetail("acc-001");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(150);
    });

    expect(apiClient.get).toHaveBeenCalledTimes(1);
  });
});
