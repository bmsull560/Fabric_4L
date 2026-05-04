/**
 * useAuth Hook Tests
 *
 * Comprehensive tests for authentication operations including:
 * - useAuth: Authentication state and CSRF header helper
 * - useRequireAuth: Protected route redirects
 * - useAuthRedirect: 401 handling
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper, createWrapperWithRouterPath } from '../test-utils';
import { useAuth, useRequireAuth, useAuthRedirect } from './useAuth';
import { useAuthContext, type UserInfo } from '../contexts/AuthContext';

// Mock react-router-dom at top level
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual as object,
    useNavigate: () => mockNavigate,
  };
});

// Mock the AuthContext
vi.mock('../contexts/AuthContext', async () => {
  const actual = await vi.importActual<typeof import('../contexts/AuthContext')>('../contexts/AuthContext');
  return {
    ...actual,
    useAuthContext: vi.fn(),
  };
});

const mockedUseAuthContext = vi.mocked(useAuthContext);

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('getCsrfHeaders', () => {
    it('returns X-CSRF-Token header when cookie is present', () => {
      mockedUseAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: null,
        accessToken: null,
        initiateLogin: vi.fn(),
        handleCallback: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      // Set the CSRF cookie
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'vf_csrf_token=test-csrf-abc123',
      });

      const wrapper = createWrapper();
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.getCsrfHeaders()).toEqual({
        'X-CSRF-Token': 'test-csrf-abc123',
      });

      // Restore
      Object.defineProperty(document, 'cookie', { writable: true, value: '' });
    });

    it('returns empty object when CSRF cookie is absent', () => {
      mockedUseAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        accessToken: null,
        initiateLogin: vi.fn(),
        handleCallback: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      Object.defineProperty(document, 'cookie', { writable: true, value: '' });

      const wrapper = createWrapper();
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.getCsrfHeaders()).toEqual({});
    });

    it('getAuthHeaders is no longer exposed — auth is cookie-based', () => {
      mockedUseAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        accessToken: null,
        initiateLogin: vi.fn(),
        handleCallback: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      const wrapper = createWrapper();
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect((result.current as Record<string, unknown>).getAuthHeaders).toBeUndefined();
    });
  });

  describe('auth state exposure', () => {
    it('exposes all auth context values', () => {
      const mockUser: UserInfo = {
        id: 'user-1',
        email: 'test@example.com',
        role: 'standard',
        tenantId: 'tenant-1',
        tenantSlug: 'test-tenant',
      };

      const mockLogout = vi.fn();
      const mockInitiateLogin = vi.fn();
      const mockHandleCallback = vi.fn();
      const mockRefreshToken = vi.fn();

      mockedUseAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: mockUser,
        accessToken: null,
        initiateLogin: mockInitiateLogin,
        handleCallback: mockHandleCallback,
        logout: mockLogout,
        refreshToken: mockRefreshToken,
      });

      const wrapper = createWrapper();
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.accessToken).toBeNull();
      expect(result.current.logout).toBe(mockLogout);
      expect(result.current.initiateLogin).toBe(mockInitiateLogin);
      expect(result.current.handleCallback).toBe(mockHandleCallback);
      expect(result.current.refreshToken).toBe(mockRefreshToken);
    });

    it('handles loading state', () => {
      mockedUseAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        accessToken: null,
        initiateLogin: vi.fn(),
        handleCallback: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      const wrapper = createWrapper();
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.isAuthenticated).toBe(false);
    });
  });
});

describe('useRequireAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('redirects to login when not authenticated and not loading', async () => {
    mockedUseAuthContext.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      accessToken: null,
      initiateLogin: vi.fn(),
      handleCallback: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    });

    const wrapper = createWrapperWithRouterPath('/protected');
    renderHook(() => useRequireAuth(), { wrapper });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login', undefined);
    });
  });

  it('does not redirect when authenticated', async () => {
    const mockUser: UserInfo = {
      id: 'user-1',
      email: 'test@example.com',
      role: 'standard',
      tenantId: 'tenant-1',
      tenantSlug: 'test-tenant',
    };

    mockedUseAuthContext.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: mockUser,
      accessToken: null,
      initiateLogin: vi.fn(),
      handleCallback: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    });

    const wrapper = createWrapperWithRouterPath('/protected');
    renderHook(() => useRequireAuth(), { wrapper });

    // Verify navigation is not triggered (with timeout for effect to run)
    await waitFor(() => expect(mockNavigate).not.toHaveBeenCalled(), {
      timeout: 100,
    });
  });

  it('does not redirect while auth state is loading', async () => {
    mockedUseAuthContext.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
      accessToken: null,
      initiateLogin: vi.fn(),
      handleCallback: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    });

    const wrapper = createWrapperWithRouterPath('/protected');
    renderHook(() => useRequireAuth(), { wrapper });

    // Verify navigation is not triggered while loading (with timeout for effect to run)
    await waitFor(() => expect(mockNavigate).not.toHaveBeenCalled(), {
      timeout: 100,
    });
  });

  it('waits for loading to complete before checking auth', async () => {
    const mockUser: UserInfo = {
      id: 'user-1',
      email: 'test@example.com',
      role: 'standard',
      tenantId: 'tenant-1',
      tenantSlug: 'test-tenant',
    };

    // Start with loading state
    mockedUseAuthContext.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
      accessToken: null,
      initiateLogin: vi.fn(),
      handleCallback: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    });

    const wrapper = createWrapperWithRouterPath('/protected');
    const { rerender } = renderHook(() => useRequireAuth(), { wrapper });

    // Initially should not redirect (still loading)
    expect(mockNavigate).not.toHaveBeenCalled();

    // Simulate auth state resolving to unauthenticated
    mockedUseAuthContext.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      accessToken: null,
      initiateLogin: vi.fn(),
      handleCallback: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    });

    rerender();

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login', undefined);
    });
  });
});

describe('useAuthRedirect', () => {
  const mockLogout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    mockLogout.mockClear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('handleUnauthorized clears auth and redirects to login', () => {
    mockedUseAuthContext.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: 'user-1', email: 'test@example.com', role: 'standard', tenantId: 't1', tenantSlug: 'tenant' },
      accessToken: null,
      initiateLogin: vi.fn(),
      handleCallback: vi.fn(),
      logout: mockLogout,
      refreshToken: vi.fn(),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useAuthRedirect(), { wrapper });

    result.current.handleUnauthorized();

    expect(mockLogout).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/login', undefined);
  });

  it('handleUnauthorized can be called multiple times', () => {
    mockedUseAuthContext.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: 'user-1', email: 'test@example.com', role: 'standard', tenantId: 't1', tenantSlug: 'tenant' },
      accessToken: null,
      initiateLogin: vi.fn(),
      handleCallback: vi.fn(),
      logout: mockLogout,
      refreshToken: vi.fn(),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useAuthRedirect(), { wrapper });

    result.current.handleUnauthorized();
    result.current.handleUnauthorized();
    result.current.handleUnauthorized();

    expect(mockLogout).toHaveBeenCalledTimes(3);
    expect(mockNavigate).toHaveBeenCalledTimes(3);
    expect(mockNavigate).toHaveBeenCalledWith('/login', undefined);
  });
});
