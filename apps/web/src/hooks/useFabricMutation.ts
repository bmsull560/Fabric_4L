/**
 * useFabricMutation — Tier 2 Domain Mutation Hook Wrapper
 *
 * Contract: Hook Architecture Contract §2.2
 * Enforces standardized error wrapping, cache invalidation, and retry policy
 * for all domain-level create/update/delete mutations.
 *
 * All new domain hooks MUST use this instead of raw `useMutation`.
 */
import { useMutation, useQueryClient, type UseMutationOptions } from '@tanstack/react-query';
import { withApiError, BaseApiError, type ApiErrorClass } from './useApiShared';

export interface FabricMutationOptions<TData, TError extends BaseApiError, TVariables>
  extends Omit<UseMutationOptions<TData, TError, TVariables>, 'mutationFn'> {
  /** Async mutation function */
  mutationFn: (variables: TVariables) => Promise<TData>;
  /** Domain-specific error class extending BaseApiError */
  errorClass: ApiErrorClass;
  /** Query keys to invalidate on success (e.g., [QK.products.all]) */
  invalidateKeys?: readonly (readonly unknown[])[];
}

/**
 * Standardized mutation hook wrapper with automatic cache invalidation.
 *
 * @example
 * ```ts
 * export function useCreateProduct() {
 *   return useFabricMutation({
 *     mutationFn: createProduct,
 *     errorClass: BaseApiError,
 *     invalidateKeys: [QK.products.all],
 *   });
 * }
 * ```
 */
export function useFabricMutation<TData, TError extends BaseApiError, TVariables = void>(
  options: FabricMutationOptions<TData, TError, TVariables>
) {
  const { mutationFn, errorClass, invalidateKeys, ...rest } = options;
  const queryClient = useQueryClient();

  return useMutation<TData, TError, TVariables>({
    ...rest,
    mutationFn: (variables) => withApiError(mutationFn(variables), errorClass),
    onSuccess: (data, variables, context) => {
      if (invalidateKeys && invalidateKeys.length > 0) {
        invalidateKeys.forEach((key) => {
          queryClient.invalidateQueries({ queryKey: [...key] });
        });
      }
      // Chain to any user-provided onSuccess
      rest.onSuccess?.(data, variables, context);
    },
  });
}
