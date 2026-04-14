/**
 * useAuth Hook — Authentication Operations
 * 
 * Simplified interface for auth operations:
 * - Check authentication status
 * - Require auth (redirect if not authenticated)
 * - Get auth headers for API calls
 */

import { useEffect } from 'react';
import { useLocation } from 'wouter';
import { useAuthContext } from '../contexts/AuthContext';

export function useAuth() {
  const auth = useAuthContext();
  const [, navigate] = useLocation();

  /**
   * Redirect to login if not authenticated
   * Use this in protected route components
   */
  const requireAuth = () => {
    useEffect(() => {
      if (!auth.isLoading && !auth.isAuthenticated) {
        navigate('/login');
      }
    }, [auth.isLoading, auth.isAuthenticated, navigate]);
  };

  /**
   * Get authorization headers for API requests
   */
  const getAuthHeaders = () => {
    if (!auth.accessToken) return {};
    return {
      Authorization: `Bearer ${auth.accessToken}`,
    };
  };

  return {
    ...auth,
    requireAuth,
    getAuthHeaders,
  };
}

/**
 * Hook for handling 401 responses and redirecting to login
 */
export function useAuthRedirect() {
  const [, navigate] = useLocation();
  const { logout } = useAuthContext();

  const handleUnauthorized = () => {
    logout();
    navigate('/login');
  };

  return { handleUnauthorized };
}
