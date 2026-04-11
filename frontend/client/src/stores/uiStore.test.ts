import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useUIStore } from "./uiStore";

describe("useUIStore", () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    const { result } = renderHook(() => useUIStore());
    act(() => result.current._reset());
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  describe("sidebar state", () => {
    it("should toggle sidebar state", () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.sidebarOpen).toBe(true);

      act(() => result.current.toggleSidebar());

      expect(result.current.sidebarOpen).toBe(false);

      act(() => result.current.toggleSidebar());

      expect(result.current.sidebarOpen).toBe(true);
    });
  });

  describe("modal state", () => {
    it("should open modal with name and data", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => result.current.openModal("test-modal", { testData: "value" }));

      expect(result.current.activeModal).toBe("test-modal");
      expect(result.current.modalData).toEqual({ testData: "value" });
    });

    it("should close modal and clear data", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => result.current.openModal("test-modal", { data: "test" }));
      act(() => result.current.closeModal());

      expect(result.current.activeModal).toBeNull();
      expect(result.current.modalData).toBeNull();
    });

    it("should open modal without data", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => result.current.openModal("simple-modal"));

      expect(result.current.activeModal).toBe("simple-modal");
      expect(result.current.modalData).toBeNull();
    });
  });

  describe("toast queue", () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it("should add toast to queue", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => result.current.addToast("Test message", "success"));

      expect(result.current.toastQueue).toHaveLength(1);
      expect(result.current.toastQueue[0].message).toBe("Test message");
      expect(result.current.toastQueue[0].type).toBe("success");
      expect(result.current.toastQueue[0].id).toBeDefined();
    });

    it("should default toast type to info", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => result.current.addToast("Info message"));

      expect(result.current.toastQueue[0].type).toBe("info");
    });

    it("should auto-remove toast after 5 seconds", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => result.current.addToast("Auto dismiss", "error"));
      expect(result.current.toastQueue).toHaveLength(1);

      act(() => vi.advanceTimersByTime(5000));

      expect(result.current.toastQueue).toHaveLength(0);
    });

    it("should manually remove toast by id", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => result.current.addToast("Toast 1"));
      act(() => result.current.addToast("Toast 2"));

      const firstToastId = result.current.toastQueue[0].id;

      act(() => result.current.removeToast(firstToastId));

      expect(result.current.toastQueue).toHaveLength(1);
      expect(result.current.toastQueue[0].message).toBe("Toast 2");
    });

    it("should handle multiple toasts with independent dismiss timers", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => result.current.addToast("First"));
      act(() => vi.advanceTimersByTime(2000));
      act(() => result.current.addToast("Second"));

      expect(result.current.toastQueue).toHaveLength(2);

      act(() => vi.advanceTimersByTime(3000));
      expect(result.current.toastQueue).toHaveLength(1);
      expect(result.current.toastQueue[0].message).toBe("Second");

      act(() => vi.advanceTimersByTime(2000));
      expect(result.current.toastQueue).toHaveLength(0);
    });
  });

  describe("theme", () => {
    it("should set theme", () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.theme).toBe("light");

      act(() => result.current.setTheme("dark"));

      expect(result.current.theme).toBe("dark");
    });

    it("should toggle between light and dark", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => result.current.setTheme("light"));
      act(() => result.current.setTheme("dark"));
      act(() => result.current.setTheme("light"));

      expect(result.current.theme).toBe("light");
    });
  });
});
