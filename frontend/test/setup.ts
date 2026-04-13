/**
 * ProgressEvent polyfill for MSW XMLHttpRequest interception
 * MUST be defined before importing MSW to avoid reference errors
 */
class MockProgressEvent extends Event {
  readonly lengthComputable: boolean;
  readonly loaded: number;
  readonly total: number;

  constructor(type: string, eventInitDict?: EventInit & { lengthComputable?: boolean; loaded?: number; total?: number }) {
    super(type, eventInitDict);
    this.lengthComputable = (eventInitDict as any)?.lengthComputable ?? false;
    this.loaded = (eventInitDict as any)?.loaded ?? 0;
    this.total = (eventInitDict as any)?.total ?? 0;
  }
}

// @ts-ignore - ProgressEvent not in jsdom types
global.ProgressEvent = MockProgressEvent;

import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { vi, beforeAll, afterAll, afterEach } from "vitest";
import { server } from "./mocks/server";
import {
  clearActiveEventSources,
  getLastEventSource,
  installMockEventSource,
} from "./mocks/event-source-mock";

// Mock localStorage for API client tenant ID
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(window, 'localStorage', {
  writable: true,
  value: localStorageMock,
});

// Set base URL for jsdom to support relative API calls
Object.defineProperty(window, 'location', {
  configurable: true,
  writable: true,
  value: {
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000',
    protocol: 'http:',
    host: 'localhost:3000',
    hostname: 'localhost',
    port: '3000',
    pathname: '/',
    search: '',
    hash: '',
  },
});

// Start MSW server before all tests
beforeAll(() => {
  server.listen({
    onUnhandledRequest: (request) => {
      // Log unhandled requests for debugging
      console.warn(`Unhandled ${request.method} request to ${request.url}`);
    },
  });
});

// Reset handlers after each test for clean state
afterEach(() => {
  cleanup();
  server.resetHandlers();
  vi.restoreAllMocks();
  vi.clearAllMocks();
  vi.clearAllTimers();
  clearActiveEventSources();
});

// Close server after all tests
afterAll(() => {
  server.close();
});

// Mock matchMedia for responsive component tests
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}

Object.defineProperty(window, "IntersectionObserver", {
  writable: true,
  value: MockIntersectionObserver,
});

installMockEventSource(window);

export { getLastEventSource };

/** Mock ResizeObserver for responsive layout components */
class MockResizeObserver {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}

Object.defineProperty(window, "ResizeObserver", {
  writable: true,
  value: MockResizeObserver,
});

// Polyfill requestAnimationFrame for jsdom environment
global.requestAnimationFrame = (callback: FrameRequestCallback) => {
  return setTimeout(callback, 16) as unknown as number;
};

global.cancelAnimationFrame = (id: number) => {
  clearTimeout(id);
};

