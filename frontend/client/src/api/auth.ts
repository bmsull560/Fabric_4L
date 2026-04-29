import { z } from 'zod';
import { apiClient } from './client';
import { AllRoles } from '../schemas/auth';

const RegisterRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

const RegisterResponseSchema = z.object({
  message: z.string().optional(),
  access_token: z.string().min(1).optional(),
  token_type: z.string().optional(),
  expires_in: z.number().int().positive().optional(),
  refresh_token: z.string().optional(),
  user_id: z.string().optional(),
  email: z.string().email().optional(),
  role: z.enum(AllRoles).optional(),
  tenant_id: z.string().optional(),
  tenant_slug: z.string().optional(),
});

export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;
export type RegisterResponse = z.infer<typeof RegisterResponseSchema>;

export async function registerWithEmailPassword(payload: RegisterRequest): Promise<RegisterResponse> {
  const request = RegisterRequestSchema.parse(payload);
  const response = await apiClient.post('l4', '/auth/register', request) as { data: unknown };
  return RegisterResponseSchema.parse(response.data);
}
