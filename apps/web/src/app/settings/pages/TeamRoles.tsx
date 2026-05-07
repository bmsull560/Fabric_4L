import PermissionsAdmin from "@/pages/admin/PermissionsAdmin";
import { CapabilityGate } from "../components/CapabilityGate";

export function TeamRoles() {
  return (
    <CapabilityGate capability="team">
      <PermissionsAdmin />
    </CapabilityGate>
  );
}
