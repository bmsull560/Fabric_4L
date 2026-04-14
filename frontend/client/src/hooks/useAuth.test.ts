/**
 * useAuth Hook Tests
 *
 * Comprehensive tests for authentication operations including:
 * - useAuth: Authentication state and header generation
 * - useRequireAuth: Protected route redirects
 * - useAuthRedirect: 401 handling
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper, createWrapperWithRouterPath } from '../test-utils';
import { useAuth, useRequireAuth, useAuthRedirect } from './useAuth';
import { useAuthContext, type UserInfo } from '../contexts/AuthContext';

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

  describe('getAuthHeaders', () => {
    it('returns Authorization header when accessToken exists', () => {
      const mockUser: UserInfo = {
        id: 'user-1',
        email: 'test@example.com',
        role: 'admin',
        tenantId: 'tenant-1',
        tenantSlug: 'test-tenant',
      };

      mockedUseAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: mockUser,
        accessToken: 'test-token-123',
        initiateLogin: vi.fn(),
        handleCallback: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      const wrapper = createWrapper();
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.getAuthHeaders()).toEqual({
        Authorization: 'Bearer test-token-123',
      });
    });

    it('returns empty object when accessToken is null', () => {
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

      expect(result.current.getAuthHeaders()).toEqual({});
    });

    it('returns empty object when accessToken is empty string', () => {
      mockedUseAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        accessToken: '',
        initiateLogin: vi.fn(),
        handleCallback: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      const wrapper = createWrapper();
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.getAuthHeaders()).toEqual({});
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
        accessToken: 'token-123',
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
      expect(result.current.accessToken).toBe('token-123');
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
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    // Mock wouter's useLocation
    vi.mock('wouter', async () => {
      const actual = await vi.importActual('wouter');
      return {
        ...actual,
        useLocation: () => ['/protected', mockNavigate],
      };
    });
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
      expect(mockNavigate).toHaveBeenCalledWith('/login');
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
      accessToken: 'token-123',
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
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });
});

describe('useAuthRedirect', () => {
  const mockNavigate = vi.fn();
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
      accessToken: 'token-123',
      initiateLogin: vi.fn(),
      handleCallback: vi.fn(),
      logout: mockLogout,
      refreshToken: vi.fn(),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useAuthRedirect(), { wrapper });

    result.current.handleUnauthorized();

    expect(mockLogout).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('handleUnauthorized can be called multiple times', () => {
    mockedUseAuthContext.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: 'user-1', email: 'test@example.com', role: 'standard', tenantId: 't1', tenantSlug: 'tenant' },
      accessToken: 'token-123',
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
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });
});
