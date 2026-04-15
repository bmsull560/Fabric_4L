/**
 * Auth Context — OIDC Authentication State Management
 * 
 * Manages:
 * - JWT token storage (memory + localStorage for refresh)
 * - User info (id, email, role, tenant)
 * - Login/logout flows
 * - Token refresh
 * - 401 redirect handling
 */

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useUserTierStore } from '../stores/userTierStore';

export interface UserInfo {
  id: string;
  email: string;
  role: string;
  tenantId: string;
  tenantSlug: string;
}

interface AuthContextType {
  // State
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserInfo | null;
  accessToken: string | null;
  
  // Actions
  initiateLogin: (tenantSlug: string) => Promise<void>;
  handleCallback: (code: string, state: string) => Promise<boolean>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  devBypass?: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Constants
const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';
const L4_PREFIX = import.meta.env.VITE_L4_PREFIX || '/agents';
const TOKEN_EXPIRY_BUFFER_MS = 60_000; // 1 minute buffer before actual expiry

/**
 * Validate JWT structure without verifying signature.
 * Checks that token has 3 parts (header.payload.signature) and parsable JSON.
 */
function isValidJwtStructure(token: string): boolean {
  const parts = token.split('.');
  if (parts.length !== 3) return false;
  
  try {
    // Try to parse header and payload as base64url
    atob(parts[0].replace(/-/g, '+').replace(/_/g, '/'));
    atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'));
    return true;
  } catch {
    return false;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  // Initialize auth state from storage on mount
  useEffect(() => {
    const initAuth = () => {
      const storedToken = localStorage.getItem('accessToken');
      const storedUser = localStorage.getItem('userInfo');
      
      if (storedToken && storedUser) {
        try {
          const userInfo = JSON.parse(storedUser) as UserInfo;
          setAccessToken(storedToken);
          setUser(userInfo);
          setIsAuthenticated(true);
          
          // Synchronize restored role with userTierStore
          useUserTierStore.getState().setUserRole(userInfo.role);
        } catch (e) {
          // Invalid stored data, clear it
          localStorage.removeItem('accessToken');
          localStorage.removeItem('userInfo');
        }
      }
      
      setIsLoading(false);
    };
    
    initAuth();
  }, []);

  /**
   * Step 1: Initiate OIDC login flow
   * Calls backend to get authorization URL, then redirects browser to IdP
   */
  const initiateLogin = useCallback(async (tenantSlug: string) => {
    setIsLoading(true);
    try {
      // Build callback URL (must match backend redirect_uri)
      const callbackUrl = `${window.location.origin}/login/callback`;
      
      // Call backend to initiate OIDC flow
      const response = await fetch(
        `${API_BASE}${L4_PREFIX}/auth/oidc/${tenantSlug}/login?redirect_uri=${encodeURIComponent(callbackUrl)}`
      );
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to initiate login');
      }
      
      const { authorization_url, state } = await response.json();
      
      // Store state for verification on callback
      sessionStorage.setItem('oidcState', state);
      sessionStorage.setItem('oidcTenantSlug', tenantSlug);
      
      // Redirect to IdP
      window.location.href = authorization_url;
    } catch (error) {
      console.error('Login initiation failed:', error);
      setIsLoading(false);
      throw error;
    }
  }, []);

  /**
   * Step 2: Handle OIDC callback
   * Backend exchanges code for tokens and returns JWT
   */
  const handleCallback = useCallback(async (code: string, state: string): Promise<boolean> => {
    try {
      // Verify state matches what we stored
      const storedState = sessionStorage.getItem('oidcState');
      if (state !== storedState) {
        throw new Error('Invalid state parameter');
      }
      
      // Call backend callback endpoint
      const response = await fetch(
        `${API_BASE}${L4_PREFIX}/auth/oidc/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
      );
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Authentication failed');
      }
      
      const data = await response.json();
      const { access_token, user_id, email, role } = data;
      const tenantSlug = sessionStorage.getItem('oidcTenantSlug') || 'default';
      
      // Build user info
      const userInfo: UserInfo = {
        id: user_id,
        email,
        role,
        tenantId: tenantSlug, // Backend uses slug as tenant identifier
        tenantSlug,
      };
      
      // Store auth data
      setAccessToken(access_token);
      setUser(userInfo);
      setIsAuthenticated(true);
      
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('userInfo', JSON.stringify(userInfo));
      localStorage.setItem('tenantId', tenantSlug);

      // Synchronize role with userTierStore so tier/permissions reflect the OIDC role
      useUserTierStore.getState().setUserRole(role);
      
      // Clean up session storage
      sessionStorage.removeItem('oidcState');
      sessionStorage.removeItem('oidcTenantSlug');
      
      return true;
    } catch (error) {
      console.error('Callback handling failed:', error);
      // Clean up on failure
      sessionStorage.removeItem('oidcState');
      sessionStorage.removeItem('oidcTenantSlug');
      return false;
    }
  }, []);

  /**
   * Logout — clear all auth state
   */
  const logout = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    setIsAuthenticated(false);
    
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userInfo');
    localStorage.removeItem('tenantId');
    sessionStorage.removeItem('oidcState');
    sessionStorage.removeItem('oidcTenantSlug');

    // Reset userTierStore to default state
    const tierStore = useUserTierStore.getState();
    tierStore.setTier('standard');
    tierStore.disableAdvancedMode();
    
    // Redirect to login
    window.location.href = '/login';
  }, []);

  /**
   * Token refresh — placeholder for future refresh token implementation
   */
  const refreshToken = useCallback(async (): Promise<boolean> => {
    // Currently tokens are 1-hour JWTs. In future, implement refresh token flow.
    // For now, just check if token is still valid
    const token = localStorage.getItem('accessToken');
    if (!token) return false;
    
    // Validate JWT structure first
    if (!isValidJwtStructure(token)) {
      console.error('Invalid token structure');
      logout();
      return false;
    }
    
    // Check expiry (JWTs have exp claim)
    try {
      // base64url decode with proper padding
      const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      const padding = '='.repeat((4 - base64.length % 4) % 4);
      const payload = JSON.parse(atob(base64 + padding));
      
      const exp = payload.exp * 1000; // Convert to milliseconds
      if (Date.now() >= exp - TOKEN_EXPIRY_BUFFER_MS) {
        // Token expired or expiring soon, logout
        logout();
        return false;
      }
      return true;
    } catch (e) {
      console.error('Failed to parse token payload:', e);
      logout();
      return false;
    }
  }, [logout]);

  /**
   * Development bypass — creates mock auth state without credentials
   * Only available in development mode
   */
  const devBypass = useCallback(() => {
    if (!import.meta.env.DEV) {
      console.warn('devBypass only available in development mode');
      return;
    }
    
    const mockUser: UserInfo = {
      id: 'dev-user-001',
      email: 'dev@value-fabric.com',
      role: 'admin',
      tenantId: 'dev-tenant',
      tenantSlug: 'development',
    };
    
    // Create a mock JWT token (valid structure but not verified)
    const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' +
      btoa(JSON.stringify({ 
        sub: mockUser.id, 
        email: mockUser.email, 
        role: mockUser.role,
        exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour expiry
      })) + 
      '.mock-signature';
    
    setAccessToken(mockToken);
    setUser(mockUser);
    setIsAuthenticated(true);
    
    localStorage.setItem('accessToken', mockToken);
    localStorage.setItem('userInfo', JSON.stringify(mockUser));
    localStorage.setItem('tenantId', mockUser.tenantSlug);
    
    useUserTierStore.getState().setUserRole(mockUser.role);
    
    console.log('[DEV] Authentication bypassed — logged in as', mockUser.email);
  }, []);

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    user,
    accessToken,
    initiateLogin,
    handleCallback,
    logout,
    refreshToken,
    devBypass: import.meta.env.DEV ? devBypass : undefined,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}
