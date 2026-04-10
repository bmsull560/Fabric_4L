/**
 * User Tier Store — Role-based access control and progressive disclosure state
 * 
 * Manages:
 * - User tier/role (standard, advanced, admin)
 * - Advanced mode toggle state
 * - Route protection permissions
 * - Tier-specific feature flags
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type UserTier = 'standard' | 'advanced' | 'admin';

export interface UserPermissions {
  canAccessAdvanced: boolean;
  canAccessAdmin: boolean;
  canEditFormulas: boolean;
  canManageBenchmarks: boolean;
  canManageVariables: boolean;
  canManagePacks: boolean;
  canManageUsers: boolean;
}

export interface UserTierState {
  // Current tier
  currentTier: UserTier;
  
  // Advanced mode toggle (for standard users to temporarily access advanced features)
  isAdvancedModeEnabled: boolean;
  
  // User role from backend
  userRole: string | null;
  
  // Feature flags based on tier
  permissions: UserPermissions;
  
  // Actions
  setTier: (tier: UserTier) => void;
  setUserRole: (role: string) => void;
  toggleAdvancedMode: () => void;
  enableAdvancedMode: () => void;
  disableAdvancedMode: () => void;
  
  // Permission checks
  canAccessRoute: (routeTier: UserTier) => boolean;
  canAccessFeature: (feature: keyof UserPermissions) => boolean;
  
  // Computed
  effectiveTier: UserTier;
  isPrivileged: boolean;
}

// Default permissions by tier
const getDefaultPermissions = (tier: UserTier): UserPermissions => {
  const base: UserPermissions = {
    canAccessAdvanced: false,
    canAccessAdmin: false,
    canEditFormulas: false,
    canManageBenchmarks: false,
    canManageVariables: false,
    canManagePacks: false,
    canManageUsers: false,
  };

  switch (tier) {
    case 'standard':
      return base;
    case 'advanced':
      return {
        ...base,
        canAccessAdvanced: true,
        canEditFormulas: true,
      };
    case 'admin':
      return {
        canAccessAdvanced: true,
        canAccessAdmin: true,
        canEditFormulas: true,
        canManageBenchmarks: true,
        canManageVariables: true,
        canManagePacks: true,
        canManageUsers: true,
      };
  }
};

// Routes and their required tiers
const ROUTE_TIER_MAP: Record<string, UserTier> = {
  // Tier 1 (Standard) routes
  '/command-center': 'standard',
  '/value-packs': 'standard',
  '/agents': 'standard',
  '/agents/business-cases': 'standard',
  '/agents/dashboard': 'standard',
  '/research': 'standard',
  '/data-sources/targets': 'standard',
  '/data-sources/jobs': 'standard',
  '/audit': 'standard',
  '/audit/traces': 'standard',
  '/settings': 'standard',
  
  // Tier 2 (Advanced) routes
  '/extraction-engine': 'advanced',
  '/value-trees': 'advanced',
  '/value-trees/explorer': 'advanced',
  '/value-trees/normalization': 'advanced',
  '/value-trees/formulas': 'advanced',
  '/graph': 'advanced',
  '/graph/explorer': 'advanced',
  '/graph/query': 'advanced',
  '/graph/communities': 'advanced',
  '/ontology': 'advanced',
  '/ontology/entities': 'advanced',
  '/ontology/extractions': 'advanced',
  '/ontology/validation': 'advanced',
  '/audit/lineage': 'advanced',
  '/audit/reports': 'advanced',
  
  // Tier 3 (Admin) routes
  '/admin': 'admin',
  '/admin/formulas': 'admin',
  '/admin/formulas/versions': 'admin',
  '/admin/formulas/approvals': 'admin',
  '/admin/benchmarks': 'admin',
  '/admin/benchmarks/policies': 'admin',
  '/admin/variables': 'admin',
  '/admin/variables/bindings': 'admin',
  '/admin/packs': 'admin',
  '/admin/permissions': 'admin',
  '/admin/permissions/teams': 'admin',
};

export const useUserTierStore = create<UserTierState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentTier: 'standard',
      isAdvancedModeEnabled: false,
      userRole: null,
      permissions: getDefaultPermissions('standard'),

      // Actions
      setTier: (tier) => {
        set({ 
          currentTier: tier, 
          permissions: getDefaultPermissions(tier) 
        });
      },

      setUserRole: (role) => {
        set({ userRole: role });
        // Auto-set tier based on role
        const roleTierMap: Record<string, UserTier> = {
          'admin': 'admin',
          'editor': 'advanced',
          'analyst': 'advanced',
          'viewer': 'standard',
          'user': 'standard',
        };
        const tier = roleTierMap[role.toLowerCase()] || 'standard';
        set({ 
          currentTier: tier,
          permissions: getDefaultPermissions(tier)
        });
      },

      toggleAdvancedMode: () => {
        const newValue = !get().isAdvancedModeEnabled;
        set({ isAdvancedModeEnabled: newValue });
      },

      enableAdvancedMode: () => {
        set({ isAdvancedModeEnabled: true });
      },

      disableAdvancedMode: () => {
        set({ isAdvancedModeEnabled: false });
      },

      // Permission checks
      canAccessRoute: (routeTier) => {
        const { currentTier, isAdvancedModeEnabled } = get();
        
        // Admin can access everything
        if (currentTier === 'admin') return true;
        
        // Advanced users can access standard and advanced routes
        if (currentTier === 'advanced') {
          return routeTier === 'standard' || routeTier === 'advanced';
        }
        
        // Standard users can access standard routes
        // And advanced routes if advanced mode is enabled
        if (currentTier === 'standard') {
          if (routeTier === 'standard') return true;
          if (routeTier === 'advanced' && isAdvancedModeEnabled) return true;
          return false;
        }
        
        return false;
      },

      canAccessFeature: (feature) => {
        return get().permissions[feature];
      },

      // Computed properties
      get effectiveTier() {
        const { currentTier, isAdvancedModeEnabled } = get();
        if (currentTier === 'standard' && isAdvancedModeEnabled) {
          return 'advanced';
        }
        return currentTier;
      },

      get isPrivileged() {
        const tier = get().effectiveTier;
        return tier === 'advanced' || tier === 'admin';
      },
    }),
    {
      name: 'user-tier-storage',
      partialize: (state) => ({
        currentTier: state.currentTier,
        isAdvancedModeEnabled: state.isAdvancedModeEnabled,
        userRole: state.userRole,
      }),
    }
  )
);

// Helper function to check route access outside of components
export function getRouteTier(path: string): UserTier {
  // Exact match
  if (ROUTE_TIER_MAP[path]) {
    return ROUTE_TIER_MAP[path];
  }
  
  // Check parent routes
  for (const [route, tier] of Object.entries(ROUTE_TIER_MAP).sort((a, b) => b[0].length - a[0].length)) {
    if (path.startsWith(route + '/')) {
      return tier;
    }
  }
  
  // Default to standard
  return 'standard';
}

export default useUserTierStore;
