import HealthMonitor from "@/pages/admin/HealthMonitor";
import { CapabilityGate } from "../components/CapabilityGate";

export function GovernanceHealth() {
  return (
    <CapabilityGate capability="governance">
      <HealthMonitor />
    </CapabilityGate>
  );
}
