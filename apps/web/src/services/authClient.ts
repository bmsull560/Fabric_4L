/**
 * AuthClient — contract boundary for all identity operations
 *
 * Architecture: AuthContext → AuthClient → HTTP API → IdP
 *
 * Token delivery model:
 *   - The backend sets `vf_session` (httpOnly Secure SameSite=Strict) on the
 *     OIDC callback response. The frontend never reads or stores the token.
 *   - All API requests include the cookie automatically via `credentials: include`.
 *   - Refresh and logout are explicit backend calls that rotate / clear the cookie.
 */
import {
  type TokenResponse,
  type LoginInitiationResponse,
  type UserInfo,
  validateTokenResponse,
  validateLoginInitiationResponse,
  AuthError,
  AuthErrorCategory,
} from '../schemas/auth';
import { sessionService } from './sessionService';

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';
const L4_PREFIX = import.meta.env.VITE_L4_PREFIX || '/agents';
const CSRF_COOKIE_NAME = 'vf_csrf_token';

function readCookie(name: string): string | null {
  if (typeof document === 'undefined' || !document.cookie) {
    return null;
  }
  const encodedName = `${encodeURIComponent(name)}=`;
  const entry = document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(encodedName));
  return entry ? decodeURIComponent(entry.slice(encodedName.length)) : null;
}

function csrfHeaders(): Record<string, string> {
  const token = readCookie(CSRF_COOKIE_NAME);
  return token ? { 'X-CSRF-Token': token } : {};
}

export class AuthClient {
  /**
   * Step 1: Initiate OIDC login flow.
   * Returns the IdP authorization URL and state parameter.
   */
  async initiateLogin(
    tenantSlug: string,
    redirectUri: string
  ): Promise<LoginInitiationResponse> {
    const normalizedTenantSlug = tenantSlug.trim();
    const isSafeTenantSlug = /^[a-z0-9-]{1,64}$/i.test(normalizedTenantSlug);
    if (!isSafeTenantSlug) {
      throw new AuthError(
        'Tenant slug contains unsafe characters. Contact your administrator.',
        AuthErrorCategory.VALIDATION
      );
    }

    const url = `${API_BASE}${L4_PREFIX}/auth/oidc/${encodeURIComponent(normalizedTenantSlug)}/login?redirect_uri=${encodeURIComponent(redirectUri)}`;

    let response: Response;
    try {
      response = await fetch(url, { credentials: 'include' });
    } catch {
      throw new AuthError(
        'Failed to connect to authentication service',
        AuthErrorCategory.NETWORK
      );
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Authentication failed' }));
      throw new AuthError(
        errorData.detail || `Authentication error (${response.status})`,
        response.status === 401 ? AuthErrorCategory.AUTHENTICATION : AuthErrorCategory.VALIDATION,
        response.status
      );
    }

    const data = await response.json().catch(() => {
      throw new AuthError(
        'Invalid response from authentication service',
        AuthErrorCategory.MALFORMED_RESPONSE
      );
    });

    return validateLoginInitiationResponse(data);
  }

  /**
   * Step 2: Exchange OIDC authorization code for tokens.
   *
   * The backend sets the `vf_session` httpOnly cookie and returns only
   * non-secret user metadata in the JSON body. The frontend stores that
   * metadata in sessionStorage for UI rendering.
   */
  async exchangeCodeForTokens(
    code: string,
    state: string
  ): Promise<TokenResponse> {
    const url = `${API_BASE}${L4_PREFIX}/auth/oidc/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`;

    let response: Response;
    try {
      response = await fetch(url, { credentials: 'include' });
    } catch {
      throw new AuthError(
        'Failed to connect to authentication service',
        AuthErrorCategory.NETWORK
      );
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Token exchange failed' }));
      throw new AuthError(
        errorData.detail || `Token exchange error (${response.status})`,
        response.status === 401 ? AuthErrorCategory.AUTHENTICATION : AuthErrorCategory.VALIDATION,
        response.status
      );
    }

    const data = await response.json().catch(() => {
      throw new AuthError(
        'Invalid response from authentication service',
        AuthErrorCategory.MALFORMED_RESPONSE
      );
    });

    return validateTokenResponse(data);
  }

  /**
   * Refresh the session cookie.
   *
   * Calls POST /auth/refresh. The backend rotates the `vf_session` cookie
   * and returns updated user metadata. Returns false if the session has
   * expired (401) or the backend is unreachable.
   */
  async refreshToken(): Promise<boolean> {
    const url = `${API_BASE}${L4_PREFIX}/auth/oidc/refresh`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', ...csrfHeaders() },
      });
    } catch {
      // Network error — keep existing metadata, let next API call surface 401
      return !!sessionService.getSessionMeta();
    }

    if (response.status === 401 || response.status === 403) {
      sessionService.clearSession();
      return false;
    }

    if (!response.ok) {
      // Non-auth error (5xx) — don't clear session, retry later
      return !!sessionService.getSessionMeta();
    }

    // A 200 with an unparseable or missing body is treated as malformed — we
    // cannot safely update session metadata without a valid token response, and
    // silently returning true would leave the user with stale role/email data.
    const data = await response.json().catch(() => null);
    if (!data) {
      throw new AuthError(
        'Invalid response from authentication service',
        AuthErrorCategory.MALFORMED_RESPONSE
      );
    }

    const result = validateTokenResponse(data);
    // Tenant is stable across refreshes — read from existing metadata rather
    // than deriving it from the response (which carries no tenant field).
    // If existing metadata is absent the session is already invalid; the
    // backend will return 401 on the next API call, so we return false here
    // rather than persisting a broken tenant context.
    const existingMeta = sessionService.getSessionMeta();
    if (!existingMeta?.tenantId) {
      sessionService.clearSession();
      return false;
    }
    const tenantId = existingMeta.tenantId;
    const user: UserInfo = {
      id: result.user_id,
      email: result.email,
      role: result.role,
      tenantId,
      tenantSlug: tenantId,
    };
    sessionService.persistSessionMeta(user, tenantId);

    return true;
  }

  /**
   * Logout: clear the server-side session cookie.
   *
   * Calls POST /auth/logout which clears the `vf_session` cookie via
   * Set-Cookie with Max-Age=0. Local metadata is cleared regardless of
   * whether the network call succeeds.
   */
  async logout(): Promise<void> {
    sessionService.clearSession();
    sessionService.clearOidcState();

    try {
      await fetch(`${API_BASE}${L4_PREFIX}/auth/oidc/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: csrfHeaders(),
      });
    } catch {
      // Best-effort — local state is already cleared
    }
  }

  getCurrentSession(): UserInfo | null {
    return sessionService.getCurrentUser();
  }

  clearSession(): void {
    sessionService.clearSession();
  }

  clearOidcState(): void {
    sessionService.clearOidcState();
  }
}

export const authClient = new AuthClient();
