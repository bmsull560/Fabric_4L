import { useRef } from "react";

/**
 * usePersistFn instead of useCallback to reduce cognitive load.
 *
 * Creates a stable function reference that persists across renders without
 * needing dependency arrays. The returned function always calls the latest
 * version of the provided function.
 *
 * TypeScript Note:
 * Uses `(...args: never[]) => unknown` constraint because:
 * 1. `never[]` makes the constraint contravariant (safer for function args)
 * 2. It allows any function signature to be passed through while maintaining
 *    full type safety for the returned function
 * 3. Alternative `unknown[]` would be more permissive but less type-safe
 *
 * @param fn - The function to persist across renders
 * @returns A stable function reference with the same signature
 */
export function usePersistFn<T extends (...args: never[]) => unknown>(fn: T) {
  type PersistedFunction = (...args: Parameters<T>) => ReturnType<T>;

  const fnRef = useRef<T>(fn);
  fnRef.current = fn;

  const persistFn = useRef<PersistedFunction>(
    ((...args: Parameters<T>) => fnRef.current(...args)) as PersistedFunction
  );

  return persistFn.current;
}
