import { describe, it, expect, vi } from 'vitest';
import { SessionService, type StorageLike, type LocationLike } from './sessionService';
import type { UserInfo } from '../schemas/auth';

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeStorage(): StorageLike & { _store: Map<string, string> } {
  const _store = new Map<string, string>();
  return {
    _store,
    getItem: (key) => _store.get(key) ?? null,
    setItem: (key, value) => _store.set(key, value),
    removeItem: (key) => _store.delete(key),
  };
}

function makeLocation(pathname = '/'): LocationLike & { _href: string } {
  const loc: LocationLike & { _href: string } = {
    _href: '',
    href: '',
    origin: 'https://app.example.com',
    pathname,
    replace: vi.fn((url: string) => { loc.href = url; }),
  };
  return loc;
}

function makeUser(overrides: Partial<UserInfo> = {}): UserInfo {
  return {
    id: 'user-1',
    email: 'test@example.com',
    role: 'standard',
    tenantId: 'tenant-abc',
    tenantSlug: 'my-org',
    ...overrides,
  };
}

function makeService(pathname = '/dashboard') {
  const storage = makeStorage();
  const location = makeLocation(pathname);
  const service = new SessionService({ sessionStorage: storage, location });
  return { service, storage, location };
}

// ── Session Metadata ──────────────────────────────────────────────────────────

describe('SessionService — session metadata', () => {
  it('returns null when no session is stored', () => {
    const { service } = makeService();
    expect(service.getSessionMeta()).toBeNull();
  });

  it('persists and retrieves session metadata', () => {
    const { service } = makeService();
    const user = makeUser();
    const meta = service.persistSessionMeta(user, 'tenant-1');

    expect(meta.user).toEqual(user);
    expect(meta.tenantId).toBe('tenant-1');

    const retrieved = service.getSessionMeta();
    expect(retrieved).toEqual(meta);
  });

  it('returns null when sessionStorage is unavailable', () => {
    const service = new SessionService({ sessionStorage: null, location: null });
    expect(service.getSessionMeta()).toBeNull();
  });

  it('clearSession removes session metadata', () => {
    const { service } = makeService();
    service.persistSessionMeta(makeUser(), 'tenant-1');
    expect(service.getSessionMeta()).not.toBeNull();

    service.clearSession();
    expect(service.getSessionMeta()).toBeNull();
  });

  it('clearSession is a no-op when sessionStorage is unavailable', () => {
    const service = new SessionService({ sessionStorage: null, location: null });
    expect(() => service.clearSession()).not.toThrow();
  });

  it('clears and returns null for corrupt stored JSON', () => {
    const { service, storage } = makeService();
    // Inject invalid JSON directly
    storage.setItem('vf.auth.session.meta', '{invalid json}');
    expect(service.getSessionMeta()).toBeNull();
    // Should have been cleaned up
    expect(storage.getItem('vf.auth.session.meta')).toBeNull();
  });

  it('clears and returns null for JSON that fails schema validation', () => {
    const { service, storage } = makeService();
    storage.setItem('vf.auth.session.meta', JSON.stringify({ bad: 'data' }));
    expect(service.getSessionMeta()).toBeNull();
  });
});

// ── Derived getters ───────────────────────────────────────────────────────────

describe('SessionService — derived getters', () => {
  it('getCurrentUser returns the stored user', () => {
    const { service } = makeService();
    const user = makeUser();
    service.persistSessionMeta(user, 'tenant-1');
    expect(service.getCurrentUser()).toEqual(user);
  });

  it('getCurrentUser returns null when no session', () => {
    const { service } = makeService();
    expect(service.getCurrentUser()).toBeNull();
  });

  it('getTenantId returns stored tenant ID', () => {
    const { service } = makeService();
    service.persistSessionMeta(makeUser(), 'tenant-42');
    expect(service.getTenantId()).toBe('tenant-42');
  });

  it('getTenantId returns default when no session', () => {
    const { service } = makeService();
    expect(service.getTenantId()).toBe('default');
    expect(service.getTenantId('my-default')).toBe('my-default');
  });

  it('getAccessToken always returns null', () => {
    const { service } = makeService();
    service.persistSessionMeta(makeUser(), 'tenant-1');
    expect(service.getAccessToken()).toBeNull();
  });

  it('isSessionValid returns true when session exists', () => {
    const { service } = makeService();
    service.persistSessionMeta(makeUser(), 'tenant-1');
    expect(service.isSessionValid()).toBe(true);
  });

  it('isSessionValid returns false when no session', () => {
    const { service } = makeService();
    expect(service.isSessionValid()).toBe(false);
  });
});

// ── Compatibility shims ───────────────────────────────────────────────────────

describe('SessionService — legacy compatibility shims', () => {
  it('getSessionSnapshot returns snapshot with empty accessToken', () => {
    const { service } = makeService();
    const user = makeUser();
    service.persistSessionMeta(user, 'tenant-1');
    const snap = service.getSessionSnapshot();
    expect(snap?.accessToken).toBe('');
    expect(snap?.tenantId).toBe('tenant-1');
    expect(snap?.user).toEqual(user);
  });

  it('getSessionSnapshot returns null when no session', () => {
    const { service } = makeService();
    expect(service.getSessionSnapshot()).toBeNull();
  });

  it('persistSession ignores the accessToken parameter', () => {
    const { service } = makeService();
    const user = makeUser();
    const snap = service.persistSession('should-be-ignored', user, 'tenant-1');
    expect(snap.accessToken).toBe('');
    expect(snap.tenantId).toBe('tenant-1');
  });
});

// ── OIDC Flow State ───────────────────────────────────────────────────────────

