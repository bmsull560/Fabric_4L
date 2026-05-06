/**
 * Tests for useRoutePrefetch hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useRoutePrefetch, usePrefetchHandlers } from "./useRoutePrefetch";

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock window.setTimeout and clearTimeout using vi.spyOn for proper cleanup
const setTimeoutSpy = vi.spyOn(global, "setTimeout");
const clearTimeoutSpy = vi.spyOn(global, "clearTimeout");

describe("useRoutePrefetch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should prefetch route after debounce delay", () => {
    setTimeoutSpy.mockImplementation((callback: () => void) => {
      callback();
      return 1 as unknown as NodeJS.Timeout;
    });

    const { result } = renderHook(() =>
      useRoutePrefetch({ path: "/intelligence", debounceMs: 150 })
    );

    result.current.prefetch();

    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 150);
  });

  it("should cancel prefetch on mouse leave", () => {
    const { result } = renderHook(() =>
      useRoutePrefetch({ path: "/intelligence", debounceMs: 150 })
    );

    result.current.prefetch();
    result.current.cancelPrefetch();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it("should skip prefetch on mobile devices", () => {
    (window.matchMedia as any).mockReturnValue({ matches: true });

    const { result } = renderHook(() =>
      useRoutePrefetch({ path: "/intelligence", skipMobile: true })
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

    const { result } = renderHook(() =>
      useRoutePrefetch({ path: "/intelligence", debounceMs: 150 })
    );

    result.current.prefetch();
    result.current.prefetch();

    expect(setTimeoutSpy).toHaveBeenCalledTimes(1);
  });

  it("should cleanup timeout on unmount", () => {
    const { unmount } = renderHook(() =>
      useRoutePrefetch({ path: "/intelligence", debounceMs: 150 })
    );

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });
});

describe("usePrefetchHandlers", () => {
  it("should return event handler props", () => {
    const { result } = renderHook(() => usePrefetchHandlers("/intelligence"));

    expect(result.current).toHaveProperty("onMouseEnter");
    expect(result.current).toHaveProperty("onFocus");
    expect(result.current).toHaveProperty("onMouseLeave");
    expect(result.current).toHaveProperty("onBlur");
  });
});
