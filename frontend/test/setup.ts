import "@testing-library/jest-dom";
import { vi, beforeAll, afterAll, afterEach } from "vitest";
import { server } from "./mocks/server";

// Set base URL for jsdom to support relative API calls
Object.defineProperty(window, 'location', {
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
  server.resetHandlers();
  vi.clearAllMocks();
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

// Mock EventSource for SSE testing
class MockEventSource {
  url: string;
  readyState: number = 0;
  CONNECTING = 0;
  OPEN = 1;
  CLOSED = 2;
  withCredentials = false;
  onopen: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  dispatchEvent = vi.fn();

  constructor(url: string | URL) {
    this.url = url.toString();
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = 1;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  close() {
    this.readyState = 2;
  }

  // Helper for tests to simulate incoming messages
  _emitMessage(data: unknown) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  _emitError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

Object.defineProperty(window, "EventSource", {
  writable: true,
  value: MockEventSource,
});

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

/**
 * ProgressEvent polyfill for MSW XMLHttpRequest interception
 * MSW's XMLHttpRequest interceptor requires ProgressEvent which is not available in jsdom
 */
class MockProgressEvent extends Event {
  readonly lengthComputable: boolean;
  readonly loaded: number;
  readonly total: number;

  constructor(type: string, eventInitDict?: { lengthComputable?: boolean; loaded?: number; total?: number }) {
    super(type, eventInitDict);
    this.lengthComputable = eventInitDict?.lengthComputable ?? false;
    this.loaded = eventInitDict?.loaded ?? 0;
    this.total = eventInitDict?.total ?? 0;
  }
}

// @ts-expect-error - ProgressEvent not in jsdom types
global.ProgressEvent = MockProgressEvent;

// Reset all mocks after each test to ensure isolation
afterEach(() => {
  vi.clearAllMocks();
});
