/**
 * Tests for useRoutePrefetch hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { useRoutePrefetch, usePrefetchHandlers } from "./useRoutePrefetch";

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
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should prefetch route after debounce delay", () => {
    setTimeoutSpy.mockImplementation((callback: () => void) => {
      callback();
      return 1 as unknown as NodeJS.Timeout;
    });

    const { result } = renderHook(
      () => useRoutePrefetch({ path: "/intelligence", debounceMs: 150 }),
      { wrapper: BrowserRouter }
    );

    result.current.prefetch();

    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 150);
  });

  it("should cancel prefetch on mouse leave", () => {
    const { result } = renderHook(
      () => useRoutePrefetch({ path: "/intelligence", debounceMs: 150 }),
      { wrapper: BrowserRouter }
    );

    result.current.prefetch();
    result.current.cancelPrefetch();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it("should skip prefetch on mobile devices", () => {
    (window.matchMedia as any).mockReturnValue({ matches: true });

    const { result } = renderHook(
      () => useRoutePrefetch({ path: "/intelligence", skipMobile: true }),
      { wrapper: BrowserRouter }
    );

    result.current.prefetch();

    expect(setTimeoutSpy).not.toHaveBeenCalled();
    expect(result.current.isMobile).toBe(true);
  });

  it("should not prefetch the same route twice", () => {
    setTimeoutSpy.mockImplementation((callback: () => void) => {
      callback();
      return 1 as unknown as NodeJS.Timeout;
    });

    const { result } = renderHook(
      () => useRoutePrefetch({ path: "/intelligence", debounceMs: 150 }),
      { wrapper: BrowserRouter }
    );

    result.current.prefetch();
    result.current.prefetch();

    expect(setTimeoutSpy).toHaveBeenCalledTimes(1);
  });

  it("should cleanup timeout on unmount", () => {
    const { unmount, result } = renderHook(
      () => useRoutePrefetch({ path: "/intelligence", debounceMs: 150 }),
      { wrapper: BrowserRouter }
    );

    // Create a timeout by calling prefetch
    result.current.prefetch();

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });
});

describe("usePrefetchHandlers", () => {
  let setTimeoutSpy: any;
  let clearTimeoutSpy: any;

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
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should return event handler props", () => {
    const { result } = renderHook(
      () => usePrefetchHandlers("/intelligence"),
      { wrapper: BrowserRouter }
    );

    expect(result.current).toBeDefined();
    expect(typeof result.current.onMouseEnter).toBe("function");
    expect(typeof result.current.onFocus).toBe("function");
    expect(typeof result.current.onMouseLeave).toBe("function");
    expect(typeof result.current.onBlur).toBe("function");
  });
});
