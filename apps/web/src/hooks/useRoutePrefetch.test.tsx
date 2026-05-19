/**
 * Tests for useRoutePrefetch hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
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
  interface MockApiResponse<TData> {
    data: TData;
  }

  interface AccountDetailResponse {
    id: string;
    name?: string;
  }

  type SetTimeoutSpy = ReturnType<typeof vi.spyOn<typeof window, "setTimeout">>;
  type ClearTimeoutSpy = ReturnType<typeof vi.spyOn<typeof window, "clearTimeout">>;

  const mockApiGet = () => vi.mocked(apiClient.get);

  function setApiGetResolvedValue<TData>(data: TData) {
    const response: MockApiResponse<TData> = { data };
    mockApiGet().mockResolvedValue(response);
  }

  function setApiGetRejectedValue(error: Error) {
    mockApiGet().mockRejectedValue(error);
  }

  function setMatchMediaReturnValue(matches: boolean) {
    // Centralize loose cast to one helper because mocked DOM APIs are intentionally partial.
    matchMediaMock.mockReturnValue({ matches } as MediaQueryList);
  }

  let setTimeoutSpy: SetTimeoutSpy;
  let clearTimeoutSpy: ClearTimeoutSpy;
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
  });

  function createWrapper() {
    return ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }

  it("should prefetch account detail after debounce delay", async () => {
    setApiGetResolvedValue<AccountDetailResponse>({ id: "acc-001", name: "Test Account" });

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchAccountDetail("acc-001");

    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 150);

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith("l4", "/accounts/acc-001");
    });
    const firstCallResponse = await mockApiGet().mock.results[0]?.value;
    expect(firstCallResponse).toHaveProperty("data.id");
  });

  it("should prefetch business case detail after debounce delay", async () => {
    setApiGetResolvedValue<AccountDetailResponse>({ id: "case-001", name: "Test Case" });

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchBusinessCaseDetail("case-001");

    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 150);

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith("l4", "/workflows/case-001/result");
    });
    const firstCallResponse = await mockApiGet().mock.results[0]?.value;
    expect(firstCallResponse).toHaveProperty("data.id");
  });

  it("should cancel pending prefetch", () => {
    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchAccountDetail("acc-001");
    result.current.cancelPrefetch();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it("should skip prefetch on mobile devices", () => {
    setMatchMediaReturnValue(true);

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
    setApiGetRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    // Should not throw
    expect(() => result.current.prefetchAccountDetail("acc-001")).not.toThrow();

    expect(setTimeoutSpy).toHaveBeenCalled();
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith("l4", "/accounts/acc-001");
    });
  });

  it("should deduplicate prefetches for the same ID", async () => {
    setApiGetResolvedValue<AccountDetailResponse>({ id: "acc-001" });

    const { result } = renderHook(() => useRoutePrefetch(), { wrapper: createWrapper() });

    result.current.prefetchAccountDetail("acc-001");

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledTimes(1);
    });

    result.current.prefetchAccountDetail("acc-001");

    await new Promise(resolve => setTimeout(resolve, 200));

    expect(apiClient.get).toHaveBeenCalledTimes(1);
  });
});
