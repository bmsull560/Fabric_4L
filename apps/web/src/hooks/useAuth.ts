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
import { useNavigation } from '@/hooks/useNavigation';

export function useRequireAuth() {
  const { isLoading, isAuthenticated } = useAuthContext();
  const { navigateTo } = useNavigation();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigateTo('login');
    }
  }, [isLoading, isAuthenticated, navigateTo]);
}

/**
 * Hook for handling 401 responses and redirecting to login
 */
export function useAuthRedirect() {
  const { navigateTo } = useNavigation();
  const { logout } = useAuthContext();

  const handleUnauthorized = () => {
    logout();
    navigateTo('login');
  };

  return { handleUnauthorized };
}
