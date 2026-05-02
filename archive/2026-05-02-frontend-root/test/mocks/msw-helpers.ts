/**
 * MSW Test Helpers
 *
 * Simplified primitives for common MSW mock patterns.
 * Extracted from repeated patterns in hook tests.
 *
 * Usage:
 * ```ts
 * import { mockEndpoint, mockErrorResponse, mockDelayedResponse } from './msw-helpers';
 *
 * // Simple success mock
 * server.use(mockEndpoint('get', '/api/settings', { data: 'value' }));
 *
 * // Error mock
 * server.use(mockErrorResponse('post', '/api/settings', 403, 'Permission denied'));
 *
 * // Delayed response
 * server.use(mockDelayedResponse('get', '/api/data', 200, { data: 'value' }));
 * ```
 */
import { http, HttpResponse, type HttpHandler } from 'msw';

type HttpMethod = 'get' | 'post' | 'put' | 'patch' | 'delete';

/**
 * Mock a simple endpoint with JSON response
 *
 * @param method - HTTP method ('get', 'post', 'patch', etc.)
 * @param path - URL path to match (e.g., '/api/v1/settings')
 * @param response - Response body object
 * @param status - HTTP status code (default: 200)
 * @returns MSW handler for server.use()
 *
 * @example
 * server.use(mockEndpoint('get', '/api/settings', { enabled: true }));
 * server.use(mockEndpoint('post', '/api/items', { id: 1 }, 201));
 */
export function mockEndpoint<T>(
  method: HttpMethod,
  path: string,
  response: T,
  status = 200
): HttpHandler {
  const handler = http[method];
  return handler(path, () => {
    return HttpResponse.json(response, { status });
  });
}

/**
 * Mock an endpoint with artificial delay
 *
 * @param method - HTTP method
 * @param path - URL path to match
 * @param delayMs - Delay in milliseconds
 * @param response - Response body object
 * @param status - HTTP status code (default: 200)
 * @returns MSW handler for server.use()
 *
 * @example
 * server.use(mockDelayedResponse('get', '/api/data', 500, { data: 'value' }));
 */
export function mockDelayedResponse<T>(
  method: HttpMethod,
  path: string,
  delayMs: number,
  response: T,
  status = 200
): HttpHandler {
  const handler = http[method];
  return handler(path, async () => {
    await new Promise(resolve => setTimeout(resolve, delayMs));
    return HttpResponse.json(response, { status });
  });
}

/**
 * Mock an error response
 *
 * @param method - HTTP method
 * @param path - URL path to match
 * @param status - HTTP error status code (e.g., 404, 500)
 * @param message - Error message
 * @returns MSW handler for server.use()
 *
 * @example
 * server.use(mockErrorResponse('get', '/api/missing', 404, 'Not found'));
 * server.use(mockErrorResponse('post', '/api/data', 403, 'Permission denied'));
 */
export function mockErrorResponse(
  method: HttpMethod,
  path: string,
  status: number,
  message: string
): HttpHandler {
  const handler = http[method];
  return handler(path, () => {
    return HttpResponse.json({ error: message }, { status });
  });
}

/**
 * Mock a network-level error (connection failure, timeout, etc.)
 *
 * @param method - HTTP method
 * @param path - URL path to match
 * @returns MSW handler for server.use()
 *
 * @example
 * server.use(mockNetworkError('get', '/api/data'));
 */
export function mockNetworkError(method: HttpMethod, path: string): HttpHandler {
  const handler = http[method];
  return handler(path, () => {
    return HttpResponse.error();
  });
}

/**
 * Create a mock endpoint with request tracking
 *
 * Useful for tests that need to verify request count, order, or payload.
 *
 * @param method - HTTP method
 * @param path - URL path to match
 * @param response - Response body or function that receives call count
 * @returns Object with handler and call tracking
 *
 * @example
 * const { handler, getCallCount } = mockWithTracking('get', '/api/data', (count) => ({
 *   version: count
 * }));
 * server.use(handler);
 * expect(getCallCount()).toBe(2);
 */
export function mockWithTracking<T>(
  method: HttpMethod,
  path: string,
  response: T | ((callCount: number) => T),
  status = 200
): {
  handler: HttpHandler;
  getCallCount: () => number;
  reset: () => void;
} {
  let callCount = 0;
  const handler = http[method](path, () => {
    callCount++;
    const responseBody = typeof response === 'function'
      ? (response as (count: number) => T)(callCount)
      : response;
    return HttpResponse.json(responseBody, { status });
  });

  return {
    handler,
    getCallCount: () => callCount,
    reset: () => { callCount = 0; },
  };
}

/**
 * Mock an endpoint that conditionally succeeds or fails
 *
 * @param method - HTTP method
 * @param path - URL path to match
 * @param successResponse - Response when condition passes
 * @param failureResponse - Response when condition fails
 * @param condition - Function that returns true for success
 * @returns MSW handler for server.use()
 *
 * @example
 * let shouldFail = true;
 * server.use(mockConditional('post', '/api/data', { ok: true }, { error: 'fail' }, () => !shouldFail));
 */
export function mockConditional<T, E>(
  method: HttpMethod,
  path: string,
  successResponse: T,
  failureResponse: E,
  condition: () => boolean,
  successStatus = 200,
  failureStatus = 500
): HttpHandler {
  const handler = http[method];
  return handler(path, () => {
    if (condition()) {
      return HttpResponse.json(successResponse, { status: successStatus });
    }
    return HttpResponse.json(failureResponse, { status: failureStatus });
  });
}
