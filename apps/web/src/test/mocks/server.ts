/**
 * MSW server setup for Node.js test environment.
 * Use this in test setup files to enable API mocking.
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Create the MSW server with all handlers
export const server = setupServer(...handlers);

// Helper to reset handlers after each test
export function resetHandlers() {
  server.resetHandlers();
}

// Helper to add temporary handlers for specific tests
export function addHandler(...newHandlers: Parameters<typeof server.use>) {
  server.use(...newHandlers);
}
