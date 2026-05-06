/**
 * Tests for useRoutePrefetch hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRoutePrefetch } from "./useRoutePrefetch";
import { apiClient } from "@/api/client";

// Mock apiClient
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

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
    setTimeoutSpy = vi.spyOn(global, "setTimeout");
    clearTimeoutSpy = vi.spyOn(global, "clearTimeout");

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
  });

  function createWrapper() {
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }

  it("should prefetch account detail after debounce delay", async () => {
    setTimeoutSpy.mockImplementation((callback: () => void) => {
      callback();
      return 1 as unknown as NodeJS.Timeout;
    });

    (apiClient.get as any).mockResolvedValue({ data: { id: "acc-001", name: "Test Account" } });

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchAccountDetail("acc-001");

    await waitFor(() => {
      expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 150);
    });
  });

  it("should prefetch business case detail after debounce delay", async () => {
    setTimeoutSpy.mockImplementation((callback: () => void) => {
      callback();
      return 1 as unknown as NodeJS.Timeout;
    });

    (apiClient.get as any).mockResolvedValue({ data: { id: "case-001", name: "Test Case" } });

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchBusinessCaseDetail("case-001");

    await waitFor(() => {
      expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 150);
    });
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
    setTimeoutSpy.mockImplementation((callback: () => void) => {
      callback();
      return 1 as unknown as NodeJS.Timeout;
    });

    (apiClient.get as any).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    // Should not throw
    expect(() => result.current.prefetchAccountDetail("acc-001")).not.toThrow();

    await waitFor(() => {
      expect(setTimeoutSpy).toHaveBeenCalled();
    });
  });

  it("should deduplicate prefetches for the same ID", async () => {
    setTimeoutSpy.mockImplementation((callback: () => void) => {
      callback();
      return 1 as unknown as NodeJS.Timeout;
    });

    (apiClient.get as any).mockResolvedValue({ data: { id: "acc-001" } });

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchAccountDetail("acc-001");
    result.current.prefetchAccountDetail("acc-001");

    await waitFor(() => {
      expect(setTimeoutSpy).toHaveBeenCalledTimes(1);
    });
  });
});