describe('SessionService — OIDC flow state', () => {
  it('returns null when no OIDC state is stored', () => {
    const { service } = makeService();
    expect(service.getOidcFlowState()).toBeNull();
  });

  it('persists and retrieves OIDC flow state', () => {
    const { service } = makeService();
    const flowState = service.persistOidcFlowState({
      state: 'random-state-value',
      tenantSlug: 'my-org',
      postLoginRedirect: '/dashboard',
    });
    expect(flowState.state).toBe('random-state-value');
    expect(service.getOidcFlowState()).toEqual(flowState);
  });

  it('clearOidcState removes OIDC data', () => {
    const { service } = makeService();
    service.persistOidcFlowState({ state: 'abc', tenantSlug: 'org' });
    service.clearOidcState();
    expect(service.getOidcFlowState()).toBeNull();
  });

  it('clearOidcState is a no-op when sessionStorage is unavailable', () => {
    const service = new SessionService({ sessionStorage: null, location: null });
    expect(() => service.clearOidcState()).not.toThrow();
  });

  it('migrates legacy OIDC keys on first read', () => {
    const { service, storage } = makeService();
    storage.setItem('oidcState', 'legacy-state');
    storage.setItem('oidcTenantSlug', 'legacy-org');
    storage.setItem('postLoginRedirect', '/home');

    const result = service.getOidcFlowState();
    expect(result?.state).toBe('legacy-state');
    expect(result?.tenantSlug).toBe('legacy-org');
    expect(result?.postLoginRedirect).toBe('/home');

    // After migration, the unified key should be set
    expect(storage.getItem('vf.auth.oidc')).not.toBeNull();
  });

  it('returns null and clears when OIDC state JSON is invalid', () => {
    const { service, storage } = makeService();
    storage.setItem('vf.auth.oidc', '{invalid}');
    expect(service.getOidcFlowState()).toBeNull();
  });

  it('returns null when legacy state is present but tenantSlug is missing', () => {
    const { service, storage } = makeService();
    storage.setItem('oidcState', 'state-value');
    // No tenantSlug
    expect(service.getOidcFlowState()).toBeNull();
  });
});

// ── Post-Login Redirect ───────────────────────────────────────────────────────

describe('SessionService — post-login redirect', () => {
  it('consumePostLoginRedirect returns null when nothing stored', () => {
    const { service } = makeService();
    expect(service.consumePostLoginRedirect()).toBeNull();
  });

  it('consumePostLoginRedirect returns redirect from OIDC flow state', () => {
    const { service } = makeService();
    service.persistOidcFlowState({
      state: 'st',
      tenantSlug: 'org',
      postLoginRedirect: '/target',
    });
    const redirect = service.consumePostLoginRedirect();
    expect(redirect).toBe('/target');
    // After consuming, postLoginRedirect should be cleared
    const after = service.getOidcFlowState();
    expect(after?.postLoginRedirect).toBeUndefined();
  });

  it('setPostLoginRedirect updates existing OIDC flow state', () => {
    const { service } = makeService();
    service.persistOidcFlowState({ state: 'st', tenantSlug: 'org' });
    service.setPostLoginRedirect('/new-target');
    expect(service.getOidcFlowState()?.postLoginRedirect).toBe('/new-target');
  });

  it('setPostLoginRedirect writes to legacy key when no OIDC state', () => {
    const { service, storage } = makeService();
    service.setPostLoginRedirect('/fallback');
    expect(storage.getItem('postLoginRedirect')).toBe('/fallback');
  });

  it('setPostLoginRedirect with null removes the legacy key', () => {
    const { service, storage } = makeService();
    storage.setItem('postLoginRedirect', '/old');
    service.setPostLoginRedirect(null);
    expect(storage.getItem('postLoginRedirect')).toBeNull();
  });
});

// ── Navigation helpers ────────────────────────────────────────────────────────

describe('SessionService — navigation helpers', () => {
  it('getCallbackUrl returns origin + /login/callback', () => {
    const { service } = makeService();
    expect(service.getCallbackUrl()).toBe('https://app.example.com/login/callback');
  });

  it('getCallbackUrl includes /login/callback path', () => {
    // When location is null, the service falls back to window.location from jsdom
    const service = new SessionService({ sessionStorage: null, location: null });
    expect(service.getCallbackUrl()).toMatch(/\/login\/callback$/);
  });

  it('redirectTo sets location.href', () => {
    const { service, location } = makeService();
    service.redirectTo('https://example.com/page');
    expect(location.href).toBe('https://example.com/page');
  });

  it('redirectToLogin calls location.replace with /login', () => {
    const { service, location } = makeService('/dashboard');
    service.redirectToLogin();
    expect(location.replace).toHaveBeenCalledWith('/login');
  });

  it('redirectToLogin does nothing when already on /login', () => {
    const { service, location } = makeService('/login');
    service.redirectToLogin();
    expect(location.replace).not.toHaveBeenCalled();
  });

  it('handleUnauthorized clears session and redirects to login', () => {
    const { service, location } = makeService('/protected');
    service.persistSessionMeta(makeUser(), 'tenant-1');
    service.handleUnauthorized();
    expect(service.getSessionMeta()).toBeNull();
    expect(location.replace).toHaveBeenCalledWith('/login');
  });
});

// ── configure / resetEnvironment ──────────────────────────────────────────────

describe('SessionService — configure', () => {
  it('configure updates the sessionStorage', () => {
    const service = new SessionService({ sessionStorage: null, location: null });
    const storage = makeStorage();
    service.configure({ sessionStorage: storage });

    service.persistSessionMeta(makeUser(), 'tenant-1');
    expect(service.getSessionMeta()).not.toBeNull();
  });
});
