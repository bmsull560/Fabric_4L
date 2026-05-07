import { useMemo } from "react";
import { useAuthContext } from "@/contexts/AuthContext";

export type SettingsCapability =
  | "personal"
  | "billing"
  | "team"
  | "integrations"
  | "governance"
  | "super_admin";

const ROLE_CAPABILITIES: Record<string, SettingsCapability[]> = {
  super_admin: [
    "personal",
    "billing",
    "team",
    "integrations",
    "governance",
    "super_admin",
  ],
  tenant_admin: ["personal", "billing", "team", "integrations", "governance"],
  content_admin: ["personal", "governance"],
  analyst: ["personal"],
  read_only: ["personal"],
  admin: ["personal", "billing", "team", "integrations", "governance"],
  advanced: ["personal"],
  standard: ["personal"],
  viewer: ["personal"],
  user: ["personal"],
};

function normalizeRole(role: string | null | undefined): string {
  return role?.trim().toLowerCase() || "user";
}

export function getCapabilitiesForRole(role: string | null | undefined): Set<SettingsCapability> {
  const normalizedRole = normalizeRole(role);
  return new Set(ROLE_CAPABILITIES[normalizedRole] ?? ["personal"]);
}

export function hasSettingsCapability(
  role: string | null | undefined,
  capability: SettingsCapability
): boolean {
  return getCapabilitiesForRole(role).has(capability);
}

export function useSettingsAccess() {
  const { user } = useAuthContext();

  return useMemo(() => {
    const role = normalizeRole(user?.role);
    const capabilities = getCapabilitiesForRole(role);

    return {
      role,
      capabilities,
      hasCapability: (capability: SettingsCapability) => capabilities.has(capability),
    };
  }, [user?.role]);
}
