import { z } from 'zod';
import { createFeatureLogger } from '@/lib/telemetry';
import { type UserInfo, UserInfoSchema } from '../schemas/auth';

const log = createFeatureLogger('auth-session');

const SESSION_STORAGE_KEY = 'vf.auth.session';
const OIDC_STORAGE_KEY = 'vf.auth.oidc';
const LEGACY_ACCESS_TOKEN_KEY = 'accessToken';
const LEGACY_USER_INFO_KEY = 'userInfo';
const LEGACY_TENANT_ID_KEY = 'tenantId';
const LEGACY_OIDC_STATE_KEY = 'oidcState';
const LEGACY_OIDC_TENANT_KEY = 'oidcTenantSlug';
const LEGACY_POST_LOGIN_REDIRECT_KEY = 'postLoginRedirect';
const TOKEN_EXPIRY_BUFFER_MS = 60_000;

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export interface LocationLike {
  href: string;
  origin: string;
  pathname: string;
  replace(url: string): void;
}

export interface SessionServiceEnvironment {
  localStorage: StorageLike | null;
  sessionStorage: StorageLike | null;
  location: LocationLike | null;
}

const SessionSnapshotSchema = z.object({
  accessToken: z.string().min(1, 'Access token is required'),
  tenantId: z.string().min(1, 'Tenant ID is required'),
  user: UserInfoSchema,
});

const OidcFlowStateSchema = z.object({
  state: z.string().min(1, 'State is required'),
  tenantSlug: z.string().min(1, 'Tenant slug is required'),
  postLoginRedirect: z.string().min(1).optional(),
});

export type SessionSnapshot = z.infer<typeof SessionSnapshotSchema>;
export type OidcFlowState = z.infer<typeof OidcFlowStateSchema>;

function getWindowStorage(kind: 'localStorage' | 'sessionStorage'): StorageLike | null {
  if (typeof window === 'undefined') {
    return null;
  }

  return window[kind];
}

