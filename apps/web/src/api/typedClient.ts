/**
 * Typed API client wrappers.
 *
 * These thin wrappers around {@link apiClient} remove the `unknown` default
 * generic, forcing every call site to declare the expected response type.
 * Over time hooks should migrate from `apiClient.*` to `apiGet` / `apiPost`
 * etc. so that response shapes are explicit and type-safe.
 */

import type { AxiosRequestConfig, AxiosResponse } from 'axios';
import { apiClient, type LayerKey } from './client';

export async function apiGet<TResponse>(
  layer: LayerKey,
  path: string,
  config?: AxiosRequestConfig
): Promise<AxiosResponse<TResponse>> {
  return apiClient.get<TResponse>(layer, path, config);
}

export async function apiPost<TResponse>(
  layer: LayerKey,
  path: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<AxiosResponse<TResponse>> {
  return apiClient.post<TResponse>(layer, path, data, config);
}

export async function apiPut<TResponse>(
  layer: LayerKey,
  path: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<AxiosResponse<TResponse>> {
  return apiClient.put<TResponse>(layer, path, data, config);
}

export async function apiPatch<TResponse>(
  layer: LayerKey,
  path: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<AxiosResponse<TResponse>> {
  return apiClient.patch<TResponse>(layer, path, data, config);
}

export async function apiDelete<TResponse>(
  layer: LayerKey,
  path: string,
  config?: AxiosRequestConfig
): Promise<AxiosResponse<TResponse>> {
  return apiClient.delete<TResponse>(layer, path, config);
}
