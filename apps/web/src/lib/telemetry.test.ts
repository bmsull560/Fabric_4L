import { describe, it, expect, vi, afterEach } from 'vitest';
import { createFeatureLogger } from './telemetry';

describe('createFeatureLogger', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('enriches log context with feature defaults', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const logger = createFeatureLogger('auth-session', {
      route: '/login',
      tenantId: 'tenant-1',
    });

    logger.error('Session restore failed', { authPhase: 'restore' });

    expect(errorSpy).toHaveBeenCalledWith(
      '[Fabric]',
      expect.stringContaining('[Fabric][auth-session] Session restore failed'),
      expect.objectContaining({
        feature: 'auth-session',
        route: '/login',
        tenantId: 'tenant-1',
        authPhase: 'restore',
      })
    );
  });
});