function getWindowLocation(): LocationLike | null {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.location;
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const parts = token.split('.');
  if (parts.length !== 3) {
    return null;
  }

  try {
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padding = '='.repeat((4 - base64.length % 4) % 4);
    return JSON.parse(atob(base64 + padding)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export class SessionService {
  private environment: SessionServiceEnvironment;

  constructor(environment: Partial<SessionServiceEnvironment> = {}) {
    this.environment = {
      localStorage: environment.localStorage ?? getWindowStorage('localStorage'),
      sessionStorage: environment.sessionStorage ?? getWindowStorage('sessionStorage'),
      location: environment.location ?? getWindowLocation(),
    };
  }

  configure(environment: Partial<SessionServiceEnvironment>): void {
    this.environment = {
      localStorage: environment.localStorage ?? this.environment.localStorage,
      sessionStorage: environment.sessionStorage ?? this.environment.sessionStorage,
      location: environment.location ?? this.environment.location,
    };
  }

  resetEnvironment(): void {
    this.environment = {
      localStorage: getWindowStorage('localStorage'),
      sessionStorage: getWindowStorage('sessionStorage'),
      location: getWindowLocation(),
    };
  }

  getSessionSnapshot(): SessionSnapshot | null {
    const localStorage = this.environment.localStorage;
    if (!localStorage) {
      return null;
    }

    const storedSnapshot = localStorage.getItem(SESSION_STORAGE_KEY);
    if (storedSnapshot) {
      const parsed = this.safeParseSnapshot(storedSnapshot);
      if (parsed) {
        this.mirrorLegacySessionKeys(parsed);
        return parsed;
      }
      this.clearSession();
      return null;
    }

    const accessToken = localStorage.getItem(LEGACY_ACCESS_TOKEN_KEY);
    const storedUser = localStorage.getItem(LEGACY_USER_INFO_KEY);
    const tenantId = localStorage.getItem(LEGACY_TENANT_ID_KEY);
    if (!accessToken && !storedUser && !tenantId) {
      return null;
    }

    if (!accessToken || !storedUser || !tenantId) {
      this.clearSession();
      return null;
    }

    const parsed = this.safeParseSnapshot(
      JSON.stringify({
        accessToken,
        tenantId,
        user: this.safeParseJson(storedUser),
      })
    );

    if (!parsed) {
      this.clearSession();
      return null;
    }

    this.persistSession(parsed.accessToken, parsed.user, parsed.tenantId);
    return parsed;
  }

  getCurrentUser(): UserInfo | null {
    return this.getSessionSnapshot()?.user ?? null;
  }

  getAccessToken(): string | null {
    return this.getSessionSnapshot()?.accessToken ?? null;
  }

  getTenantId(defaultTenantId = 'default'): string {
    return this.getSessionSnapshot()?.tenantId ?? defaultTenantId;
  }

  isSessionValid(snapshot: SessionSnapshot | null = this.getSessionSnapshot()): boolean {
    if (!snapshot) {
      return false;
    }

    const payload = decodeJwtPayload(snapshot.accessToken);
    const exp = typeof payload?.exp === 'number' ? payload.exp * 1000 : null;
    if (exp === null || Date.now() >= exp - TOKEN_EXPIRY_BUFFER_MS) {
      this.clearSession();
      return false;
    }

    return true;
  }

  persistSession(accessToken: string, user: UserInfo, tenantId: string): SessionSnapshot {
    const localStorage = this.environment.localStorage;
    const snapshot = SessionSnapshotSchema.parse({ accessToken, tenantId, user });

    if (!localStorage) {
      return snapshot;
    }

    const serialized = JSON.stringify(snapshot);
    localStorage.setItem(SESSION_STORAGE_KEY, serialized);
    this.mirrorLegacySessionKeys(snapshot);

    return snapshot;
  }

  clearSession(): void {
    const localStorage = this.environment.localStorage;
    if (!localStorage) {
      return;
    }

    localStorage.removeItem(SESSION_STORAGE_KEY);
    localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
    localStorage.removeItem(LEGACY_USER_INFO_KEY);
    localStorage.removeItem(LEGACY_TENANT_ID_KEY);
  }

  persistOidcFlowState(flowState: OidcFlowState): OidcFlowState {
    const sessionStorage = this.environment.sessionStorage;
    const parsed = OidcFlowStateSchema.parse(flowState);

    if (!sessionStorage) {
      return parsed;
    }

    sessionStorage.setItem(OIDC_STORAGE_KEY, JSON.stringify(parsed));
    sessionStorage.setItem(LEGACY_OIDC_STATE_KEY, parsed.state);
    sessionStorage.setItem(LEGACY_OIDC_TENANT_KEY, parsed.tenantSlug);
    if (parsed.postLoginRedirect) {
      sessionStorage.setItem(LEGACY_POST_LOGIN_REDIRECT_KEY, parsed.postLoginRedirect);
    } else {
      sessionStorage.removeItem(LEGACY_POST_LOGIN_REDIRECT_KEY);
    }

    return parsed;
  }

  getOidcFlowState(): OidcFlowState | null {
    const sessionStorage = this.environment.sessionStorage;
    if (!sessionStorage) {
      return null;
    }

    const storedFlow = sessionStorage.getItem(OIDC_STORAGE_KEY);
    if (storedFlow) {
      const parsed = this.safeParseOidcFlow(storedFlow);
      if (parsed) {
        return parsed;
      }
      this.clearOidcState();
      return null;
    }

    const state = sessionStorage.getItem(LEGACY_OIDC_STATE_KEY);
    const tenantSlug = sessionStorage.getItem(LEGACY_OIDC_TENANT_KEY);
    const postLoginRedirect = sessionStorage.getItem(LEGACY_POST_LOGIN_REDIRECT_KEY) ?? undefined;

    if (!state && !tenantSlug && !postLoginRedirect) {
      return null;
    }

    if (!state || !tenantSlug) {
      this.clearOidcState();
      return null;
    }

    return this.persistOidcFlowState({
      state,
      tenantSlug,
      postLoginRedirect,
    });
  }

  setPostLoginRedirect(redirect: string | null): void {
    const currentState = this.getOidcFlowState();

    if (currentState) {
      this.persistOidcFlowState({
        ...currentState,
        postLoginRedirect: redirect ?? undefined,
      });
      return;
    }

    const sessionStorage = this.environment.sessionStorage;
    if (!sessionStorage) {
      return;
    }

    if (redirect) {
      sessionStorage.setItem(LEGACY_POST_LOGIN_REDIRECT_KEY, redirect);
    } else {
      sessionStorage.removeItem(LEGACY_POST_LOGIN_REDIRECT_KEY);
    }
  }

  consumePostLoginRedirect(): string | null {
    const currentState = this.getOidcFlowState();
    const redirect = currentState?.postLoginRedirect ?? this.environment.sessionStorage?.getItem(LEGACY_POST_LOGIN_REDIRECT_KEY) ?? null;

    if (currentState) {
      this.persistOidcFlowState({
        state: currentState.state,
        tenantSlug: currentState.tenantSlug,
      });
    } else {
      this.environment.sessionStorage?.removeItem(LEGACY_POST_LOGIN_REDIRECT_KEY);
    }

    return redirect;
  }

  clearOidcState(): void {
    const sessionStorage = this.environment.sessionStorage;
    if (!sessionStorage) {
      return;
    }

    sessionStorage.removeItem(OIDC_STORAGE_KEY);
    sessionStorage.removeItem(LEGACY_OIDC_STATE_KEY);
    sessionStorage.removeItem(LEGACY_OIDC_TENANT_KEY);
    sessionStorage.removeItem(LEGACY_POST_LOGIN_REDIRECT_KEY);
  }

  getCallbackUrl(): string {
    return `${this.environment.location?.origin ?? ''}/login/callback`;
  }

  redirectTo(url: string): void {
    const location = this.environment.location;
    if (!location) {
      return;
    }

    location.href = url;
  }

  redirectToLogin(): void {
    const location = this.environment.location;
    if (!location || location.pathname === '/login') {
      return;
    }

    location.replace('/login'); // navigation-guardrail: ignore - service boundary auth redirect
  }

  handleUnauthorized(context: { traceId?: string | null; route?: string } = {}): void {
    const snapshot = this.getSessionSnapshot();

    log.warn('Unauthorized response received; clearing session', {
      route: context.route ?? this.environment.location?.pathname,
      tenantId: snapshot?.tenantId ?? null,
      userId: snapshot?.user.id ?? null,
      authPhase: 'unauthorized-response',
      traceId: context.traceId ?? null,
    });

    this.clearSession();
    this.redirectToLogin();
  }

  private safeParseSnapshot(rawValue: string): SessionSnapshot | null {
    try {
      const parsed = SessionSnapshotSchema.safeParse(JSON.parse(rawValue));
      return parsed.success ? parsed.data : null;
    } catch {
      return null;
    }
  }

  private safeParseOidcFlow(rawValue: string): OidcFlowState | null {
    try {
      const parsed = OidcFlowStateSchema.safeParse(JSON.parse(rawValue));
      return parsed.success ? parsed.data : null;
    } catch {
      return null;
    }
  }

  private safeParseJson(rawValue: string): unknown {
    try {
      return JSON.parse(rawValue);
    } catch {
      return null;
    }
  }

  private mirrorLegacySessionKeys(snapshot: SessionSnapshot): void {
    const localStorage = this.environment.localStorage;
    if (!localStorage) {
      return;
    }

    localStorage.setItem(LEGACY_ACCESS_TOKEN_KEY, snapshot.accessToken);
    localStorage.setItem(LEGACY_USER_INFO_KEY, JSON.stringify(snapshot.user));
    localStorage.setItem(LEGACY_TENANT_ID_KEY, snapshot.tenantId);
  }
}

export const sessionService = new SessionService();
