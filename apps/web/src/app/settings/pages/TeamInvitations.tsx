import PermissionsAdmin from "@/pages/admin/PermissionsAdmin";
import { CapabilityGate } from "../components/CapabilityGate";

export function TeamInvitations() {
  return (
    <CapabilityGate capability="team">
      <PermissionsAdmin />
    </CapabilityGate>
  );
}
