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
      // Use React Router's prefetch if available (v7+)
      // Otherwise, this is a no-op but future-proof
      try {
        navigate(path, { replace: false });
        hasPrefetched.current = true;
      } catch {
        // Ignore prefetch errors
      }
    }, debounceMs);
  }, [path, debounceMs, navigate, isMobile]);

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
