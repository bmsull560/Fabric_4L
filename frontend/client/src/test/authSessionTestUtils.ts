import { sessionService, type LocationLike, type SessionSnapshot, type StorageLike, type OidcFlowState } from '@/services/sessionService';
import type { UserInfo } from '@/schemas/auth';

export class MemoryStorage implements StorageLike {
  private store = new Map<string, string>();

  getItem(key: string): string | null {
    return this.store.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.store.set(key, value);
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }

  clear(): void {
    this.store.clear();
  }
}

export interface MutableLocationLike extends LocationLike {
  href: string;
  pathname: string;
}

export function createLocationMock(
  initialUrl = 'http://localhost:3000/'
): MutableLocationLike {
  const parsed = new URL(initialUrl);

  return {
    href: parsed.toString(),
    origin: parsed.origin,
    pathname: parsed.pathname,
    replace(url: string) {
      const nextUrl = new URL(url, this.origin);
      this.href = nextUrl.toString();
      this.pathname = nextUrl.pathname;
    },
  };
}

export function applySessionServiceTestEnvironment(options: {
  localStorage?: MemoryStorage;
  sessionStorage?: MemoryStorage;
  location?: MutableLocationLike;
} = {}) {
  const localStorage = options.localStorage ?? new MemoryStorage();
  const sessionStorage = options.sessionStorage ?? new MemoryStorage();
  const location = options.location ?? createLocationMock();

  sessionService.configure({
    localStorage,
    sessionStorage,
    location,
  });

  return {
    localStorage,
    sessionStorage,
    location,
    reset() {
      localStorage.clear();
      sessionStorage.clear();
      location.href = 'http://localhost:3000/';
      location.pathname = '/';
      sessionService.configure({ localStorage, sessionStorage, location });
    },
  };
}

const baseUser: UserInfo = {
  id: 'user-123',
  email: 'user@example.com',
  role: 'tenant_admin',
  tenantId: 'tenant-123',
  tenantSlug: 'tenant-123',
};

function createToken(expOffsetSeconds: number): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + expOffsetSeconds }));
  return `${header}.${payload}.signature`;
}

export const authFixtures = {
  user(overrides: Partial<UserInfo> = {}): UserInfo {
    return { ...baseUser, ...overrides };
  },
  validSession(overrides: Partial<SessionSnapshot> = {}): SessionSnapshot {
    const user = overrides.user ?? baseUser;
    return {
      accessToken: overrides.accessToken ?? createToken(3600),
      tenantId: overrides.tenantId ?? user.tenantId,
      user,
    };
  },
  expiredSession(overrides: Partial<SessionSnapshot> = {}): SessionSnapshot {
    const user = overrides.user ?? baseUser;
    return {
      accessToken: overrides.accessToken ?? createToken(-60),
      tenantId: overrides.tenantId ?? user.tenantId,
      user,
    };
  },
  malformedUserPayload(): string {
    return 'invalid-json{';
  },
  oidcFlow(overrides: Partial<OidcFlowState> = {}): OidcFlowState {
    return {
      state: overrides.state ?? 'oidc-state-123',
      tenantSlug: overrides.tenantSlug ?? 'test-tenant',
      postLoginRedirect: overrides.postLoginRedirect,
    };
  },
};
