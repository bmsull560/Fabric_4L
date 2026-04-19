/**
 * AuthClient — Contract-based authentication service
 *
 * Centralizes all identity provider interactions with:
 * - Typed request/response contracts
 * - Deterministic error handling
 * - Zod schema validation
 *
 * Architecture: AuthContext → AuthClient → HTTP API → IdP
 */
import {
  type TokenResponse,
  type LoginInitiationResponse,
  type UserInfo,
  validateTokenResponse,
  validateLoginInitiationResponse,
  AuthError,
  AuthErrorCategory,
  UserInfoSchema,
} from '../schemas/auth';

// API configuration from environment
const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';
const L4_PREFIX = import.meta.env.VITE_L4_PREFIX || '/agents';

/**
 * AuthClient — Formal contract boundary for identity operations
 *
 * All methods return validated responses or throw categorized AuthErrors.
 * No raw fetch calls should exist outside this class.
 */
export class AuthClient {
  /**
   * Step 1: Initiate OIDC login flow
   *
   * Calls backend to get authorization URL from IdP.
   *
   * @param tenantSlug — tenant identifier for routing
   * @param redirectUri — OAuth2 callback URL (must match backend registration)
   * @returns LoginInitiationResponse with authorization_url and state
   * @throws AuthError (NETWORK, AUTHENTICATION, MALFORMED_RESPONSE)
   */
  async initiateLogin(
    tenantSlug: string,
    redirectUri: string
  ): Promise<LoginInitiationResponse> {
    const url = `${API_BASE}${L4_PREFIX}/auth/oidc/${tenantSlug}/login?redirect_uri=${encodeURIComponent(redirectUri)}`;

    let response: Response;
    try {
      response = await fetch(url);
    } catch (networkError) {
      throw new AuthError(
        'Failed to connect to authentication service',
        AuthErrorCategory.NETWORK
      );
    }

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: 'Authentication failed' }));
      throw new AuthError(
        errorData.detail || `Authentication error (${response.status})`,
        response.status === 401
          ? AuthErrorCategory.AUTHENTICATION
          : AuthErrorCategory.VALIDATION,
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
   * Step 2: Exchange OIDC authorization code for tokens
   *
   * Called on OAuth2 callback after IdP redirects back to application.
   *
   * @param code — authorization code from IdP callback
   * @param state — state parameter for CSRF protection
   * @returns TokenResponse with access_token and user info
   * @throws AuthError (NETWORK, AUTHENTICATION, MALFORMED_RESPONSE)
   */
  async exchangeCodeForTokens(
    code: string,
    state: string
  ): Promise<TokenResponse> {
    const url = `${API_BASE}${L4_PREFIX}/auth/oidc/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`;

    let response: Response;
    try {
      response = await fetch(url);
    } catch (networkError) {
      throw new AuthError(
        'Failed to connect to authentication service',
        AuthErrorCategory.NETWORK
      );
    }

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: 'Token exchange failed' }));
      throw new AuthError(
        errorData.detail || `Token exchange error (${response.status})`,
        response.status === 401
          ? AuthErrorCategory.AUTHENTICATION
          : AuthErrorCategory.VALIDATION,
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
   * Get current session from storage
   *
   * Validates stored token and user info against schemas.
   * Returns null if no valid session exists.
   *
   * @returns UserInfo if valid session, null otherwise
   */
  getCurrentSession(): UserInfo | null {
    const storedToken = localStorage.getItem('accessToken');
    const storedUser = localStorage.getItem('userInfo');

    if (!storedToken || !storedUser) {
      return null;
    }

    try {
      const parsedUser = JSON.parse(storedUser);
      const result = UserInfoSchema.safeParse(parsedUser);
      if (!result.success) {
        this.clearSession();
        return null;
      }
      return result.data;
    } catch {
      this.clearSession();
      return null;
    }
  }

  /**
   * Refresh token — placeholder for future refresh implementation
   *
   * Currently validates existing token structure and expiry.
   * In future, will implement proper refresh token flow.
   *
   * @returns true if token is valid, false if expired/invalid
   */
  async refreshToken(): Promise<boolean> {
    const token = localStorage.getItem('accessToken');
    if (!token) return false;

    // Validate JWT structure (header.payload.signature)
    const parts = token.split('.');
    if (parts.length !== 3) {
      this.clearSession();
      return false;
    }

    try {
      // base64url decode with proper padding
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padding = '='.repeat((4 - base64.length % 4) % 4);
      const payload = JSON.parse(atob(base64 + padding));

      const exp = payload.exp * 1000; // Convert to milliseconds
      const TOKEN_EXPIRY_BUFFER_MS = 60_000; // 1 minute buffer

      if (Date.now() >= exp - TOKEN_EXPIRY_BUFFER_MS) {
        this.clearSession();
        return false;
      }
      return true;
    } catch {
      this.clearSession();
      return false;
    }
  }

  /**
   * Persist session to storage
   *
   * @param token — access token
   * @param user — user info
   * @param tenantId — tenant identifier
   */
  persistSession(token: string, user: UserInfo, tenantId: string): void {
    localStorage.setItem('accessToken', token);
    localStorage.setItem('userInfo', JSON.stringify(user));
    localStorage.setItem('tenantId', tenantId);
  }

  /**
   * Clear all session storage
   */
  clearSession(): void {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userInfo');
    localStorage.removeItem('tenantId');
  }

  /**
   * Clear OIDC flow state from session storage
   */
  clearOidcState(): void {
    sessionStorage.removeItem('oidcState');
    sessionStorage.removeItem('oidcTenantSlug');
  }
}

// Singleton instance for application use
export const authClient = new AuthClient();
