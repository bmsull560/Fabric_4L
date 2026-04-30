import { describe, it } from 'vitest';

/**
 * Contract tests: Governance / Admin / Settings (L4)
 */

describe('Contract: Governance Tenants', () => {
  it.todo('should expose GET /v1/tenants');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return array of tenants with id, name, slug, created_at, status');
  it.todo('should require admin or owner scope');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Governance Users', () => {
  it.todo('should expose GET /v1/users and POST /v1/users/invite');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return user list with id, email, role, tenant_id, created_at');
  it.todo('should require admin or owner scope for invite');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Governance API Keys', () => {
  it.todo('should expose GET /v1/api-keys and DELETE /v1/api-keys/{keyId}');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return API key list with id, name, prefix, created_at, last_used_at');
  it.todo('should mask full key value on list endpoint');
  it.todo('should require admin or owner scope');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Platform Settings', () => {
  it.todo('should expose GET /v1/tenant/settings and PATCH /v1/tenant/settings');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return settings shape: { tenant_name, features, integrations, notifications, branding }');
  it.todo('should reject invalid setting keys with 422');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});
