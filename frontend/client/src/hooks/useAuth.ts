/**
 * useAuth Hook — Authentication Operations
 * 
 * Simplified interface for auth operations:
 * - Check authentication status
 * - Get auth headers for API calls
 */

import { useAuthContext } from '../contexts/AuthContext';

export function useAuth() {
  const auth = useAuthContext();

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
    getAuthHeaders,
  };
}

/**
 * useRequireAuth Hook — Redirect to login if not authenticated
 * 
 * Use this in protected route components at the top level.
 * Must follow React Hooks rules (call at component top level, not conditionally).
 * 
 * Example:
 *   function ProtectedPage() {
 *     useRequireAuth();
 *     return <div>Protected content</div>;
 *   }
 */
import { useEffect } from 'react';
import { useLocation } from 'wouter';

export function useRequireAuth() {
  const { isLoading, isAuthenticated } = useAuthContext();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isLoading, isAuthenticated, navigate]);
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
