/**
 * Authentication Configuration
 *
 * Shared configuration for OIDC SSO providers.
 * Used by Login, Signup, and other auth-related components.
 */

/**
 * Maps SSO provider key to OIDC tenant slug.
 * This mapping allows the frontend to resolve which OIDC tenant
 * configuration to use for each SSO provider button.
 *
 * In production, this could be fetched from a config endpoint or
 * derived from the user's email domain.
 */
export const SSO_PROVIDER_TENANT: Record<string, string> = {
  google: import.meta.env.VITE_OIDC_TENANT_GOOGLE || 'google',
  microsoft: import.meta.env.VITE_OIDC_TENANT_MICROSOFT || 'microsoft',
};

/**
 * Supported SSO provider keys
 */
export type SSOProvider = 'google' | 'microsoft';

/**
 * Validate if a provider key is supported
 */
export function isValidSSOProvider(provider: string): provider is SSOProvider {
  return provider in SSO_PROVIDER_TENANT;
}

/**
 * Get tenant slug for a provider, returns null if invalid
 */
export function getSSOTenantSlug(provider: string): string | null {
  return SSO_PROVIDER_TENANT[provider] || null;
}
