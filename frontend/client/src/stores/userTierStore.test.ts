import { describe, it, expect, vi, beforeEach } from 'vitest';
import { waitFor } from '@testing-library/react';
import { renderHook, act } from "@testing-library/react";
import { useUserTierStore, getRouteTier, type UserTier } from "./userTierStore";

describe("useUserTierStore", () => {
  beforeEach(() => {
    // Clear localStorage to reset persisted state
    localStorage.clear();

    // Reset store to initial state - use setTier to properly reset permissions
    const { result } = renderHook(() => useUserTierStore());
    act(() => {
      result.current.setTier("standard");
      result.current.disableAdvancedMode();
      // Note: setUserRole with empty string triggers tier reset, so we skip it
      // The store will reset role to null when tier is set to standard
    });
  });

  describe("initial state", () => {
    it("should start with standard tier", () => {
      const { result } = renderHook(() => useUserTierStore());

      expect(result.current.currentTier).toBe("standard");
    });

    it("should have advanced mode disabled initially", () => {
      const { result } = renderHook(() => useUserTierStore());

      expect(result.current.isAdvancedModeEnabled).toBe(false);
    });

    it("should have no user role initially", () => {
      const { result } = renderHook(() => useUserTierStore());

      expect(result.current.userRole).toBeNull();
    });

    it("should have standard permissions initially", () => {
      const { result } = renderHook(() => useUserTierStore());

      expect(result.current.permissions.canAccessAdmin).toBe(false);
      expect(result.current.permissions.canAccessAdvanced).toBe(false);
      expect(result.current.permissions.canEditFormulas).toBe(false);
    });
  });

  describe("setTier", () => {
    it("should set tier to advanced", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("advanced"));

      expect(result.current.currentTier).toBe("advanced");
      expect(result.current.permissions.canAccessAdvanced).toBe(true);
      expect(result.current.permissions.canEditFormulas).toBe(true);
    });

    it("should set tier to admin", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("admin"));

      expect(result.current.currentTier).toBe("admin");
      expect(result.current.permissions.canAccessAdmin).toBe(true);
      expect(result.current.permissions.canManageUsers).toBe(true);
    });

    it("should set tier back to standard", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("advanced"));
      act(() => result.current.setTier("standard"));

      expect(result.current.currentTier).toBe("standard");
      expect(result.current.permissions.canAccessAdvanced).toBe(false);
    });

    it("should update permissions when tier changes", () => {
      const { result } = renderHook(() => useUserTierStore());

      const tiers: UserTier[] = ["standard", "advanced", "admin", "standard"];
      const expectedPermissions = [
        { canAccessAdvanced: false, canManageUsers: false },
        { canAccessAdvanced: true, canManageUsers: false },
        { canAccessAdvanced: true, canManageUsers: true },
        { canAccessAdvanced: false, canManageUsers: false },
      ];

      tiers.forEach((tier, index) => {
        act(() => result.current.setTier(tier));
        expect(result.current.permissions.canAccessAdvanced).toBe(
          expectedPermissions[index].canAccessAdvanced
        );
        expect(result.current.permissions.canManageUsers).toBe(
          expectedPermissions[index].canManageUsers
        );
      });
    });
  });

  describe("setUserRole", () => {
    it("should set user role", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setUserRole("admin"));

      expect(result.current.userRole).toBe("admin");
    });

    it("should auto-set tier to admin for admin role", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setUserRole("admin"));

      expect(result.current.currentTier).toBe("admin");
    });

    it("should auto-set tier to advanced for editor role", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setUserRole("editor"));

      expect(result.current.currentTier).toBe("advanced");
    });

    it("should auto-set tier to advanced for analyst role", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setUserRole("analyst"));

      expect(result.current.currentTier).toBe("advanced");
    });

    it("should default to standard for unknown role", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setUserRole("unknown"));

      expect(result.current.currentTier).toBe("standard");
    });

    it("should handle role case insensitively", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setUserRole("ADMIN"));

      expect(result.current.currentTier).toBe("admin");
    });
  });

  describe("advanced mode toggle", () => {
    it("should toggle advanced mode", () => {
      const { result } = renderHook(() => useUserTierStore());

      expect(result.current.isAdvancedModeEnabled).toBe(false);

      act(() => result.current.toggleAdvancedMode());

      expect(result.current.isAdvancedModeEnabled).toBe(true);

      act(() => result.current.toggleAdvancedMode());

      expect(result.current.isAdvancedModeEnabled).toBe(false);
    });

    it("should enable advanced mode", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.enableAdvancedMode());

      expect(result.current.isAdvancedModeEnabled).toBe(true);
    });

    it("should disable advanced mode", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.enableAdvancedMode());
      act(() => result.current.disableAdvancedMode());

      expect(result.current.isAdvancedModeEnabled).toBe(false);
    });
  });

  describe("canAccessRoute", () => {
    it("should allow admin to access all route tiers", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("admin"));

      expect(result.current.canAccessRoute("standard")).toBe(true);
      expect(result.current.canAccessRoute("advanced")).toBe(true);
      expect(result.current.canAccessRoute("admin")).toBe(true);
    });

    it("should allow advanced user to access standard and advanced routes", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("advanced"));

      expect(result.current.canAccessRoute("standard")).toBe(true);
      expect(result.current.canAccessRoute("advanced")).toBe(true);
      expect(result.current.canAccessRoute("admin")).toBe(false);
    });

    it("should allow standard user to access only standard routes", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("standard"));

      expect(result.current.canAccessRoute("standard")).toBe(true);
      expect(result.current.canAccessRoute("advanced")).toBe(false);
      expect(result.current.canAccessRoute("admin")).toBe(false);
    });

    it("should allow standard user with advanced mode to access advanced routes", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("standard"));
      act(() => result.current.enableAdvancedMode());

      expect(result.current.canAccessRoute("standard")).toBe(true);
      expect(result.current.canAccessRoute("advanced")).toBe(true);
      expect(result.current.canAccessRoute("admin")).toBe(false);
    });
  });

  describe("canAccessFeature", () => {
    it("should check feature permissions for standard tier", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("standard"));

      expect(result.current.canAccessFeature("canAccessAdvanced")).toBe(false);
      expect(result.current.canAccessFeature("canAccessAdmin")).toBe(false);
    });

    it("should check feature permissions for advanced tier", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("advanced"));

      expect(result.current.canAccessFeature("canAccessAdvanced")).toBe(true);
      expect(result.current.canAccessFeature("canEditFormulas")).toBe(true);
      expect(result.current.canAccessFeature("canAccessAdmin")).toBe(false);
    });

    it("should check feature permissions for admin tier", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("admin"));

      expect(result.current.canAccessFeature("canAccessAdmin")).toBe(true);
      expect(result.current.canAccessFeature("canManageUsers")).toBe(true);
      expect(result.current.canAccessFeature("canManagePacks")).toBe(true);
    });
  });

  describe("computed properties via behavior", () => {
    // Note: Zustand getters (effectiveTier, isPrivileged) don't trigger React re-renders
    // when their dependencies change. We test the actual behavior through canAccessRoute
    // which internally uses the same effectiveTier logic.

    it("effectiveTier works - standard user can access advanced routes with advanced mode enabled", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("standard"));
      act(() => result.current.disableAdvancedMode());

      // Without advanced mode, standard user cannot access advanced routes
      expect(result.current.canAccessRoute("advanced")).toBe(false);

      act(() => result.current.enableAdvancedMode());

      // With advanced mode, effectiveTier becomes 'advanced', allowing access
      expect(result.current.canAccessRoute("advanced")).toBe(true);
    });

    it("isPrivileged works - tier-based privileges are enforced", () => {
      const { result } = renderHook(() => useUserTierStore());

      // Standard user is not privileged
      act(() => result.current.setTier("standard"));
      act(() => result.current.disableAdvancedMode());
      expect(result.current.canAccessFeature("canAccessAdvanced")).toBe(false);

      // Advanced user is privileged (can access advanced features)
      act(() => result.current.setTier("advanced"));
      expect(result.current.canAccessFeature("canAccessAdvanced")).toBe(true);

      // Admin user is fully privileged
      act(() => result.current.setTier("admin"));
      expect(result.current.canAccessFeature("canAccessAdmin")).toBe(true);
      expect(result.current.canAccessFeature("canManageUsers")).toBe(true);
    });

    it("standard user with advanced mode gains privileged access", () => {
      const { result } = renderHook(() => useUserTierStore());

      act(() => result.current.setTier("standard"));
      act(() => result.current.disableAdvancedMode());

      // Standard user without advanced mode - no advanced access
      expect(result.current.canAccessRoute("advanced")).toBe(false);
      expect(result.current.canAccessFeature("canEditFormulas")).toBe(false);

      // Enable advanced mode
      act(() => result.current.enableAdvancedMode());

      // Now has advanced access via effectiveTier logic
      expect(result.current.canAccessRoute("advanced")).toBe(true);
    });
  });
});

describe("getRouteTier helper", () => {
  it("should return tier for exact route matches", () => {
    expect(getRouteTier("/command-center")).toBe("standard");
    expect(getRouteTier("/extraction-engine")).toBe("advanced");
    expect(getRouteTier("/admin")).toBe("admin");
  });

  it("should return tier for nested routes", () => {
    expect(getRouteTier("/command-center/dashboard")).toBe("standard");
    expect(getRouteTier("/graph/explorer/nodes")).toBe("advanced");
    expect(getRouteTier("/admin/formulas/versions")).toBe("admin");
  });

  it("should default to standard for unknown routes", () => {
    expect(getRouteTier("/unknown-route")).toBe("standard");
    expect(getRouteTier("/new-feature")).toBe("standard");
  });

  it("should handle root route", () => {
    expect(getRouteTier("/")).toBe("standard");
  });
});
