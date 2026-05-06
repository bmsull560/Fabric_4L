/**
 * MSW Server Instance
 *
 * Creates a mock server for API testing using MSW (Mock Service Worker).
 * Used in test setup to intercept and mock HTTP requests.
 */
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Create the mock server with all handlers
export const server = setupServer(...handlers);
