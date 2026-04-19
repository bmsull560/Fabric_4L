/**
 * MSW browser setup for development/staging environments.
 * Enable this in main.tsx to intercept API calls in the browser.
 */

import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

// Create the MSW worker with all handlers
export const worker = setupWorker(...handlers);
