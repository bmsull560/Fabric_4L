/**
 * Mock EventSource for SSE Testing
 *
 * Simulates Server-Sent Events (EventSource) in tests without actual HTTP connections.
 * Allows tests to programmatically emit events to drive hook state machines.
 */

export type EventSourceEvent = {
  type: string;
  data: unknown;
};

export type EventSourceConfig = {
  url: string;
  withCredentials?: boolean;
};

export class MockEventSource {
  url: string;
  withCredentials: boolean;
  readyState: number = 0; // 0=CONNECTING, 1=OPEN, 2=CLOSED

  // Event handlers
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  // Private event listeners storage
  private listeners: Map<string, Array<(event: Event) => void>> = new Map();

  constructor(url: string, eventSourceInitDict?: EventSourceInit) {
    this.url = url;
    this.withCredentials = eventSourceInitDict?.withCredentials ?? false;

    // Simulate connection opening after a brief delay
    setTimeout(() => {
      this.readyState = 1; // OPEN
      this.dispatchEvent(new Event('open'));
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  addEventListener(type: string, listener: (event: Event) => void): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type)?.push(listener);
  }

  removeEventListener(type: string, listener: (event: Event) => void): void {
    const typeListeners = this.listeners.get(type);
    if (typeListeners) {
      const index = typeListeners.indexOf(listener);
      if (index > -1) {
        typeListeners.splice(index, 1);
      }
    }
  }

  dispatchEvent(event: Event): boolean {
    const typeListeners = this.listeners.get(event.type);
    if (typeListeners) {
      typeListeners.forEach(listener => listener(event));
    }
    return true;
  }

  close(): void {
    this.readyState = 2; // CLOSED
  }

  // Test helper: Simulate receiving a message
  simulateMessage(data: unknown): void {
    const event = new MessageEvent('message', {
      data: JSON.stringify(data),
      origin: this.url,
    });

    this.dispatchEvent(event);
    if (this.onmessage) {
      this.onmessage(event);
    }
  }

  // Test helper: Simulate an error
  simulateError(): void {
    const event = new Event('error');
    this.dispatchEvent(event);
    if (this.onerror) {
      this.onerror(event);
    }
  }

  // Test helper: Simulate job progress update
  simulateProgress(progress: number, status: string = 'running'): void {
    this.simulateMessage({
      type: 'progress',
      data: progress,
      status,
      timestamp: new Date().toISOString(),
    });
  }

  // Test helper: Simulate job completion
  simulateCompletion(): void {
    this.simulateMessage({
      type: 'complete',
      data: 100,
      status: 'completed',
      timestamp: new Date().toISOString(),
    });
  }

  // Test helper: Simulate job failure
  simulateFailure(error: string = 'Job failed'): void {
    this.simulateMessage({
      type: 'error',
      error,
      status: 'failed',
      timestamp: new Date().toISOString(),
    });
  }

  // Test helper: Simulate log entry
  simulateLog(level: string, message: string): void {
    this.simulateMessage({
      type: 'log',
      data: {
        timestamp: new Date().toISOString(),
        level,
        message,
        status: level === 'ERROR' ? 'ERROR' : 'OK',
      },
    });
  }

  // Test helper: Simulate entity extraction
  simulateEntity(type: string, name: string): void {
    this.simulateMessage({
      type: 'entity',
      data: { type, name },
    });
  }
}

// Store active mock instances for test access
export const activeEventSources: MockEventSource[] = [];

// Factory function that tracks instances
export function createMockEventSource(
  url: string,
  eventSourceInitDict?: EventSourceInit
): MockEventSource {
  const instance = new MockEventSource(url, eventSourceInitDict);
  activeEventSources.push(instance);
  return instance;
}

// Clear all active instances (call in afterEach)
export function clearActiveEventSources(): void {
  activeEventSources.forEach(es => es.close());
  activeEventSources.length = 0;
}

// Get the most recent EventSource instance (useful for emitting events)
export function getLastEventSource(): MockEventSource | undefined {
  return activeEventSources[activeEventSources.length - 1];
}
