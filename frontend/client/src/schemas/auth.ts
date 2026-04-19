/**
 * Auth Schemas — Zod validation for identity provider contracts
 *
 * Defines the formal contract between Frontend and Identity Provider.
 * All token responses must conform to these schemas.
 */
import { z } from 'zod';

/**
 * UserInfo schema — user identity attributes from IdP
 */
export const UserInfoSchema = z.object({
  id: z.string().min(1, 'User ID is required'),
  email: z.string().email('Valid email required'),
  role: z.enum(['standard', 'advanced', 'admin']).default('standard'),
  tenantId: z.string().min(1, 'Tenant ID is required'),
  tenantSlug: z.string().min(1, 'Tenant slug is required'),
});

export type UserInfo = z.infer<typeof UserInfoSchema>;

/**
 * TokenResponse schema — OAuth2/OIDC token exchange response
 *
 * This is the formal contract for the callback endpoint response.
 * All fields are validated to ensure type safety across the auth boundary.
 */
export const TokenResponseSchema = z.object({
  access_token: z.string().min(1, 'Access token is required'),
  refresh_token: z.string().optional(),
  expires_in: z.number().int().positive().optional().default(3600),
  token_type: z.string().transform(val => val.charAt(0).toUpperCase() + val.slice(1).toLowerCase()).default('Bearer'),
  user_id: z.string().min(1, 'User ID is required'),
  email: z.string().email('Valid email required'),
  role: z.enum(['standard', 'advanced', 'admin']).default('standard'),
});

export type TokenResponse = z.infer<typeof TokenResponseSchema>;

/**
 * LoginInitiationResponse schema — OIDC authorization URL response
 */
export const LoginInitiationResponseSchema = z.object({
  authorization_url: z.string().url('Valid authorization URL required'),
  state: z.string().min(1, 'State parameter is required'),
});

export type LoginInitiationResponse = z.infer<typeof LoginInitiationResponseSchema>;

/**
 * Auth error categories for deterministic error handling
 */
export enum AuthErrorCategory {
  NETWORK = 'NETWORK',
  AUTHENTICATION = 'AUTHENTICATION',
  MALFORMED_RESPONSE = 'MALFORMED_RESPONSE',
  SSO_PROVIDER_ERROR = 'SSO_PROVIDER_ERROR',
  SESSION_EXPIRED = 'SESSION_EXPIRED',
  VALIDATION = 'VALIDATION',
}

/**
 * Structured auth error with category for precise handling
 */
export class AuthError extends Error {
  public readonly category: AuthErrorCategory;
  public readonly statusCode?: number;

  constructor(
    message: string,
    category: AuthErrorCategory,
    statusCode?: number
  ) {
    super(message);
    this.name = 'AuthError';
    this.category = category;
    this.statusCode = statusCode;
  }
}

/**
 * Validate a token response against the schema
 * @throws AuthError with MALFORMED_RESPONSE category if validation fails
 */
export function validateTokenResponse(data: unknown): TokenResponse {
  const result = TokenResponseSchema.safeParse(data);
  if (!result.success) {
    throw new AuthError(
      `Invalid token response: ${result.error.message}`,
      AuthErrorCategory.MALFORMED_RESPONSE
    );
  }
  return result.data;
}

/**
 * Validate login initiation response
 * @throws AuthError with MALFORMED_RESPONSE category if validation fails
 */
export function validateLoginInitiationResponse(data: unknown): LoginInitiationResponse {
  const result = LoginInitiationResponseSchema.safeParse(data);
  if (!result.success) {
    throw new AuthError(
      `Invalid login initiation response: ${result.error.message}`,
      AuthErrorCategory.MALFORMED_RESPONSE
    );
  }
  return result.data;
}
