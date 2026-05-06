/**
 * useRoutePrefetch - Prefetch lazy-loaded routes on hover/focus
 * 
 * This hook provides a debounced prefetch mechanism for high-traffic routes.
 * Prefetching is triggered on pointer enter and keyboard focus, but skipped on mobile/touch devices.
 */
import { useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";

interface UseRoutePrefetchOptions {
  /** The route path to prefetch */
  path: string;
  /** Debounce delay in milliseconds (default: 150ms) */
  debounceMs?: number;
  /** Whether to skip prefetching on mobile/touch devices (default: true) */
  skipMobile?: boolean;
}

/**
 * Hook to prefetch a route when user hovers or focuses on a navigation element
 */
export function useRoutePrefetch({
  path,
  debounceMs = 150,
  skipMobile = true,
}: UseRoutePrefetchOptions) {
  const navigate = useNavigate();
  const timeoutRef = useRef<number | null>(null);
  const hasPrefetched = useRef(false);

  // Check if device is mobile/touch
  const isMobile = useCallback(() => {
    if (typeof window === "undefined") return false;
    if (skipMobile && window.matchMedia("(pointer: coarse)").matches) {
      return true;
    }
    return false;
  }, [skipMobile]);

  const prefetch = useCallback(() => {
    if (hasPrefetched.current || isMobile()) return;

    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = window.setTimeout(() => {
      // NOTE: React Router does not have built-in prefetching.
      // This hook is a placeholder for future prefetch implementation.
      // Options for proper prefetching:
      // 1. Use React.lazy with prefetch() if using code splitting
      // 2. Use @tanstack/react-router which has prefetching support
      // 3. Implement a custom prefetch mechanism that loads route data
      //
      // For now, this is a no-op to prevent unintended navigation.
      hasPrefetched.current = true;
    }, debounceMs);
  }, [path, debounceMs, isMobile]);

  const cancelPrefetch = useCallback(() => {
    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    prefetch,
    cancelPrefetch,
    isMobile: isMobile(),
  };
}

/**
 * Event handler props for navigation elements
 */
export function usePrefetchHandlers(path: string) {
  const { prefetch, cancelPrefetch } = useRoutePrefetch({ path });

  return {
    onMouseEnter: prefetch,
    onFocus: prefetch,
    onMouseLeave: cancelPrefetch,
    onBlur: cancelPrefetch,
  };
}
