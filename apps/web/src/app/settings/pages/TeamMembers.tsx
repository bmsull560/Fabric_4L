import PermissionsAdmin from "@/pages/admin/PermissionsAdmin";
import { CapabilityGate } from "../components/CapabilityGate";

export function TeamMembers() {
  return (
    <CapabilityGate capability="team">
      <PermissionsAdmin />
    </CapabilityGate>
  );
}
