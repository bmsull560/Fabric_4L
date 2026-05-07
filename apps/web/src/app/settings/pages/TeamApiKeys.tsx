import PermissionsAdmin from "@/pages/admin/PermissionsAdmin";
import { CapabilityGate } from "../components/CapabilityGate";

export function TeamApiKeys() {
  return (
    <CapabilityGate capability="team">
      <PermissionsAdmin />
    </CapabilityGate>
  );
}
