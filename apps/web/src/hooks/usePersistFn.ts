import { useRef } from "react";

/**
 * usePersistFn instead of useCallback to reduce cognitive load.
 *
 * Creates a stable function reference that persists across renders without
 * needing dependency arrays. The returned function always calls the latest
 * version of the provided function.
 *
 * TypeScript Note:
 * Uses `(...args: any[]) => any` constraint (with eslint-disable) because:
 * 1. It is the standard TypeScript pattern for "any callable function" used
 *    by the language itself (e.g. in Parameters<T>, ReturnType<T> utilities)
 * 2. The full type safety is preserved for callers via `Parameters<T>` and
 *    `ReturnType<T>` — `any` only appears in the generic bound, not the API
 * 3. Alternative `unknown[]` / `never[]` bounds are more restrictive and
 *    reject valid function signatures in practice
 *
 * @param fn - The function to persist across renders
 * @returns A stable function reference with the same signature
 */
export function usePersistFn<T extends (...args: any[]) => any>(fn: T) { // eslint-disable-line @typescript-eslint/no-explicit-any
  type PersistedFunction = (...args: Parameters<T>) => ReturnType<T>;

  const fnRef = useRef<T>(fn);
  fnRef.current = fn;

  const persistFn = useRef<PersistedFunction>(
    ((...args: Parameters<T>) => fnRef.current(...args)) as PersistedFunction
  );

  return persistFn.current;
}
