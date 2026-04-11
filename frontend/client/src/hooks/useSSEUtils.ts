/**
 * Shared utilities for Server-Sent Events (SSE) URL construction
 *
 * Provides consistent URL building for SSE connections across hooks,
 * ensuring environment variables are handled uniformly.
 */

/**
 * Build SSE URL with consistent environment variable handling
 */
function buildSSEUrl(
  prefix: string,
  endpointPath: string
): string {
  const baseUrl = import.meta.env.VITE_API_BASE || '/api/v1';
  return `${baseUrl}${prefix}${endpointPath}`;
}

/**
 * Pre-configured builders for each service layer
 * Uses explicit env var access for Vite compatibility
 */
export const SSEBuilders = {
  l2: (endpointPath: string) =>
    buildSSEUrl(import.meta.env.VITE_L2_PREFIX || '/extract', endpointPath),
  l3: (endpointPath: string) =>
    buildSSEUrl(import.meta.env.VITE_L3_PREFIX || '/v1', endpointPath),
  l4: (endpointPath: string) =>
    buildSSEUrl(import.meta.env.VITE_L4_PREFIX || '/agents', endpointPath),
};

/**
 * Default SSE connection timeout
 */
export const SSE_TIMEOUT_MS = 30 * 1000;

/**
 * Check if EventSource is supported in current environment
 */
export function isSSESupported(): boolean {
  return typeof EventSource !== 'undefined';
}
